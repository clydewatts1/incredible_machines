import os
import pygame
from entities.base import GamePart

BALL_DEFAULT_RADIUS = 10

class PayloadBallPart(GamePart):
    """A dynamic ball that visually changes color based on its payload score."""

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        # Generate default icon if it doesn't exist
        icon_path = f"assets/icons/{self.variant_key}_button.png"
        if not os.path.exists(icon_path):
            os.makedirs("assets/icons", exist_ok=True)
            # Create a transparent surface
            icon_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            
            # Draw a default shiny blue ball for the icon
            pygame.draw.circle(icon_surf, (0, 0, 255), (20, 20), BALL_DEFAULT_RADIUS)
            pygame.draw.circle(icon_surf, (255, 255, 255), (14, 14), 5) # Highlight
            pygame.draw.circle(icon_surf, (0, 0, 0), (20, 20), BALL_DEFAULT_RADIUS, 1)   # Outline
            
            try:
                pygame.image.save(icon_surf, icon_path)
            except Exception as e:
                print(f"Warning: Could not save icon for payload ball: {e}")

    def get_color_for_score(self, score):
        """Calculates a progressive color blend based on the score threshold."""
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 100.0

        if score >= 100:
            return (0, 255, 0)  # Solid Green
        elif score >= 50:
            # Interpolate 50 to 100: Orange (255, 128, 0) -> Green (0, 255, 0)
            t = (score - 50) / 50.0
            r = int(255 + t * (0 - 255))
            g = int(128 + t * (255 - 128))
            return (r, g, 0)
        elif score >= 0:
            # Interpolate 0 to 50: Red (255, 0, 0) -> Orange (255, 128, 0)
            t = score / 50.0
            r = 255
            g = int(0 + t * (128 - 0))
            return (r, g, 0)
        else:
            # Interpolate < 0 to 0: Yellow (255, 255, 0) -> Red (255, 0, 0)
            # We cap the transition so it reaches full yellow at a score of -50
            t = max(0.0, min(1.0, (score + 50) / 50.0))
            r = 255
            g = int(255 + t * (0 - 255))
            return (r, g, 0)

    def draw(self, surface, camera=None):
        if not self.body:
            return

        pos = self.body.position
        if camera:
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        else:
            screen_x, screen_y = pos.x, pos.y

        # Determine the score from the payload dictionary
        score = 100
        if hasattr(self, 'payload') and isinstance(self.payload, dict):
            score = self.payload.get('score', 100)
        else:
            # Fallback to direct property if the payload dict isn't fully populated
            score = self.get_property('score', 100)
        print(f"PayloadBall at ({screen_x}, {screen_y}) has score: {score}")
        color = self.get_color_for_score(score)
        print(f"Calculated color for score {score}: {color}")
        radius = float(self.get_property('radius', BALL_DEFAULT_RADIUS))

        # 1. Draw the main colored circle (No background)
        pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), int(radius))

        # 2. Draw a subtle 3D highlight (slightly offset) to give it a spherical, shiny look
        highlight_radius = int(radius * 0.3)
        if highlight_radius > 0:
            highlight_x = int(screen_x - radius * 0.3)
            highlight_y = int(screen_y - radius * 0.3)
            pygame.draw.circle(surface, (255, 255, 255, 150), (highlight_x, highlight_y), highlight_radius)

        # 3. Draw a sharp black outline to make it pop against the background
        pygame.draw.circle(surface, (0, 0, 0), (int(screen_x), int(screen_y)), int(radius), 1)