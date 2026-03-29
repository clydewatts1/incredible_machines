import pygame
import pymunk
import math
from typing import Any, Dict, List, Optional

from entities.base import GamePart, FlowEntity

def get_pipe_curve_point(start_pos, end_pos, t):
    """Calculates a point on a quadratic Bezier curve and returns pymunk.Vec2d."""
    mid_x = (start_pos[0] + end_pos[0]) / 2
    control = (mid_x, start_pos[1])
    
    inv_t = 1.0 - t
    x = inv_t**2 * start_pos[0] + 2 * inv_t * t * control[0] + t**2 * end_pos[0]
    y = inv_t**2 * start_pos[1] + 2 * inv_t * t * control[1] + t**2 * end_pos[1]
    return pymunk.Vec2d(x, y)

class DataPipePart(FlowEntity):
    """
    Kinematic entity that moves payloads along a visual path.
    Inherits from FlowEntity to participate in standardized signaling.
    """
    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        # Ensure kinematic body for pipes
        if self.body:
            self.body.body_type = pymunk.Body.KINEMATIC
            
        self.pos = (x, y)
        self.transit_queue = [] # List of {payload, start_time, duration}
        self.visual_state = "IDLE"
        
        # FR-003 Properties
        self.properties.setdefault("source_uuid", "")
        self.properties.setdefault("target_uuid", "")
        self.properties.setdefault("capacity", 5)
        self.properties.setdefault("transit_time", 2.0)
        self.properties.setdefault("route_state", "any") # FR-002: Default to wildcard routing

        self.logic_signal = "IDLE"
        self.last_broadcast_signal = None

    def ingest_payload(self, payload):
        """Standard FlowEntity ingestion."""
        # Sanity check for payload body
        if not payload or not payload.body:
             return False

        capacity = int(self.get_property("capacity", 5))
        if len(self.transit_queue) >= capacity:
            return False
            
        duration = float(self.get_property("transit_time", 2.0))
        self.transit_queue.append({
            "payload": payload,
            "start_time": 0.0,
            "duration": duration
        })
        
        # Set payload to kinematic and hide while in transit
        payload.body.body_type = pymunk.Body.KINEMATIC
        payload.is_hidden = True
            
        return True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        # 1. Standard FlowEntity signal processing
        super().update_logic(dt, game_state, entities, active_instances)
        
        # Use passed-in instances or cached ref
        instances = active_instances or getattr(self, "active_instances_ref", {})
        
        # 2. Determine current signal based on internal state + downstream pressure
        current_signal = "IDLE"
        capacity = int(self.get_property("capacity", 5))
        
        if self.downstream_status == "JAMMED" or len(self.transit_queue) >= capacity:
            current_signal = "JAMMED"
        
        # 3. Delta Threshold Signaling (FR-003)
        if current_signal != self.last_broadcast_signal:
            self.logic_signal = current_signal
            self.last_broadcast_signal = current_signal
            self.broadcast_status(instances)
            
        # 4. Move payloads along the pipe
        if not self.is_paused:
            for item in list(self.transit_queue):
                if item["start_time"] < item["duration"]:
                    item["start_time"] = min(item["duration"], item["start_time"] + dt)
                
                if item["start_time"] >= item["duration"]:
                    target_uuid = self.get_property("target_uuid", "")
                    target_node = instances.get(target_uuid)
                    
                    payload = item["payload"]
                    if target_node and hasattr(target_node, "ingest_payload"):
                        # If the target accepts it, remove from queue
                        if target_node.ingest_payload(payload, instances):
                            self.transit_queue.remove(item)
                            payload.is_hidden = False
                            if payload.body:
                                payload.body.body_type = pymunk.Body.DYNAMIC
                            continue

    def draw(self, surface, camera):
        instances = getattr(self, "active_instances_ref", {})
        source_node = instances.get(self.get_property("source_uuid", ""))
        target_node = instances.get(self.get_property("target_uuid", ""))
        
        if not source_node or not target_node:
            return

        # Calculate curve positions
        p1 = camera.world_to_screen(source_node.body.position.x, source_node.body.position.y)
        p2 = camera.world_to_screen(target_node.body.position.x, target_node.body.position.y)
        
        points = []
        for i in range(21):
            t = i / 20.0
            pt = get_pipe_curve_point(p1, p2, t)
            points.append((int(pt.x), int(pt.y)))
            
        # Draw the pipe body
        if len(points) > 1:
            # Teal for active, red for jammed
            color = (150, 230, 255, 180) if self.logic_signal != "JAMMED" else (255, 100, 100, 180)
            
            # Draw glow and core
            pygame.draw.lines(surface, (*color[:3], 80), False, points, 18)
            pygame.draw.lines(surface, color, False, points, 6)
            
        # Draw payloads in transit
        for item in self.transit_queue:
            prog = item["start_time"] / item["duration"]
            pos = get_pipe_curve_point(p1, p2, prog)
            # Match payload color or standard white
            pygame.draw.circle(surface, (255, 255, 255), (int(pos.x), int(pos.y)), 10)
            pygame.draw.circle(surface, (200, 240, 255), (int(pos.x), int(pos.y)), 10, 2)