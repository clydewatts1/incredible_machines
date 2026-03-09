import pygame
import pymunk
import math
import uuid
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
                
            for side in active_sides:
                side = side.lower()
                offset = 1.0 
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
                sensor_seg.collision_type = 2 if self.variant_key == "basket" else (3 if self.variant_key == "cannon" else 4)
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
        
        texture_rel_path = str(self.get_property("texture_path", ""))
        tex_path = texture_rel_path if texture_rel_path else f"assets/sprites/{self.variant_key}.png"
        
        label_text = self.properties.get("label", self.variant_key)
        self.base_texture = asset_manager.get_image(
            tex_path, 
            fallback_size=(int(tex_width), int(tex_height)), 
            text_label=label_text
        )

    def update_visual(self, surface):
        """
        Reads the Pymunk body position and rotation to render the Pygame visual.
        MUST fail loudly if physics components are missing.
        """
        assert self.body is not None, "FAIL LOUDLY: GamePart is missing a physics body!"
        assert self.shape is not None, "FAIL LOUDLY: GamePart is missing a physics shape!"
        
        # Render the specific entity visual first
        self.draw(surface)
        
        # Overlay universal interaction highlight if hovered
        if self.is_hovered:
            self.draw_highlight(surface)

    def draw_highlight(self, surface):
        """
        Universally draws a distinct visual highlight (a yellow outline box)
        around the object using its physics bounding box.
        """
        assert getattr(self, "is_hovered", None) is not None, "FAIL LOUDLY: GamePart missing is_hovered state attribute!"
        
        # Calculate full bounding box covering all shapes
        bb = self.shapes[0].cache_bb()
        for s in self.shapes[1:]:
            bb = bb.merge(s.cache_bb())
        
        # Pymunk's bb.bottom is the minimum Y value (visually the top in Pygame where Y goes down)
        pad = 5
        left = int(bb.left) - pad
        top = int(bb.bottom) - pad
        width = int(bb.right - bb.left) + (pad * 2)
        height = int(bb.top - bb.bottom) + (pad * 2)
        
        rect = pygame.Rect(left, top, width, height)
        # Draw a yellow-ish outline with 3px thickness
        pygame.draw.rect(surface, (255, 255, 100), rect, width=3)

    def draw(self, surface):
        """
        Draws the sprite texture. Primitive shapes are replaced by auto-generated fallbacks.
        """
        if self.base_texture:
            self.draw_texture(surface)

    def play_event_sound(self, event_type):
        """
        Plays a generalized event sound (e.g. spawn_sound, hover_sound)
        if it exists in the entity's YAML properties.
        """
        sound_file = self.properties.get(event_type)
        if sound_file:
            sound_manager.play_sound(sound_file)

    def draw_texture(self, surface):
        """
        Renders the cached texture synchronized strictly with Pymunk orientation.
        """
        if not self.base_texture or not self.body:
            return
            
        import math
        # 1. Constitution Sec 10: Invert degrees for Pygame logic constraints
        angle_degrees = -math.degrees(self.body.angle)
        
        # 2. Re-rotate exactly once per render cycle
        rotated_surface = pygame.transform.rotate(self.base_texture, angle_degrees)
        
        # 3. Securely center the new rect on the exact physical center of mass
        rect = rotated_surface.get_rect(center=(int(self.body.position.x), int(self.body.position.y)))
        
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

    def receive_signal(self, payload=None):
        """Phase 3/17: Standard logical interface triggered by connected Sender entities."""
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

    def update_logic(self, dt, game_state, entities, active_instances=None):
        """
        Executes active logic (e.g. Cannon spawning) during PLAY state.
        """
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
