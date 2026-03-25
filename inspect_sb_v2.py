import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar

pygame.init()
pygame.display.set_mode((100, 100))
manager = pygame_gui.UIManager((100, 100))
try:
    # Try with keyword arguments to avoid positional issues
    h_sb = UIHorizontalScrollBar(relative_rect=pygame.Rect(0, 0, 100, 20), manager=manager)
    
    print("\nH ScrollBar Instance Attributes:")
    for attr in sorted(dir(h_sb)):
        if "percentage" in attr or "scroll" in attr or "visible" in attr:
            try:
                val = getattr(h_sb, attr)
                if not callable(val):
                    print(f"{attr}: {val}")
            except:
                pass
except Exception as e:
    print(f"FAILED to create ScrollBar: {e}")
    # If it failed, let's see the help(...)
    import pydoc
    print("\nHelp for UIHorizontalScrollBar:")
    print(pydoc.render_doc(UIHorizontalScrollBar))

pygame.quit()
