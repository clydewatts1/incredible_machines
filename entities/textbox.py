import pygame
import pymunk
from entities.base import GamePart

class TextBoxPart(GamePart):
    """A purely visual text box for comments and descriptions. Does not impact physics collisions."""

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        # Turn off all physical collisions so objects flow right through it
        if self.shape:
            # Making it a sensor lets physical objects pass right through it
            self.shape.sensor = True
            
        if self.body:
            # CRITICAL FIX: Make the body kinematic so gravity doesn't pull it through the floor!
            self.body.body_type = pymunk.Body.KINEMATIC

    def draw(self, surface, camera=None):
        # Safe fallback if the object is missing its physics body
        if self.body:
            pos_x, pos_y = self.body.position.x, self.body.position.y
        else:
            pos_x, pos_y = getattr(self, 'x', 0), getattr(self, 'y', 0)

        if camera:
            screen_x, screen_y = camera.world_to_screen(pos_x, pos_y)
        else:
            screen_x, screen_y = pos_x, pos_y

        # Fetch visual properties
        text = str(self.get_property("text", "Comment..."))
        font_size = int(self.get_property("font_size", 20))
        text_color = self.get_property("text_color", (255, 255, 255))
        bg_color = self.get_property("bg_color", (40, 40, 40, 180)) # Supports alpha for transparency
        
        # Ensure colors are tuples (YAML arrays load as lists)
        if isinstance(text_color, list): text_color = tuple(text_color)
        if isinstance(bg_color, list): bg_color = tuple(bg_color)
        
        font = pygame.font.SysFont(None, font_size)
        
        # Support multiline text via \n character
        lines = text.split('\\n') if '\\n' in text else text.split('\n')
        
        rendered_lines = [font.render(line, True, text_color) for line in lines]
        
        # Calculate bounding box for the text
        max_width = max([r.get_width() for r in rendered_lines]) if rendered_lines else 0
        total_height = sum([r.get_height() for r in rendered_lines])
        
        padding = 10
        rect_w = max_width + padding * 2
        rect_h = total_height + padding * 2
        
        # Draw background with alpha transparency and a border
        bg_surf = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, bg_color, bg_surf.get_rect(), border_radius=6)
        pygame.draw.rect(bg_surf, (150, 150, 150), bg_surf.get_rect(), 2, border_radius=6)
        
        # Center the text box directly over the physics body
        rect_x = int(screen_x - rect_w / 2)
        rect_y = int(screen_y - rect_h / 2)
        
        surface.blit(bg_surf, (rect_x, rect_y))
        
        # Draw the text lines
        current_y = rect_y + padding
        for r in rendered_lines:
            surface.blit(r, (rect_x + padding, current_y))
            current_y += r.get_height()