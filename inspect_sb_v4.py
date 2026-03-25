import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))

# Pass visible_percentage (e.g. 0.5 for 50% visibility)
h_sb = UIHorizontalScrollBar(relative_rect=pygame.Rect(0, 0, 100, 20), 
                               manager=manager, 
                               visible_percentage=0.5)

print("\nH ScrollBar Instance Attributes (with visible_percentage=0.5):")
for attr in sorted(dir(h_sb)):
    if any(x in attr for x in ["scroll", "visible", "percentage", "amount"]):
        try:
            val = getattr(h_sb, attr)
            if not callable(val):
                print(f"{attr}: {val}")
        except:
            pass

pygame.quit()
