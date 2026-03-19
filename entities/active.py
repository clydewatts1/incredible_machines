import copy
import math
import queue
import threading
import uuid
from typing import Any, Dict, List, Optional

import pygame

import constants
from entities.base import GamePart
from utils.engines import create_engine
from utils.asset_manager import asset_manager
from utils.sprite_manager import sprite_manager


class FloatingTextLabel:
    """Lightweight floating label used for Factory diagnostics."""

    def __init__(self, x: float, y: float, text: str, color=(255, 60, 60), lifetime=2.0):
        self.uuid = str(uuid.uuid4())
        self.x = float(x)
        self.y = float(y)
        self.text = str(text)
        self.color = color
        self.lifetime = float(lifetime)
        self.elapsed = 0.0
        self.to_delete = False
        self.is_hovered = False
        self.body = None
        self.shape = None
        self.shapes = []
        self.connected_uuids = []

    def update_logic(self, dt: float, game_state, entities, active_instances=None):
        self.elapsed += dt
        self.y -= constants.FLOATING_LABEL_RISE_SPEED * dt
        if self.elapsed >= self.lifetime:
            self.to_delete = True

    def update_visual(self, surface, camera=None, **kwargs):
        alpha_ratio = max(0.0, 1.0 - (self.elapsed / max(self.lifetime, 0.001)))
        alpha = int(255 * alpha_ratio)
        font = pygame.font.SysFont(None, 18)
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        
        # Apply camera offset if provided
        if camera:
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        else:
            screen_x, screen_y = self.x, self.y
        
        rect = text_surf.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(text_surf, rect)


class FactoryPart(GamePart):
    """Milestone 22 active processor entity with async engine execution."""

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.visual_state = "IDLE"
        self.queue = queue.Queue()
        self._is_destroyed = False
        self.cooldown_timer = 0.0
        self.current_payload_uuid: Optional[str] = None

        # REMOVED cached properties (self.instructions, self.routing, etc.)
        # so the factory is forced to dynamically fetch the live YAML/Saved Overrides!

        self._animation_textures = {}
        self._load_animation_textures()
        self.visual_state = "INITIALIZING"
        self._set_state("IDLE")

    def _load_animation_textures(self):
        animations = self.get_property("animations", {})
        if not isinstance(animations, dict):
            return

        width = int(float(self.get_property("width", 96)))
        height = int(float(self.get_property("height", 96)))
        for state_name, base_name in animations.items():
            self._animation_textures[state_name] = sprite_manager.get_sprite(
                base_name, width, height, label=f"Factory {state_name}"
            )

    def _set_state(self, new_state: str):
        old_state = self.visual_state
        self.visual_state = new_state
        if old_state != new_state and (new_state == "EMITTING" or old_state == "EMITTING"):
            self.cooldown_timer = max(self.cooldown_timer, constants.FACTORY_COOLDOWN_SECONDS)

    def is_in_cooldown(self) -> bool:
        return self.cooldown_timer > 0.0

    def cleanup(self):
        self._is_destroyed = True
        self.current_payload_uuid = None
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def destroy(self):
        self._is_destroyed = True

    def _ensure_payload_defaults(self, payload_entity: GamePart):
        payload = getattr(payload_entity, "payload", None)
        if not isinstance(payload, dict):
            payload = {}

        now_secs = pygame.time.get_ticks() / 1000.0
        payload.setdefault("ttl", constants.DEFAULT_PAYLOAD_TTL)
        payload.setdefault("cost", constants.DEFAULT_PAYLOAD_COST)
        payload.setdefault("drop_dead_age", constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE)
        payload.setdefault("routing_depth", 0)
        payload.setdefault("processing_history", [])
        payload.setdefault("start_time", now_secs)
        payload.setdefault("age", 0.0)

        payload_entity.payload = payload

    def _audit_payload_lifecycle(self, payload_entity: GamePart):
        payload = payload_entity.payload
        now_secs = pygame.time.get_ticks() / 1000.0
        payload["age"] = max(0.0, now_secs - float(payload.get("start_time", now_secs)))

        # Dynamically fetch cost_modifier
        cost_modifier = float(self.get_property("cost_modifier", -10.0))
        payload["cost"] = float(payload.get("cost", constants.DEFAULT_PAYLOAD_COST)) + cost_modifier

        if payload.get("cost", 0.0) <= 0.0:
            return "bottom"

        if payload.get("age", 0.0) > float(payload.get("drop_dead_age", constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE)):
            return "top"

        if int(payload.get("ttl", 0)) <= 0:
            return "bottom"

        if int(payload.get("routing_depth", 0)) > constants.MAX_ROUTING_DEPTH:
            return "bottom"

        return "healthy"

    def _start_worker(self, payload_entity: GamePart):
        payload_copy = copy.deepcopy(payload_entity.payload)
        
        # === AUTO-SANITIZER ===
        # Clean the payload to prevent CSV whitespace from breaking regex matching
        for k, v in list(payload_copy.items()):
            clean_k = k.strip() if isinstance(k, str) else k
            clean_v = v.strip() if isinstance(v, str) else v
            if clean_k != k:
                del payload_copy[k]
            payload_copy[clean_k] = clean_v
            
        # Dynamically fetch latest instructions and engine_type!
        instructions_copy = copy.deepcopy(self.get_property("instructions", {}))
        engine_type = str(self.get_property("engine_type", "regex"))
        engine = create_engine(engine_type, {"variant_key": self.variant_key})
        
        payload_uuid = payload_entity.uuid

        def _worker():
            try:
                result = engine.process(payload_copy, instructions_copy)
            except Exception as exc:
                result = f"fatal: {exc}"

            if not self._is_destroyed:
                self.queue.put({"payload_uuid": payload_uuid, "result": result})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def ingest_payload(self, payload_entity: GamePart) -> bool:
        if self._is_destroyed:
            return False

        if self.is_in_cooldown():
            return False

        if self.current_payload_uuid is not None:
            self._set_state("JAMMED")
            return False

        self._ensure_payload_defaults(payload_entity)
        gate = self._audit_payload_lifecycle(payload_entity)

        if gate == "bottom":
            self._eject_payload(payload_entity, edge="bottom")
            return True

        if gate == "top":
            self._eject_payload(payload_entity, edge="top", floating=True)
            return True

        self.current_payload_uuid = payload_entity.uuid
        self._set_state("PROCESSING")
        self._start_worker(payload_entity)
        return True

    def _find_route(self, state_value: float) -> Optional[Dict[str, Any]]:
        # Dynamically fetch the latest routing list!
        routing_list = self.get_property("routing", [])
        
        if not isinstance(routing_list, list):
            return None

        for rule in routing_list:
            if not isinstance(rule, dict):
                continue
            try:
                if float(state_value) <= float(rule.get("max_state")):
                    return rule
            except (TypeError, ValueError):
                continue
        return None

    def _apply_score_modifier(self, payload_entity: GamePart, route_rule: Dict[str, Any]):
        payload = payload_entity.payload
        if "score" not in payload:
            payload["score"] = 100

        try:
            score_delta = int(route_rule.get("score", 0))
        except (TypeError, ValueError):
            score_delta = 0

        payload["score"] = max(0, int(payload.get("score", 100)) + score_delta)

        history = payload.get("processing_history", [])
        if not isinstance(history, list):
            history = []
        history.append((self.uuid, score_delta))
        payload["processing_history"] = history

    def _spawn_fatal_label(self, entities: List[GamePart], reason: str):
        label = FloatingTextLabel(self.body.position.x, self.body.position.y - 40, reason)
        entities.append(label)

    def _eject_payload(self, payload_entity: GamePart, edge: str, route_rule: Optional[Dict[str, Any]] = None, floating: bool = False, entities: Optional[List[GamePart]] = None):
        """Ejects the processed payload, applying targeting calculations if applicable."""
        width = float(self.get_property("width", 96))
        height = float(self.get_property("height", 96))
        half_w = width / 2.0
        half_h = height / 2.0
        margin = 12.0
        
        # Dynamically fetch tired_velocity
        tired_velocity = float(self.get_property("tired_velocity", 150.0))

        fx = self.body.position.x
        fy = self.body.position.y

        if edge == "bottom":
            payload_entity.body.position = (fx, fy + half_h + margin)
            payload_entity.body.velocity = (0.0, abs(tired_velocity))
        elif edge == "top":
            payload_entity.body.position = (fx, fy - half_h - margin)
            payload_entity.body.velocity = (0.0, -abs(tired_velocity))
            payload_entity.floating = floating
            payload_entity.floating_timer = constants.FLOATING_TIMEOUT_SECONDS if floating else 0.0
        else:
            # === TARGETING LOGIC ===
            eject_x = fx - half_w - margin
            eject_y = fy
            payload_entity.body.position = (eject_x, eject_y)

            # Look for target in route_rule first, then fallback to Factory properties
            target_val = (route_rule or {}).get("target", self.get_property("target", None))
            
            # Allow payload to dictate its own target dynamically
            if not target_val and hasattr(payload_entity, 'payload') and isinstance(payload_entity.payload, dict):
                target_val = payload_entity.payload.get("target", None)
                
            target_pos = None
            if target_val:
                # Type A: Coordinate string (e.g., "500, 300")
                if isinstance(target_val, str) and "," in target_val:
                    try:
                        parts = target_val.split(",")
                        target_pos = (float(parts[0].strip()), float(parts[1].strip()))
                    except ValueError:
                        pass
                # Type B: Find Entity by UUID or Name (requires entities list)
                elif entities is not None:
                    for ent in entities:
                        if ent.uuid == target_val or ent.get_property("name") == target_val:
                            target_pos = ent.body.position
                            break
            
            if target_pos:
                print(f"🎯 [Factory Debug] Overriding angle. Shooting at Target: {target_val}")
                # Vector math to shoot directly at the target
                dx = target_pos[0] - eject_x
                dy = target_pos[1] - eject_y
                dist = math.hypot(dx, dy)
                
                if dist > 0:
                    # Prefer the route velocity, fallback to factory shoot_speed, fallback to 300
                    speed = float((route_rule or {}).get("velocity", self.get_property("shoot_speed", 300.0)))
                    vx = (dx / dist) * speed
                    vy = (dy / dist) * speed
                else:
                    vx, vy = 0.0, 0.0
            else:
                # Default angle-based logic (if no target is found or set)
                print(f"🔍 [Factory Debug] RAW ROUTE RULE DICT: {route_rule}")
                
                # Check for angle in route rule, fallback to factory property, fallback to 45.0
                route_angle = (route_rule or {}).get("angle")
                if route_angle is None:
                    angle_deg = float(self.get_property("angle", 45.0))
                else:
                    angle_deg = float(route_angle)
                    
                vel = float((route_rule or {}).get("velocity", 120.0))
                print(f"📐 [Factory Debug] Shooting at Angle: {angle_deg} degrees with Velocity: {vel}")
                
                world_angle = math.radians(180.0 - angle_deg)
                vx = vel * math.cos(world_angle)
                vy = -vel * math.sin(world_angle)
                
            payload_entity.body.velocity = (vx, vy)

        payload = payload_entity.payload
        payload["ttl"] = int(payload.get("ttl", constants.DEFAULT_PAYLOAD_TTL)) - 1
        payload["routing_depth"] = int(payload.get("routing_depth", 0)) + 1

        self._set_state("EMITTING")

    def draw(self, surface, camera=None):
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            old_texture = self.base_texture
            self.base_texture = state_texture
            self.draw_texture(surface, camera=camera)
            self.base_texture = old_texture
            return
        super().draw(surface, camera=camera)

    def poll_results(self, entities: List[GamePart], active_instances: Dict[str, GamePart]):
        if self._is_destroyed:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            return

        while not self.queue.empty():
            result_data = self.queue.get()
            payload_uuid = result_data.get("payload_uuid")
            result = result_data.get("result")

            payload_entity = active_instances.get(payload_uuid)
            self.current_payload_uuid = None

            if payload_entity is None or getattr(payload_entity, "to_delete", False):
                continue

            if isinstance(result, str) and result.lower().startswith("fatal"):
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, result)
                continue

            try:
                state_value = float(result)
                print(f"🏭 [Factory Debug] Engine evaluated payload to state: {state_value}")
            except (TypeError, ValueError):
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, f"fatal: non-numeric state {result}")
                continue

            route_rule = self._find_route(state_value)
            if route_rule is None:
                self._set_state("FATAL")
                self._spawn_fatal_label(entities, "fatal: no matching routing rule")
                print(f"🏭 [Factory Debug] NO ROUTE matched for state: {state_value}")
                continue

            print(f"🏭 [Factory Debug] Matched Route: {route_rule.get('desc', 'Unnamed Route')} (Max State: {route_rule.get('max_state')})")
            
            self._apply_score_modifier(payload_entity, route_rule)
            
            # Pass the entities list into the ejection logic so it can resolve Name/UUID targets
            self._eject_payload(payload_entity, edge="left", route_rule=route_rule, entities=entities)

    def update_logic(self, dt, game_state, entities, active_instances=None):
        if game_state.get("mode") != "PLAY":
            return

        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
            if self.cooldown_timer > 0.0:
                self._set_state("COOLDOWN")
            elif self.visual_state == "COOLDOWN":
                self._set_state("IDLE")

        if self.visual_state not in {"PROCESSING", "FATAL", "JAMMED", "COOLDOWN"}:
            self._set_state("IDLE")