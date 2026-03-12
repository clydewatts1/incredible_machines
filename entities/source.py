"""
M23: DataSource Entity

Stationary ingestion node that pulls data from external sources (CSV, MCP)
and packages it into physics payloads. Implements safe asynchronous fetching
with background worker threads and thread-safe queue handoff.

Thread Safety: All network/file I/O occurs in background threads. Results
are passed to the main Pygame thread via queue.Queue(). The _is_destroyed
flag prevents ghost threads from queuing stale results after deletion.
"""

import copy
import math
import queue
import threading
import time
from typing import Optional, Dict, Any, List

import pygame
import pymunk

from entities.base import GamePart
from utils.generators import get_generator, GeneratorExhausted
import constants
from utils.asset_manager import asset_manager


class FloatingTextLabel:
    """
    Lightweight floating label for diagnostic messages (e.g., errors).
    Floats upward and disappears after FLOATING_LABEL_TIMEOUT_SECONDS.
    Reuses M18/M22 pattern.
    """
    
    def __init__(self, x: float, y: float, text: str):
        self.x = x
        self.y = y
        self.text = text
        self.birth_time = pygame.time.get_ticks() / 1000.0
        self.font = pygame.font.Font(None, 24)
        self.surface = self.font.render(text, True, (255, 0, 0))
        self.uuid = f"label_{id(self)}"
        self.to_delete = False
    
    def update(self, dt: float):
        """Update position (float upward) and lifetime."""
        self.y -= constants.FLOATING_LABEL_RISE_SPEED * dt
        
        age = pygame.time.get_ticks() / 1000.0 - self.birth_time
        if age > constants.FLOATING_TIMEOUT_SECONDS:
            self.to_delete = True
    
    def draw(self, surface, camera=None):
        """Draw label at current position."""
        if not self.to_delete:
            # Apply camera offset if provided
            if camera:
                screen_x, screen_y = camera.world_to_screen(self.x, self.y)
            else:
                screen_x, screen_y = self.x, self.y
            
            surface.blit(self.surface, (screen_x - self.surface.get_width() // 2, screen_y))
    
    def update_visual(self, surface, camera=None):
        """Wrapper for main render loop compatibility."""
        self.draw(surface, camera)


class DataSource(GamePart):
    """
    M23 Data Source entity.
    
    Pulls data from external sources (CSV, MCP) via background worker threads,
    packages payloads, and spawns physics projectiles.
    
    State Machine: OFF → INITIALIZING → IDLE → POLLING → EMITTING → IDLE (repeat)
                   or EXHAUSTED (source empty) or FATAL (error)
    """
    
    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "data_source"):
        """
        Initialize DataSource entity.
        
        Args:
            space: Pymunk physics space.
            x, y: World position.
            variant_name: YAML variant name (e.g., "data_source_csv", "data_source_mcp").
        """
        super().__init__(space, x, y, variant_name)
        
        # Thread-safe queue for generator results
        self.queue = queue.Queue()
        
        # Lifecycle state
        self.visual_state = "OFF"
        self._is_destroyed = False
        
        # Timing
        self.next_emit_time = time.time()
        self.emit_interval = float(self.get_property("emit_interval", 2.0))
        
        # Generator engine
        self.engine = None
        self.engine_type = self.get_property("engine_type", "null")
        self.instructions = self.get_property("instructions", {})
        
        # Current fetch state
        self.current_worker_thread = None
        
        # Animation & sound
        self._animation_textures = {}
        self._load_animation_textures()

    def _debug_enabled(self) -> bool:
        return bool(self.instructions.get("debug", False))

    def _debug_log(self, message: str):
        if self._debug_enabled():
            print(f"[DataSource:{self.variant_key}:{self.uuid[:8]}] {message}")
    
    def _load_animation_textures(self):
        """
        Load state-specific texture images from assets/sprites.
        Uses asset_manager to handle missing files gracefully.
        """
        animations = self.get_property("animations", {})
        if not isinstance(animations, dict):
            return
        
        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        
        for state_name, sprite_name in animations.items():
            sprite_rel = f"assets/sprites/{sprite_name}.png"
            try:
                self._animation_textures[state_name] = asset_manager.get_image(
                    sprite_rel,
                    fallback_size=(width, height),
                    text_label=f"DataSource:{state_name}",
                )
            except Exception:
                # Silent fail: missing animation texture is non-fatal
                pass
    
    def _set_state(self, new_state: str):
        """
        Transition to a new state.
        Updates visual_state and triggers audio/animation updates.
        
        Args:
            new_state: One of OFF, INITIALIZING, IDLE, POLLING, EMITTING, EXHAUSTED, FATAL.
        """
        old_state = self.visual_state
        self.visual_state = new_state
        self._debug_log(f"State change: {old_state} -> {new_state}")
        
        # Play state transition sound (if configured)
        sounds = self.get_property("sounds", {})
        sound_file = sounds.get(new_state)
        
        if sound_file:
            try:
                # Use game's sound manager (M6 integration)
                from utils.sound_manager import sound_manager
                sound_manager.play_sound(sound_file)
            except Exception:
                # Silent fail: missing sound file is non-fatal
                pass
    
    def _initialize_engine(self):
        """
        Create the generator engine instance.
        Called once when DataSource enters INITIALIZING state.
        """
        self._set_state("INITIALIZING")
        try:
            self._debug_log(f"Initializing engine type={self.engine_type} with instructions={self.instructions}")
            self.engine = get_generator(self.engine_type, self.instructions)
            self._debug_log(f"Engine initialized: {type(self.engine).__name__}")
        except Exception as e:
            # Engine initialization failure → FATAL
            self._set_state("FATAL")
            self._debug_log(f"Engine initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize {self.engine_type} engine: {e}") from e
    
    def _start_worker(self):
        """
        Start a background thread to fetch the next data item from the generator.
        The worker thread checks _is_destroyed before queuing results.
        """
        def _worker():
            try:
                # Fetch from generator (may block on I/O)
                self._debug_log("Worker started fetch_next()")
                data = self.engine.fetch_next(self.instructions)
            except GeneratorExhausted:
                # Source exhausted (CSV EOF with loop=false)
                data = None
                error = None
                exhausted = True
                self._debug_log("Worker marked source exhausted")
            except Exception as exc:
                # Wrap error for main thread to handle
                data = None
                error = str(exc)
                exhausted = False
                self._debug_log(f"Worker captured error: {error}")
            else:
                error = None
                exhausted = False
                self._debug_log(f"Worker fetched data: keys={list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
            
            # Guard: if DataSource was destroyed, silently discard result
            if not self._is_destroyed:
                self.queue.put({"data": data, "error": error, "exhausted": exhausted})
                self._debug_log(f"Worker queued result: exhausted={exhausted}, has_error={bool(error)}, has_data={data is not None}")
        
        self.current_worker_thread = threading.Thread(target=_worker, daemon=True)
        self.current_worker_thread.start()
        self._debug_log(f"Spawned worker thread: {self.current_worker_thread.name}")
    
    def cleanup(self):
        """
        Gracefully shutdown the DataSource and clean up generator resources.
        Called when user deletes the entity or game unloads.
        
        This is CRITICAL for safe cleanup: set _is_destroyed immediately to prevent
        any pending worker threads from queuing stale results.
        """
        self._is_destroyed = True
        
        # Drain any pending queue results to prevent dangling references
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        
        # Shutdown generator (close files, MCP sessions, etc.)
        if self.engine:
            try:
                self.engine.cleanup()
            except Exception:
                pass
    
    def destroy(self):
        """Alias for cleanup; called by physics deletion."""
        self.cleanup()
    
    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        """
        Poll the background fetch queue and handle results.
        Called once per frame from main loop.
        
        This is where:
        - Success paths spawn balls with payloads.
        - Empty signals return to IDLE.
        - Error paths transition to FATAL.
        
        Args:
            entities: World entity list (may append spawned balls or labels).
            active_instances: UUID -> entity map (register new entities).
        """
        # If destroyed, drain queue without processing
        if self._is_destroyed:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            return
        
        # Process up to MAX_BATCH_QUEUE_POLLS results per frame
        polls = 0
        while not self.queue.empty() and polls < constants.MAX_BATCH_QUEUE_POLLS:
            result_data = self.queue.get()
            polls += 1
            
            error = result_data.get("error")
            data = result_data.get("data")
            exhausted = result_data.get("exhausted", False)
            self._debug_log(f"Processing queue result: exhausted={exhausted}, error={error}, has_data={data is not None}")
            
            # Error path: network timeout, JSON parse, file error, etc.
            if error:
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, f"fatal: {error}")
                self._debug_log(f"Entered FATAL due to error: {error}")
                continue
            
            # Exhausted path: CSV EOF with loop=false
            if exhausted:
                self._set_state("EXHAUSTED")
                self._debug_log("Entered EXHAUSTED state")
                continue
            
            # Empty signal: MCP returned {"status": "empty"} (not an error)
            if data is None:
                self._set_state("IDLE")
                self._debug_log("Received empty result; returning to IDLE")
                continue
            
            # Success: construct payload and emit ball
            payload = self._construct_payload(data)
            self._debug_log(f"Constructed payload with data keys={list(data.keys()) if isinstance(data, dict) else []}")
            self._emit_ball(payload, entities, active_instances)
    
    def _construct_payload(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the full payload dict from raw generator data.
        
        Payload MUST include:
        - data: Raw fetched content
        - score: 100 (initialization)
        - cost: Default energy value
        - start_time: Current timestamp
        - routing_depth: 0
        - ttl: Time-to-live hops
        - drop_dead_age: Age threshold for floating
        - processing_history: List of processor history
        
        Args:
            raw_data: Data dict from generator (CSV row, MCP response, etc.).
        
        Returns:
            dict: Complete payload ready for physics emission.
        """
        now_secs = time.time()
        
        payload = {
            "data": raw_data,
            "score": constants.DEFAULT_PAYLOAD_SCORE,  # 100
            "cost": constants.DEFAULT_PAYLOAD_COST,  # 100
            "start_time": now_secs,
            "routing_depth": 0,
            "ttl": constants.DEFAULT_PAYLOAD_TTL,  # 50
            "drop_dead_age": constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE,  # 10.0
            "processing_history": [],
        }
        
        return payload
    
    def _compute_emission_velocity(self) -> tuple:
        """
        Compute world-space velocity (vx, vy) from exit_velocity, exit_angle, and active_side.
        
        Angle Reference Frame:
        - 0° points right (east)
        - 90° points up (north)
        - 180° points left (west)
        - 270° points down (south)
        
        Per-Side Adjustments:
        - Top: Y-axis, offset = 90°
        - Bottom: Y-axis, offset = 270°
        - Left: X-axis, offset = 180°
        - Right: X-axis, offset = 0°
        
        Returns:
            (vx, vy): Velocity vector in pixels/sec.
        """
        exit_velocity = float(self.get_property("exit_velocity", 150.0))
        exit_angle_deg = float(self.get_property("exit_angle", 0.0))
        active_side = self.get_property("active_side", "Bottom")
        
        # Compute global angle offset per active_side
        if active_side == "Top":
            angle_offset = 90.0
        elif active_side == "Bottom":
            angle_offset = 270.0
        elif active_side == "Left":
            angle_offset = 180.0
        else:  # Right
            angle_offset = 0.0
        
        final_angle_deg = exit_angle_deg + angle_offset
        final_angle_rad = math.radians(final_angle_deg)
        
        # Compute velocity components
        vx = exit_velocity * math.cos(final_angle_rad)
        vy = -exit_velocity * math.sin(final_angle_rad)  # Negate Y (screen coords)
        
        return (vx, vy)
    
    def _emit_ball(
        self,
        payload: Dict[str, Any],
        entities: List[GamePart],
        active_instances: Dict[str, GamePart],
    ):
        """
        Spawn a new physics ball with the given payload at the output port position.
        
        Args:
            payload: Initialized payload dict.
            entities: World entity list (append new ball).
            active_instances: UUID -> entity map (register new ball).
        """
        # 1. Compute port position (center of active edge)
        width = float(self.get_property("width", 96))
        height = float(self.get_property("height", 96))
        half_w = width / 2.0
        half_h = height / 2.0
        
        fx = self.body.position.x
        fy = self.body.position.y
        active_side = self.get_property("active_side", "Bottom")
        
        if active_side == "Top":
            port_x, port_y = fx, fy - half_h
        elif active_side == "Bottom":
            port_x, port_y = fx, fy + half_h
        elif active_side == "Left":
            port_x, port_y = fx - half_w, fy
        else:  # Right
            port_x, port_y = fx + half_w, fy
        
        # 2. Create physics ball (configurable output variant)
        output_variant = self.get_property("output_variant", "bouncy_ball")
        try:
            ball = GamePart(self.body.space, port_x, port_y, output_variant)
        except Exception as exc:
            self._set_state("FATAL")
            self._spawn_fatal_label(entities, f"fatal: invalid output_variant '{output_variant}'")
            self._debug_log(f"Failed to emit output_variant={output_variant}: {exc}")
            return
        ball.payload = payload
        
        # 3. Apply calculated velocity
        vx, vy = self._compute_emission_velocity()
        ball.body.velocity = (vx, vy)
        
        # 4. Add to world
        entities.append(ball)
        active_instances[ball.uuid] = ball
        
        # 5. State transition
        self._set_state("EMITTING")
    
    def _spawn_fatal_label(self, entities: List[GamePart], reason: str):
        """
        Spawn a floating red diagnostic label for FATAL errors.
        Reuses FloatingTextLabel from M18/M22 pattern.
        
        Args:
            entities: World entity list (append label).
            reason: Error message (e.g., "fatal: MCP connection failed").
        """
        label = FloatingTextLabel(
            self.body.position.x,
            self.body.position.y - 40,  # Above the DataSource
            reason,
        )
        entities.append(label)
    
    def draw(self, surface, camera=None):
        """
        Draw the DataSource with state-specific texture.
        Falls back to default sprite if no state texture is available.
        
        Args:
            surface: Pygame surface to draw on.
            camera: Optional camera for coordinate translation.
        """
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            # Temporarily replace base_texture to use state-specific sprite
            old_texture = self.base_texture
            self.base_texture = state_texture
            self.draw_texture(surface, camera=camera)
            self.base_texture = old_texture
            return
        
        # Fallback to default sprite if no state texture
        super().draw(surface, camera=camera)
    
    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Dict[str, GamePart] = None):
        """
        Update DataSource state and drive the emit interval.
        
        State Transitions:
        - OFF → INITIALIZING (on first update).
        - INITIALIZING → IDLE (on success).
        - IDLE → POLLING (every emit_interval seconds).
        - POLLING → EMITTING or IDLE (on poll_results, handled in poll_results).
        - EMITTING → IDLE (after brief emission time).
        - EXHAUSTED, FATAL → dormant (no more polling).
        
        Args:
            dt: Delta time (seconds).
            game_state: Current game mode and state.
            entities: World entity list.
            active_instances: UUID -> entity map.
        """
        if game_state.get("mode") != "PLAY":
            return
        
        # Initialize engine on first update (in OFF state)
        if self.visual_state == "OFF":
            try:
                self._initialize_engine()
                self._set_state("IDLE")
                self.next_emit_time = time.time() + self.emit_interval
            except Exception:
                # Initialization failed; FATAL was already set in _initialize_engine
                return
        
        # Dormant states: do nothing
        if self.visual_state in {"EXHAUSTED", "FATAL"}:
            return
        
        current_time = time.time()
        
        # Transition from IDLE to POLLING when emit interval is reached
        if current_time >= self.next_emit_time and self.visual_state == "IDLE":
            self._set_state("POLLING")
            self._start_worker()
            self.next_emit_time = current_time + self.emit_interval
        
        # Return to IDLE from EMITTING after brief time
        if self.visual_state == "EMITTING":
            self._set_state("IDLE")
