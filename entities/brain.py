import copy
import queue
import threading
import uuid
import json
from typing import Any, Dict, List, Optional

import pygame

import constants
from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.asset_manager import asset_manager
from utils.routing import calculate_ejection_kinematics, find_route
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


class BrainPart(FlowEntity):
    """An active processor entity that uses a Local LLM to evaluate payloads.  [M32: inherits FlowEntity]"""

    can_provide_output = True
    can_accept_input = True

    VALID_STATES = {"OFF", "INITIALIZING", "IDLE", "INGESTING", "WRITING", "FATAL", "JAMMED", "COOLDOWN", "PAUSED"}

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        # visual_state, _is_destroyed, is_paused, signal_received, signal_state,
        # needs_broadcast, cooldown_timer, _animation_textures are all set by FlowEntity.__init__
        self.queue = queue.Queue()
        self.current_payload_uuid: Optional[str] = None
        
        # --- Explicitly register defaults for the Save/Load system ---
        self.properties.setdefault("model", "llama3.1")
        self.properties.setdefault("system_prompt", "Analyze the payload data. Determine its routing state.")
        self.properties.setdefault("routing", [])
        self.properties.setdefault("input_side", "top")
        self.properties.setdefault("output_side", "right")
        self.properties.setdefault("cost_modifier", -10.0)
        self.properties.setdefault("tired_velocity", 150.0)
        self.properties.setdefault("shoot_speed", 250.0)
        self.properties.setdefault("target", "")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        self._set_state("INITIALIZING")
        self._set_state("IDLE")

    # Inherited from FlowEntity: _set_state, draw,
    #                             receive_signal, broadcast_status, _process_incoming_signal

    def _load_animation_textures(self):
        """
        Override: inject default ai_brain sprite names when YAML `animations` is absent.
        FlowEntity._load_animation_textures handles the actual loading and procedural fallback.
        """
        from utils.sprite_manager import sprite_manager
        animations = self.get_property("animations", {})
        if not isinstance(animations, dict) or not animations:
            # Hardcoded defaults for ai_brain sprites
            animations = {
                "OFF":          "ai_brain_off",
                "INITIALIZING": "ai_brain_initializing",
                "IDLE":         "ai_brain_idle",
                "INGESTING":    "ai_brain_ingesting",
                "WRITING":      "ai_brain_writing",
                "FATAL":        "ai_brain_fatal",
                "JAMMED":       "ai_brain_jammed",
                "COOLDOWN":     "ai_brain_cooldown",
                "PAUSED":       "ai_brain_paused",
            }
        width  = int(float(self.get_property("width",  96)))
        height = int(float(self.get_property("height", 96)))
        for state_name, base_name in animations.items():
            surf = sprite_manager.get_sprite(base_name, width, height, label=f"Brain {state_name}")
            if surf is None:
                surf = self._make_procedural_fallback(width, height, state_name)
            self._animation_textures[state_name] = surf

    def receive_signal(self, payload):
        """Delegate to FlowEntity; also handles SmartSplitter dict feedback."""
        super().receive_signal(payload)

    def _set_state(self, new_state: str):
        """Override to trigger cooldown on WRITING transitions."""
        super()._set_state(new_state)

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

    def _spawn_fatal_label(self, entities: List[GamePart], reason: str):
        label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, reason)
        entities.append(label)

    # Removed: _find_matching_pipe_for_state — superseded by resolve_exit_path (FlowEntity)
    # Removed: _eject_payload — superseded by resolve_exit_path (FlowEntity)

    def draw(self, surface, camera=None):
        """Delegate to FlowEntity (state texture + pause icon)."""
        super().draw(surface, camera=camera)

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
                # M32: Error results are treated as state 0
                self.resolve_exit_path(payload_entity, 0.0, entities, active_instances)
                continue

            route_state = result_data.get("route_state", 0.0)
            injected_data = result_data.get("injected_data", {})

            if isinstance(injected_data, dict) and injected_data:
                if not isinstance(payload_entity.payload.get("data"), dict):
                    payload_entity.payload["data"] = {}
                payload_entity.payload["data"].update(injected_data)

            # M32: Use resolve_exit_path instead of manual pipe search + _eject_payload
            exit_result = self.resolve_exit_path(
                payload_entity, route_state, entities, active_instances
            )
            if exit_result == "pipe":
                self.current_payload_uuid = None
                self._set_state("IDLE")
            elif exit_result == "jammed":
                self._set_state("JAMMED")
                self.current_payload_uuid = payload_entity.uuid
                self.queue.put(result_data)
                break
            else:  # ejected
                self.current_payload_uuid = None

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        # --- SIGNAL BROADCAST (M32: use inherited broadcast_status) ---
        if self.needs_broadcast:
            self.needs_broadcast = False
            self.broadcast_status(active_instances or {})

        # --- PROCESS SIGNALS (M32: use inherited _process_incoming_signal) ---
        self._process_incoming_signal()
        if self.is_paused and self.visual_state == "IDLE":
            self._set_state("PAUSED")
        elif not self.is_paused and self.visual_state == "PAUSED":
            self._set_state("IDLE")

        # Cooldown tick
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
            if self.cooldown_timer > 0.0:
                self._set_state("COOLDOWN")
            elif self.visual_state == "COOLDOWN":
                self._set_state("IDLE")

        # Keep state accurate
        if self.is_paused and self.visual_state not in {"INGESTING", "FATAL", "JAMMED", "COOLDOWN"}:
            self._set_state("PAUSED")
        elif not self.is_paused and self.visual_state not in {"INGESTING", "FATAL", "JAMMED", "COOLDOWN", "PAUSED"}:
            self._set_state("IDLE")