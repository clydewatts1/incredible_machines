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

from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.generators import get_generator, GeneratorExhausted
from utils.routing import calculate_ejection_kinematics
import constants
from utils.asset_manager import asset_manager
from utils.sprite_manager import sprite_manager


class DataSource(FlowEntity):
    """
    M23 Data Source entity  [M32: now inherits FlowEntity]
    
    Pulls data from external sources (CSV, MCP) via background worker threads,
    packages payloads, and spawns physics projectiles.
    
    State Machine: OFF -> INITIALIZING -> IDLE -> POLLING -> EMITTING -> IDLE (repeat)
                   or EXHAUSTED (source empty) or FATAL (error) or JAMMED (backpressure)
    """

    can_provide_output = True
    
    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "data_source"):
        """
        Initialize DataSource entity.
        
        Args:
            space: Pymunk physics space.
            x, y: World position.
            variant_name: YAML variant name (e.g., "data_source_csv", "data_source_mcp").
        """
        super().__init__(space, x, y, variant_name)
        
        # --- Explicitly register all defaults into self.properties ---
        # This guarantees that the Save/Load system and the Left Inspector
        # capture all inherited values instead of missing the Python fallbacks.
        self.properties.setdefault("emit_interval", 2.0)
        self.properties.setdefault("engine_type", "null")
        self.properties.setdefault("instructions", {})
        self.properties.setdefault("output_variant", "bouncy_ball")
        self.properties.setdefault("active_side", "Bottom")
        self.properties.setdefault("exit_velocity", 150.0)
        self.properties.setdefault("exit_angle", 0.0)
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)
        self.properties.setdefault("start_paused", False)
        
        # Thread-safe queue for generator results
        self.queue = queue.Queue()
        
        # Pause & Signal State
        self.is_paused = str(self.get_property("start_paused", "False")).lower() == "true"
        
        # Timing
        self.next_emit_time = time.time()
        self.emit_interval = float(self.get_property("emit_interval", 2.0))
        
        # Generator engine
        self.engine = None
        self.engine_type = self.get_property("engine_type", "null")
        self.instructions = self.get_property("instructions", {})
        
        # Current fetch state
        self.current_worker_thread = None
        
        # M27 Extension: Backpressure & Pipe Integration
        self.held_payload = None  # Stores a PayloadBallPart if the pipe is full

    def receive_signal(self, payload):
        """Delegate to FlowEntity standard handler."""
        super().receive_signal(payload)

    def _debug_enabled(self) -> bool:
        return bool(self.instructions.get("debug", False))

    def _debug_log(self, message: str):
        if self._debug_enabled():
            print(f"[DataSource:{self.variant_key}:{self.uuid[:8]}] {message}")
    
    # Inherited from FlowEntity: _load_animation_textures, _set_state, draw

    def _set_state(self, new_state: str):
        """Override to also update emit_interval from properties on each state change."""
        super()._set_state(new_state)

    
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
            # Engine initialization failure -> FATAL
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
        - Flat data mapping (CSV columns directly mapped to payload keys)
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
        
        # FIX: Spread the raw CSV data directly into the root of the payload
        # This allows Factory Regex Engines to find fields like "status" immediately!
        if isinstance(raw_data, dict):
            payload = copy.deepcopy(raw_data)
        else:
            payload = {"data": raw_data}
        
        # Add required tracking fields, but don't overwrite if the CSV explicitly provided them
        payload.setdefault("score", constants.DEFAULT_PAYLOAD_SCORE)
        payload.setdefault("cost", constants.DEFAULT_PAYLOAD_COST)
        payload.setdefault("start_time", now_secs)
        payload.setdefault("routing_depth", 0)
        payload.setdefault("ttl", constants.DEFAULT_PAYLOAD_TTL)
        payload.setdefault("drop_dead_age", constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE)
        payload.setdefault("processing_history", [])
        
        return payload
    

    
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
        # 1. Look for a dedicated DataPipePart for logical transit (M27 Extension)
        pipe = None
        for entity in entities:
            if getattr(entity, "variant_key", "") == "data_pipe" and \
               str(entity.get_property("source_uuid", "")) == str(self.uuid):
                pipe = entity
                break
        
        # 2. Compute port position (center of active edge)
        width = float(self.get_property("width", 96))
        height = float(self.get_property("height", 96))
        half_w = width / 2.0
        half_h = height / 2.0
        
        fx = self.body.position.x
        fy = self.body.position.y
        active_side = self.get_property("active_side", "Bottom")
        
        # Map active_side to edge for calculate_ejection_kinematics
        edge_map = {
            "Top": "top",
            "Bottom": "bottom",
            "Left": "left",
            "Right": "right"
        }
        edge = edge_map.get(active_side, "bottom")
        
        if active_side == "Top":
            port_x, port_y = fx, fy - half_h
        elif active_side == "Bottom":
            port_x, port_y = fx, fy + half_h
        elif active_side == "Left":
            port_x, port_y = fx - half_w, fy
        else:  # Right
            port_x, port_y = fx + half_w, fy
        
        # 3. Create physics ball using the main router so Custom Parts work
        output_variant = self.get_property("output_variant", "bouncy_ball")
        try:
            from main import create_part
            ball = create_part(self.body.space, port_x, port_y, output_variant)
        except Exception as exc:
            self._set_state("FATAL")
            self._spawn_fatal_label(entities, f"fatal: invalid output_variant '{output_variant}'")
            self._debug_log(f"Failed to emit output_variant={output_variant}: {exc}")
            return
            
        # Bind the flattened payload directly to the newly created ball
        ball.payload = payload
        
        # --- M27 Extension: Pipe Ingestion Path ---
        if pipe:
            self._debug_log(f"Found connected pipe {pipe.uuid}. Attempting ingestion...")
            accepted = pipe.ingest_payload(ball)
            if accepted:
                self._debug_log("Pipe accepted payload. Transitioning to EMITTING.")
                self._set_state("EMITTING")
                # Register the ball in dictionaries so it exists in memory, 
                # though it's hidden and physics-disabled by the pipe.
                active_instances[ball.uuid] = ball
                return
            else:
                self._debug_log("Pipe FULL. Entering JAMMED state.")
                self.held_payload = ball
                self._set_state("JAMMED")
                active_instances[ball.uuid] = ball
                return

        # 4. Physical Fallback (if no pipe or pipe ingestion logic skipped)
        # Calculate velocity using centralized routing utility
        exit_velocity = float(self.get_property("exit_velocity", 150.0))
        exit_angle = float(self.get_property("exit_angle", 0.0))
        route_rule = {"velocity": exit_velocity, "angle": exit_angle}
        
        # Get default angle for this side
        default_angles = {"top": 90.0, "bottom": 270.0, "left": 180.0, "right": 0.0}
        default_angle = default_angles.get(edge, 0.0)
        
        # Compute position and velocity using shared utility
        (eject_x, eject_y), (vx, vy) = calculate_ejection_kinematics(
            self, edge, route_rule, exit_velocity, default_angle, entities
        )
        
        # Apply calculated velocity
        ball.body.velocity = (vx, vy)
        
        # 5. Add to world
        entities.append(ball)
        active_instances[ball.uuid] = ball
        
        # 6. State transition
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
        """Delegate state-based rendering to FlowEntity, then draw pause icon."""
        super().draw(surface, camera=camera)
    
    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Dict[str, GamePart] = None):
        """
        Update DataSource state and drive the emit interval.
        
        State Transitions:
        - OFF -> INITIALIZING (on first update).
        - INITIALIZING -> IDLE (on success).
        - IDLE -> POLLING (every emit_interval seconds).
        - POLLING -> EMITTING or IDLE (on poll_results, handled in poll_results).
        - EMITTING -> IDLE (after brief emission time).
        - EXHAUSTED, FATAL -> dormant (no more polling).
        
        Args:
            dt: Delta time (seconds).
            game_state: Current game mode and state.
            entities: World entity list.
            active_instances: UUID -> entity map.
        """
        if game_state.get("mode") != "PLAY":
            return
            
        current_time = time.time()
        
        # --- PROCESS SIGNALS (Warehouse Flow Control) ---
        self._process_incoming_signal()
        if self.signal_state == "FULL":
            self.is_paused = True
        elif self.signal_state in ["IDLE", "OFF"] and self.signal_state is not None:
            self.is_paused = False
            self.next_emit_time = current_time + self.emit_interval
        self.signal_state = None  # consume

        # Apply Pause Logic (Fixes the Deadlock!)
        if self.is_paused:
            self.next_emit_time = current_time + self.emit_interval # Keep pushing the timer forward
            
            # CRITICAL FIX: We must keep our visual state as "IDLE" internally, 
            # otherwise the downstream Warehouse will see we aren't IDLE and it will refuse 
            # to release its own balls! The new draw() method will show the pause icon instead.
            if self.visual_state not in {"IDLE", "OFF"}:
                self._set_state("IDLE")
            return
        
        # Initialize engine on first update (in OFF state)
        if self.visual_state == "OFF":
            try:
                self._initialize_engine()
                self._set_state("IDLE")
                self.next_emit_time = current_time + self.emit_interval
            except Exception:
                return
        
        # Dormant states: do nothing
        if self.visual_state in {"EXHAUSTED", "FATAL"}:
            return
        
        # Transition from IDLE to POLLING when emit interval is reached
        if current_time >= self.next_emit_time and self.visual_state == "IDLE":
            self._set_state("POLLING")
            self._start_worker()
            self.next_emit_time = current_time + self.emit_interval
        
        # Return to IDLE from EMITTING after brief time
        if self.visual_state == "EMITTING":
            self._set_state("IDLE")
            
        # --- JAMMED RETRY LOGIC (M27 Extension) ---
        if self.visual_state == "JAMMED" and self.held_payload:
            # We must freeze the emit timer
            self.next_emit_time = current_time + self.emit_interval
            
            # Look for the pipe again
            pipe = None
            for entity in entities:
                if getattr(entity, "variant_key", "") == "data_pipe" and \
                   str(entity.get_property("source_uuid", "")) == str(self.uuid):
                    pipe = entity
                    break
            
            if pipe:
                accepted = pipe.ingest_payload(self.held_payload)
                if accepted:
                    self._debug_log("JAMMED cleared: Pipe accepted held payload.")
                    self.held_payload = None
                    self._set_state("IDLE")
                # Else: still jammed, we will try again next frame
            else:
                # Pipe was deleted/moved? Fallback to physical ejection
                self._debug_log("JAMMED fallback: Pipe missing. Ejecting physically.")
                self._emit_ball(self.held_payload.payload, entities, active_instances)
                self.held_payload.to_delete = True # Cleanup the held reference
                self.held_payload = None
                self._set_state("IDLE")