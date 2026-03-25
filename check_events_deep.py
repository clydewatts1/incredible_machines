import pygame_gui
import pygame

print("ALL pygame_gui Attributes:")
attrs = sorted(dir(pygame_gui))
for a in attrs:
    if "UI_" in a:
        print(a)

print("\nTrying to find SCROLLBAR in all submodules...")
import pkgutil
for loader, name, ispkg in pkgutil.walk_packages(pygame_gui.__path__, pygame_gui.__name__ + "."):
    try:
        module = __import__(name, fromlist=['*'])
        for attr in dir(module):
            if "SCROLLBAR" in attr and "UI_" in attr:
                print(f"Found {attr} in {name}")
    except:
        pass
