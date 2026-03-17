import pygame
import pymunk
import math
from entities.base import GamePart

class AxlePart(GamePart):
    def __init__(self, space, x, y, variant_key="axle"):
        super().__init__(space, x, y, variant_key)
        
        # 1. Physical Properties
        mass = float(self.get_property("mass", 1.0))
        radius = float(self.get_property("radius", 15))
        moment = pymunk.moment_for_circle(mass, 0, radius)
        
        # 2. Body Setup: Dynamic so it can rotate, but Pinned to world
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, radius)
        
        # 3. Collision Filtering: Usually ignore physics collisions
        self.shape.filter = pymunk.ShapeFilter(categories=0x4, mask=0)
        
        # 4. The Axle Pin
        self.pin = pymunk.PivotJoint(self.space.static_body, self.body, (x, y))
        self.space.add(self.body, self.shape, self.pin)
        self.connected_belts = [] # Store UUIDs of axles we are linked to by belt

    def connect_gear(self, gear_entity, ratio=1.0):
        """Mechanically locks a gear to this axle at a specific ratio."""
        joint = pymunk.GearJoint(self.body, gear_entity.body, 0, ratio)
        self.space.add(joint)
        return joint


    def connect_belt(self, other_axle):
        """Creates a belt drive connection and ensures it is saved."""
        r1 = float(self.get_property("radius", 15))
        r2 = float(other_axle.get_property("radius", 15))
        
        ratio = (r1 / r2)
        joint = pymunk.GearJoint(self.body, other_axle.body, 0, ratio)
        self.space.add(joint)
        
        # Add to local list for fast drawing
        self.connected_belts.append(other_axle.uuid)
        
        # NEW: Store in overrides so LevelManager saves the connection
        existing_belts = self.overrides.get("connected_belts", [])
        if other_axle.uuid not in existing_belts:
            existing_belts.append(other_axle.uuid)
            self.apply_draft_overrides({"connected_belts": existing_belts})
            
        return joint

    def draw(self, surface, camera=None,active_instances=None):
        """Custom procedural drawing for a rotating axle with knobs and belts"""
        # 1. Get screen coordinates
        pos = self.body.position
        if camera:
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        else:
            screen_x, screen_y = pos.x, pos.y
            
        angle = self.body.angle
        length = float(self.get_property("radius", 15)) * 1.5
        knob_radius = 6
        shaft_width = 4
        
        # 2. Calculate end points based on rotation
        # Start Nob
        x1 = screen_x + length * math.cos(angle)
        y1 = screen_y + length * math.sin(angle)
        # End Nob
        x2 = screen_x - length * math.cos(angle)
        y2 = screen_y - length * math.sin(angle)
        
        # 3. Draw Thin Middle Section (Shaft)
        pygame.draw.line(surface, (100, 100, 100), (int(x1), int(y1)), (int(x2), int(y2)), shaft_width)
        
        # 4. Draw Knobs at ends
        pygame.draw.circle(surface, (150, 150, 150), (int(x1), int(y1)), knob_radius)
        pygame.draw.circle(surface, (60, 60, 60), (int(x1), int(y1)), knob_radius, 1) # Outline
        
        pygame.draw.circle(surface, (150, 150, 150), (int(x2), int(y2)), knob_radius)
        pygame.draw.circle(surface, (60, 60, 60), (int(x2), int(y2)), knob_radius, 1) # Outline
        
        # 5. Draw Center Pin
        pygame.draw.circle(surface, (40, 40, 40), (int(screen_x), int(screen_y)), 3)

        # 6. Draw Belts
        if active_instances:
            for target_uuid in self.connected_belts:
                target = active_instances.get(target_uuid)
                if target and hasattr(target, 'body'):
                    # Get world positions
                    start_world = self.body.position
                    end_world = target.body.position
                    
                    # Convert to screen positions
                    if camera:
                        start_p = camera.world_to_screen(start_world.x, start_world.y)
                        end_p = camera.world_to_screen(end_world.x, end_world.y)
                    else:
                        start_p = (start_world.x, start_world.y)
                        end_p = (end_world.x, end_world.y)

                    # Calculate belt offset (perpindicular to the direction)
                    dx = end_p[0] - start_p[0]
                    dy = end_p[1] - start_p[1]
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist > 0:
                        # 8px offset for a belt that sits on the edges of the pulleys
                        offset_x = (-dy / dist) * 8
                        offset_y = (dx / dist) * 8
                        
                        belt_color = (40, 40, 40) # Dark rubber
                        thickness = 3

                        # Top and Bottom belt lines
                        pygame.draw.line(surface, belt_color, 
                                         (start_p[0] + offset_x, start_p[1] + offset_y), 
                                         (end_p[0] + offset_x, end_p[1] + offset_y), thickness)
                        pygame.draw.line(surface, belt_color, 
                                         (start_p[0] - offset_x, start_p[1] - offset_y), 
                                         (end_p[0] - offset_x, end_p[1] - offset_y), thickness)