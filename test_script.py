import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import main

# fake some events
main.pygame.event.post(main.pygame.event.Event(main.pygame.MOUSEBUTTONDOWN, button=1, pos=(800, 500))) # click cannon tool
main.pygame.event.post(main.pygame.event.Event(main.pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 200))) # spawn cannon
main.pygame.event.post(main.pygame.event.Event(main.pygame.MOUSEBUTTONDOWN, button=1, pos=(200, 200))) # select cannon

main.running = False

try:
    with open("main.py", "r") as f:
        src = f.read()
    
    # We will just patch main to run 3 loops and break
    src = src.replace("while running:", "for _ in range(10):")
    src = src.replace("running = False", "break")
    
    with open("test_main.py", "w") as f:
        f.write(src)
        
    import test_main
except Exception as e:
    print(e)
