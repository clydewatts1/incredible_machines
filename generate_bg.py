import pygame
import os

def generate_background():
    pygame.init()
    width, height = 800, 600
    surface = pygame.Surface((width, height))
    
    # Draw a simple grid
    surface.fill((20, 30, 60)) # Dark blue/slate background
    
    grid_color = (40, 60, 100)
    grid_size = 40
    
    for x in range(0, width, grid_size):
        pygame.draw.line(surface, grid_color, (x, 0), (x, height), 1)
    for y in range(0, height, grid_size):
        pygame.draw.line(surface, grid_color, (0, y), (width, y), 1)
        
    os.makedirs('assets/images', exist_ok=True)
    pygame.image.save(surface, 'assets/images/bg.png')
    print("Generated placeholder background at assets/images/bg.png")

if __name__ == "__main__":
    generate_background()
