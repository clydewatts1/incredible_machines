import pygame
import pymunk
from entities.base import GamePart
import constants

class Ball(GamePart):
    def __init__(self, space, x, y):
        super().__init__(space, "bouncy_ball")
        mass = self.properties["mass"]
        self.radius = 15.0
        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0, 0))
        self.body = pymunk.Body(mass, inertia, body_type=pymunk.Body.DYNAMIC)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, self.radius, (0, 0))
        self.shape.elasticity = self.properties["elasticity"]
        self.shape.friction = self.properties["friction"]
        self.shape.collision_type = 1
        
        # Add to space
        self.space.add(self.body, self.shape)

    def draw(self, surface):
        """
        Draws the ball using Pymunk physics position.
        Called strictly by GamePart.update_visual() to ensure Fail Loudly assertions run.
        """
        import math
        x = int(self.body.position.x)
        y = int(self.body.position.y)
        pygame.draw.circle(surface, constants.COLOR_BALL, (x, y), int(self.radius))
        
        # Draw a line from center to edge to visually confirm it is rolling
        end_x = x + math.cos(self.body.angle) * self.radius
        end_y = y + math.sin(self.body.angle) * self.radius
        pygame.draw.line(surface, (0, 0, 0), (x, y), (int(end_x), int(end_y)), 2)
