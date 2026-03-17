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

    def connect_to_gear(self, other_gear, ratio=-1.0):
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

    def draw(self, surface, camera=None):
        """Inherits the synchronized rotation drawing from base.py."""
        if self.base_texture:
            self.draw_texture(surface, camera=camera)
        