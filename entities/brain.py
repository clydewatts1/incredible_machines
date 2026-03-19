import copy
import math
import queue
import threading
import uuid
import json
from typing import Any, Dict, List, Optional

import pygame

import constants
from entities.base import GamePart
from entities.active import FloatingTextLabel
from utils.asset_manager import asset_manager
from utils.sound_manager import sound_manager
from utils.sprite_manager import sprite_manager

# --- AI Dependencies ---
try:
    from openai import OpenAI
    from pydantic import BaseModel, Field
    
    class BrainDecision(BaseModel):
        thought: str = Field(description="Internal reasoning for the decision.")
        route_state: float = Field(description="The numeric state to route the payload to (e.g., 0, 1, 2).")
        injected_data: Dict[str, str] = Field(description="Any new data or labels to add to the payload.")
        
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class BrainPart(GamePart):
    """An active processor entity that uses a Local LLM to evaluate payloads."""

    VALID_STATES = {"OFF", "INITIALIZING", "IDLE", "INGESTING", "WRITING", "FATAL", "JAMMED", "COOLDOWN", "PAUSED"}

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.visual_state = "OFF"
        self.queue = queue.Queue()
        self._is_destroyed = False
        self.cooldown_timer = 0.0
        self.current_payload_uuid: Optional[str] = None
        
        # --- Pause & Signal State ---
        self.is_paused = False
        self.signal_received = False
        self.signal_state = None

        # --- Explicitly register defaults for the Save/Load system ---
        self.properties.setdefault("model", "llama3.1")
        self.properties.setdefault("system_prompt", "Analyze the payload data. Determine its routing state.")
        self.properties.setdefault("routing", [])
        
        # New I/O and Lifecycle Defaults
        self.properties.setdefault("input_side", "top")    # top, left, right
        self.properties.setdefault("output_side", "right") # top, left, right, bottom
        self.properties.setdefault("cost_modifier", -10.0) # Energy cost per thought
        
        self.properties.setdefault("tired_velocity", 150.0)
        self.properties.setdefault("shoot_speed", 250.0)
        self.properties.setdefault("target", "")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        self._create_default_visuals()

        self._animation_textures = {}
        self._load_animation_textures()
        
        self._set_state("INITIALIZING")
        self._set_state("IDLE")

    def _create_default_visuals(self):
        """Creates a fallback UI icon if missing, but respects existing realistic sprites."""
        pass

    def _load_animation_textures(self):
        """Loads animation frames, gracefully falling back to the IDLE sprite if missing."""
        animations = self.get_property("animations", {})
        
        if not isinstance(animations, dict) or not animations:
            animations = {
                "OFF": "ai_brain_off",
                "INITIALIZING": "ai_brain_initializing",
                "IDLE": "ai_brain_idle",
                "INGESTING": "ai_brain_ingesting",
                "WRITING": "ai_brain_writing",
                "FATAL": "ai_brain_fatal",
                "JAMMED": "ai_brain_jammed",
                "COOLDOWN": "ai_brain_cooldown",
                "PAUSED": "ai_brain_paused"
            }

        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))

        for state_name, base_name in animations.items():
            self._animation_textures[state_name] = sprite_manager.get_sprite(
                base_name, width, height, label=f"Brain {state_name}"
            )

    def receive_signal(self, payload):
        """Called by the main loop when another object (like a Warehouse) sends a logic pulse."""
        if hasattr(payload, "visual_state"):
            self.signal_state = payload.visual_state
            self.signal_received = True

    def _set_state(self, new_state: str):
        if new_state not in self.VALID_STATES:
            return

        old_state = self.visual_state
        self.visual_state = new_state
        
        if old_state != new_state and (new_state == "WRITING" or old_state == "WRITING"):
            self.cooldown_timer = max(self.cooldown_timer, constants.FACTORY_COOLDOWN_SECONDS)
            
        if old_state != new_state:
            sounds = self.get_property("sounds", {})
            if isinstance(sounds, dict):
                sound_file = sounds.get(new_state)
                if sound_file:
                    try:
                        sound_manager.play_sound(sound_file)
                    except Exception:
                        pass
            
            # Broadcast state changes out to connected components!
            self.needs_broadcast = True

    def is_in_cooldown(self) -> bool:
        return self.cooldown_timer > 0.0

    def cleanup(self):
        self._is_destroyed = True
        self.current_payload_uuid = None
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def destroy(self):
        self._is_destroyed = True

    def _ensure_payload_defaults(self, payload_entity: GamePart):
        payload = getattr(payload_entity, "payload", None)
        if not isinstance(payload, dict):
            payload = {}

        now_secs = pygame.time.get_ticks() / 1000.0
        payload.setdefault("ttl", constants.DEFAULT_PAYLOAD_TTL)
        payload.setdefault("cost", constants.DEFAULT_PAYLOAD_COST)
        payload.setdefault("drop_dead_age", constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE)
        payload.setdefault("routing_depth", 0)
        payload.setdefault("processing_history", [])
        payload.setdefault("start_time", now_secs)
        payload.setdefault("age", 0.0)

        payload_entity.payload = payload

    def _audit_payload_lifecycle(self, payload_entity: GamePart):
        payload = payload_entity.payload
        now_secs = pygame.time.get_ticks() / 1000.0
        payload["age"] = max(0.0, now_secs - float(payload.get("start_time", now_secs)))

        cost_modifier = float(self.get_property("cost_modifier", -10.0))
        payload["cost"] = float(payload.get("cost", constants.DEFAULT_PAYLOAD_COST)) + cost_modifier

        if payload.get("cost", 0.0) <= 0.0:
            return "bottom" 
        if payload.get("age", 0.0) > float(payload.get("drop_dead_age", constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE)):
            return "bottom" 
        if int(payload.get("ttl", 0)) <= 0:
            return "bottom" 
        if int(payload.get("routing_depth", 0)) > constants.MAX_ROUTING_DEPTH:
            return "bottom"

        return "healthy"

    def ingest_payload(self, payload_entity: GamePart) -> bool:
        if self._is_destroyed or self.is_in_cooldown():
            return False

        # --- PAUSE CHECK ---
        # If we are paused, reject incoming balls. This creates physical backpressure!
        if getattr(self, 'is_paused', False):
            return False

        if self.current_payload_uuid is not None:
            self._set_state("JAMMED")
            return False

        input_side = str(self.get_property("input_side", "top")).lower()
        dx = payload_entity.body.position.x - self.body.position.x
        dy = payload_entity.body.position.y - self.body.position.y
        
        if input_side == "top" and not (dy < 0 and abs(dy) >= abs(dx) * 0.5):
            return False
        elif input_side == "left" and not (dx < 0 and abs(dx) >= abs(dy) * 0.5):
            return False
        elif input_side == "right" and not (dx > 0 and abs(dx) >= abs(dy) * 0.5):
            return False

        self._ensure_payload_defaults(payload_entity)
        gate = self._audit_payload_lifecycle(payload_entity)
        
        if gate == "bottom":
            self.current_payload_uuid = payload_entity.uuid
            self._set_state("INGESTING")
            self.queue.put({"payload_uuid": payload_entity.uuid, "result": "fatal: out of energy"})
            return True

        self.current_payload_uuid = payload_entity.uuid
        self._set_state("INGESTING")
        self._start_worker(payload_entity)
        return True

    def _start_worker(self, payload_entity: GamePart):
        payload_copy = copy.deepcopy(getattr(payload_entity, "payload", {}))
        payload_uuid = payload_entity.uuid
        
        model_name = str(self.get_property("model", "llama3.1"))
        system_prompt = str(self.get_property("system_prompt", "Determine routing state."))

        def _worker():
            if not AI_AVAILABLE:
                if not self._is_destroyed:
                    self.queue.put({"payload_uuid": payload_uuid, "result": "fatal: pip install openai pydantic"})
                return

            try:
                client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                data_str = json.dumps(payload_copy.get("data", payload_copy))
                
                print(f"🧠 [Brain] Sending payload to {model_name}...")
                response = client.beta.chat.completions.parse(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Incoming Payload Data: {data_str}"}
                    ],
                    response_format=BrainDecision,
                )
                
                decision = response.choices[0].message.parsed
                print(f"🧠 [Brain] Thought: {decision.thought}")
                print(f"🧠 [Brain] Decision Route: {decision.route_state}")

                if not self._is_destroyed:
                    self.queue.put({
                        "payload_uuid": payload_uuid, 
                        "route_state": decision.route_state,
                        "injected_data": decision.injected_data
                    })
                    
            except Exception as exc:
                if not self._is_destroyed:
                    self.queue.put({"payload_uuid": payload_uuid, "result": f"fatal: AI Error: {exc}"})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _find_route(self, state_value: float) -> Optional[Dict[str, Any]]:
        routing_list = self.get_property("routing", [])
        if not isinstance(routing_list, list): return None
        for rule in routing_list:
            if not isinstance(rule, dict): continue
            try:
                if float(state_value) <= float(rule.get("max_state")):
                    return rule
            except (TypeError, ValueError):
                continue
        return None

    def _spawn_fatal_label(self, entities: List[GamePart], reason: str):
        label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, reason)
        entities.append(label)

    def _find_matching_pipe_for_state(self, entities: List[GamePart], route_state: float):
        for entity in entities:
            if getattr(entity, "variant_key", "") != "data_pipe":
                continue

            if str(entity.get_property("source_uuid", "")) != str(self.uuid):
                continue

            try:
                pipe_state = float(entity.get_property("route_state", 10.0))
            except (TypeError, ValueError):
                continue

            if abs(pipe_state - float(route_state)) <= 1e-6:
                return entity

        return None

    def _eject_payload(self, payload_entity: GamePart, edge: str, route_rule: Optional[Dict[str, Any]] = None, entities: Optional[List[GamePart]] = None):
        width = float(self.get_property("width", 96))
        height = float(self.get_property("height", 96))
        half_w = width / 2.0
        half_h = height / 2.0
        margin = 25.0 
        
        fx, fy = self.body.position.x, self.body.position.y
        
        if edge == "bottom":
            eject_x, eject_y = fx, fy + half_h + margin
        elif edge == "top":
            eject_x, eject_y = fx, fy - half_h - margin
        elif edge == "left":
            eject_x, eject_y = fx - half_w - margin, fy
        elif edge == "right":
            eject_x, eject_y = fx + half_w + margin, fy
        else:
            eject_x, eject_y = fx, fy
            
        payload_entity.body.position = (eject_x, eject_y)

        if edge == "bottom":
            tired_velocity = float(self.get_property("tired_velocity", 150.0))
            payload_entity.body.velocity = (0.0, abs(tired_velocity))
        else:
            target_val = (route_rule or {}).get("target", self.get_property("target", None))
            target_pos = None
            
            # --- NEW UX FEATURE ---
            # If no explicit target is typed in the properties, but the user wired this Brain 
            # to another object, automatically aim and shoot the balls at the wired object!
            if not target_val and self.connected_uuids:
                target_val = self.connected_uuids[0]
                
            if target_val and entities is not None:
                for ent in entities:
                    if ent.uuid == target_val or ent.get_property("name") == target_val:
                        target_pos = ent.body.position
                        break
                        
            if target_pos:
                dx, dy = target_pos[0] - eject_x, target_pos[1] - eject_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    speed = float((route_rule or {}).get("velocity", self.get_property("shoot_speed", 250.0)))
                    vx, vy = (dx / dist) * speed, (dy / dist) * speed
                else:
                    vx, vy = 0.0, 0.0
            else:
                default_angles = {
                    "right": 0.0,
                    "top": 90.0,
                    "left": 180.0,
                    "bottom": 270.0
                }
                fallback_angle = default_angles.get(edge, 0.0)
                
                angle_deg = float((route_rule or {}).get("angle", fallback_angle))
                vel = float((route_rule or {}).get("velocity", 200.0))
                
                world_angle = math.radians(angle_deg)
                vx = vel * math.cos(world_angle)
                vy = vel * -math.sin(world_angle) 
                
            payload_entity.body.velocity = (vx, vy)
            
        self._set_state("WRITING")

    def draw(self, surface, camera=None):
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            old_texture = self.base_texture
            self.base_texture = state_texture
            super().draw(surface, camera=camera)
            self.base_texture = old_texture
        else:
            super().draw(surface, camera=camera)
            
        # --- NEW UX: Draw visual Pause symbol! ---
        if getattr(self, 'is_paused', False) and self.body:
            if camera:
                screen_x, screen_y = camera.world_to_screen(self.body.position.x, self.body.position.y)
            else:
                screen_x, screen_y = self.body.position.x, self.body.position.y
                
            pygame.draw.rect(surface, (255, 200, 0), (screen_x - 8, screen_y - 20, 5, 15), border_radius=1)
            pygame.draw.rect(surface, (255, 200, 0), (screen_x + 3, screen_y - 20, 5, 15), border_radius=1)

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        if self._is_destroyed:
            return

        # --- PAUSE QUEUE CHECK ---
        # If we are paused, hold the completed results in the queue!
        # The main game loop automatically keeps the ball safely hidden in the center of the brain until this releases.
        if getattr(self, 'is_paused', False):
            return

        while not self.queue.empty():
            result_data = self.queue.get()
            payload_uuid = result_data.get("payload_uuid")
            payload_entity = active_instances.get(payload_uuid)

            if payload_entity is None or getattr(payload_entity, "to_delete", False):
                self.current_payload_uuid = None
                continue

            error_msg = result_data.get("result", "")
            if isinstance(error_msg, str) and error_msg.startswith("fatal"):
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, error_msg)
                self.current_payload_uuid = None
                self._eject_payload(payload_entity, edge="bottom", entities=entities)
                continue

            route_state = result_data.get("route_state", 0.0)
            injected_data = result_data.get("injected_data", {})

            if isinstance(injected_data, dict) and injected_data:
                if not isinstance(payload_entity.payload.get("data"), dict):
                    payload_entity.payload["data"] = {}
                payload_entity.payload["data"].update(injected_data)

            route_rule = self._find_route(route_state)
            
            if route_rule is None:
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, f"fatal: no route for state {route_state}")
                self.current_payload_uuid = None
                self._eject_payload(payload_entity, edge="bottom", entities=entities)
                continue

            matching_pipe = self._find_matching_pipe_for_state(entities, route_state)
            if matching_pipe is not None:
                accepted = bool(matching_pipe.ingest_payload(payload_entity))
                if accepted:
                    self.current_payload_uuid = None
                    self._set_state("IDLE")
                    continue

                self._set_state("JAMMED")
                self.current_payload_uuid = payload_entity.uuid
                self.queue.put(result_data)
                break
            
            output_side = str(route_rule.get("output_side", self.get_property("output_side", "right"))).lower()
            self.current_payload_uuid = None
            self._eject_payload(payload_entity, edge=output_side, route_rule=route_rule, entities=entities)

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        # --- SIGNAL BROADCAST ---
        if getattr(self, 'needs_broadcast', False):
            self.needs_broadcast = False
            for tgt_uuid in self.connected_uuids:
                tgt = active_instances.get(tgt_uuid)
                if tgt and hasattr(tgt, 'receive_signal'):
                    tgt.receive_signal(self)

        # --- PROCESS SIGNALS (Warehouse Flow Control) ---
        if self.signal_received:
            self.signal_received = False
            if self.signal_state == "FULL":
                self.is_paused = True
                if self.visual_state == "IDLE":
                    self._set_state("PAUSED")
            elif self.signal_state in ["IDLE", "OFF"]:
                self.is_paused = False
                if self.visual_state == "PAUSED":
                    self._set_state("IDLE")

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
            if self.cooldown_timer > 0.0:
                self._set_state("COOLDOWN")
            elif self.visual_state == "COOLDOWN":
                self._set_state("IDLE")

        # Keep state accurate so downstream polling works
        if getattr(self, 'is_paused', False) and self.visual_state not in {"INGESTING", "FATAL", "JAMMED", "COOLDOWN"}:
            self._set_state("PAUSED")
        elif not getattr(self, 'is_paused', False) and self.visual_state not in {"INGESTING", "FATAL", "JAMMED", "COOLDOWN", "PAUSED"}:
            self._set_state("IDLE")