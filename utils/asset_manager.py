import os
import pygame

class AssetManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AssetManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.init_manager()
        return cls._instance
        
    def init_manager(self):
        self.cache = {}
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        # Ensure directories exist
        os.makedirs(os.path.join(self.base_dir, "assets", "sprites"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "assets", "icons"), exist_ok=True)
        
    def get_image(self, rel_path, fallback_size=(50, 50), text_label="X"):
        """
        Retrieves an image from the cache or disk.
        If missing, auto-generates a distinct placeholder, saves to disk, and caches.
        """
        if rel_path in self.cache:
            return self.cache[rel_path]
            
        abs_path = os.path.join(self.base_dir, rel_path)
        
        try:
            img = pygame.image.load(abs_path).convert_alpha()
            self.cache[rel_path] = img
            return img
        except FileNotFoundError:
            print(f"AssetManager: Generating missing asset -> {rel_path}")
            
            # Auto-Generation Fallback
            # 1. Create Surface
            surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
            
            # 2. Draw grey box with red outline
            pygame.draw.rect(surf, (150, 150, 150, 255), (0, 0, fallback_size[0], fallback_size[1]))
            pygame.draw.rect(surf, (255, 50, 50, 255), (0, 0, fallback_size[0], fallback_size[1]), width=3)
            
            # 3. Draw a big red X
            pygame.draw.line(surf, (255, 50, 50, 255), (0, 0), (fallback_size[0], fallback_size[1]), 3)
            pygame.draw.line(surf, (255, 50, 50, 255), (0, fallback_size[1]), (fallback_size[0], 0), 3)
            
            # 4. Render label text if Pygame fonts are initialized
            if pygame.font.get_init():
                font = pygame.font.SysFont(None, 20)
                text_surf = font.render(text_label, True, (0, 0, 0))
                # Center text
                text_rect = text_surf.get_rect(center=(fallback_size[0] // 2, fallback_size[1] // 2))
                # Add background for readability
                bg_rect = text_rect.copy()
                bg_rect.inflate_ip(4, 4)
                pygame.draw.rect(surf, (255, 255, 255, 200), bg_rect)
                surf.blit(text_surf, text_rect)
            
            # 5. Save to disk so user can edit it
            # Ensure the relative directory exists before saving (in case it targets a subfolder)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            pygame.image.save(surf, abs_path)
            
            # 6. Cache and return
            self.cache[rel_path] = surf
            return surf

asset_manager = AssetManager()
