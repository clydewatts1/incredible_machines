import time
from typing import Any, Dict, List, Optional

import pygame
import pymunk

import constants
from entities.base import GamePart, FlowEntity
from utils.asset_manager import asset_manager
from utils.sound_manager import sound_manager


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

        self.emit_interval = float(self.get_property("emit_interval", 2.0))
        self.emit_timer = 0.0
        
        self.visual_state = "IDLE"

    # Redundant animation and physics methods removed per M32 requirements

    def _emit_ball(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        """Standardized emission using main.create_part and resolve_exit_path."""
        # Local import to avoid circular dependency with main.py
        from main import create_part
        
        variant = str(self.get_property("output_variant", "payload_ball"))
        ball = create_part(self.space, self.body.position.x, self.body.position.y, variant)
        
        if ball:
            # Metadata initialization
            if hasattr(ball, "payload") and isinstance(ball.payload, dict):
                ball.payload["origin_uuid"] = self.uuid
                ball.payload.setdefault("score", 100)
            
            entities.append(ball)
            if active_instances is not None:
                active_instances[ball.uuid] = ball

            # Hybrid Routing: Pipe > Vector fallback
            # Sources use state '10' for standardized emission
            self.resolve_exit_path(ball, 10, entities, active_instances)

        # Cycle complete
        self.visual_state = "IDLE"

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[GamePart], active_instances: Optional[Dict[str, GamePart]] = None):
        if game_state.get("mode") != "PLAY":
            return

        # Milestone 32: Receiver-Led Handshake
        self._process_incoming_signal() # Inherited from FlowEntity, updates self.is_paused

        # Handshake: If downstream is FULL, JAMMED, etc., stay in IDLE and pause timer
        if self.is_paused:
            self.visual_state = "IDLE"
            return

        # Timer-based emission
        self.emit_timer += dt
        if self.emit_timer >= self.emit_interval:
            self.emit_timer = 0.0
            self.visual_state = "WRITING"
            self._emit_ball(entities, active_instances or {})