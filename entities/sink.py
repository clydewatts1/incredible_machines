import copy
import queue
import threading
import time
from typing import Any, Dict, List, Optional

import pymunk

import constants
from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.exporters import get_exporter


class DataSink(FlowEntity):
    """
    Asynchronous sink node for external data egestion.
    Terminal node with consumption-based backpressure (M32).
    """

    can_accept_input = True
    can_provide_output = False

    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "data_sink"):
        super().__init__(space, x, y, variant_name)

        # --- Default Properties ---
        self.properties.setdefault("accepts_types", ["all"])
        self.properties.setdefault("exporter_type", "null")
        self.properties.setdefault("export", {})
        self.properties.setdefault("consumption_time", 1.0)
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        self.queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.consumption_timer: float = 0.0
        self.current_consuming_payload: Optional[GamePart] = None

        # Background Worker for Exports
        self._worker_running = True
        self._fatal_latched = False
        self._is_destroyed = False
        self._flush_requested = False
        self._processed_entity_uuids = set()

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        self.visual_state = "IDLE"

    # Redundant text drawing and visual creation methods removed per M32 requirements

    def _worker_loop(self) -> None:
        exporter = None
        exporter_type = str(self.get_property("exporter_type", "null"))
        export_config = copy.deepcopy(self.get_property("export", {}))

        try:
            exporter = get_exporter(exporter_type, export_config)
        except Exception as exc:
            self.result_queue.put({"type": "fatal", "error": str(exc)})

        while self._worker_running:
            if self._fatal_latched:
                time.sleep(1.0)
                continue
            try:
                item = self.queue.get(timeout=0.1)
                if exporter:
                    data = item.get("data", {})
                    data["score"] = item.get("score", 0.0)
                    exporter.export(data)
            except queue.Empty:
                if self._flush_requested: break
                continue
            except Exception as exc:
                self.result_queue.put({"type": "fatal", "error": str(exc)})
                break

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, GamePart] = None) -> bool:
        if self._is_destroyed or self._fatal_latched:
            return False

        # Milestone 32: Standardized Ingestion & Signaling
        if self.visual_state != "IDLE":
            print(f"DEBUG: Sink {self.uuid} Rejecting ball - NOT IDLE (state: {self.visual_state})")
            return False

        # Types check
        payload = getattr(payload_entity, "payload", None)
        if not isinstance(payload, dict):
            print(f"DEBUG: Sink {self.uuid} Rejecting ball - No payload dict")
            return False
        
        accept_list = self.get_property("accepts_types", ["all"])
        if isinstance(accept_list, str): accept_list = [accept_list]
        
        if "all" not in accept_list:
            # Fallback to variant_key if payload 'type' is missing
            p_type = str(payload.get("type", payload_entity.variant_key)).lower()
            if p_type not in [t.lower() for t in accept_list]:
                print(f"DEBUG: Sink {self.uuid} Rejecting ball - Type mismatch: {p_type} not in {accept_list}")
                return False

        print(f"DEBUG: Sink {self.uuid} ACCEPTING ball {payload_entity.uuid}")

        # Ingest
        self._processed_entity_uuids.add(payload_entity.uuid)
        self.visual_state = "INGESTING"
        self.consumption_timer = float(self.get_property("consumption_time", 1.0))
        self.current_consuming_payload = payload_entity
        payload_entity.is_hidden = True
        
        # Immediate signal to upstream neighbors (tells them we are now BUSY/FULL)
        self.broadcast_status(active_instances or {})

        # Queue for actual export logic
        self.queue.put({
            "data": copy.deepcopy(payload.get("data", {})),
            "score": float(payload.get("score", 0.0))
        })
        
        payload_entity.to_delete = False # Explicitly hide and wait for consumption
        return True

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]) -> None:
        while not self.result_queue.empty():
            event = self.result_queue.get()
            if event.get("type") == "fatal":
                self._fatal_latched = True
                self.visual_state = "FATAL"
                label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, f"fatal: {event.get('error')}")
                entities.append(label)

    def cleanup(self) -> None:
        self._is_destroyed = True
        self._worker_running = False
        self._flush_requested = True
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

    def destroy(self) -> None:
        self.cleanup()

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Optional[Dict[str, GamePart]] = None):
        if game_state.get("mode") != "PLAY":
            return

        # Milestone 32: Consumption Handshake
        self._process_incoming_signal() # Handled by FlowEntity; terminal node still observes for state uniformity

        if self.visual_state == "INGESTING":
            self.consumption_timer -= dt
            if self.consumption_timer <= 0.0:
                self.visual_state = "IDLE"
                if self.current_consuming_payload:
                    self.current_consuming_payload.to_delete = True
                    self.current_consuming_payload = None
                # Notify upstream that we are clear to receive again
                self.broadcast_status(active_instances or {})

        self.poll_results(entities, active_instances or {})