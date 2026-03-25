import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))
h_sb = UIHorizontalScrollBar(pygame.Rect(0, 0, 100, 20), manager)

print("\nH ScrollBar Instance Attributes:")
for attr in sorted(dir(h_sb)):
    if not attr.startswith("__"):
        try:
            val = getattr(h_sb, attr)
            if not callable(val):
                print(f"{attr}: {val}")
        except:
            pass

pygame.quit()
