import os
import pygame
import math
from collections import OrderedDict

class AssetManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AssetManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.init_manager()
        return cls._instance
        
    def init_manager(self):
        self.cache = OrderedDict()
        self.max_size = 500
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # Ensure base directories exist
        os.makedirs(os.path.join(self.base_dir, "assets", "sprites"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "assets", "icons"), exist_ok=True)
        
    def _draw_gear(self, surf, size):
        """Draws a procedural gear with teeth and an axle hole."""
        w, h = size
        center = (w // 2, h // 2)
        outer_radius = min(w, h) // 2 - 4
        gear_color = (130, 130, 130) # Classic metal grey
        outline_color = (50, 50, 50)

        # Draw 8 teeth using trigonometry
        num_teeth = 8
        tooth_h = 6
        for i in range(num_teeth):
            angle = (i * 2 * math.pi) / num_teeth
            # Create a trapezoidal tooth shape
            pts = [
                (center[0] + outer_radius * math.cos(angle - 0.2), center[1] + outer_radius * math.sin(angle - 0.2)),
                (center[0] + outer_radius * math.cos(angle + 0.2), center[1] + outer_radius * math.sin(angle + 0.2)),
                (center[0] + (outer_radius + tooth_h) * math.cos(angle + 0.1), center[1] + (outer_radius + tooth_h) * math.sin(angle + 0.1)),
                (center[0] + (outer_radius + tooth_h) * math.cos(angle - 0.1), center[1] + (outer_radius + tooth_h) * math.sin(angle - 0.1))
            ]
            pygame.draw.polygon(surf, gear_color, pts)
            pygame.draw.polygon(surf, outline_color, pts, 1)

        # Main circle body and center hole
        pygame.draw.circle(surf, gear_color, center, outer_radius)
        pygame.draw.circle(surf, outline_color, center, outer_radius, 2)
        pygame.draw.circle(surf, (0, 0, 0, 0), center, outer_radius // 4) # Axle hole

    def get_image(self, rel_path, fallback_size=(50, 50), text_label="X"):
        """Safe image retrieval: Loads existing or generates fallback without overwriting."""
        if rel_path in self.cache:
            self.cache.move_to_end(rel_path)
            return self.cache[rel_path]
            
        abs_path = os.path.join(self.base_dir, rel_path)
        
        # 1. ATTEMPT TO LOAD EXISTING
        if os.path.exists(abs_path):
            try:
                img = pygame.image.load(abs_path).convert_alpha()
                if len(self.cache) >= self.max_size:
                    self.cache.popitem(last=False)
                self.cache[rel_path] = img
                return img
            except pygame.error:
                print(f"AssetManager: Failed to load existing file at {rel_path}")

        # 2. GENERATE FALLBACK IF MISSING
        print(f"AssetManager: Missing file. Generating fallback for -> {rel_path}")
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        
        # Determine if it's a gear (sprite or icon)
        is_gear = "gear" in rel_path.lower() or text_label == "⚙"
        
        if is_gear:
            self._draw_gear(surf, fallback_size)
        else:
            # Generic box placeholder
            pygame.draw.rect(surf, (100, 100, 100, 200), (0, 0, fallback_size[0], fallback_size[1]))
            pygame.draw.line(surf, (255, 50, 50), (0, 0), (fallback_size[0], fallback_size[1]), 2)
            if pygame.font.get_init():
                font = pygame.font.SysFont(None, 18)
                txt = font.render(text_label[:10], True, (255, 255, 255))
                surf.blit(txt, (5, 5))

        # 3. SAVE ONLY IF FILE IS GONE
        if not os.path.exists(abs_path):
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            pygame.image.save(surf, abs_path)
        
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[rel_path] = surf
        return surf

asset_manager = AssetManager()