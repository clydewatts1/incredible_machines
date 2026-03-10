"""
M24: DataSink entity.

Sensor-based ingestion node that captures payload-carrying entities, queues export
jobs, and performs asynchronous egestion through registry-selected exporters.
"""

from __future__ import annotations

import copy
import queue
import threading
import time
from typing import Any, Dict, List, Optional

import pymunk

import constants
from entities.active import FloatingTextLabel
from entities.base import GamePart
from utils.asset_manager import asset_manager
from utils.exporters import get_exporter
from utils.sound_manager import sound_manager


class DataSink(GamePart):
    """Asynchronous sink node for external data egestion."""

    VALID_STATES = {"OFF", "INITIALIZING", "IDLE", "INGESTING", "WRITING", "FATAL"}

    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "data_sink"):
        super().__init__(space, x, y, variant_name)

        self.queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()

        self.visual_state = "OFF"
        self._is_destroyed = False
        self._flush_requested = False
        self._accept_ingestion = True
        self._worker_running = True
        self._fatal_latched = False
        self._last_ingest_state_time = 0.0

        self.accepts_types = self.get_property("accepts_types", ["all"])
        if isinstance(self.accepts_types, str):
            self.accepts_types = [self.accepts_types]
        if not isinstance(self.accepts_types, list):
            self.accepts_types = ["all"]

        self.exporter_type = str(self.get_property("exporter_type", "null"))
        self.export_config = copy.deepcopy(self.get_property("export", {}))
        if not isinstance(self.export_config, dict):
            self.export_config = {}

        self._processed_entity_uuids = set()

        self._animation_textures = {}
        self._load_animation_textures()

        self._set_state("INITIALIZING")

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _load_animation_textures(self) -> None:
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
                    text_label=f"DataSink:{state_name}",
                )
            except Exception:
                pass

    def _set_state(self, new_state: str) -> None:
        if new_state not in self.VALID_STATES:
            return

        if new_state == "INGESTING":
            now = time.time()
            if (now - self._last_ingest_state_time) < constants.SINK_INGEST_STATE_COOLDOWN:
                return
            self._last_ingest_state_time = now

        old_state = self.visual_state
        if old_state == new_state:
            return

        self.visual_state = new_state
        sounds = self.get_property("sounds", {})
        if isinstance(sounds, dict):
            sound_file = sounds.get(new_state)
            if sound_file:
                try:
                    sound_manager.play_sound(sound_file)
                except Exception:
                    pass

    def _spawn_fatal_label(self, entities: List[GamePart], reason: str) -> None:
        label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, reason)
        entities.append(label)

    def _worker_loop(self) -> None:
        exporter = None

        try:
            exporter = get_exporter(self.exporter_type, self.export_config)
            self.result_queue.put({"type": "state", "state": "IDLE"})
        except Exception as exc:
            self.result_queue.put({"type": "fatal", "error": str(exc)})
            self._worker_running = False
            return

        try:
            while True:
                should_exit = self._flush_requested and self.queue.empty()
                if should_exit:
                    break

                try:
                    item = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                self.result_queue.put({"type": "state", "state": "WRITING"})
                try:
                    exporter.export(item)
                except Exception as exc:
                    self.result_queue.put({"type": "fatal", "error": str(exc)})
                finally:
                    self.queue.task_done()
                    if self.queue.empty() and not self._fatal_latched:
                        self.result_queue.put({"type": "state", "state": "IDLE"})

            exporter.flush()
        except Exception as exc:
            self.result_queue.put({"type": "fatal", "error": str(exc)})
        finally:
            try:
                if exporter is not None:
                    exporter.cleanup()
            except Exception as exc:
                self.result_queue.put({"type": "fatal", "error": str(exc)})
            self._worker_running = False

    def accepts_entity(self, entity: GamePart) -> bool:
        if not self._accept_ingestion or self._is_destroyed or self.visual_state == "FATAL":
            return False
        if entity.uuid in self._processed_entity_uuids:
            return False
        if "all" in self.accepts_types:
            return True
        return entity.variant_key in self.accepts_types

    def _build_queue_item(self, payload_entity: GamePart) -> Dict[str, Any]:
        payload = getattr(payload_entity, "payload", None)
        if not isinstance(payload, dict):
            payload = {}

        data = payload.get("data")
        if not isinstance(data, dict):
            data = {}

        score = payload.get("score", 0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0

        processing_history = payload.get("processing_history", [])
        if not isinstance(processing_history, list):
            processing_history = []

        return {
            "sink_uuid": self.uuid,
            "payload_uuid": payload_entity.uuid,
            "data": data,
            "score": score,
            "processing_history": processing_history,
            "ingested_at": time.time(),
        }

    def ingest_payload(self, payload_entity: GamePart) -> bool:
        if not self.accepts_entity(payload_entity):
            return False

        self._processed_entity_uuids.add(payload_entity.uuid)
        self._set_state("INGESTING")

        item = self._build_queue_item(payload_entity)
        self.queue.put(item)
        payload_entity.to_delete = True
        return True

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]) -> None:
        if self._is_destroyed:
            return

        polls = 0
        while not self.result_queue.empty() and polls < constants.MAX_BATCH_QUEUE_POLLS:
            polls += 1
            event = self.result_queue.get()
            event_type = event.get("type")

            if event_type == "state":
                state = event.get("state")
                if state:
                    self._set_state(str(state))
                continue

            if event_type == "fatal":
                self._fatal_latched = True
                self._accept_ingestion = False
                self._set_state("FATAL")
                reason = str(event.get("error", "Exporter failure"))
                self._spawn_fatal_label(entities, reason)

    def cleanup(self) -> None:
        if self._is_destroyed:
            return

        self._is_destroyed = True
        self._flush_requested = True
        self._accept_ingestion = False

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=constants.SINK_WORKER_JOIN_TIMEOUT_SECONDS)
            if self._worker_thread.is_alive():
                print("WARNING: DataSink worker did not terminate before timeout.")

        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

    def destroy(self) -> None:
        self.cleanup()

    def draw(self, surface, camera=None) -> None:
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            old_texture = self.base_texture
            self.base_texture = state_texture
            self.draw_texture(surface, camera=camera)
            self.base_texture = old_texture
            return
        super().draw(surface, camera=camera)

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Optional[Dict[str, GamePart]] = None):
        # Keep sink behavior stable in both EDIT and PLAY so queued writes can finish.
        return
