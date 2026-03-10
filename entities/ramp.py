import pygame
import pymunk
from entities.base import GamePart
import constants

class Ramp(GamePart):
    def __init__(self, space, x, y, variant_key="long_ramp"):
        super().__init__(space, variant_key)
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (x, y)
        
        # Pull dimensions from YAML
        length = self.properties.get("length", 100)
        thickness = self.properties.get("thickness", 5.0)
        self.shape = pymunk.Segment(self.body, (-length, 0), (length, 0), thickness)
        
        # Scale texture once if it exists
        if self.base_texture:
            # We scale to width = length*2, height = thickness*2 to cover the segment
            self.base_texture = pygame.transform.scale(self.base_texture, (int(length * 2), int(thickness * 2)))
        self.shape.elasticity = self.properties["elasticity"]
        self.shape.friction = self.properties["friction"]
        self.shape.collision_type = 2
        
        # Add to space
        self.space.add(self.body, self.shape)

    def draw(self, surface, camera=None):
        """
        Draws the sprite if texture loaded, else falls back to static primitive line.
        M25 Phase 2: Applies camera offset if provided.
        """
        if self.base_texture:
            self.draw_texture(surface, camera=camera)
        else:
            p1 = self.body.local_to_world(self.shape.a)
            p2 = self.body.local_to_world(self.shape.b)
            
            # Apply camera transformation if provided
            if camera:
                screen_p1 = camera.world_to_screen(p1.x, p1.y)
                screen_p2 = camera.world_to_screen(p2.x, p2.y)
            else:
                screen_p1 = (p1.x, p1.y)
                screen_p2 = (p2.x, p2.y)
            
            pygame.draw.line(
                surface, 
                constants.COLOR_RAMP, 
                (int(screen_p1[0]), int(screen_p1[1])), 
                (int(screen_p2[0]), int(screen_p2[1])), 
                int(self.shape.radius * 2)
            )
