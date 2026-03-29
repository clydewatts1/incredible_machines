import math
from typing import Dict, Any, List, Optional
import pygame
import pymunk
from entities.base import FlowEntity

class WarehousePart(FlowEntity):
    """
    WOLF-style buffer/Interaction entity (N-In, N-Out Broker).
    Exposes `last_state` reliably to downstream Guards.
    """
    can_accept_input = True
    can_provide_output = True

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.stored_payload_uuids = []
        self.release_timer = 0.0

    def extract_payload(self, payload_uuid):
        """API for Guard nodes to surgically pull specific payloads."""
        if payload_uuid in self.stored_payload_uuids:
            self.stored_payload_uuids.remove(payload_uuid)
            return payload_uuid
        return None

    @property
    def last_state(self):
        """FR-004: Reflects internal buffer status. IDLE if empty, ACTIVE if populated."""
        return "ACTIVE" if len(self.stored_payload_uuids) > 0 else "IDLE"

    def ingest_payload(self, payload_entity, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        capacity = int(self.get_property("capacity", 20))
        if len(self.stored_payload_uuids) >= capacity:
            return False 

        input_side = str(self.get_property("input_side", "top")).lower()
        if getattr(payload_entity, "body", None):
            # Proximity check
            dx = payload_entity.body.position.x - self.body.position.x
            dy = payload_entity.body.position.y - self.body.position.y
            if input_side == "top" and dy > 5: return False
            elif input_side == "left" and dx > 5: return False
            elif input_side == "right" and dx < -5: return False
            elif input_side == "bottom" and dy < -5: return False

            if not hasattr(payload_entity, "payload") or not isinstance(payload_entity.payload, dict):
                payload_entity.payload = {}
            vx, vy = payload_entity.body.velocity
            payload_entity.payload["_entry_speed"] = math.hypot(vx, vy)

        if payload_entity.uuid not in self.stored_payload_uuids:
            self.stored_payload_uuids.append(payload_entity.uuid)
            
        self._set_state("INGESTING")
        return True

    def _eject_payload(self, payload_entity):
        width = float(self.get_property("width", 96))
        height = float(self.get_property("height", 96))
        half_w, half_h = width / 2.0, height / 2.0
        margin = 25.0
        fx, fy = self.body.position.x, self.body.position.y
        output_side = str(self.get_property("output_side", "bottom")).lower()
        
        if output_side == "bottom":
            eject_x, eject_y, default_angle = fx, fy + half_h + margin, 270.0
        elif output_side == "left":
            eject_x, eject_y, default_angle = fx - half_w - margin, fy, 180.0
        elif output_side == "right":
            eject_x, eject_y, default_angle = fx + half_w + margin, fy, 0.0
        else: 
            eject_x, eject_y, default_angle = fx, fy - half_h - margin, 90.0
            
        payload_entity.body.position = (eject_x, eject_y)
        speed = float(self.get_property("velocity", payload_entity.payload.get("_entry_speed", 150.0)) or 150.0)
        angle_deg = float(self.get_property("angle", default_angle) or default_angle)
        world_angle = math.radians(angle_deg)
        
        payload_entity.body.velocity = (speed * math.cos(world_angle), speed * -math.sin(world_angle))
        payload_entity.is_hidden = False

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)

        if game_state.get("mode") != "PLAY":
            return

        capacity = int(self.get_property("capacity", 20))

        if self.stored_payload_uuids and active_instances:
            self.stored_payload_uuids = [
                uid for uid in self.stored_payload_uuids 
                if uid in active_instances and not getattr(active_instances[uid], 'to_delete', False)
            ]

        is_physically_full = len(self.stored_payload_uuids) >= capacity
        is_logically_full = is_physically_full or self.downstream_status in ["FULL", "JAMMED"]
        
        self._set_state("FULL" if is_logically_full else ("IDLE" if not self.stored_payload_uuids else "INGESTING"))

        auto_release = str(self.get_property("auto_release", "true")).lower() == "true"
        if not self.stored_payload_uuids or not auto_release:
            return

        self.release_timer -= dt
        if self.release_timer <= 0 and self.downstream_status == "IDLE":
            uid_to_release = self.stored_payload_uuids.pop(0)
            payload_to_release = active_instances.get(uid_to_release) if active_instances else None
            if payload_to_release:
                self._eject_payload(payload_to_release)
            
            try:
                self.release_timer = float(self.get_property("release_interval", 1.0))
            except ValueError:
                self.release_timer = 1.0

    def draw(self, surface, camera=None):
        if not self.body: return
        pos = self.body.position
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
        
        width = float(self.get_property("width", 96.0))
        height = float(self.get_property("height", 96.0))

        color = (50, 60, 80)
        if self.visual_state == "FULL": color = (100, 50, 50)
        
        pygame.draw.rect(surface, color, (screen_x - width/2, screen_y - height/2, width, height))
        pygame.draw.rect(surface, (100, 150, 255), (screen_x - width/2, screen_y - height/2, width, height), 2)
            
        count = len(self.stored_payload_uuids)
        capacity = int(self.get_property("capacity", 20))
        
        font = pygame.font.SysFont(None, 24)
        txt_color = (0, 255, 0) if count < capacity else (255, 100, 100)
        text_surf = font.render(f"{count}/{capacity}", True, txt_color)
        surface.blit(text_surf, text_surf.get_rect(center=(int(screen_x), int(screen_y))))