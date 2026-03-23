import pygame
import pymunk
import math
import uuid
import constants
from utils.config_loader import load_entity_config
from utils.sound_manager import sound_manager
from utils.geometry_utils import get_diamond_vertices, get_arc_vertices

class GamePart:
    """
    Base class for all entities in the game.
    Enforces the 'Pymunk Rule' by strictly separating physics and rendering.
    """
    def __init__(self, space, x, y, property_key):
        self.space = space
        self.uuid = str(uuid.uuid4())
        self.variant_key = property_key
        self.properties = load_entity_config(property_key)
        self.overrides = {}
        self.template = self.get_property("template")
        self.is_hovered = False
        self.to_delete = False
        self.connected_uuids = []
        self.payload = {}
        self.floating = False
        self.floating_timer = 0.0
        
        # Determine Body Type
        mass = float(self.get_property("mass", 1.0))
        is_static = self.get_property("is_static", False)
        
        if is_static:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        else:
            self.body = pymunk.Body(mass, pymunk.moment_for_box(mass, (10, 10))) # placeholder moment
        
        self.body.position = (x, y)
        
        # Shape Creation
        tex_width, tex_height = 0, 0
        self.shapes = []
        if self.template == "Circle":
            radius = float(self.get_property("radius", 15))
            self.shapes = [pymunk.Circle(self.body, radius)]
            tex_width, tex_height = radius * 2, radius * 2
            if not is_static:
                self.body.moment = pymunk.moment_for_circle(mass, 0, radius)
        elif self.template in ["Rectangle", "Square"]:
            width = float(self.get_property("width", 50))
            height = float(self.get_property("height", 50))
            self.shapes = [pymunk.Poly.create_box(self.body, size=(width, height))]
            
            # Phase 2: Directional Sensors in Pymunk (Active Sides)
            active_sides = list(self.get_property("active_sides", []))
            if self.get_property("active_side"):
                active_sides.append(self.get_property("active_side"))
            
            if "sink" in self.variant_key:
                pass
                
            for side in active_sides:
                side = side.lower()
                offset = 2.0 
                hw = width / 2.0
                hh = height / 2.0
                if side == "top":
                    p1, p2 = (-hw, -hh - offset), (hw, -hh - offset)
                elif side == "bottom":
                    p1, p2 = (-hw, hh + offset), (hw, hh + offset)
                elif side == "left":
                    p1, p2 = (-hw - offset, -hh), (-hw - offset, hh)
                elif side == "right":
                    p1, p2 = (hw + offset, -hh), (hw + offset, hh)
                else:
                    continue
                    
                sensor_seg = pymunk.Segment(self.body, p1, p2, 2.0)
                sensor_seg.sensor = False  # False so we can conditionally bounce!
                if self.variant_key == "basket":
                    sensor_seg.collision_type = constants.COLLISION_TYPE_BASKET
                elif self.variant_key == "cannon":
                    sensor_seg.collision_type = constants.COLLISION_TYPE_CANNON
                elif self.variant_key == "logic_factory" and side == "top":
                    sensor_seg.collision_type = constants.COLLISION_TYPE_FACTORY_TOP
                elif self.variant_key.startswith("data_sink") and side == "top":
                    sensor_seg.collision_type = constants.COLLISION_TYPE_SINK_TOP
                else:
                    sensor_seg.collision_type = 4
                self.shapes.append(sensor_seg)

            tex_width, tex_height = width, height
            if not is_static:
                self.body.moment = pymunk.moment_for_box(mass, (width, height))
        elif self.template == "Diamond":
            width = float(self.get_property("width", 50))
            height = float(self.get_property("height", 50))
            verts = get_diamond_vertices(width, height)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = width, height
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "Half-Circle":
            radius = float(self.get_property("radius", 50))
            segments = int(self.get_property("segments", 15))
            verts = get_arc_vertices(radius, 0, math.pi, segments)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = radius * 2, radius
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "Quarter-Circle":
            radius = float(self.get_property("radius", 50))
            segments = int(self.get_property("segments", 15))
            verts = get_arc_vertices(radius, 0, math.pi / 2, segments)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = radius, radius
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "UShape":
            width = float(self.get_property("width", 60))
            height = float(self.get_property("height", 60))
            thick = 10
            base_verts = [(-width/2, height/2 - thick), (width/2, height/2 - thick), (width/2, height/2), (-width/2, height/2)]
            left_verts = [(-width/2, -height/2), (-width/2 + thick, -height/2), (-width/2 + thick, height/2), (-width/2, height/2)]
            right_verts = [(width/2 - thick, -height/2), (width/2, -height/2), (width/2, height/2), (width/2 - thick, height/2)]
            
            self.shapes = [
                pymunk.Poly(self.body, base_verts),
                pymunk.Poly(self.body, left_verts),
                pymunk.Poly(self.body, right_verts)
            ]
            
            if self.variant_key in ["basket", "cannon"]:
                sensor_verts = [(-width/2 + thick, -height/2), (width/2 - thick, -height/2), 
                                (width/2 - thick, -height/2 + 5), (-width/2 + thick, -height/2 + 5)]
                sensor_shape = pymunk.Poly(self.body, sensor_verts)
                sensor_shape.sensor = True
                sensor_shape.collision_type = 2 if self.variant_key == "basket" else 3
                self.shapes.append(sensor_shape)
                
            tex_width, tex_height = width, height
            if not is_static:
                self.body.moment = pymunk.moment_for_box(mass, (width, height))
        else:
            raise ValueError(f"Unknown template {self.template}")
            
        self.shape = self.shapes[0]
        self.space.add(self.body)
        for s in self.shapes:
            s.elasticity = float(self.get_property("elasticity", 0.5))
            s.friction = float(self.get_property("friction", 0.5))
            self.space.add(s)

        # Phase 3: Motors require explicit bracing to the static space and driving
        if self.variant_key == "motor":
            # Pin the dynamic motor body to the static background so it spins in place
            pivot = pymunk.PivotJoint(self.space.static_body, self.body, self.body.position)
            # Create the driving motor constraint
            rate = float(self.get_property("motor_speed", 3.14))
            direction = self.get_property("direction", "clockwise")
            if direction == "counter-clockwise":
                rate = -rate
            motor = pymunk.SimpleMotor(self.space.static_body, self.body, rate)
            self.space.add(pivot, motor)
            self.motor_constraint = motor
        
        # Texture Loading & Caching (Milestone 8 & 16)
        from utils.asset_manager import asset_manager
        import os
        
        texture_rel_path = str(self.get_property("texture_path", ""))
        tex_path = texture_rel_path if texture_rel_path else f"assets/sprites/{self.variant_key}.png"
        
        label_text = self.properties.get("label", self.variant_key)
        self.base_texture = asset_manager.get_image(
            tex_path, 
            fallback_size=(int(tex_width), int(tex_height)), 
            text_label=label_text
        )

        # M36: Reactive Geometry
        self.is_reactive = self.get_property("is_reactive", False)
        self.flash_timer = 0.0
        self.active_texture = None
        
        if self.is_reactive and self.base_texture:
            # Check for explicit active sprite
            active_sprite_path = f"assets/sprites/{self.variant_key}_active.png"
            if os.path.exists(active_sprite_path):
                self.active_texture = asset_manager.get_image(
                    active_sprite_path,
                    fallback_size=(int(tex_width), int(tex_height)),
                    text_label=f"{label_text} ACTIVE"
                )
            else:
                # Procedural brightness boost (20%)
                self.active_texture = self.base_texture.copy()
                self.active_texture.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_ADD)

        # New payload defaults are primarily used by Factory processing pipelines.
        if self.template == "Circle":
            self.payload = {
                "ttl": constants.DEFAULT_PAYLOAD_TTL,
                "cost": constants.DEFAULT_PAYLOAD_COST,
                "drop_dead_age": constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE,
                "routing_depth": 0,
                "processing_history": [],
            }

    def trim_payload(self):
        """Milestone 34: Recursively limits depth, string length, and list size in self.payload."""
        if not isinstance(self.payload, dict):
            return

        def _recursive_limit(data, depth=0):
            if depth > 3:
                return "{...DEPTH_LIMIT...}"
            if isinstance(data, dict):
                # Filter out verbose internal logs
                return {k: _recursive_limit(v, depth + 1) for k, v in data.items() 
                        if k not in ("_logs", "_debug", "transitional_data")}
            elif isinstance(data, list):
                # Cap list size to 20 elements
                return [_recursive_limit(item, depth + 1) for item in data[:20]]
            elif isinstance(data, str):
                # Cap string size to 1024 chars
                if len(data) > 1024:
                    return data[:1021] + "..."
                return data
            return data

        self.payload = _recursive_limit(self.payload)

    def update_visual(self, surface, camera=None, **kwargs):
        """
        Reads the Pymunk body position and rotation to render the Pygame visual.
        MUST fail loudly if physics components are missing.
        
        M25 Phase 2: Accepts optional camera parameter for coordinate translation.
        If camera is provided, world coordinates are transformed to screen coordinates.
        """
        assert self.body is not None, "FAIL LOUDLY: GamePart is missing a physics body!"
        assert self.shape is not None, "FAIL LOUDLY: GamePart is missing a physics shape!"
        
        # Render the specific entity visual first
        self.draw(surface, camera=camera, **kwargs)
        
        # Overlay universal interaction highlight if hovered
        if self.is_hovered:
            self.draw_highlight(surface, camera=camera)

    def draw_highlight(self, surface, camera=None):
        """
        Universally draws a distinct visual highlight (a yellow outline box)
        around the object using its physics bounding box.
        
        M25 Phase 2: Applies camera offset if provided.
        """
        assert getattr(self, "is_hovered", None) is not None, "FAIL LOUDLY: GamePart missing is_hovered state attribute!"
        
        # Calculate full bounding box covering all shapes
        bb = self.shapes[0].cache_bb()
        for s in self.shapes[1:]:
            bb = bb.merge(s.cache_bb())
        
        # Get bounding box corners in world space
        world_left = bb.left
        world_top = bb.bottom  # Pymunk's bb.bottom is min Y
        world_width = bb.right - bb.left
        world_height = bb.top - bb.bottom
        
        # Apply camera transformation if provided
        if camera:
            screen_left, screen_top = camera.world_to_screen(world_left, world_top)
        else:
            screen_left, screen_top = world_left, world_top
        
        pad = 5
        rect = pygame.Rect(
            int(screen_left) - pad,
            int(screen_top) - pad,
            int(world_width) + (pad * 2),
            int(world_height) + (pad * 2)
        )
        # Draw a yellow-ish outline with 3px thickness
        pygame.draw.rect(surface, (255, 255, 100), rect, width=3)

    def draw(self, surface, camera=None, **kwargs):
        """
        Draws the sprite texture. Primitive shapes are replaced by auto-generated fallbacks.
        
        M25 Phase 2: Applies camera offset if provided.
        """
        if self.base_texture:
            self.draw_texture(surface, camera=camera)

    def play_event_sound(self, event_type):
        """
        Plays a generalized event sound (e.g. spawn_sound, hover_sound)
        if it exists in the entity's YAML properties.
        """
        sound_file = self.properties.get(event_type)
        if sound_file:
            sound_manager.play_sound(sound_file)

    def draw_texture(self, surface, camera=None):
        """
        Renders the cached texture synchronized strictly with Pymunk orientation.
        
        M25 Phase 2: Applies camera offset if provided.
        """
        if not self.base_texture or not self.body:
            return
            
        # 1. Constitution Sec 10: Invert degrees for Pygame logic constraints
        angle_degrees = -math.degrees(self.body.angle)
        
        # 2. Reactive Flash?
        tex = self.base_texture
        if self.is_reactive and self.flash_timer > 0 and self.active_texture:
            tex = self.active_texture
            
        # 3. Re-rotate exactly once per render cycle
        rotated_surface = pygame.transform.rotate(tex, angle_degrees)
        
        # 3. Get world-space position
        world_x, world_y = self.body.position.x, self.body.position.y
        
        # 4. Apply camera transformation if provided
        if camera:
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        else:
            screen_x, screen_y = world_x, world_y
        
        # 5. Securely center the new rect on the screen position
        rect = rotated_surface.get_rect(center=(int(screen_x), int(screen_y)))
        
        surface.blit(rotated_surface, rect)

    def reset_logic(self):
        """ Resets internal logic variables when entering PLAY mode """
        if self.variant_key == "cannon":
            self.shoot_timer = 0.0
            self.shoot_count = 0
            self.force_shoot = False
        elif self.variant_key == "conveyor_belt":
            speed = float(self.get_property("speed", 100.0))
            direction = self.get_property("direction", "right")
            if direction == "left":
                speed = -speed
            for s in self.shapes:
                s.surface_velocity = (speed, 0)
        elif self.variant_key == "motor":
            if hasattr(self, 'motor_constraint'):
                rate = float(self.get_property("motor_speed", 3.14))
                direction = self.get_property("direction", "clockwise")
                if direction == "counter-clockwise":
                    rate = -rate
                self.motor_constraint.rate = rate

    def receive_signal(self, sender, signal_data=None):
        """Phase 3/17/34: Standard logical interface triggered by connected Sender entities."""
        if self.variant_key == "cannon":
            self.force_shoot = True
        elif self.variant_key == "conveyor_belt":
            # Toggle surface velocity
            current_x, current_y = self.shapes[0].surface_velocity
            if current_x == 0:
                speed = float(self.get_property("speed", 100.0))
                direction = self.get_property("direction", "right")
                if direction == "left":
                    speed = -speed
                for s in self.shapes:
                    s.surface_velocity = (speed, 0)
            else:
                for s in self.shapes:
                    s.surface_velocity = (0, 0)
        elif self.variant_key == "motor":
            if hasattr(self, 'motor_constraint'):
                if self.motor_constraint.rate == 0:
                    rate = float(self.get_property("motor_speed", 3.14))
                    direction = self.get_property("direction", "clockwise")
                    if direction == "counter-clockwise":
                        rate = -rate
                    self.motor_constraint.rate = rate
                else:
                    self.motor_constraint.rate = 0.0

    def get_property(self, key, default=None):
        if key in self.overrides:
            return self.overrides[key]
        return self.properties.get(key, default)

    def cleanup(self):
        """Base no-op cleanup. Subclasses should call super().cleanup() to support MRO chaining."""
        pass

    def destroy(self):
        """Alias for cleanup(). Subclasses may override."""
        self.cleanup()

    def apply_draft_overrides(self, new_dict):
        """
        Applies a dictionary of drafted overrides.
        Requires re-establishing physical properties on the body.
        For Phase 2/3, we update simple things like mass, friction, bounce directly if possible.
        """
        for k, v in new_dict.items():
            self.overrides[k] = v
            
        # Re-calc dynamic mass
        if "mass" in new_dict and not self.get_property("is_static", False):
            mass = float(self.get_property("mass", 1.0))
            self.body.mass = mass
            
        for shape in self.shapes:
            if "elasticity" in new_dict:
                shape.elasticity = float(self.get_property("elasticity", 0.3))
            if "friction" in new_dict:
                shape.friction = float(self.get_property("friction", 0.5))
                
        # Phase 4: Dynamic Motor/Conveyor Speed Tuning
        if self.variant_key == "conveyor_belt" and ("speed" in new_dict or "direction" in new_dict):
            speed = float(self.get_property("speed", 100.0))
            direction = self.get_property("direction", "right")
            if direction == "left":
                speed = -speed
            for s in self.shapes:
                s.surface_velocity = (speed, 0)
                
        if self.variant_key == "motor" and ("motor_speed" in new_dict or "direction" in new_dict):
            if hasattr(self, 'motor_constraint'):
                rate = float(self.get_property("motor_speed", 3.14))
                direction = self.get_property("direction", "clockwise")
                if direction == "counter-clockwise":
                    rate = -rate
                self.motor_constraint.rate = rate
                
    def handle_collision(self, arbiter):
        """M36: Triggers visual reaction on impact for reactive geometry."""
        if self.is_reactive:
            self.flash_timer = float(self.get_property("flash_duration", 0.3))

    def update_logic(self, dt, game_state, entities, active_instances=None):
        """
        Executes active logic (e.g. Cannon spawning) during PLAY state.
        """
        # Reactive Flash Decay
        if self.flash_timer > 0:
            self.flash_timer -= dt
            
        if self.variant_key == "cannon" and game_state.get("mode") == "PLAY":
            freq = float(self.get_property("shoot_frequency", 1.0))
            max_count = int(self.get_property("max_count", -1))
            
            if getattr(self, 'shoot_timer', None) is None:
                self.shoot_timer = 0.0
                self.shoot_count = 0
                self.force_shoot = False
                
            force_shoot = getattr(self, 'force_shoot', False)
            if max_count == -1 or self.shoot_count < max_count or force_shoot:
                self.shoot_timer += dt
                if self.shoot_timer >= freq or force_shoot:
                    self.shoot_timer = 0.0
                    self.force_shoot = False
                    if not force_shoot:
                        self.shoot_count += 1
                    
                    # Phase 4: Cannon Emitter Logic
                    proj_id = str(self.get_property("ammo_id", "bouncy_ball"))
                    act_side = str(self.get_property("active_side", "right")).lower()
                    vel_mag = float(self.get_property("exit_velocity", 800.0))
                    ex_angle_deg = float(self.get_property("exit_angle", 0.0))
                    
                    import math
                    base_angle = self.body.angle 
                    
                    width = float(self.get_property("width", 60))
                    height = float(self.get_property("height", 60))
                    hw, hh = width / 2.0, height / 2.0
                    
                    # Convert side into local unit vector
                    if act_side == "top":
                        local_x, local_y = 0, -hh - 15
                        local_angle = -math.pi / 2
                    elif act_side == "bottom":
                        local_x, local_y = 0, hh + 15
                        local_angle = math.pi / 2
                    elif act_side == "left":
                        local_x, local_y = -hw - 15, 0
                        local_angle = math.pi
                    else: # right
                        local_x, local_y = hw + 15, 0
                        local_angle = 0
                        
                    # Rotate local offsets by world angle
                    spawn_x = self.body.position.x + local_x * math.cos(base_angle) - local_y * math.sin(base_angle)
                    spawn_y = self.body.position.y + local_x * math.sin(base_angle) + local_y * math.cos(base_angle)
                    
                    final_angle = base_angle + local_angle + math.radians(ex_angle_deg)
                    vx = vel_mag * math.cos(final_angle)
                    vy = vel_mag * math.sin(final_angle)
                    
                    new_part = GamePart(self.space, spawn_x, spawn_y, proj_id)
                    new_part.body.angle = final_angle
                    new_part.body.velocity = (vx, vy)
                    self.space.reindex_shapes_for_body(new_part.body)
                    entities.append(new_part)
                    if active_instances is not None:
                        active_instances[new_part.uuid] = new_part
                    self.play_event_sound("spawn_sound")

    def collect_projectile(self, projectile):
        """Milestone 12: Handles ball ingestion into Basket and Cannon sensors."""
        if self.variant_key == "basket":
            projectile.to_delete = True
            self.play_event_sound("collision_sound")


# ---------------------------------------------------------------------------
#  M32: FlowEntity – Unified Base for all I/O and Processing Nodes
# ---------------------------------------------------------------------------

class FlowEntity(GamePart):
    """
    M32: Unified base class for DataSource, DataSink, BrainPart and future nodes.

    Centralises:
    - Sprite-based animation state machine with procedural fallback.
    - Pause icon rendering.
    - Standardised receive_signal / broadcast_status.
    - refresh_parameters hook for runtime property updates.
    - resolve_exit_path for Pipe-first / Vector-fallback / Error-default routing.
    - Shared queue + _is_destroyed guard + cleanup().
    """

    # Subclasses should override these class-level flags.
    can_provide_output: bool = False
    can_accept_input: bool = False

    # Valid state names — subclasses may extend.
    VALID_STATES = {
        "OFF", "INITIALIZING", "IDLE",
        "INGESTING", "WRITING", "FATAL",
        "JAMMED", "COOLDOWN", "PAUSED", "EXHAUSTED",
        "POLLING", "EMITTING",
    }

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)

        # --- Lifecycle ---
        self.visual_state: str = "IDLE"
        self._is_destroyed: bool = False

        # --- Signaling ---
        self.is_paused: bool = False
        self.downstream_status: str = "IDLE"
        self.signal_received: bool = False
        self.needs_broadcast: bool = False

        # --- Logic Generation (M35 Cancellation) ---
        self.logic_generation: int = 0

        # --- Cooldown ---
        self.cooldown_timer: float = 0.0

        # --- Animation ---
        self._animation_textures: dict = {}
        self.load_animations()

    # ------------------------------------------------------------------ #
    #  Animation
    # ------------------------------------------------------------------ #

    def load_animations(self):
        """
        Load state-specific textures from YAML `animations` mapping.
        Supports both single strings (frame base name) and lists of frame names.
        Missing sprites fall back to a procedural surface (grey box + state label).
        """
        from utils.sprite_manager import sprite_manager

        animations = self.get_property("animations", {})
        if not isinstance(animations, dict):
            return

        width  = int(float(self.get_property("width",  96)))
        height = int(float(self.get_property("height", 96)))

        for state_name, frames in animations.items():
            if isinstance(frames, list) and frames:
                # M32: if a list is provided, we take the FIRST frame for now.
                # Future iteration could implement an actual index-based cycler in draw().
                sprite_name = frames[0]
            else:
                sprite_name = frames

            surf = sprite_manager.get_sprite(
                sprite_name, width, height,
                label=f"{self.__class__.__name__} {state_name}"
            )
            if surf is None:
                surf = self._make_procedural_fallback(width, height, state_name)
            self._animation_textures[state_name] = surf

    def _make_procedural_fallback(self, width: int, height: int, state_name: str) -> pygame.Surface:
        """
        Render a Light Gray (#E0E0E0) surface with a 1px Black border
        and the state name centred in Black text.
        """
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((224, 224, 224))                               # Light gray
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)  # 1px black border
        font = pygame.font.SysFont("arial", max(9, height // 7))
        label_surf = font.render(state_name, True, (0, 0, 0))
        label_rect = label_surf.get_rect(center=(width // 2, height // 2))
        surf.blit(label_surf, label_rect)
        return surf

    def _set_state(self, new_state: str):
        """
        Transition to a new visual state.
        Plays config-defined state sounds and sets the broadcast flag.
        """
        if new_state not in self.VALID_STATES:
            return
        if new_state == self.visual_state:
            return

        old_state = self.visual_state
        self.visual_state = new_state

        # Cooldown on WRITING exit/entry (matches original Brain/Factory behaviour)
        if "WRITING" in (old_state, new_state):
            self.cooldown_timer = max(
                self.cooldown_timer,
                getattr(import_constants(), "FACTORY_COOLDOWN_SECONDS",
                        getattr(__import__("constants"), "FACTORY_COOLDOWN_SECONDS", 0.5))
            )

        # Sound
        sounds = self.get_property("sounds", {})
        if isinstance(sounds, dict):
            sound_file = sounds.get(new_state)
            if sound_file:
                try:
                    sound_manager.play_sound(sound_file)
                except Exception:
                    pass

        # Signal broadcast flag
        self.needs_broadcast = True

    def is_in_cooldown(self) -> bool:
        return self.cooldown_timer > 0.0

    def draw(self, surface, camera=None, **kwargs):
        """
        Renders state-specific texture if available; otherwise delegates to
        the parent draw_texture method (base sprite).
        Also renders the pause ‖ icon when self.is_paused is True.
        """
        state_texture = self._animation_textures.get(self.visual_state)
        if state_texture is not None:
            old_texture = self.base_texture
            self.base_texture = state_texture
            self.draw_texture(surface, camera=camera)
            self.base_texture = old_texture
        else:
            super().draw(surface, camera=camera)

        # Pause icon overlay
        if self.is_paused and self.body:
            if camera:
                sx, sy = camera.world_to_screen(self.body.position.x, self.body.position.y)
            else:
                sx, sy = self.body.position.x, self.body.position.y
            pygame.draw.rect(surface, (255, 200, 0), (sx - 8, sy - 20, 5, 15), border_radius=1)
            pygame.draw.rect(surface, (255, 200, 0), (sx + 3, sy - 20, 5, 15), border_radius=1)

    # ------------------------------------------------------------------ #
    #  Signalling
    # ------------------------------------------------------------------ #

    def receive_signal(self, sender, signal_data: dict):
        """
        Standardised handler for backpressure/flow-control signals.
        Updates internal downstream_status based on the incoming signal.
        """
        if isinstance(signal_data, dict):
            self.downstream_status = signal_data.get("status", "IDLE")
            self.signal_received = True

    def broadcast_status(self, active_instances: dict):
        """
        Notifies all connected entities of current status.
        Sends {"status": self.visual_state} to each neighbor.
        """
        status_packet = {"status": self.visual_state}
        for tgt_uuid in self.connected_uuids:
            tgt = active_instances.get(tgt_uuid)
            if tgt and hasattr(tgt, "receive_signal"):
                tgt.receive_signal(self, status_packet)

    def _process_incoming_signal(self):
        """
        Consume a pending signal and apply pause logic.
        Call this at the top of update_logic() in subclasses.
        """
        if not self.signal_received:
            return
        self.signal_received = False
        
        # M32 Unified Flow Control
        if self.downstream_status in ("FULL", "JAMMED", "FATAL", "INGESTING", "WRITING", "POLLING", "EMITTING"):
            self.is_paused = True
        else:
            self.is_paused = False

    # ------------------------------------------------------------------ #
    #  Parameter Refresh Hook  (M32 stigmergic optimization support)
    # ------------------------------------------------------------------ #

    def refresh_parameters(self, updates_dict: dict):
        """
        Merge new property values into self.properties at runtime.
        Delegates to apply_draft_overrides for physics re-calc.
        """
        for k, v in updates_dict.items():
            self.properties[k] = v
        self.apply_draft_overrides(updates_dict)

    # ------------------------------------------------------------------ #
    #  Hybrid Routing  –  resolve_exit_path  (The Zero Rule)
    # ------------------------------------------------------------------ #

    def resolve_exit_path(
        self,
        payload_entity,
        state_result,
        entities: list,
        active_instances: dict = None,
    ) -> str:
        """
        M32: Unified exit-path resolver with the Zero Rule.

        State Normalisation:
          If state_result <= 0, treat as error: search_state = 0.

        Precedence (for BOTH normal and error paths):
          1. Error/Matched Pipe – DataPipePart with source_uuid==self.uuid and
             route_state == search_state. If full → JAMMED.
          2. Explicit Rule – routing entry whose max_state == search_state.
             Uses its velocity / angle / output_side.
          3. Hard Exit (error default) – eject from "bottom" at tired_velocity,
             set FATAL state.

        Returns:
            "pipe"    – payload handed to pipe; caller must NOT touch physics.
            "ejected" – payload physically moved; caller should clear payload_uuid.
            "jammed"  – pipe found but full; caller should set JAMMED and retry.
        """
        from utils.routing import find_route, calculate_ejection_kinematics

        # ── Zero Rule: set FATAL immediately if result <= 0 ──────────────
        raw = float(state_result)
        if raw <= 0:
            search_state = 0.0
            self._set_state("FATAL")
            is_error = True
        else:
            search_state = raw
            is_error = False

        # ── 1. Pipe First ─────────────────────────────────────────────────
        matching_pipe = None
        for entity in entities:
            if getattr(entity, "variant_key", "") != "data_pipe":
                continue
            if str(entity.get_property("source_uuid", "")) != str(self.uuid):
                continue
            try:
                pipe_state = float(entity.get_property("route_state", -999))
            except (TypeError, ValueError):
                continue
            if abs(pipe_state - search_state) <= 1e-6:
                matching_pipe = entity
                break

        if matching_pipe is not None:
            accepted = bool(matching_pipe.ingest_payload(payload_entity))
            if accepted:
                if is_error:
                    self._set_state("FATAL")
                return "pipe"
            return "jammed"

        # ── 2. Explicit Rule ──────────────────────────────────────────────
        routing_rules = self.get_property("routing", [])
        route_rule = find_route(search_state, routing_rules)

        if route_rule is not None:
            output_side = str(
                route_rule.get("output_side", self.get_property("output_side", "right"))
            ).lower()
            shoot_speed  = float(self.get_property("shoot_speed", 250.0))
            tired_velocity = float(self.get_property("tired_velocity", 150.0))
            velocity = shoot_speed if output_side != "bottom" else tired_velocity

            default_angles = {"right": 0.0, "top": 90.0, "left": 180.0, "bottom": 270.0}
            default_angle  = default_angles.get(output_side, 0.0)

            eff_rule = dict(route_rule)
            if not eff_rule.get("target") and self.connected_uuids:
                eff_rule["target"] = self.connected_uuids[0]

            (ex, ey), (vx, vy) = calculate_ejection_kinematics(
                self, output_side, eff_rule, velocity, default_angle, entities
            )
            payload_entity.body.position = (ex, ey)
            payload_entity.body.velocity = (vx, vy)
            if is_error:
                self._set_state("FATAL")
            else:
                self._set_state("WRITING")
            return "ejected"

        # ── 3. Hard Exit (error default) ──────────────────────────────────
        tired_velocity = float(self.get_property("tired_velocity", 150.0))
        (ex, ey), (vx, vy) = calculate_ejection_kinematics(
            self, "bottom", None, tired_velocity, 270.0, entities
        )
        payload_entity.body.position = (ex, ey)
        payload_entity.body.velocity = (vx, vy)
        # Always enter FATAL on a hard exit — no pipe, no rule
        self._set_state("FATAL")
        return "ejected"

    # ------------------------------------------------------------------ #
    #  Shared cleanup
    # ------------------------------------------------------------------ #

    def cleanup(self):
        """Mark destroyed and drain the work queue if one exists."""
        self._is_destroyed = True
        q = getattr(self, "queue", None)
        if q is not None:
            while not q.empty():
                try:
                    q.get_nowait()
                except Exception:
                    break

    def reset_flow_logic(self):
        """
        Clears pending queues and increments the generation counter
        to invalidate any background workers currently in flight.
        """
        self.logic_generation += 1
        self.visual_state = "IDLE"
        self.is_paused = False
        
        q = getattr(self, "queue", None)
        if q is not None:
            while not q.empty():
                try:
                    q.get_nowait()
                except Exception:
                    break

    def destroy(self):
        self.cleanup()


def import_constants():
    """Lazy import helper used inside FlowEntity._set_state."""
    import constants as _c
    return _c
