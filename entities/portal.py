import pygame
import pymunk
import os
import math
from typing import List, Dict
from entities.base import GamePart
from utils.asset_manager import asset_manager

class PortalPart(GamePart):
    """
    Quantum Portal Entity.
    Absorbs payloads and teleports them to a linked target_uuid portal after a brief delay.
    """
    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        self.transit_queue = []
        self.visual_state = "IDLE"
        self.flash_timer = 0
        
        # Portals are sensors (objects fall into them)
        if self.shape:
            self.shape.sensor = True
            
        if self.body:
            self.body.body_type = pymunk.Body.KINEMATIC
            
        self.properties.setdefault("transit_time", 0.5)
        self.properties.setdefault("capacity", 5)
        
        width = int(float(self.get_property("width", 80)))
        height = int(float(self.get_property("height", 80)))
        
        # Generate default visuals
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (150, 50, 255, 180), (0, 0, width, height))
        pygame.draw.ellipse(surf, (200, 150, 255), (0, 0, width, height), 4)
        self.base_texture = surf
        
        icon_path = f"assets/icons/{self.variant_key}_button.png"
        if not os.path.exists(icon_path):
            os.makedirs("assets/icons", exist_ok=True)
            icon_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            scaled_frame = pygame.transform.smoothscale(surf, (36, 36))
            icon_surf.blit(scaled_frame, (2, 2))
            try:
                pygame.image.save(icon_surf, icon_path)
            except Exception:
                pass

    def ingest_payload(self, payload_entity: GamePart) -> bool:
        capacity = int(self.get_property("capacity", 5))
        if len(self.transit_queue) >= capacity:
            return False
            
        payload_entity.is_hidden = True
        if getattr(payload_entity, "body", None):
            payload_entity.body.velocity = (0, 0)
            payload_entity.body.angular_velocity = 0
            
        self.transit_queue.append({
            "entity": payload_entity,
            "payload_uuid": payload_entity.uuid,
            "timer": float(self.get_property("transit_time", 0.5))
        })
        self.flash_timer = 15
        return True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        if game_state.get("mode") != "PLAY":
            return
            
        if self.flash_timer > 0:
            self.flash_timer -= 1
            
        target_uuid = self.get_property("target_uuid")
        target_portal = active_instances.get(target_uuid) if active_instances else None
        
        for item in self.transit_queue:
            item["timer"] -= dt
            
            if item["timer"] <= 0:
                if target_portal and hasattr(target_portal, "body") and target_portal.body:
                    # Eject from target portal
                    payload = item["entity"]
                    payload.is_hidden = False
                    
                    # Eject downwards slightly below the target portal
                    px, py = target_portal.body.position
                    payload.body.position = (px, py + 50)
                    payload.body.velocity = (0, 150) # Shoot out
                    
                    # Physics Re-indexing: Ensure the engine detects the teleportation immediately
                    if self.body and self.body.space:
                        self.body.space.reindex_shapes_for_body(payload.body)
                    
                    target_portal.flash_timer = 15
                    item["to_remove"] = True
                else:
                    # Target missing/deleted, dump it back out of THIS portal
                    item["entity"].is_hidden = False
                    item["to_remove"] = True

        self.transit_queue = [item for item in self.transit_queue if not item.get("to_remove")]

    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        if not self.body:
            return
            
        # Draw a glowing center when active
        if self.flash_timer > 0 or len(self.transit_queue) > 0:
            pos = self.body.position
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
            
            glow_radius = 20 + math.sin(pygame.time.get_ticks() / 100.0) * 5
            pygame.draw.circle(surface, (255, 200, 255), (int(screen_x), int(screen_y)), int(glow_radius))