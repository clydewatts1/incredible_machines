import pygame
import pymunk
from entities.base import GamePart
import constants

class Ramp(GamePart):
    def __init__(self, space, x, y):
        super().__init__(space)
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (x, y)
        
        # A simple horizontal ramp, 200 units wide
        length = 100
        thickness = 5.0
        self.shape = pymunk.Segment(self.body, (-length, 0), (length, 0), thickness)
        self.shape.elasticity = 0.5
        self.shape.friction = 0.6
        self.shape.collision_type = 2
        
        # Add to space
        self.space.add(self.body, self.shape)

    def draw(self, surface):
        """
        Draws the static ramp line based on Pymunk physics placement.
        """
        p1 = self.body.local_to_world(self.shape.a)
        p2 = self.body.local_to_world(self.shape.b)
        
        pygame.draw.line(
            surface, 
            constants.COLOR_RAMP, 
            (int(p1.x), int(p1.y)), 
            (int(p2.x), int(p2.y)), 
            int(self.shape.radius * 2)
        )
