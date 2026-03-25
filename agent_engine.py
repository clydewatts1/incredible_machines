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
    """Milestone 22 active processor entity with async engine execution.  [M32: inherits FlowEntity]"""

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        # visual_state, is_paused, needs_broadcast, etc. are set by FlowEntity
        self.queue = queue.Queue()
        self.current_payload_uuid: Optional[str] = None
        
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        self._set_state("INITIALIZING")
        self._set_state("IDLE")

    # Inherited from FlowEntity: load_animations, _set_state, draw,
    #                             receive_signal, broadcast_status, _process_incoming_signal,
    #                             cleanup, destroy, resolve_exit_path, etc.

    def is_in_cooldown(self) -> bool:
        return self.cooldown_timer > 0.0

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
            return "top"

        if int(payload.get("ttl", 0)) <= 0:
            return "bottom"

        if int(payload.get("routing_depth", 0)) > constants.MAX_ROUTING_DEPTH:
            return "bottom"

        return "healthy"

    def _start_worker(self, payload_entity: GamePart):
        payload_copy = copy.deepcopy(payload_entity.payload)

        for k, v in list(payload_copy.items()):
            clean_k = k.strip() if isinstance(k, str) else k
            clean_v = v.strip() if isinstance(v, str) else v
            if clean_k != k:
                del payload_copy[k]
            payload_copy[clean_k] = clean_v

        instructions_copy = copy.deepcopy(self.get_property("instructions", {}))
        engine_type = str(self.get_property("engine_type", "regex"))
        engine = create_engine(engine_type, {"variant_key": self.variant_key})

        payload_uuid = payload_entity.uuid

        def _worker():
            try:
                result = engine.process(payload_copy, instructions_copy)
            except Exception as exc:
                # M32: Error results are treated as state 0
                result = 0.0
                print(f"ERROR: FactoryPart {self.uuid} engine fatal: {exc}")
                if not self._is_destroyed:
                    self._spawn_fatal_label(pygame.display.get_surface(), f"engine fatal: {exc}")

            if not self._is_destroyed:
                self.queue.put({"payload_uuid": payload_uuid, "result": result})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        if self._is_destroyed:
            return False

        if self.is_in_cooldown():
            return False

        if self.current_payload_uuid is not None:
            self._set_state("JAMMED")
            return False

        self._ensure_payload_defaults(payload_entity)
        gate = self._audit_payload_lifecycle(payload_entity)

        if gate == "bottom":
            self.resolve_exit_path(payload_entity, 0.0, [], active_instances or {})
            return True

        if gate == "top":
            self.resolve_exit_path(payload_entity, -1.0, [], active_instances or {}) # -1 triggers error path
            return True

        self.current_payload_uuid = payload_entity.uuid
        self._set_state("PROCESSING")
        self._start_worker(payload_entity)
        return True

    def _apply_score_modifier(self, payload_entity: GamePart, route_rule: Dict[str, Any]):
        payload = payload_entity.payload
        if "score" not in payload:
            payload["score"] = 100

        try:
            score_delta = int(route_rule.get("score", 0))
        except (TypeError, ValueError):
            score_delta = 0

        payload["score"] = max(0, int(payload.get("score", 100)) + score_delta)

        history = payload.get("processing_history", [])
        if not isinstance(history, list):
            history = []
        history.append((self.uuid, score_delta))
        payload["processing_history"] = history

    def _spawn_fatal_label(self, entities: List[GamePart], reason: str):
        label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, reason)
        entities.append(label)

    # Removed: _find_matching_pipe_for_state — superseded by resolve_exit_path
    # Removed: _eject_payload — superseded by resolve_exit_path
    # Removed: draw — handled by FlowEntity

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        if self._is_destroyed:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            return

        while not self.queue.empty():
            result_data = self.queue.get()
            payload_uuid = result_data.get("payload_uuid")
            result = result_data.get("result")

            payload_entity = active_instances.get(payload_uuid)

            if payload_entity is None or getattr(payload_entity, "to_delete", False):
                self.current_payload_uuid = None
                continue

            try:
                state_value = float(result)
            except (TypeError, ValueError):
                # M32: Treat invalid results as error state 0
                state_value = 0.0
                print(f"🏭 [Factory Debug] Engine error: non-numeric state {result}")

            # Apply score modifier if not already done
            route_rule = find_route(state_value, self.get_property("routing", []))
            if route_rule and not result_data.get("_score_applied", False):
                self._apply_score_modifier(payload_entity, route_rule)
                result_data["_score_applied"] = True

            # Use resolve_exit_path for Pipe, Explicit Rule, or Hard Exit
            exit_result = self.resolve_exit_path(
                payload_entity, state_value, entities, active_instances
            )

            if exit_result == "pipe":
                self.current_payload_uuid = None
                if state_value <= 0:
                    self._set_state("FATAL")
                else:
                    self._set_state("IDLE")
            elif exit_result == "jammed":
                self._set_state("JAMMED")
                self.current_payload_uuid = payload_entity.uuid
                self.queue.put(result_data)
                break
            else: # ejected
                self.current_payload_uuid = None
                # resolve_exit_path handles FATAL/WRITING state based on Zero Rule

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        # --- SIGNAL BROADCAST (M32: use inherited broadcast_status) ---
        if getattr(self, "needs_broadcast", False):
            self.needs_broadcast = False
            self.broadcast_status(active_instances or {})

        # --- PROCESS SIGNALS (M32: use inherited _process_incoming_signal) ---
        self._process_incoming_signal()

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
            if self.cooldown_timer > 0.0:
                self._set_state("COOLDOWN")
            elif self.visual_state == "COOLDOWN":
                self._set_state("IDLE")

        if self.visual_state not in {"PROCESSING", "FATAL", "JAMMED", "COOLDOWN", "EMITTING"}:
            self._set_state("IDLE")

        # Milestone 40 Fix: Poll async engine results
        self.poll_results(entities, active_instances or {})