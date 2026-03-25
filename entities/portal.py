import pygame
import pymunk
import os
import math
from typing import List, Dict, Any
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

    def ingest_payload(self, payload_entity: GamePart, active_instances: Dict[str, Any] = None, **kwargs) -> bool:
        """M36: Logical interface for incoming payloads from Pipes/Logic entities."""
        return self.warp_payload(payload_entity)

    def warp_payload(self, payload_entity: GamePart, entities: List[GamePart] = None) -> bool:
        capacity = int(self.get_property("capacity", 5))
        if len(self.transit_queue) >= capacity:
            return False
            
        # Milestone 36 Bugfix: Prevent duplicate entry in queue for same payload
        if any(item["payload_uuid"] == payload_entity.uuid for item in self.transit_queue):
            return False
            
        # Milestone 35: Teleport Counter & Threshold Logic
        if not hasattr(payload_entity, "payload") or payload_entity.payload is None:
            payload_entity.payload = {}
        
        counts = payload_entity.payload.setdefault("teleport_count", {})
        counts[self.uuid] = counts.get(self.uuid, 0) + 1
        current_visit = counts[self.uuid]
        
        max_threshold = int(self.get_property("max_threshold_count", 10))
        error_target = self.get_property("error_entity_id")
        
        # Determine Target UUID branch
        if current_visit <= max_threshold:
            # Normal routing: check override property then fall back to wiring
            chosen_target_uuid = self.get_property("target_uuid")
            if not chosen_target_uuid and hasattr(self, 'connected_uuids') and self.connected_uuids:
                chosen_target_uuid = self.connected_uuids[0]
        else:
            # Threshold Exceeded branch
            if error_target:
                chosen_target_uuid = error_target
            else:
                # No error portal defined -> Ejection logic (teleport back to entrance)
                chosen_target_uuid = self.uuid

        payload_entity.is_hidden = True
        if getattr(payload_entity, "body", None):
            payload_entity.body.velocity = (0, 0)
            payload_entity.body.angular_velocity = 0
            # M36 Fix: Move to portal center as staging area
            payload_entity.body.position = self.body.position
            
            # Milestone 36 Fix: Remove from space so it doesn't stay in sensor areas
            if self.body.space:
                space = self.body.space
                # 1. Remove Shapes
                for s in getattr(payload_entity, "shapes", [getattr(payload_entity, "shape", None)]):
                    if s and s in space.shapes:
                        space.remove(s)
                # 2. Remove Body
                if payload_entity.body and payload_entity.body in space.bodies:
                    space.remove(payload_entity.body)
            
        self.transit_queue.append({
            "entity": payload_entity,
            "payload_uuid": payload_entity.uuid,
            "timer": float(self.get_property("transit_time", 0.5)),
            "target_uuid": chosen_target_uuid  # Store at entry time
        })
        self.flash_timer = 15
        return True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        if game_state.get("mode") != "PLAY":
            return
            
        if self.flash_timer > 0:
            self.flash_timer -= 1
            
        for item in self.transit_queue:
            item["timer"] -= dt
            
            if item["timer"] <= 0:
                target_uuid = item.get("target_uuid")
                target_portal = active_instances.get(target_uuid) if active_instances and target_uuid else None

                if target_portal:
                    # M36: Data Pipe Hand-off support
                    if getattr(target_portal, 'variant_key', '') == 'data_pipe' and hasattr(target_portal, 'ingest_payload'):
                        # M36 Fix: Re-add to space before pipe ingestion so pipe can remove it again 
                        # (or just assume pipe handle it if we pass it logically)
                        # Actually pipe.ingest_payload(e) handles removal itself.
                        accepted = target_portal.ingest_payload(item["entity"])
                        if accepted:
                            target_portal.flash_timer = 15 # Visual sync
                            item["to_remove"] = True
                            continue
                            
                    if hasattr(target_portal, "body") and target_portal.body:
                        # Eject from target portal
                        payload = item["entity"]
                        payload.is_hidden = False
                        
                        # Eject downwards slightly below the target portal
                        px, py = target_portal.body.position
                        payload.body.position = (px, py + 50)
                        payload.body.velocity = (0, 150) # Shoot out
                        
                        # Milestone 36 Fix: Re-add to space upon ejection (Body FIRST)
                        if self.body and self.body.space:
                            space = self.body.space
                            if payload.body and payload.body not in space.bodies:
                                space.add(payload.body)
                                
                            for s in getattr(payload, "shapes", [getattr(payload, "shape", None)]):
                                if s and s not in space.shapes:
                                    space.add(s)
                            space.reindex_shapes_for_body(payload.body)
                        
                        target_portal.flash_timer = 15
                        item["to_remove"] = True
                else:
                    # Target missing/deleted/None, dump it back out of THIS portal
                    payload = item["entity"]
                    payload.is_hidden = False
                    
                    # M36 Fix: Also update position for local ejection
                    px, py = self.body.position
                    payload.body.position = (px, py + 50)
                    payload.body.velocity = (0, 150)
                    
                    # Milestone 36 Fix: Re-add to space upon ejection (Body FIRST)
                    if self.body.space:
                        space = self.body.space
                        if payload.body and payload.body not in space.bodies:
                            space.add(payload.body)
                            
                        for s in getattr(payload, "shapes", [getattr(payload, "shape", None)]):
                            if s and s not in space.shapes:
                                space.add(s)
                        space.reindex_shapes_for_body(payload.body)
                    
                    item["to_remove"] = True

        self.transit_queue = [item for item in self.transit_queue if not item.get("to_remove")]

    def cleanup(self):
        """M36 Extension: Drop payloads at current portal position if destroyed."""
        for item in self.transit_queue:
            payload = item.get("entity")
            if payload is None:
                continue
                
            payload.is_hidden = False
            if getattr(payload, "body", None):
                payload.body.velocity = (0.0, 0.0)
                payload.body.angular_velocity = 0.0
                payload.body.position = self.body.position
                
                # Re-add to space (Body FIRST)
                if self.body.space:
                    space = self.body.space
                    if payload.body and payload.body not in space.bodies:
                        space.add(payload.body)
                        
                    for s in getattr(payload, "shapes", [getattr(payload, "shape", None)]):
                        if s and s not in space.shapes:
                            space.add(s)
                    space.reindex_shapes_for_body(payload.body)

        self.transit_queue.clear()
        super().cleanup()

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