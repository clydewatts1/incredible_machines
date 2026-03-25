import pygame
import pymunk
from typing import Any, Dict, List, Optional
from entities.base import FlowEntity

class PressurePlatePart(FlowEntity):
    """
    Milestone 41: Pressure Plate Trigger.
    Detects when a dynamic body is on top and broadcasts a TRIGGER_EVENT signal.
    """
    def __init__(self, space: pymunk.Space, x: float, y: float, variant_name: str = "pressure_plate"):
        super().__init__(space, x, y, variant_name)
        
        # Default Properties
        self.properties.setdefault("width", 80.0)
        self.properties.setdefault("height", 10.0)
        self.properties.setdefault("is_sensor", False)
        self.properties.setdefault("cooldown", 0.5)
        
        # Logic State
        self.cooldown_timer = 0.0
        self.is_pressed = False
        self.last_pressed_state = False
        
        # M41: Configure shape sensor property
        is_sensor = self.get_property("is_sensor", False)
        for s in self.shapes:
            s.sensor = is_sensor

    def update_logic(self, dt: float, game_state: Dict[str, Any], entities: List[Any], active_instances: Optional[Dict[str, Any]] = None):
        if game_state.get("mode") != "PLAY":
            return

        super().update_logic(dt, game_state, entities, active_instances)
        
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            return

        # 1. Detection: Query the space for dynamic shapes overlapping with our plate
        # We query a slightly expanded area above the plate to ensure contact detection
        bb = self.shape.cache_bb()
        query_rect = pymunk.BB(bb.left + 2, bb.bottom - 5, bb.right - 2, bb.top + 2)
        
        # filter to avoid detecting ourselves or static bodies
        query_filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS() ^ 1) # assuming category 1 is static/base
        
        # In Pymunk, we can use bb_query or shape_query
        overlapping_shapes = self.space.bb_query(query_rect, query_filter)
        
        is_currently_pressed = False
        for s in overlapping_shapes:
            if s.body != self.space.static_body and s.body != self.body:
                is_currently_pressed = True
                break
        
        # 2. State Change & Signaling
        if is_currently_pressed and not self.last_pressed_state:
            # Triggered!
            self._trigger(active_instances)
        
        self.last_pressed_state = is_currently_pressed
        
        # Visual feedback: update state for sprite flipping if configured
        if is_currently_pressed:
            self._set_state("EMITTING")
        else:
            self._set_state("IDLE")

    def _trigger(self, active_instances):
        """Broadcasts the signal and starts cooldown."""
        self.cooldown_timer = float(self.get_property("cooldown", 0.5))
        
        # Broadcast the standard TRIGGER_EVENT signal
        signal = {
            "status": "EMITTING",
            "event": "TRIGGER_EVENT",
            "source_uuid": self.uuid
        }
        self.broadcast_status(active_instances, custom_signal=signal)
        
        # Play trigger sound if any
        # self.play_event_sound("trigger_sound") # Optional

    def draw(self, surface, camera=None, **kwargs):
        # Pressure plates are thin, so we use the base draw
        super().draw(surface, camera, **kwargs)
