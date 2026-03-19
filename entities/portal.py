import math
import os
from typing import Any, Dict, List, Optional

import pygame
import pymunk

import constants
from entities.base import GamePart
from utils.asset_manager import asset_manager
from utils.sound_manager import sound_manager


class PortalPart(GamePart):
    """
    A teleportation entity. 
    Role (Inbound/Outbound) is determined by wire connections.
    """

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        # Format: {"payload_uuid": str, "timer": float, "is_kickout": bool}
        self.transit_queue = []
        self.visual_state = "UNLINKED"

        # --- Defaults ---
        self.properties.setdefault("inbound_sides", "top") # comma separated: "top, left, right"
        self.properties.setdefault("outbound_side", "left")
        self.properties.setdefault("velocity", 100.0)
        self.properties.setdefault("angle", "") # overrides defaults if set
        self.properties.setdefault("delay", 0.0)
        
        self.properties.setdefault("max_transitions", 0) # 0 means unlimited
        self.properties.setdefault("zombie_portal_name", "")
        
        self.properties.setdefault("width", 64.0)
        self.properties.setdefault("height", 64.0)

        self._create_default_visuals()
        self._animation_textures = {}
        self._load_animation_textures()

    def _generate_state_sprite(self, state_name: str, width: int, height: int) -> pygame.Surface:
        """Programmatically draws glowing portal rings."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)
        
        base_color = (100, 100, 100)
        glow_color = (150, 150, 150)
        
        if state_name.startswith("INBOUND"):
            base_color = (50, 0, 150)   # Deep purple/blue
            glow_color = (100, 100, 255) if state_name == "INBOUND_ACTIVE" else (80, 50, 200)
        elif state_name.startswith("OUTBOUND"):
            base_color = (150, 50, 0)   # Deep orange
            glow_color = (255, 150, 50) if state_name == "OUTBOUND_ACTIVE" else (200, 100, 0)

        # Outer Ring
        pygame.draw.circle(surf, base_color, center, width // 2 - 2, 8)
        # Inner Glow
        pygame.draw.circle(surf, glow_color, center, width // 2 - 10, 4)
        
        # Event Horizon (Center)
        if state_name != "UNLINKED":
            pygame.draw.circle(surf, (0, 0, 0), center, width // 2 - 14)
            if "ACTIVE" in state_name:
                # Add swirling stars/particles for active state
                pygame.draw.circle(surf, (255, 255, 255), (center[0] - 5, center[1] - 5), 2)
                pygame.draw.circle(surf, (200, 255, 255), (center[0] + 8, center[1] + 2), 3)
                pygame.draw.circle(surf, (255, 200, 255), (center[0] - 2, center[1] + 8), 2)

        return surf

    def _create_default_visuals(self):
        width = int(float(self.get_property("width", 64)))
        height = int(float(self.get_property("height", 64)))
        
        surf = self._generate_state_sprite("UNLINKED", width, height)
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

    def _load_animation_textures(self):
        width = int(float(self.get_property("width", 64)))
        height = int(float(self.get_property("height", 64)))
        states = ["UNLINKED", "INBOUND_IDLE", "INBOUND_ACTIVE", "OUTBOUND_IDLE", "OUTBOUND_ACTIVE"]
        
        os.makedirs("assets/sprites", exist_ok=True)
        for state in states:
            sprite_rel = f"assets/sprites/portal_{state.lower()}.png"
            if not os.path.exists(sprite_rel):
                generated_surf = self._generate_state_sprite(state, width, height)
                try:
                    pygame.image.save(generated_surf, sprite_rel)
                except Exception:
                    pass
            self._animation_textures[state] = asset_manager.get_image(sprite_rel, fallback_size=(width, height))

    def get_role(self, entities: List[GamePart]) -> str:
        """Dynamically determines if this is INBOUND, OUTBOUND, or UNLINKED."""
        if len(self.connected_uuids) > 0:
            return "INBOUND"
        
        for ent in entities:
            if hasattr(ent, 'connected_uuids') and self.uuid in ent.connected_uuids:
                return "OUTBOUND"
                
        return "UNLINKED"

    def ingest_payload(self, payload_entity: GamePart, entities: List[GamePart]) -> bool:
        """Called by pre_solve. Only swallows if it is an INBOUND portal."""
        if not getattr(payload_entity, 'body', None) or payload_entity.body.body_type != pymunk.Body.DYNAMIC:
            return False

        if self.get_role(entities) != "INBOUND":
            return False

        # Direction Check
        allowed_sides = [s.strip().lower() for s in str(self.get_property("inbound_sides", "top")).split(",")]
        dx = payload_entity.body.position.x - self.body.position.x
        dy = payload_entity.body.position.y - self.body.position.y
        
        valid = False
        if "top" in allowed_sides and dy < -5: valid = True
        if "left" in allowed_sides and dx < -5: valid = True
        if "right" in allowed_sides and dx > 5: valid = True
        
        if not valid:
            return False

        # Swallow!
        try:
            sound_manager.play_sound("woosh.wav")
        except: pass

        # Track usage to prevent infinite loops
        if not hasattr(payload_entity, "payload") or not isinstance(payload_entity.payload, dict):
            payload_entity.payload = {}
            
        usage_dict = payload_entity.payload.setdefault("portal_usage", {})
        current_usage = usage_dict.get(self.uuid, 0) + 1
        usage_dict[self.uuid] = current_usage

        max_trans = int(self.get_property("max_transitions", 0))
        is_kickout = False
        if max_trans > 0 and current_usage > max_trans:
            is_kickout = True

        delay = float(self.get_property("delay", 0.0))
        self.transit_queue.append({
            "payload_uuid": payload_entity.uuid,
            "timer": delay,
            "is_kickout": is_kickout
        })
        
        self.flash_timer = 15
        return True

    def eject_payload(self, payload_entity: GamePart):
        """Called on the OUTBOUND portal when a payload arrives."""
        try:
            sound_manager.play_sound("dinge.wav")
        except: pass

        width = float(self.get_property("width", 64))
        height = float(self.get_property("height", 64))
        margin = 30.0
        
        fx, fy = self.body.position.x, self.body.position.y
        output_side = str(self.get_property("outbound_side", "left")).lower()
        
        # Spawn Pos & Default Angles
        if output_side == "left":
            eject_x, eject_y = fx - (width/2) - margin, fy
            default_angle = 180.0
        elif output_side == "right":
            eject_x, eject_y = fx + (width/2) + margin, fy
            default_angle = 0.0
        elif output_side == "bottom":
            eject_x, eject_y = fx, fy + (height/2) + margin
            default_angle = 270.0
        else: # top
            eject_x, eject_y = fx, fy - (height/2) - margin
            default_angle = 45.0 # User requested Top defaults to 45 degrees
            
        payload_entity.body.position = (eject_x, eject_y)

        # Velocity & Angle
        speed = float(self.get_property("velocity", 100.0))
        conf_angle = self.get_property("angle", "")
        
        try:
            angle_deg = float(conf_angle) if str(conf_angle).strip() != "" else default_angle
        except ValueError:
            angle_deg = default_angle

        world_angle = math.radians(angle_deg)
        payload_entity.body.velocity = (speed * math.cos(world_angle), speed * -math.sin(world_angle))
        payload_entity.is_hidden = False
        
        self.flash_timer = 15

    def _eject_fatal(self, payload_entity: GamePart):
        """Ejects the payload out the bottom if kicked out or unlinked."""
        width = float(self.get_property("width", 64))
        height = float(self.get_property("height", 64))
        margin = 30.0
        
        fx, fy = self.body.position.x, self.body.position.y
        eject_x, eject_y = fx, fy + (height / 2) + margin
        
        payload_entity.body.position = (eject_x, eject_y)
        payload_entity.body.velocity = (0.0, 150.0) # Drop down
        payload_entity.is_hidden = False
        
        self.flash_timer = 15

    def update_logic(self, dt, game_state, entities, active_instances=None):
        role = self.get_role(entities)
        
        # Update Visual State dynamically
        if role == "UNLINKED":
            self.visual_state = "UNLINKED"
        else:
            is_active = getattr(self, "flash_timer", 0) > 0
            self.visual_state = f"{role}_ACTIVE" if is_active else f"{role}_IDLE"

        if game_state.get("mode") != "PLAY":
            return

        # Process Limbo Queue (Only Inbound portals hold the queue)
        if role == "INBOUND" and self.transit_queue:
            target_uuid = self.connected_uuids[0] if len(self.connected_uuids) > 0 else None
            target_portal = active_instances.get(target_uuid) if target_uuid else None
            
            ready_to_eject = []
            
            for item in self.transit_queue:
                item["timer"] -= dt
                payload = active_instances.get(item["payload_uuid"])
                
                if payload and hasattr(payload, 'body'):
                    # Keep it safely suspended in Limbo
                    payload.body.position = self.body.position
                    payload.body.velocity = (0, 0)
                    payload.is_hidden = True
                
                if item["timer"] <= 0:
                    ready_to_eject.append(item)

            for item in ready_to_eject:
                self.transit_queue.remove(item)
                payload = active_instances.get(item["payload_uuid"])
                
                if not payload:
                    continue

                # Zombie overflow or fatal rejection logic
                if item.get("is_kickout"):
                    zombie_name = str(self.get_property("zombie_portal_name", "")).strip()
                    zombie_portal = None
                    if zombie_name:
                        for ent in entities:
                            if getattr(ent, 'variant_key', '').startswith('portal') and str(ent.get_property('name', '')).strip() == zombie_name:
                                zombie_portal = ent
                                break
                    
                    if zombie_portal and hasattr(zombie_portal, 'eject_payload'):
                        zombie_portal.eject_payload(payload)
                    else:
                        self._eject_fatal(payload)
                else:
                    # Standard routing
                    if target_portal and hasattr(target_portal, 'eject_payload'):
                        target_portal.eject_payload(payload)
                    else:
                        # Fallback if connection was somehow lost during transit
                        self._eject_fatal(payload)

    def draw(self, surface, camera=None):
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            old_texture = self.base_texture
            self.base_texture = state_texture
            super().draw(surface, camera=camera)
            self.base_texture = old_texture
        else:
            super().draw(surface, camera=camera)