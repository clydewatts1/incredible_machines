import copy
import math
from typing import Any, Dict, List, Optional

import pygame
import pymunk

from utils.routing import calculate_ejection_kinematics
import constants
from entities.base import GamePart, FlowEntity
from utils.asset_manager import asset_manager
from utils.sprite_manager import sprite_manager


class WarehousePart(FlowEntity):
    """
    A WOLF-style buffer entity.
    Absorbs balls, stores them up to a capacity, and releases them at a controlled rate.
    Supports Pass-Through Logic: Will halt and forward PAUSE/FULL signals to upstream sources.
    """

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        self.stored_payload_uuids = []
        self.release_timer = 0.0
        
        self.signal_received = False
        self.signal_state = None
        self.visual_state = "IDLE"
        self.is_downstream_paused = False

        self.properties.setdefault("input_side", "top")
        self.properties.setdefault("output_side", "bottom")
        self.properties.setdefault("capacity", 20)
        self.properties.setdefault("release_interval", 1.0)
        self.properties.setdefault("velocity", "")
        self.properties.setdefault("angle", "")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)
        self.properties.setdefault("send_full_signal", True)
        self.properties.setdefault("auto_release", True)

        self._create_default_visuals()

    def _create_default_visuals(self):
        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        self.base_texture = sprite_manager.get_sprite(self.variant_key, width, height)

    def receive_signal(self, sender, signal_data: Dict[str, Any]):
        # Extract standardized logic signal, or fallback to the sender's visual state
        if isinstance(signal_data, dict):
            self.signal_state = signal_data.get("status", "IDLE")
        else:
            # Fallback for old callers
            self.signal_state = getattr(sender, "logic_signal", getattr(sender, "visual_state", "IDLE"))
        
        self.signal_received = True

    def ingest_payload(self, payload_entity: "GamePart", active_instances: Dict[str, Any] = None, skip_proximity: bool = False, **kwargs) -> bool:
        """
        Standardized ingestion with backpressure support.
        """
        # Store active_instances ref for later signal broadcasting
        if active_instances:
            self.active_instances_ref = active_instances

        if self.visual_state != "IDLE":
            return False

        if not getattr(payload_entity, 'body', None) or payload_entity.body.body_type != pymunk.Body.DYNAMIC:
            return False

        capacity = int(self.get_property("capacity", 20))
        if len(self.stored_payload_uuids) >= capacity:
            return False 

        input_side = str(self.get_property("input_side", "top")).lower()
        if not skip_proximity:
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
        
        self.flash_timer = 10
        
        # Milestone 38: Event-Driven WOLF
        # Force a refresh signal so downstream guards wake up immediately
        print(f"DEBUG: Warehouse {self.uuid} Ingested ball. Broadcasting REFRESH to {len(self.connected_uuids)} connections.")
        self.broadcast_status(active_instances or {}, {"status": "REFRESH"})
        
        return True

    def extract_payload(self, uuid: str, active_instances: Dict[str, Any]) -> Optional[GamePart]:
        """
        Milestone 38: Atomic extraction for pull-based WOLF logic.
        Surgically removes the payload from the buffer and returns the entity.
        Returns None if already removed (prevents double-processing by multiple guards).
        """
        if uuid in self.stored_payload_uuids:
            self.stored_payload_uuids.remove(uuid)
            payload = active_instances.get(uuid)
            if payload:
                # Visual feedback on extraction
                self.flash_timer = 15
                return payload
        return None

    def _eject_payload(self, payload_entity: GamePart, entities: list, active_instances: dict):
        """
        M44: Eject the payload using standardized routing.
        Preferentially enters a Data Pipe (state 10) or falls back to physical ejection.
        """
        # Determine if we should match by generic type if the payload has one
        payload_type = None
        if hasattr(payload_entity, "payload") and isinstance(payload_entity.payload, dict):
            payload_type = payload_entity.payload.get("type")

        # Use unified router
        result = self.resolve_exit_path(
            payload_entity, 
            10.0,  # Generic success state
            entities, 
            active_instances,
            data_type=payload_type
        )

        if result == "pipe":
            # Handled by pipe visuals
            pass
        elif result == "jammed":
            # Repush to front of buffer and wait
            if payload_entity.uuid not in self.stored_payload_uuids:
                self.stored_payload_uuids.insert(0, payload_entity.uuid)
            return
        
        # Flash on exit
        self.flash_timer = 10

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        capacity = int(self.get_property("capacity", 20))

        if self.stored_payload_uuids:
            self.stored_payload_uuids = [
                uid for uid in self.stored_payload_uuids 
                if uid in active_instances and not getattr(active_instances[uid], 'to_delete', False)
            ]

        # === PROCESS INCOMING SIGNALS ===
        if self.signal_received:
            self.signal_received = False
            if self.signal_state in ["IDLE", "OFF"]:
                self.is_downstream_paused = False
            else:
                self.is_downstream_paused = True

        # === SIGNAL BROADCAST LOGIC (Pass-Through) ===
        is_physically_full = len(self.stored_payload_uuids) >= capacity
        
        # We act "FULL" to upstream components if we are physically out of space, 
        # OR if downstream told us to pause (passing the backpressure upwards!)
        is_logically_full = is_physically_full or self.is_downstream_paused
        new_state = "FULL" if is_logically_full else "IDLE"
        
        if getattr(self, "visual_state", "IDLE") != new_state:
            self.visual_state = new_state
            self.logic_signal = new_state # Expose standard protocol
            
            if str(self.get_property("send_full_signal", "true")).lower() == "true":
                self.broadcast_status(active_instances or {})

        # === RELEASE LOGIC ===
        if not self.stored_payload_uuids:
            return
            
        # Milestone 38: Interaction State (Passive buffer mode)
        if not self.get_bool_property("auto_release", True):
            return

        self.release_timer -= dt

        # Only release balls if downstream is ready for them!
        if self.release_timer <= 0:
            if not self.is_downstream_paused:
                uid_to_release = self.stored_payload_uuids.pop(0)
                payload_to_release = active_instances.get(uid_to_release)
                if payload_to_release:
                    self._eject_payload(payload_to_release, entities, active_instances)
                
                try:
                    self.release_timer = float(self.get_property("release_interval", 1.0))
                except ValueError:
                    self.release_timer = 1.0
            else:
                self.release_timer = 0.0 # Ready to fire instantly once unpaused

    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        if not self.body:
            return
            
        count = len(self.stored_payload_uuids)
        capacity = int(self.get_property("capacity", 20))
        
        pos = self.body.position
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
            
        font = pygame.font.SysFont(None, 24)
        color = (0, 255, 0) if count < capacity else (255, 100, 100)
        text_surf = font.render(f"{count}/{capacity}", True, color)
        
        rect = text_surf.get_rect(center=(int(screen_x), int(screen_y) - 15))
        bg_surf = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        surface.blit(bg_surf, (rect.x - 2, rect.y - 2))
        surface.blit(text_surf, rect)