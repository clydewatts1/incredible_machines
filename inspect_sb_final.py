import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))
# The signature on my system might allow 0-1 percentage
h_sb = UIHorizontalScrollBar(pygame.Rect(0, 0, 100, 20), manager)

print("\nH ScrollBar Keys:")
print([k for k in h_sb.__dict__.keys() if "scroll" in k or "visible" in k])
pygame.quit()
