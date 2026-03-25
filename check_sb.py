import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar, UIVerticalScrollBar

pygame.init()
window = pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))
h_sb = UIHorizontalScrollBar(pygame.Rect(0, 0, 100, 20), manager)
v_sb = UIVerticalScrollBar(pygame.Rect(0, 0, 20, 100), manager)

print("H ScrollBar attributes:")
print([a for a in dir(h_sb) if "visible" in a or "scrollable" in a])
print("V ScrollBar attributes:")
print([a for a in dir(v_sb) if "visible" in a or "scrollable" in a])

pygame.quit()
