import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))

# Use keyword arguments to avoid positional mismatches
h_sb = UIHorizontalScrollBar(relative_rect=pygame.Rect(0, 0, 100, 20), manager=manager)

print("\nH ScrollBar Instance Attributes:")
for attr in sorted(dir(h_sb)):
    if any(x in attr for x in ["scroll", "visible", "percentage", "amount"]):
        try:
            val = getattr(h_sb, attr)
            if not callable(val):
                print(f"{attr}: {val}")
        except:
            pass

pygame.quit()
