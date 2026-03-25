import pygame_gui
import pygame

with open("pg_gui_all.txt", "w") as f:
    for a in sorted(dir(pygame_gui)):
        f.write(a + "\n")
