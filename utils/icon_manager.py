import os
import pygame
from utils.environment_manager import env_manager
from utils.asset_manager import asset_manager

class IconManager:
    """
    Manages loading and generation of UI icon buttons for the palette.
    Creates a default 40x40 icon with the object's name if the file is missing.
    """
    def __init__(self):
        pass

    def get_icon(self, variant_key: str, label: str = None) -> pygame.Surface:
        """
        Loads the icon from the environment-configured directory.
        If it does not exist, generates a 40x40 icon with the name inside.
        """
        # 2. Icon directory is specified in the environment configuration
        icon_dir = env_manager.get_string("icon_dir", "assets/icons")
        
        # Ensure the directory exists
        os.makedirs(icon_dir, exist_ok=True)
        
        # Format the expected file name based on the variant
        icon_filename = f"{variant_key}_button.png"
        icon_path = os.path.join(icon_dir, icon_filename)

        # 0. If an icon file exists, load the icon file via the asset manager cache
        if os.path.exists(icon_path):
            return asset_manager.get_image(icon_path, fallback_size=(40, 40))

        # 1. If it does not exist, create a default icon 40x40 with the object name in it
        icon_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        
        # Draw base background (dark gray with light border)
        pygame.draw.rect(icon_surf, (60, 60, 60), (2, 2, 36, 36), border_radius=4)
        pygame.draw.rect(icon_surf, (200, 200, 200), (2, 2, 36, 36), 2, border_radius=4)
        
        # Render the name in the icon
        display_name = label if label else variant_key.replace("_", " ").title()
        
        font = pygame.font.SysFont(None, 12)
        words = display_name.split()
        
        # Split text into 2 lines if possible to fit cleanly inside 40x40
        if len(words) >= 2:
            text1 = font.render(words[0][:6], True, (255, 255, 255))
            text2 = font.render(words[1][:6], True, (255, 255, 255))
            icon_surf.blit(text1, text1.get_rect(center=(20, 14)))
            icon_surf.blit(text2, text2.get_rect(center=(20, 26)))
        else:
            text = font.render(display_name[:8], True, (255, 255, 255))
            icon_surf.blit(text, text.get_rect(center=(20, 20)))

        # Save the newly generated icon for future runs
        try:
            pygame.image.save(icon_surf, icon_path)
            print(f"Generated default icon: {icon_path}")
        except Exception as e:
            print(f"Warning: Could not save generated icon {icon_path}: {e}")

        # Return using the asset manager so it is properly cached in memory
        return asset_manager.get_image(icon_path, fallback_size=(40, 40))

# Singleton instance
icon_manager = IconManager()