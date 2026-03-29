import pygame
import pymunk
from entities.base import FlowEntity
try:
    import rule_engine
except ImportError:
    rule_engine = None

class GuardPart(FlowEntity):
    """
    Active WOLF Router. (Strict 1-In, 1-Out Subscriber)
    Checks the upstream Warehouse's 'last_state' before pulling items.
    """
    can_accept_input = False
    can_provide_output = True

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.scan_timer = 0.5
        self.needs_scan = False
        
        query = str(self.get_property("guard_query", "true"))
        try:
            self.rule = rule_engine.Rule(query) if rule_engine else None
        except Exception as e:
            print(f"Guard Rule Error: {e}")
            self.rule = None

    def receive_signal(self, sender, signal_data):
        if signal_data.get("status") == "REFRESH":
            self.needs_scan = True

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        if game_state.get("mode") != "PLAY" or not self.rule or not active_instances:
            return

        # Downstream Awareness
        if self.downstream_status in ["FULL", "JAMMED"]:
            self._set_state("JAMMED")
            return

        # Upstream Awareness: Pass the last state of upstream warehouse
        source_uuid = self.get_property("source_uuid")
        source = active_instances.get(source_uuid)
        
        if not source:
            return
            
        # Check the exposed upstream state. 
        if getattr(source, "last_state", "IDLE") == "IDLE" and not self.needs_scan:
            self._set_state("IDLE")
            return

        # Trigger scan if upstream is active or we have a pending REFRESH
        if not self.needs_scan and getattr(source, "last_state") == "ACTIVE":
            self.needs_scan = True
            
        if not self.needs_scan:
            return
            
        self.scan_timer -= dt
        if self.scan_timer <= 0:
            self.scan_timer = 0.5
            self.needs_scan = False
            
            stored_uuids = getattr(source, "stored_payload_uuids", [])
            for uid in list(stored_uuids):
                payload_ent = active_instances.get(uid)
                if not payload_ent or not hasattr(payload_ent, "payload"):
                    continue
                    
                try:
                    # v1.3.0 logic: use rule.matches for consistency check
                    if self.rule.matches(payload_ent.payload):
                        if hasattr(source, "extract_payload"):
                            pulled_uid = source.extract_payload(uid)
                            if pulled_uid:
                                self._set_state("WRITING")
                                self.resolve_exit_path(payload_ent, 10, entities, active_instances)
                                break 
                except Exception:
                    pass

    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        if not self.body: return
        pos = self.body.position
        sx, sy = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
        
        # Overlay a scan line for visual feedback
        w = float(self.get_property("width", 96))
        h = float(self.get_property("height", 96))
        
        if self.visual_state in ["IDLE", "WRITING"]:
            scan_y = sy - h/2 + ((pygame.time.get_ticks() / 10) % h)
            pygame.draw.line(surface, (0, 255, 0), (sx - w/2, scan_y), (sx + w/2, scan_y), 1)
