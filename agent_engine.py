import copy
import queue
import threading
from typing import Any, Dict, List, Optional

import pygame

import constants
from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.routing import calculate_ejection_kinematics, find_route
from utils.engines import create_engine
from utils.asset_manager import asset_manager
from utils.sprite_manager import sprite_manager


class FactoryPart(FlowEntity):
    """
    Simplified Factory Entity (Strict 1-In, 1-Out Mutator).
    Relies completely on FlowEntity.resolve_exit_path without complex multi-routing tables.
    """
    can_accept_input = True
    can_provide_output = True

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.queue = queue.Queue()
        self.current_payload_uuid = None

    def ingest_payload(self, payload_entity, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        if self.visual_state in ["INGESTING", "WRITING", "JAMMED", "FATAL"] or self.downstream_status in ["FULL", "JAMMED"]:
            return False

        self.current_payload_uuid = payload_entity.uuid
        self._set_state("INGESTING")
        self._start_worker(payload_entity)
        return True

    def _start_worker(self, payload_entity):
        payload_copy = copy.deepcopy(payload_entity.payload) if hasattr(payload_entity, "payload") else {}
        instructions = self.get_property("instructions", {})
        engine = create_engine(self.get_property("engine_type", "regex"))
        payload_uuid = payload_entity.uuid

        def _task():
            try:
                result = engine.process(payload_copy, instructions)
                if isinstance(result, str) and result.startswith("fatal"):
                    result = 0
            except Exception:
                result = 0
            
            self.queue.put({"uuid": payload_uuid, "result": result})

        threading.Thread(target=_task, daemon=True).start()

    def poll_results(self, entities: List[Any], active_instances: Dict[str, Any]):
        if not self.queue.empty():
            data = self.queue.get()
            uid = data.get("uuid") or data.get("payload_uuid")
            payload = active_instances.get(uid)
            
            # Robust fallback for tests or out-of-sync states
            if not payload and entities:
                for e in entities:
                    if getattr(e, "uuid", None) == uid:
                        payload = e
                        break
            
            self.current_payload_uuid = None

            if payload:
                # Strict 1-Out: Delegate to resolve_exit_path without explicit YAML routing properties required
                self.resolve_exit_path(payload, data["result"], entities, active_instances)
                
                if self.visual_state != "FATAL":
                    self._set_state("IDLE")

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances) 
        
        if game_state.get("mode") == "PLAY":
            if self.downstream_status in ["FULL", "JAMMED"] and self.visual_state == "WRITING":
                self._set_state("JAMMED")
            
            self.poll_results(entities, active_instances or {})