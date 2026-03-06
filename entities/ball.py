import pygame
import pymunk
from entities.base import GamePart
import constants

class Ball(GamePart):
    def __init__(self, space, x, y):
        super().__init__(space)
        mass = 1.0
        self.radius = 15.0
        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0, 0))
        self.body = pymunk.Body(mass, inertia, body_type=pymunk.Body.DYNAMIC)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, self.radius, (0, 0))
        self.shape.elasticity = 0.95
        self.shape.friction = 0.5
        self.shape.collision_type = 1
        
        # Add to space
        self.space.add(self.body, self.shape)

    def draw(self, surface):
        """
        Draws the ball using Pymunk physics position.
        Called strictly by GamePart.update_visual() to ensure Fail Loudly assertions run.
        """
        x = int(self.body.position.x)
        y = int(self.body.position.y)
        pygame.draw.circle(surface, constants.COLOR_BALL, (x, y), int(self.radius))
