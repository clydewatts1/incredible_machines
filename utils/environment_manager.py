import pygame
import yaml
import os

class EnvironmentManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvironmentManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, screen_width, screen_height):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'environment.yaml')
        
        # Load YAML configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f) or {}

        # Allow environment.yaml to override window size.
        self.window_width = self._to_int(self.config.get("window_width"), screen_width)
        self.window_height = self._to_int(self.config.get("window_height"), screen_height)
            
        self.fallback_color = tuple(self.config.get("fallback_color", [50, 50, 50]))
        self.edit_mode_color = tuple(self.config.get("edit_mode_color", [255, 200, 0]))
        self.play_mode_color = tuple(self.config.get("play_mode_color", [0, 255, 0]))
        
        bg_path_relative = self.config.get("background_image", "")
        bg_path_absolute = os.path.join(os.path.dirname(__file__), '..', bg_path_relative)
        
        self.background_image = None
        
        try:
            image = pygame.image.load(bg_path_absolute)
            self.background_image = pygame.transform.smoothscale(
                image,
                (self.window_width, self.window_height)
            )
        except FileNotFoundError:
            print(f"FAIL LOUDLY: Background image not found at {bg_path_absolute}. Falling back to solid color.")
        except Exception as e:
            print(f"FAIL LOUDLY: Failed to load background image {bg_path_absolute}: {e}. Falling back to solid color.")

    def _to_int(self, value, default):
        """Safely convert YAML values to int with fallback."""
        try:
            if value is None:
                return int(default)
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    def get_int(self, key, default):
        """Get an integer config value from environment.yaml."""
        return self._to_int(self.config.get(key), default)

    def draw_background(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(self.fallback_color)

# Global singleton
env_manager = EnvironmentManager()
