import pygame_gui
import pygame

print("pygame_gui Events:")
events = [attr for attr in dir(pygame_gui) if "SCROLLBAR" in attr]
if not events:
    # Try searching for all UI events
    events = [attr for attr in dir(pygame_gui) if "UI_" in attr]

for e in sorted(events):
    print(e)

# Also check pygame.USEREVENT based ones if they are there
print("\nChecking for scrollbar events in pygame_gui constants...")
try:
    from pygame_gui import UI_HORIZONTAL_SCROLLBAR_CHANGED
    print("Found UI_HORIZONTAL_SCROLLBAR_CHANGED directly in pygame_gui")
except ImportError:
    print("NOT found directly in pygame_gui")
