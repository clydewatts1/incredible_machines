# constants.py
import pygame

# Window Dimensions
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Physics Configuration
PHYSICS_STEP = 1 / 60.0
GRAVITY = (0, 900)  # Pygame Y goes down, so positive Y is "down" in Pymunk too

# Colors (RGB)
COLOR_BACKGROUND = (30, 30, 30)
COLOR_TEXT = (200, 200, 200)
COLOR_RAMP = (150, 150, 150)
COLOR_BALL = (255, 100, 100)
COLOR_BOUNDARY = (100, 100, 100)
