import math
import pygame
import pymunk
from typing import Any, Dict, List, Optional

# Prerequisite: pip install rule-engine
try:
    import rule_engine
    RULE_ENGINE_AVAILABLE = True
except ImportError:
    RULE_ENGINE_AVAILABLE = False

from entities.base import GamePart, FlowEntity
from entities.floating_label import FloatingTextLabel
from utils.sprite_manager import sprite_manager

class GuardPart(FlowEntity):
    """
    Milestone 38: WOLF Active Filter node.
    Scans a source Warehouse/Factory and pulls payloads based on a rule-engine expression.
    Event-driven: Responds to REFRESH signals from source.
    Backpressure-aware: Only pulls if target is not FULL.
    Priority-aware: Sorts candidates by a specified key.
    """
    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        # --- Config Properties ---
        self.properties.setdefault("guard_query", "True")
        self.properties.setdefault("source_uuid", "")
        self.properties.setdefault("target_uuid", "")
        self.properties.setdefault("sort_by", "")
        self.properties.setdefault("sort_order", "desc")
        self.properties.setdefault("width", 96.0)
        self.properties.setdefault("height", 96.0)

        # --- Runtime State ---
        self.needs_scan = False
        self.radar_angle = 0.0
        self.pulse_timer = 0.0
        self.label = None
        
        self._compiled_rule = None
        self._last_query = None

        self._create_default_visuals()

    def _create_default_visuals(self):
        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        self.base_texture = sprite_manager.get_sprite(self.variant_key, width, height)

    def _get_rule(self):
        if not RULE_ENGINE_AVAILABLE:
            return None
            
        query = self.get_property("guard_query", "True")
        if query != self._last_query:
            try:
                self._compiled_rule = rule_engine.Rule(query)
                self._last_query = query
                # Update floating label
                if self.label:
                    self.label.text = query
            except Exception as e:
                print(f"ERROR: Guard {self.uuid} failed to compile rule '{query}': {e}")
                self._compiled_rule = rule_engine.Rule("False")
                self._last_query = query
        return self._compiled_rule

    def receive_signal(self, sender, signal_data: Dict[str, Any]):
        """Milestone 38: Event-Driven Trigger."""
        if signal_data.get("status") == "REFRESH":
            print(f"DEBUG: Guard {self.uuid} Received REFRESH. Setting needs_scan = True")
            # Milestone 38 Fix: Update instance reference from signal context
            if signal_data.get("active_instances"):
                self.active_instances_ref = signal_data["active_instances"]
            self.needs_scan = True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        # Use passed-in instances or cached ref
        active_instances = active_instances or getattr(self, "active_instances_ref", {})
        
        # 0. Auto-Register with Source (Milestone 38 Event-Driven)
        source_uuid = self.get_property("source_uuid", "")
        if source_uuid and source_uuid in active_instances:
            source_node = active_instances[source_uuid]
            if self.uuid not in source_node.connected_uuids:
                source_node.connected_uuids.append(self.uuid)
                # Keep a reference to the source's instances for broadcasting status back
                source_node.active_instances_ref = active_instances
                # Milestone 38: Proactive wake-up if source already contains payloads
                if getattr(source_node, "stored_payload_uuids", []):
                    self.needs_scan = True
        
        # 1. Update Floating Label (First run or query change)
        query = self.get_property("guard_query", "True")
        if self.label is None:
            self.label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, query, (0, 180, 255), lifetime=999999)
            entities.append(self.label)
        else:
            self.label.x = self.body.position.x
            self.label.y = self.body.position.y - 40
            if self.label.text != query:
                self.label.text = query

        # 2. Update Visuals (Radar always rotates to show "powered on" state)
        self.radar_angle = (self.radar_angle + dt * 180 * 2) % 360
        if self.pulse_timer > 0:
            self.pulse_timer -= dt

        # 3. Slumber Check
        if not self.needs_scan:
            return

        # Discovery: Find connected Data Pipes (Milestone 38 Final)
        inlet_pipe = None
        outlet_pipe = None
        for ent in entities:
             if getattr(ent, "variant_key", "") == "data_pipe":
                 if ent.get_property("target_uuid") == self.uuid:
                     inlet_pipe = ent
                 if ent.get_property("source_uuid") == self.uuid:
                     outlet_pipe = ent

        # 4. Target Backpressure Check (Standardized consumption handshake)
        # Priority: Outlet Pipe > Target UUID Property
        effective_target = outlet_pipe or active_instances.get(self.get_property("target_uuid", ""))
        
        if effective_target:
            # Milestone 38: Wait if target is BUSY (not IDLE or full if pipe)
            t_state = getattr(effective_target, "visual_state", "IDLE")
            # If it's a pipe, check capacity
            if getattr(effective_target, "variant_key", "") == "data_pipe":
                if len(getattr(effective_target, "transit_queue", [])) >= int(effective_target.get_property("capacity", 5)):
                    return
            elif t_state != "IDLE":
                return

        # 5. Pull Logic
        # Priority: Inlet Pipe Source > Source UUID Property
        source_node = None
        if inlet_pipe:
            source_node = active_instances.get(inlet_pipe.get_property("source_uuid"))
        else:
            source_node = active_instances.get(self.get_property("source_uuid", ""))
            
        if not source_node or not hasattr(source_node, "stored_payload_uuids") or not hasattr(source_node, "extract_payload"):
            self.needs_scan = False
            return
            
        rule = self._get_rule()
        if not rule:
            self.needs_scan = False
            return

        # Candidate selection and SORTING
        candidate_uuids = list(source_node.stored_payload_uuids)
        if not candidate_uuids:
            self.needs_scan = False
            return

        sort_key = self.get_property("sort_by", "")
        if sort_key:
            # Sort by priority key
            reverse = (str(self.get_property("sort_order", "desc")).lower() == "desc")
            
            def sort_func(uid):
                ent = active_instances.get(uid)
                if not ent or not hasattr(ent, 'payload'): return 0
                return ent.payload.get(sort_key, 0)
                
            candidate_uuids.sort(key=sort_func, reverse=reverse)

        # 6. Pull-Loop (Milestone 38 Final Repair)
        # We loop until the source is empty OR the target is full (backpressure)
        pull_count = 0
        while True:
            # Check backpressure every iteration
            if outlet_pipe:
                if len(getattr(outlet_pipe, "transit_queue", [])) >= int(outlet_pipe.get_property("capacity", 5)):
                    print(f"DEBUG: Guard {self.uuid} Slumbering: Outlet Pipe Full.")
                    break
            elif effective_target:
                t_state = getattr(effective_target, "visual_state", "IDLE")
                if t_state != "IDLE":
                    print(f"DEBUG: Guard {self.uuid} Slumbering: Target Node Full/Busy.")
                    break

            # Refresh candidate list from actual source buffer
            current_buffer = getattr(source_node, "stored_payload_uuids", [])
            if not current_buffer:
                print(f"DEBUG: Guard {self.uuid} Slumbering: Source Node Empty.")
                break
            
            # Sort if needed (using the already defined sort order/key)
            # For simplicity in the loop, we'll re-apply the sort to the current buffer state
            if sort_key:
                current_buffer.sort(key=sort_func, reverse=reverse)

            found_match_in_loop = False
            for uid in list(current_buffer):
                payload_entity = active_instances.get(uid)
                if not payload_entity: continue
                
                # Evaluate using rule-engine relative to payload data
                data_to_test = {}
                if hasattr(payload_entity, "payload") and isinstance(payload_entity.payload, dict):
                    data_to_test.update(payload_entity.payload)
                    if "data" in payload_entity.payload and isinstance(payload_entity.payload["data"], dict):
                        data_to_test.update(payload_entity.payload["data"])
                
                try:
                    if rule.matches(data_to_test):
                        # SUCCESS: Pull the payload atomically
                        pulled_entity = source_node.extract_payload(uid, active_instances)
                        if pulled_entity:
                            self._route_payload(pulled_entity, effective_target, active_instances)
                            self.pulse_timer = 0.5 # Flash green on success
                            pull_count += 1
                            found_match_in_loop = True
                            print(f"DEBUG: Guard {self.uuid} Pulled {uid} successfully. (Total pulled: {pull_count})")
                            break # Break inner for-loop to check backpressure before next pull
                except Exception as e:
                    print(f"DEBUG: Guard {self.uuid} rule error for {uid}: {e}")
                    continue
            
            if not found_match_in_loop:
                # No more matches in the current buffer
                print(f"DEBUG: Guard {self.uuid} No more matching items found. Slumbering.")
                break

        # Always clear scan flag after processing (or failing to find anything)
        self.needs_scan = False

    def _route_payload(self, entity, target, active_instances):
        """Handoff the pulled payload to the target destination or pipe."""
        if target:
            # 1. Try ingestion (handshake or pipe entry)
            if hasattr(target, "ingest_payload"):
                if target.ingest_payload(entity, active_instances):
                    entity.is_hidden = True
                    return

            # 2. Fallback: Teleport to target position
            entity.body.position = target.body.position
            entity.is_hidden = False
        else:
            # 3. Last fallback: Eject at guard position
            entity.body.position = self.body.position
            entity.is_hidden = False

    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        if not self.body: return
        
        pos = self.body.position
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
        
        # Radar Beam Visual
        width = int(float(self.get_property("width", 96)))
        radius = width * 0.6
        angle_rad = math.radians(self.radar_angle)
        end_x = screen_x + math.cos(angle_rad) * radius
        end_y = screen_y + math.sin(angle_rad) * radius
        
        # Color based on recent hit or scanning active
        if self.pulse_timer > 0:
            beam_color = (0, 255, 0)
        elif self.needs_scan:
            beam_color = (255, 200, 0) # Scanning active
        else:
            beam_color = (0, 180, 255) # Idle rotation
            
        pygame.draw.line(surface, beam_color, (int(screen_x), int(screen_y)), (int(end_x), int(end_y)), 3)
        
        # Outer Ring
        pygame.draw.circle(surface, (100, 100, 100), (int(screen_x), int(screen_y)), int(radius), 1)

        # Success Halo
        if self.pulse_timer > 0:
            alpha = int((self.pulse_timer / 0.5) * 120)
            glow_size = int(width * 1.2)
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 255, 0, alpha), (glow_size // 2, glow_size // 2), glow_size // 2)
            surface.blit(glow_surf, (int(screen_x - glow_size // 2), int(screen_y - glow_size // 2)))
