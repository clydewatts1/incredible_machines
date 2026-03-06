import pygame
import pymunk
import sys

import constants
from entities.ball import Ball
from entities.ramp import Ramp

def create_boundaries(space):
    """Create screen boundaries so things don't fall off screen."""
    static_body = space.static_body
    w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
    thickness = 50.0
    
    # Bottom, Left, Right (Top is optional, but we'll enclose the whole screen)
    segments = [
        pymunk.Segment(static_body, (0, h), (w, h), thickness), # Bottom
        pymunk.Segment(static_body, (0, 0), (0, h), thickness), # Left
        pymunk.Segment(static_body, (w, 0), (w, h), thickness), # Right
        pymunk.Segment(static_body, (0, 0), (w, 0), thickness)  # Top
    ]
    
    for s in segments:
        s.elasticity = 0.8
        s.friction = 0.5
        space.add(s)

def main():
    pygame.init()
    screen = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    pygame.display.set_caption("The Incredible Machine Clone - Milestone 1")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 36)

    # Initialize Pymunk Physics
    space = pymunk.Space()
    space.gravity = constants.GRAVITY

    # Build world
    create_boundaries(space)

    entities = []
    
    # State Machine
    mode = "EDIT" # "EDIT" or "PLAY"
    
    # Interaction State
    grabbed_body = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mode = "PLAY" if mode == "EDIT" else "EDIT"
                    # If switching out of EDIT mode, release any grabbed objects
                    if mode == "PLAY":
                        grabbed_body = None
                        
                # Spawning logic (only in EDIT mode)
                elif mode == "EDIT":
                    if event.key == pygame.K_b:
                        # Spawn Ball at mouse
                        m_x, m_y = pygame.mouse.get_pos()
                        entities.append(Ball(space, m_x, m_y))
                    elif event.key == pygame.K_r:
                        # Spawn Ramp at mouse
                        m_x, m_y = pygame.mouse.get_pos()
                        entities.append(Ramp(space, m_x, m_y))
            
            # Drag and drop logic (only in EDIT mode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mode == "EDIT":
                    # Query physics space for closest object under mouse
                    info = space.point_query_nearest(event.pos, 0, pymunk.ShapeFilter())
                    if info and info.shape and info.shape.body != space.static_body:
                        # Grab the body
                        grabbed_body = info.shape.body
            
            elif event.type == pygame.MOUSEMOTION:
                if mode == "EDIT" and grabbed_body:
                    grabbed_body.position = event.pos
                    # Zero out velocity from user dragging so it doesn't build up extreme forces
                    grabbed_body.velocity = (0, 0)
                    grabbed_body.angular_velocity = 0
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                grabbed_body = None

        # Game State Engine
        if mode == "PLAY":
            # Physics dictates reality ONLY here
            space.step(constants.PHYSICS_STEP)
            
        # Draw Background
        screen.fill(constants.COLOR_BACKGROUND)

        # Draw all entities
        for entity in entities:
            entity.update_visual(screen)

        # Draw UI Overlay
        ui_text = f"Mode: {mode} (SPACE to swap. B=Ball, R=Ramp)"
        text_surface = font.render(ui_text, True, constants.COLOR_TEXT)
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
