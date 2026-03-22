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

    def get_icon(self, variant_key: str, label: str = None, skip_global: bool = False, overrides: dict = None) -> pygame.Surface:
        """
        Resolution Chain:
        1. Local Project: saves/[flow_name]/icons/
        2. Global: assets/icons/
        3. Generate: Ollama x/flux2-klein fallback
        """
        # 1. Check active project directory first
        project_name = getattr(env_manager, 'active_project', None)
        if project_name:
            project_icon_dir = os.path.join("saves", project_name, "icons")
            icon_path = os.path.join(project_icon_dir, f"{variant_key}_button.png")
            if os.path.exists(icon_path):
                return asset_manager.get_image(icon_path, fallback_size=(40, 40))

        # 2. Global directory fallback
        global_icon_path = os.path.join("assets/icons", f"{variant_key}_button.png")
        if not skip_global:
            if os.path.exists(global_icon_path):
                return asset_manager.get_image(global_icon_path, fallback_size=(40, 40))

        # 3. Generate via Ollama (fallback)
        target_path = None
        if project_name:
            project_icon_dir = os.path.join("saves", project_name, "icons")
            os.makedirs(project_icon_dir, exist_ok=True)
            target_path = os.path.join(project_icon_dir, f"{variant_key}_button.png")
            
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

            prompt = f"A professional 2D game UI icon representing {obj_desc}, isolated on a clean solid light-grey background, high quality, consistent art style matching the theme: {flow_name} - {flow_desc}"
            
            print(f"IconManager: Triggering Ollama (x/flux2-klein) for '{variant_key}'...")
            if self._trigger_ollama_generation(prompt, target_path):
                print(f"IconManager: Successfully generated icon for '{variant_key}'")
                return asset_manager.get_image(target_path, fallback_size=(40, 40))
            else:
                print(f"IconManager: Ollama generation failed for '{variant_key}', falling back to primitive.")

        # Absolute Fallback: Original primitive generation
        fallback_path = target_path if project_name else global_icon_path
        return self._generate_primitive_icon(variant_key, label, fallback_path)

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

    def _generate_primitive_icon(self, variant_key, label, icon_path):
        icon_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(icon_surf, (60, 60, 60), (2, 2, 36, 36), border_radius=4)
        pygame.draw.rect(icon_surf, (200, 200, 200), (2, 2, 36, 36), 2, border_radius=4)
        display_name = label if label else variant_key.replace("_", " ").title()
        font = pygame.font.SysFont(None, 12)
        words = display_name.split()
        if len(words) >= 2:
            text1 = font.render(words[0][:6], True, (255, 255, 255))
            text2 = font.render(words[1][:6], True, (255, 255, 255))
            icon_surf.blit(text1, text1.get_rect(center=(20, 14)))
            icon_surf.blit(text2, text2.get_rect(center=(20, 26)))
        else:
            text = font.render(display_name[:8], True, (255, 255, 255))
            icon_surf.blit(text, text.get_rect(center=(20, 20)))
        try:
            os.makedirs(os.path.dirname(icon_path), exist_ok=True)
            pygame.image.save(icon_surf, icon_path)
            print(f"Generated default primitive icon: {icon_path}")
        except Exception as e:
            print(f"Warning: Could not save primitive icon {icon_path}: {e}")
        return asset_manager.get_image(icon_path, fallback_size=(40, 40))

# Singleton instance
icon_manager = IconManager()