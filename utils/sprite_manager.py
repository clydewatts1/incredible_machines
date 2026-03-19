import os
import pygame
from utils.environment_manager import env_manager
from utils.asset_manager import asset_manager

class SpriteManager:
    """
    Manages loading and generation of in-game entity sprites.
    Creates a default placeholder sprite with the object's name if the file is missing.
    """
    def __init__(self):
        pass

    def get_sprite(self, variant_key: str, width: int = 96, height: int = 96, label: str = None) -> pygame.Surface:
        """
        Loads the sprite from the environment-configured directory.
        If it does not exist, generates a placeholder sprite matching the requested dimensions.
        """
        # Sprite directory is specified in the environment configuration, fallback to assets/sprites
        sprite_dir = getattr(env_manager, 'config', {}).get("sprite_dir", "assets/sprites")
        
        # Ensure the directory exists
        os.makedirs(sprite_dir, exist_ok=True)
        
        # Format the expected file name based on the variant
        sprite_filename = f"{variant_key}.png"
        sprite_path = os.path.join(sprite_dir, sprite_filename)

        # 0. If a sprite file exists, load it via the asset manager cache
        if os.path.exists(sprite_path):
            return asset_manager.get_image(sprite_path, fallback_size=(width, height))

        # 1. If it does not exist, create a default placeholder sprite
        sprite_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw base background (a blue-ish tech box with a border)
        pygame.draw.rect(sprite_surf, (80, 100, 140), (0, 0, width, height), border_radius=8)
        pygame.draw.rect(sprite_surf, (150, 180, 255), (0, 0, width, height), 3, border_radius=8)
        
        # Render the name in the sprite
        display_name = label if label else variant_key.replace("_", " ").title()
        
        # Scale font dynamically based on the width of the requested sprite
        font_size = max(14, int(width / 6))
        font = pygame.font.SysFont(None, font_size)
        words = display_name.split()
        
        # Split text into lines to fit nicely inside the box
        if len(words) >= 2:
            text1 = font.render(words[0][:10], True, (255, 255, 255))
            text2 = font.render(" ".join(words[1:])[:10], True, (255, 255, 255))
            sprite_surf.blit(text1, text1.get_rect(center=(width // 2, height // 2 - font_size // 2)))
            sprite_surf.blit(text2, text2.get_rect(center=(width // 2, height // 2 + font_size // 2)))
        else:
            text = font.render(display_name[:12], True, (255, 255, 255))
            sprite_surf.blit(text, text.get_rect(center=(width // 2, height // 2)))

        # Save the newly generated sprite for future runs
        try:
            pygame.image.save(sprite_surf, sprite_path)
            print(f"Generated default sprite: {sprite_path}")
        except Exception as e:
            print(f"Warning: Could not save generated sprite {sprite_path}: {e}")

        # Return using the asset manager so it is properly cached in memory
        return asset_manager.get_image(sprite_path, fallback_size=(width, height))

# Singleton instance
sprite_manager = SpriteManager()