import pygame
import os

def generate_texture():
    pygame.init()
    width, height = 400, 20
    surface = pygame.Surface((width, height))
    
    # Draw simple wood grain pattern
    surface.fill((139, 69, 19)) # SaddleBrown core
    
    grain_color = (101, 67, 33) # Dark wood
    for y in range(0, height, 4):
        pygame.draw.line(surface, grain_color, (0, y), (width, y), 2)
        
    os.makedirs('assets/images', exist_ok=True)
    pygame.image.save(surface, 'assets/images/wood_texture.png')
    print("Generated placeholder texture at assets/images/wood_texture.png")

if __name__ == "__main__":
    generate_texture()
