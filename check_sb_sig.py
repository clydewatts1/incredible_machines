import pygame
import pygame_gui
from pygame_gui.elements import UIHorizontalScrollBar, UIVerticalScrollBar
import inspect

print("UIHorizontalScrollBar signature:")
print(inspect.signature(UIHorizontalScrollBar.__init__))
print("\nUIVerticalScrollBar signature:")
print(inspect.signature(UIVerticalScrollBar.__init__))
