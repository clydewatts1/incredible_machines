import math

import pygame
import pymunk
from typing import Any, Dict

from entities.base import GamePart


def get_pipe_curve_point(start_pos, end_pos, t):
    """Return one point on a swaying cubic Bezier between start and end."""
    p0 = pygame.math.Vector2(start_pos)
    p3 = pygame.math.Vector2(end_pos)
    dx = p3.x - p0.x
    dy = p3.y - p0.y
    dist = p0.distance_to(p3)

    time_sec = pygame.time.get_ticks() / 1000.0
    phase = (p0.x + p0.y) * 0.01
    max_sway = min(30.0, dist * 0.2)

    sway1 = math.sin(time_sec * 1.5 + phase) * max_sway
    sway2 = math.sin(time_sec * 2.0 + phase + 1.0) * max_sway

    if abs(dx) > abs(dy):
        p1 = p0 + pygame.math.Vector2(dx * 0.5, sway1)
        p2 = p0 + pygame.math.Vector2(dx * 0.5, dy + sway2)
    else:
        p1 = p0 + pygame.math.Vector2(sway1, dy * 0.5)
        p2 = p0 + pygame.math.Vector2(dx + sway2, dy * 0.5)

    u = 1.0 - t
    return (u ** 3) * p0 + 3.0 * (u ** 2) * t * p1 + 3.0 * u * (t ** 2) * p2 + (t ** 3) * p3


class DataPipePart(GamePart):
    """Logical transit tube that routes payloads directly between entities."""

    def __init__(self, space, x, y, property_key="data_pipe"):
        super().__init__(space, x, y, property_key)
        self.space = space

        # Purely logical/visual transit queue.
        self.transit_queue = []
        self._cached_start_pos = None
        self._cached_end_pos = None

        # Replace default physics with a tiny static sensor node for selection only.
        if self.shape and self.shape in space.shapes:
            space.remove(self.shape)
        if self.body and self.body in space.bodies and self.body != space.static_body:
            space.remove(self.body)

        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, 12)
        self.shape.sensor = True
        self.shapes = [self.shape]
        space.add(self.body, self.shape)

        self.properties.setdefault("source_uuid", "")
        self.properties.setdefault("target_uuid", "")
        self.properties.setdefault("capacity", 5)
        self.properties.setdefault("transit_time", 2.0)
        self.properties.setdefault("route_state", 10.0)

    def apply_draft_overrides(self, new_dict):
        super().apply_draft_overrides(new_dict)
        # Clear cached positions to force recalculation if endpoints changed
        if "source_uuid" in new_dict or "target_uuid" in new_dict:
            self._cached_start_pos = None
            self._cached_end_pos = None

    def receive_signal(self, sender, signal_data: Dict[str, Any]):
        """Forward signals to target for event-driven workflows."""
        if signal_data.get("status") == "REFRESH":
            pass

        target_uuid = self.get_property("target_uuid")
        # Milestone 38 Fix: Favor signal_data instances over cached ref to avoid race conditions
        instances = signal_data.get("active_instances", getattr(self, "active_instances_ref", {}))
        
        if target_uuid and instances:
            target = instances.get(target_uuid)
            if target and hasattr(target, "receive_signal"):
                target.receive_signal(self, signal_data)

    def ingest_payload(self, payload_entity, active_instances: Dict[str, Any] = None, **kwargs):
        capacity = int(self.get_property("capacity", 5))
        if len(self.transit_queue) >= capacity:
            return False

        payload_entity.is_hidden = True
        if getattr(payload_entity, "body", None):
            payload_entity.body.velocity = (0.0, 0.0)
            payload_entity.body.angular_velocity = 0.0
            
            # Milestone 34/35/36 Fix: Remove from space so it doesn't stay in sensor areas
            if self.space:
                # 1. Remove Shapes
                for s in getattr(payload_entity, "shapes", [getattr(payload_entity, "shape", None)]):
                    if s and s in self.space.shapes:
                        self.space.remove(s)
                # 2. Remove Body
                if payload_entity.body and payload_entity.body in self.space.bodies:
                    self.space.remove(payload_entity.body)

        self.transit_queue.append({"entity": payload_entity, "progress": 0.0})
        return True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)

        if not isinstance(active_instances, dict):
            return

        # Milestone 38 Fix: Store reference for signal forwarding
        self.active_instances_ref = active_instances

        source_uuid = self.get_property("source_uuid", "")
        target_uuid = self.get_property("target_uuid", "")
        source = active_instances.get(source_uuid) if source_uuid else None
        target = active_instances.get(target_uuid) if target_uuid else None

        # Auto-Register with source for signal distribution
        if source and self.uuid not in source.connected_uuids:
            source.connected_uuids.append(self.uuid)

        if source and getattr(source, "body", None):
            self._cached_start_pos = (source.body.position.x, source.body.position.y)
        if target and getattr(target, "body", None):
            self._cached_end_pos = (target.body.position.x, target.body.position.y)

        if self._cached_start_pos and self._cached_end_pos:
            mid_x = (self._cached_start_pos[0] + self._cached_end_pos[0]) * 0.5
            mid_y = (self._cached_start_pos[1] + self._cached_end_pos[1]) * 0.5
            self.body.position = (mid_x, mid_y)

        if game_state.get("mode") != "PLAY":
            return

        transit_time = float(self.get_property("transit_time", 2.0))
        if transit_time <= 0.0:
            transit_time = 0.01

        for item in self.transit_queue:
            item["progress"] = min(1.0, float(item.get("progress", 0.0)) + (dt / transit_time))

        i = 0
        while i < len(self.transit_queue):
            item = self.transit_queue[i]
            if item["progress"] < 1.0:
                i += 1
                continue

            payload_entity = item.get("entity")
            if payload_entity is None or getattr(payload_entity, "to_delete", False):
                self.transit_queue.pop(i)
                continue

            if target and hasattr(target, "ingest_payload"):
                accepted = bool(target.ingest_payload(payload_entity, active_instances))
                if accepted:
                    self.transit_queue.pop(i)
                    continue

            # Backpressure: remain queued at end of pipe.
            item["progress"] = 1.0
            i += 1

    def draw(self, surface, camera=None, **kwargs):
        if self._cached_start_pos and self._cached_end_pos:
            start_x, start_y = self._cached_start_pos
            end_x, end_y = self._cached_end_pos
        else:
            start_x, start_y = self.body.position.x, self.body.position.y
            end_x, end_y = self.body.position.x, self.body.position.y

        if camera:
            start_x, start_y = camera.world_to_screen(start_x, start_y)
            end_x, end_y = camera.world_to_screen(end_x, end_y)

        capacity = int(self.get_property("capacity", 5))
        is_full = len(self.transit_queue) >= capacity

        tube_rgba = (255, 90, 60, 110) if is_full else (110, 210, 255, 90)
        core_rgba = (255, 130, 90, 200) if is_full else (180, 235, 255, 190)

        points = [get_pipe_curve_point((start_x, start_y), (end_x, end_y), idx / 24.0) for idx in range(25)]
        int_points = [(int(p.x), int(p.y)) for p in points]

        tube_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.lines(tube_surface, tube_rgba, False, int_points, 18)
        pygame.draw.lines(tube_surface, core_rgba, False, int_points, 6)
        surface.blit(tube_surface, (0, 0))

        for item in self.transit_queue:
            payload_entity = item.get("entity")
            progress = float(item.get("progress", 0.0))
            point = get_pipe_curve_point((start_x, start_y), (end_x, end_y), progress)

            payload_color = (0, 255, 255)
            if payload_entity is not None:
                payload = getattr(payload_entity, "payload", {})
                if isinstance(payload, dict) and hasattr(payload_entity, "get_color_for_score"):
                    payload_color = payload_entity.get_color_for_score(payload.get("score", 100))

            pygame.draw.circle(surface, payload_color, (int(point.x), int(point.y)), 9)
            pygame.draw.circle(surface, (255, 255, 255), (int(point.x), int(point.y)), 9, 1)

        mid_x = int((start_x + end_x) * 0.5)
        mid_y = int((start_y + end_y) * 0.5)
        pygame.draw.circle(surface, core_rgba, (mid_x, mid_y), 7)
        pygame.draw.circle(surface, (255, 255, 255), (mid_x, mid_y), 7, 1)

    def cleanup(self):
        # M27 Extension: Drop payloads at their exact Bezier positions
        start_pos = self._cached_start_pos or self.body.position
        end_pos = self._cached_end_pos or self.body.position
        
        for item in self.transit_queue:
            payload_entity = item.get("entity")
            if payload_entity is None:
                continue
                
            progress = float(item.get("progress", 0.0))
            # Calculate the exact Bezier point where they were in the pipe
            drop_point = get_pipe_curve_point(start_pos, end_pos, progress)
            
            payload_entity.is_hidden = False
            if getattr(payload_entity, "body", None):
                payload_entity.body.velocity = (0.0, 0.0)
                payload_entity.body.angular_velocity = 0.0
                payload_entity.body.position = (drop_point.x, drop_point.y)
                
                # Milestone 36 Fix: Re-add to space (Body FIRST)
                if self.space:
                    if payload_entity.body and payload_entity.body not in self.space.bodies:
                        self.space.add(payload_entity.body)
                    for s in getattr(payload_entity, "shapes", [getattr(payload_entity, "shape", None)]):
                        if s and s not in self.space.shapes:
                            self.space.add(s)
                    self.space.reindex_shapes_for_body(payload_entity.body)

        self.transit_queue.clear()
        super().cleanup()