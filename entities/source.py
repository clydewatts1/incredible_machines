import time
from typing import Any, Dict, List, Optional

import queue
import threading
import copy
import pygame
import pymunk

import constants
from entities.base import GamePart, FlowEntity
from utils.asset_manager import asset_manager
from utils.sound_manager import sound_manager
from utils.generators import get_generator
from entities.floating_label import FloatingTextLabel


class DataSource(FlowEntity):
    """
    Standardized emitter node that generates payload balls at intervals.
    Start node with handshake-based emission (M32).
    """

    can_accept_input = False
    can_provide_output = True

    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "data_source"):
        super().__init__(space, x, y, variant_name)

        # --- Default Properties ---
        self.properties.setdefault("emit_interval", 2.0)
        self.properties.setdefault("output_variant", "payload_ball")
        self.properties.setdefault("exit_velocity", 150.0)
        self.properties.setdefault("exit_angle", 0.0)
        self.properties.setdefault("active_side", "bottom")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        self.emit_interval = max(0.1, float(self.get_property("emit_interval", 2.0)))
        self.emit_timer = 0.0
        
        # Generator Integration (M23/M32)
        self.queue = queue.Queue()
        self.generator = None
        self._worker_running = False
        
        self.visual_state = "IDLE"

    # Redundant animation and physics methods removed per M32 requirements

    def _emit_ball(self, entities: List[GamePart], active_instances: Dict[str, GamePart], data: Optional[Dict[str, Any]] = None):
        """Standardized emission using main.create_part and resolve_exit_path."""
        if data is None and str(self.get_property("engine_type", "null")) != "null":
            # If the generator returned None on a real engine (CSV/MCP), it's just empty/pacing.
            self.visual_state = "IDLE"
            return

        # Local import to avoid circular dependency with main.py
        from main import create_part
        
        variant = str(self.get_property("output_variant", "payload_ball"))
        ball = create_part(self.space, self.body.position.x, self.body.position.y, variant)
        
        if ball:
            # Metadata initialization
            if hasattr(ball, "payload") and isinstance(ball.payload, dict):
                ball.payload["origin_uuid"] = self.uuid
                ball.payload.setdefault("score", 100)
                if data:
                    # Milestone 35 Fix: Handle both nested 'data' and top-level keys
                    if "data" not in ball.payload:
                        ball.payload["data"] = {}
                    ball.payload["data"].update(data)
            
            entities.append(ball)
            if active_instances is not None:
                active_instances[ball.uuid] = ball

            # Milestone 35: Recording Hook
            import builtins
            if hasattr(builtins, "register_record_input"):
                builtins.register_record_input(ball.payload)

            # Hybrid Routing: Pipe > Vector fallback
            # Sources use state '10' for standardized emission
            self.resolve_exit_path(ball, 10, entities, active_instances)

        # Cycle complete
        self.visual_state = "IDLE"

    def _start_worker(self):
        """Starts a background thread to fetch the next data item."""
        if self._worker_running or self._is_destroyed:
            return

        engine_type = str(self.get_property("engine_type", "null"))
        instructions = copy.deepcopy(self.get_property("instructions", {}))
        
        # Milestone 35 FIX: Log what we are actually using
        print(f"DEBUG: Source {self.uuid} starting worker for {engine_type} using {instructions.get('filepath')}")

        def _worker():
            try:
                if self.generator is None:
                    self.generator = get_generator(engine_type)
                
                # Fetch data (blocking call in thread)
                data = self.generator.fetch_next(instructions)
                
                if not self._is_destroyed:
                    self.queue.put({"type": "data", "data": data})
            except Exception as e:
                if not self._is_destroyed:
                    self.queue.put({"type": "fatal", "error": str(e)})
            finally:
                self._worker_running = False

        self._worker_running = True
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def reset_flow_logic(self):
        super().reset_flow_logic()
        self.emit_timer = 0.0
        # Generator cleanup handled by FlowEntity.cleanup/reset_flow_logic queue drain

    def cleanup(self):
        super().cleanup()
        if self.generator:
            self.generator.cleanup()

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        while not self.queue.empty():
            msg = self.queue.get()
            if msg["type"] == "fatal":
                self.visual_state = "FATAL"
                print(f"ERROR: Source {self.uuid} generator fatal: {msg['error']}")
                label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, f"fatal: {msg['error']}")
                entities.append(label)
            elif msg["type"] == "data":
                self.visual_state = "WRITING"
                self._emit_ball(entities, active_instances, msg.get("data"))

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Optional[Dict[str, GamePart]] = None):
        if game_state.get("mode") != "PLAY":
            return

        # Milestone 32: Receiver-Led Handshake
        self._process_incoming_signal() 

        # Handshake: If downstream is FULL, JAMMED, etc., stay in IDLE and pause timer
        if self.is_paused:
            self.visual_state = "IDLE"
            return

        # Timer-based emission
        if self.visual_state == "IDLE":
            self.emit_timer += dt
            if self.emit_timer >= self.emit_interval:
                self.emit_timer = 0.0
                self.visual_state = "POLLING"
                self._start_worker()

        self.poll_results(entities, active_instances or {})