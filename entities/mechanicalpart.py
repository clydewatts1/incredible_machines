import pygame
import pymunk
import math
from entities.base import GamePart
import constants
from utils.asset_manager import asset_manager


class MechanicalPart(GamePart):
    def __init__(self, space, x, y, variant_key):
        super().__init__(space, x, y, variant_key)
        
        # 1. Physics Setup: Must be DYNAMIC to rotate
        mass = float(self.get_property("mass", 2.0))
        radius = float(self.get_property("radius", 30))
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        
        self.shape = pymunk.Circle(self.body, radius)
        
        # 2. COLLISION FILTERING
        # Use a high collision type (e.g., 99) to avoid the default "clunk" sound 
        # handlers in main.py that might interfere with physics stability
        self.shape.collision_type = 99 
        self.shape.filter = pymunk.ShapeFilter(
            categories=0x2, 
            mask=0xFFFFFFFF ^ 0x2  # Collide with everything except other mechanical parts (category 0x2)
        )
        
        # 3. Axle & Motor Logic
        self.axle = pymunk.PivotJoint(self.space.static_body, self.body, (x, y))
        self.space.add(self.body, self.shape, self.axle)

        if self.get_property("is_driver", False):
            rate = float(self.get_property("motor_speed", 3.14))
            self.motor = pymunk.SimpleMotor(self.space.static_body, self.body, rate)
            self.space.add(self.motor)
        
        self.connected_belts = [] # Store UUIDs of belt-linked targets

    def connect_belt(self, other_entity):
        """Creates a belt drive connection (same direction) and ensures persistence."""
        r1 = float(self.get_property("radius", 30))
        r2 = float(other_entity.get_property("radius", 30))
        
        # Positive ratio means same-direction rotation for belts
        ratio = (r1 / r2)
        joint = pymunk.GearJoint(self.body, other_entity.body, 0, ratio)
        self.space.add(joint)
        
        # Add to local list for drawing
        self.connected_belts.append(other_entity.uuid)
        
        # Store in overrides for LevelManager
        existing_belts = self.overrides.get("connected_belts", [])
        if other_entity.uuid not in existing_belts:
            existing_belts.append(other_entity.uuid)
            self.apply_draft_overrides({"connected_belts": existing_belts})
            
        return joint

    def connect_to_gear(self, other_gear, ratio=-1.0):
        # ... (rest of method same)
        """
        Manually links this gear to another gear.
        A negative ratio (e.g., -1.0) makes them spin in opposite directions,
        mimicking real meshing gears.
        """
        # GearJoint(body_a, body_b, phase, ratio)
        joint = pymunk.GearJoint(self.body, other_gear.body, 0, ratio)
        self.space.add(joint)
        return joint

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        # Phase 1: Mesh with neighbors if not already connected
        if not hasattr(self, "is_connected"):
            self.is_connected = False

        if game_state.get("mode") == "PLAY" and not self.is_connected:
            for entity in entities:
                if isinstance(entity, MechanicalPart) and entity != self:
                    # Calculate distance between centers
                    dist = self.body.position.get_distance(entity.body.position)
                    r1 = float(self.get_property("radius", 30))
                    r2 = float(entity.get_property("radius", 30))
                    
                    # If they are close enough to "touch" (with a small 5px buffer)
                    if dist <= (r1 + r2) + 5:
                        # Negative ratio ensures they spin in opposite directions
                        mesh_ratio = -(r1 / r2)
                        self.connect_to_gear(entity, ratio=mesh_ratio)
                        self.is_connected = True
                        break # Only connect to one driver for now

        # Phase 2: Handle animation frame toggling
        if game_state.get("mode") == "PLAY":
            rotation_speed = abs(self.body.angular_velocity)
            if rotation_speed > 0.1:
                # Ensure frame_timer exists (initialized in __init__ usually)
                if not hasattr(self, "frame_timer"): self.frame_timer = 0.0
                if not hasattr(self, "current_frame"): self.current_frame = 0
                
                self.frame_timer += dt * rotation_speed
                if self.frame_timer >= 1.0:
                    self.frame_timer = 0
                    self.current_frame = 1 - self.current_frame
                    if hasattr(self, "texture_frame_1") and hasattr(self, "texture_frame_2"):
                        self.base_texture = self.texture_frame_1 if self.current_frame == 0 else self.texture_frame_2

    def draw(self, surface, camera=None, active_instances=None):
        """Inherits rotation drawing from base.py and adds belt rendering."""
        if self.base_texture:
            self.draw_texture(surface, camera=camera)
        else:
             super().draw(surface, camera=camera)
            
        # Draw Belts
        if active_instances:
            import math
            for target_uuid in self.connected_belts:
                target = active_instances.get(target_uuid)
                if target and hasattr(target, 'body'):
                    start_world = self.body.position
                    end_world = target.body.position
                    
                    if camera:
                        start_p = camera.world_to_screen(start_world.x, start_world.y)
                        end_p = camera.world_to_screen(end_world.x, end_world.y)
                    else:
                        start_p = (start_world.x, start_world.y)
                        end_p = (end_world.x, end_world.y)

                    dx = end_p[0] - start_p[0]
                    dy = end_p[1] - start_p[1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist > 0:
                        # 12px offset for gears which are larger pulley surfaces
                        offset_x = (-dy / dist) * 12
                        offset_y = (dx / dist) * 12
                        
                        belt_color = (40, 40, 40) # Dark rubber
                        thickness = 3

                        pygame.draw.line(surface, belt_color, 
                                         (start_p[0] + offset_x, start_p[1] + offset_y), 
                                         (end_p[0] + offset_x, end_p[1] + offset_y), thickness)
                        pygame.draw.line(surface, belt_color, 
                                         (start_p[0] - offset_x, start_p[1] - offset_y), 
                                         (end_p[0] - offset_x, end_p[1] - offset_y), thickness)
        