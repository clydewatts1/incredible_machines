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

    def draw(self, surface):
        """
        Draws the sprite if texture loaded, else falls back to static primitive line.
        """
        if self.base_texture:
            self.draw_texture(surface)
        else:
            p1 = self.body.local_to_world(self.shape.a)
            p2 = self.body.local_to_world(self.shape.b)
            pygame.draw.line(
                surface, 
                constants.COLOR_RAMP, 
                (int(p1.x), int(p1.y)), 
                (int(p2.x), int(p2.y)), 
                int(self.shape.radius * 2)
            )
