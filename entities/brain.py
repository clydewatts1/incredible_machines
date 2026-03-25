import copy
import queue
import threading
import json
from typing import Any, Dict, List, Optional

import pygame

import constants
from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.asset_manager import asset_manager
from utils.routing import find_route

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
    """
    An active processor entity that uses a Local LLM to evaluate payloads.
    Migrated to Unified Flow Architecture (M32).
    """

    can_provide_output = True
    can_accept_input = True

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.queue = queue.Queue()
        self.current_payload_uuid: Optional[str] = None
        
        # --- Default Properties ---
        self.properties.setdefault("model", "llama3.2") # M32 default
        self.properties.setdefault("system_prompt", "Analyze the payload data. Determine its routing state.")
        self.properties.setdefault("routing", [])
        self.properties.setdefault("input_side", "top")
        self.properties.setdefault("output_side", "right")
        self.properties.setdefault("cost_modifier", -10.0)
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)
        self.properties.setdefault("auto_release", True)
        
        self.stored_payload_uuids = []

        self.visual_state = "IDLE"

    def cleanup(self):
        self._is_destroyed = True
        self.current_payload_uuid = None
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def destroy(self):
        self.cleanup()

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

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        if self._is_destroyed:
            return False

        # --- Milestone 32: Standardized Logic Handshake ---
        if self.visual_state != "IDLE" or self.downstream_status in ("FULL", "JAMMED"):
            return False

        # Physics/Bounds check for input side
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
            # Direct ejection for dead payloads
            self.resolve_exit_path(payload_entity, 0.0, [], {})
            return True

        self.current_payload_uuid = payload_entity.uuid
        self.visual_state = "INGESTING"
        self._start_worker(payload_entity)
        return True

    def _start_worker(self, payload_entity: GamePart):
        payload_copy = copy.deepcopy(getattr(payload_entity, "payload", {}))
        payload_uuid = payload_entity.uuid
        
        model_name = str(self.get_property("model", "llama3.2"))
        system_prompt = str(self.get_property("system_prompt", "Determine routing state."))
        
        # Milestone 35: Logic Generation snapshot for cancellation
        worker_gen = self.logic_generation

        def _worker():
            if not AI_AVAILABLE:
                if not self._is_destroyed and self.logic_generation == worker_gen:
                    self.queue.put({"payload_uuid": payload_uuid, "result": "fatal: AI dependencies missing"})
                return

            try:
                client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
                data_str = json.dumps(payload_copy.get("data", payload_copy))
                
                if self.logic_generation != worker_gen: return # Abort Before Call

                print(f"DEBUG: Brain {self.uuid} Calling AI with payload: {data_str}")
                response = client.beta.chat.completions.parse(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Incoming Payload Data: {data_str}"}
                    ],
                    response_format=BrainDecision,
                )
                
                if self.logic_generation != worker_gen: return # Abort After Call

                decision = response.choices[0].message.parsed
                if not self._is_destroyed:
                    # Milestone 35: Strict Fallback Logic
                    final_state = decision.route_state
                    fallback_state = int(self.get_property("fallback_state", 0))
                    
                    if final_state is None:
                        print(f"WARNING: Brain {self.uuid} AI returned None for route_state. Using fallback {fallback_state}.")
                        final_state = fallback_state
                    
                    print(f"DEBUG: Brain {self.uuid} AI Thought: {decision.thought}")
                    print(f"DEBUG: Brain {self.uuid} Route State: {final_state}")
                    
                    self.queue.put({
                        "payload_uuid": payload_uuid, 
                        "route_state": final_state,
                        "injected_data": decision.injected_data,
                        "thought": decision.thought
                    })
                    
            except Exception as exc:
                if not self._is_destroyed and self.logic_generation == worker_gen:
                    print(f"DEBUG: Brain {self.uuid} AI ERROR: {exc}")
                    self.queue.put({"payload_uuid": payload_uuid, "result": f"fatal: AI Error: {exc}"})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def extract_payload(self, uuid: str, active_instances: Dict[str, Any]) -> Optional[GamePart]:
        """
        Milestone 38: Atomic extraction for pull-based WOLF logic.
        """
        if uuid in self.stored_payload_uuids:
            self.stored_payload_uuids.remove(uuid)
            payload = active_instances.get(uuid)
            if payload:
                # Flash for visual confirmation of the pull
                self.flash_timer = 15
                return payload
        return None

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        if self._is_destroyed:
            return

        while not self.queue.empty():
            # Milestone 32: Result Handshake
            self.visual_state = "WRITING"
            
            result_data = self.queue.get()
            payload_uuid = result_data.get("payload_uuid")
            payload_entity = active_instances.get(payload_uuid)

            if payload_entity is None or getattr(payload_entity, "to_delete", False):
                self.current_payload_uuid = None
                continue

            # --- Zero Rule: Errors force state 0 ---
            error_msg = result_data.get("result", "")
            if isinstance(error_msg, str) and error_msg.startswith("fatal"):
                route_state = 0.0
            else:
                route_state = result_data.get("route_state", 0.0)

            # Inject AI data
            injected_data = result_data.get("injected_data", {})
            if isinstance(injected_data, dict) and injected_data:
                if not isinstance(payload_entity.payload.get("data"), dict):
                    payload_entity.payload["data"] = {}
                payload_entity.payload["data"].update(injected_data)
            
            payload_entity.trim_payload() # Milestone 34: Data Bloat Prevention
            
            # Milestone 38: WOLF Interaction Mode
            if not self.get_bool_property("auto_release", True):
                print(f"DEBUG: Brain {self.uuid} Holding {payload_uuid} in interaction buffer.")
                if payload_uuid not in self.stored_payload_uuids:
                    self.stored_payload_uuids.append(payload_uuid)
                self.current_payload_uuid = None
                
                # Milestone 38: Event-Driven WOLF
                self.broadcast_status(active_instances or {}, custom_signal={"status": "REFRESH"})
                continue

            # Standardized Routing
            print(f"DEBUG: Brain {self.uuid} Resolving exit for {payload_uuid} with state {route_state}")
            exit_code = self.resolve_exit_path(payload_entity, route_state, entities, active_instances)
            print(f"DEBUG: Brain {self.uuid} Routing result: {exit_code}")
            self.current_payload_uuid = None

        # Return to IDLE and broadcast updated status to neighbors
        self.visual_state = "IDLE"
        self.broadcast_status(active_instances or {})

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        # Process incoming signals (standard backpressure)
        self._process_incoming_signal()

        # Cooldown & Polling are managed by poll_results in this simplified M32 model.
        # However, we still need to poll results every frame.
        self.poll_results(entities, active_instances or {})