import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))
h_sb = UIHorizontalScrollBar(pygame.Rect(0, 0, 100, 20), manager)

with open("sb_attrs.txt", "w") as f:
    for attr in sorted(dir(h_sb)):
        f.write(attr + "\n")

pygame.quit()
