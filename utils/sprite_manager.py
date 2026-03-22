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

    def get_sprite(self, variant_key: str, width: int = 96, height: int = 96, label: str = None, skip_global: bool = False, overrides: dict = None) -> pygame.Surface:
        """
        Resolution Chain:
        1. Local Project: saves/[flow_name]/sprites/
        2. Global: assets/sprites/
        3. Generate: Ollama x/flux2-klein fallback
        """
        # 1. Check active project directory first
        project_name = getattr(env_manager, 'active_project', None)
        if project_name:
            project_sprite_dir = os.path.join("saves", project_name, "sprites")
            sprite_path = os.path.join(project_sprite_dir, f"{variant_key}.png")
            if os.path.exists(sprite_path):
                return asset_manager.get_image(sprite_path, fallback_size=(width, height))

        # 2. Global directory fallback
        global_sprite_path = os.path.join("assets/sprites", f"{variant_key}.png")
        if not skip_global:
            if os.path.exists(global_sprite_path):
                return asset_manager.get_image(global_sprite_path, fallback_size=(width, height))

        # 3. Generate via Ollama (fallback)
        target_path = None
        if project_name:
            project_sprite_dir = os.path.join("saves", project_name, "sprites")
            os.makedirs(project_sprite_dir, exist_ok=True)
            target_path = os.path.join(project_sprite_dir, f"{variant_key}.png")
            
            # Construct descriptive prompt
            flow_name = getattr(env_manager, 'active_flow_name', project_name.replace("_", " "))
            flow_desc = getattr(env_manager, 'active_flow_description', "A 2D game asset matching the theme.")

            # Rich metadata for prompt
            custom_name = overrides.get("custom_name") if overrides else None
            custom_desc = overrides.get("custom_description") if overrides else None
            obj_desc = f"{custom_name or variant_key}"
            if custom_desc:
                obj_desc += f" ({custom_desc})"
            elif label:
                obj_desc += f" ({label})"

            prompt = f"A professional 2D in-game sprite representing {obj_desc}, isolated on a clean solid light-grey background, high quality, consistent art style matching the theme: {flow_name} - {flow_desc}. The asset should be a single clear object."
            
            print(f"SpriteManager: Triggering Ollama (x/flux2-klein) for '{variant_key}'...")
            if self._trigger_ollama_generation(prompt, target_path):
                print(f"SpriteManager: Successfully generated sprite for '{variant_key}'")
                return asset_manager.get_image(target_path, fallback_size=(width, height))
            else:
                print(f"SpriteManager: Ollama generation failed for '{variant_key}', falling back to primitive.")

        # Absolute Fallback: Original primitive generation
        fallback_path = target_path if project_name else global_sprite_path
        return self._generate_primitive_sprite(variant_key, width, height, label, fallback_path)

    def _trigger_ollama_generation(self, prompt, save_path):
        import requests
        import base64
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "x/flux2-klein",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "image" in data:
                    img_data = base64.b64decode(data["image"])
                    with open(save_path, "wb") as f:
                        f.write(img_data)
                    return True
                else:
                    print(f"Ollama Debug: Response 200 but 'image' key missing. Keys: {data.keys()}")
            else:
                print(f"Ollama Debug: HTTP {response.status_code}: {response.text}")
            return False
        except Exception as e:
            print(f"Ollama Generation Error: {e}")
            return False

    def _generate_primitive_sprite(self, variant_key, width, height, label, sprite_path):
        sprite_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(sprite_surf, (80, 100, 140), (0, 0, width, height), border_radius=8)
        pygame.draw.rect(sprite_surf, (150, 180, 255), (0, 0, width, height), 3, border_radius=8)
        display_name = label if label else variant_key.replace("_", " ").title()
        font_size = max(14, int(width / 6))
        font = pygame.font.SysFont(None, font_size)
        words = display_name.split()
        if len(words) >= 2:
            text1 = font.render(words[0][:10], True, (255, 255, 255))
            text2 = font.render(" ".join(words[1:])[:10], True, (255, 255, 255))
            sprite_surf.blit(text1, text1.get_rect(center=(width // 2, height // 2 - font_size // 2)))
            sprite_surf.blit(text2, text2.get_rect(center=(width // 2, height // 2 + font_size // 2)))
        else:
            text = font.render(display_name[:12], True, (255, 255, 255))
            sprite_surf.blit(text, text.get_rect(center=(width // 2, height // 2)))
        try:
            os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
            pygame.image.save(sprite_surf, sprite_path)
            print(f"Generated default primitive sprite: {sprite_path}")
        except Exception as e:
            print(f"Warning: Could not save primitive sprite {sprite_path}: {e}")
        return asset_manager.get_image(sprite_path, fallback_size=(width, height))

# Singleton instance
sprite_manager = SpriteManager()