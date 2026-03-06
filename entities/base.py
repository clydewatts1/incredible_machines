import pygame
import pymunk

class GamePart:
    """
    Base class for all entities in the game.
    Enforces the 'Pymunk Rule' by strictly separating physics and rendering,
    and ensuring the visual representation always follows the physics body.
    """
    def __init__(self, space):
        self.space = space
        self.body = None
        self.shape = None

    def update_visual(self, surface):
        """
        Reads the Pymunk body position and rotation to render the Pygame visual.
        MUST fail loudly if physics components are missing.
        """
        assert self.body is not None, "FAIL LOUDLY: GamePart is missing a physics body!"
        assert self.shape is not None, "FAIL LOUDLY: GamePart is missing a physics shape!"
        self.draw(surface)

    def draw(self, surface):
        """
        To be implemented by subclasses. Do not call directly for game loop updates;
        use update_visual() which enforces the assertions.
        """
        raise NotImplementedError("Subclasses must implement the draw method.")
