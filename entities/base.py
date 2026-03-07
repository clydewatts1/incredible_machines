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
        self.template = self.properties.get("template")
        self.is_hovered = False
        
        # Determine Body Type
        mass = self.properties.get("mass", 1.0)
        is_static = self.properties.get("is_static", False)
        
        if is_static:
            self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        else:
            self.body = pymunk.Body(mass, pymunk.moment_for_box(mass, (10, 10))) # placeholder moment
        
        self.body.position = (x, y)
        
        # Shape Creation
        tex_width, tex_height = 0, 0
        self.shapes = []
        if self.template == "Circle":
            radius = self.properties.get("radius", 15)
            self.shapes = [pymunk.Circle(self.body, radius)]
            tex_width, tex_height = radius * 2, radius * 2
            if not is_static:
                self.body.moment = pymunk.moment_for_circle(mass, 0, radius)
        elif self.template in ["Rectangle", "Square"]:
            width = self.properties.get("width", 50)
            height = self.properties.get("height", 50)
            self.shapes = [pymunk.Poly.create_box(self.body, size=(width, height))]
            tex_width, tex_height = width, height
            if not is_static:
                self.body.moment = pymunk.moment_for_box(mass, (width, height))
        elif self.template == "Diamond":
            width = self.properties.get("width", 50)
            height = self.properties.get("height", 50)
            verts = get_diamond_vertices(width, height)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = width, height
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "Half-Circle":
            radius = self.properties.get("radius", 50)
            segments = self.properties.get("segments", 15)
            verts = get_arc_vertices(radius, 0, math.pi, segments)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = radius * 2, radius
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "Quarter-Circle":
            radius = self.properties.get("radius", 50)
            segments = self.properties.get("segments", 15)
            verts = get_arc_vertices(radius, 0, math.pi / 2, segments)
            self.shapes = [pymunk.Poly(self.body, verts)]
            tex_width, tex_height = radius, radius
            if not is_static:
                self.body.moment = pymunk.moment_for_poly(mass, verts)
        elif self.template == "UShape":
            width = self.properties.get("width", 60)
            height = self.properties.get("height", 60)
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
            s.elasticity = self.properties.get("elasticity", 0.5)
            s.friction = self.properties.get("friction", 0.5)
            self.space.add(s)
        
        # Texture Loading & Caching (Milestone 8)
        self.base_texture = None
        texture_rel_path = self.properties.get("texture_path", "")
        if texture_rel_path:
            import os
            tex_abs_path = os.path.join(os.path.dirname(__file__), '..', texture_rel_path)
            try:
                img = pygame.image.load(tex_abs_path).convert_alpha()
                self.base_texture = pygame.transform.scale(img, (int(tex_width), int(tex_height)))
            except FileNotFoundError:
                print(f"FAIL LOUDLY: Texture missing: {tex_abs_path}. Falling back to primitive.")
                self.base_texture = None

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
        Draws the texture if available; else draws the primitive shape.
        """
        if self.base_texture:
            self.draw_texture(surface)
            return
            
        color = tuple(self.properties.get("color", [200, 200, 200]))
        for shape in self.shapes:
            if getattr(shape, 'sensor', False):
                continue # Don't draw the invisible sensor!
            if isinstance(shape, pymunk.Circle):
                pos = int(self.body.position.x), int(self.body.position.y)
                pygame.draw.circle(surface, color, pos, int(shape.radius))
            elif isinstance(shape, pymunk.Poly):
                vertices = [self.body.local_to_world(v) for v in shape.get_vertices()]
                points = [(int(v.x), int(v.y)) for v in vertices]
                pygame.draw.polygon(surface, color, points)

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

    def update_logic(self, dt, game_state, entities, active_instances=None):
        """
        Executes active logic (e.g. Cannon spawning) during PLAY state.
        """
        if self.variant_key == "cannon" and game_state.get("mode") == "PLAY":
            freq = self.properties.get("shoot_frequency", 1.0)
            max_count = self.properties.get("max_count", -1)
            
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
                    
                    proj_id = self.properties.get("projectile_id", "ball")
                    import math
                    angle = self.body.angle
                    
                    vel = self.properties.get("shoot_velocity", [0, -500])
                    vx = vel[0] * math.cos(angle) - vel[1] * math.sin(angle)
                    vy = vel[0] * math.sin(angle) + vel[1] * math.cos(angle)
                    
                    height = self.properties.get("height", 60)
                    shift_local_y = -height/2 - 20 # out of the barrel
                    shift_x = -shift_local_y * math.sin(angle)
                    shift_y = shift_local_y * math.cos(angle)
                    
                    spawn_x = self.body.position.x + shift_x
                    spawn_y = self.body.position.y + shift_y
                    
                    new_part = GamePart(self.space, spawn_x, spawn_y, proj_id)
                    new_part.body.angle = angle
                    new_part.body.velocity = (vx, vy)
                    self.space.reindex_shapes_for_body(new_part.body)
                    entities.append(new_part)
                    if active_instances is not None:
                        active_instances[new_part.uuid] = new_part
                    self.play_event_sound("spawn_sound")
