import pygame
import pygame_gui
pygame.init()
window = pygame.display.set_mode((200, 200))
theme = {"panel": {"colours": {"normal_bg": "#FF00FF"}}}
# Try constructor
try:
    manager = pygame_gui.UIManager((200, 200), theme)
    print("Direct dictionary load works!")
except Exception as e:
    print(f"Direct dictionary load failed: {e}")
    manager = pygame_gui.UIManager((200, 200))
    try:
        manager.get_theme().load_theme(theme)
        print("get_theme().load_theme() works!")
    except Exception as e2:
        print(f"load_theme() failed: {e2}")
pygame.quit()
