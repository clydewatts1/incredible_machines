import pygame
import pymunk
import sys

import constants
from entities.base import GamePart
from utils.sound_manager import sound_manager
from utils.environment_manager import env_manager
from utils.config_loader import load_all_variants

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
    sound_manager.initialize()
    env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)
    
    # Load all variants for dynamic UI and input hooks
    all_variants = load_all_variants()
    key_map = {}
    ui_texts = []
    for var_key, var_data in all_variants.items():
        if "key_bind" in var_data:
            key_map[var_data["key_bind"].lower()] = var_key
            ui_texts.append(f"{var_data['key_bind']}:{var_data.get('label', var_key)}")
    ui_controls_str = ", ".join(ui_texts)
    
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
    
    def post_solve(arbiter, space, data):
        # Calculate collision magnitude
        if arbiter.total_impulse.length > 200:
            shape_a, shape_b = arbiter.shapes
            for entity in entities:
                if entity.shape in (shape_a, shape_b):
                    entity.play_event_sound("collision_sound")
        return True
        
    space.on_collision(collision_type_a=None, collision_type_b=None, post_solve=post_solve)
    
    # State Machine
    mode = "EDIT" # "EDIT" or "PLAY"
    
    # Interaction State
    grabbed_body = None

    running = True
    while running:
        # 1. Reset hover state for all entities
        for entity in entities:
            entity.is_hovered = False
            
        # 2. Detect hover in EDIT mode if not currently dragging something
        if mode == "EDIT" and not grabbed_body:
            m_pos = pygame.mouse.get_pos()
            info = space.point_query_nearest(m_pos, 5.0, pymunk.ShapeFilter())
            if info and info.shape and info.shape.body != space.static_body:
                for entity in entities:
                    if entity.shape == info.shape:
                        entity.is_hovered = True
                        break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    mode = "PLAY" if mode == "EDIT" else "EDIT"
                    # If switching out of EDIT mode, release any grabbed objects
                    if mode == "PLAY":
                        grabbed_body = None
                        # Reindex static shapes so Pymunk knows their new angles/positions
                        space.reindex_static()
                        
                # Spawning logic (only in EDIT mode)
                elif mode == "EDIT":
                    # Dynamic Spawns from key bindings
                    if event.unicode in key_map:
                        m_x, m_y = pygame.mouse.get_pos()
                        variant_key = key_map[event.unicode]
                        new_part = GamePart(space, m_x, m_y, variant_key)
                        entities.append(new_part)
                        new_part.play_event_sound("spawn_sound")
            
            # Drag and drop logic (only in EDIT mode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mode == "EDIT":
                    # Query physics space for closest object under mouse
                    info = space.point_query_nearest(event.pos, 5.0, pymunk.ShapeFilter())
                    if info and info.shape and info.shape.body != space.static_body:
                        # Grab the body
                        grabbed_body = info.shape.body
            
            elif event.type == pygame.MOUSEMOTION:
                if mode == "EDIT" and grabbed_body:
                    grabbed_body.position = event.pos
                    # Zero out velocity from user dragging so it doesn't build up extreme forces
                    if grabbed_body.body_type == pymunk.Body.DYNAMIC:
                        grabbed_body.velocity = (0, 0)
                        grabbed_body.angular_velocity = 0
                    space.reindex_shapes_for_body(grabbed_body)
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                grabbed_body = None
                
            elif event.type == pygame.MOUSEWHEEL:
                if mode == "EDIT":
                    target = grabbed_body
                    if not target:
                        info = space.point_query_nearest(pygame.mouse.get_pos(), 5.0, pymunk.ShapeFilter())
                        if info and info.shape and info.shape.body != space.static_body:
                            target = info.shape.body
                    if target:
                        target.angle += event.y * 0.1
                        space.reindex_shapes_for_body(target)

        # Continuous rotation checks while in edit mode
        if mode == "EDIT" and grabbed_body:
            keys = pygame.key.get_pressed()
            rotated = False
            if keys[pygame.K_q]:
                # Rotate Counter-Clockwise
                grabbed_body.angle -= 0.05
                rotated = True
            if keys[pygame.K_e]:
                # Rotate Clockwise
                grabbed_body.angle += 0.05
                rotated = True
            if rotated:
                space.reindex_shapes_for_body(grabbed_body)

        # Game State Engine
        if mode == "PLAY":
            # Physics dictates reality ONLY here
            space.step(constants.PHYSICS_STEP)
            
        # Draw Background via EnvironmentManager
        env_manager.draw_background(screen)

        # Draw all entities
        for entity in entities:
            entity.update_visual(screen)

        # Mode Indicator Border
        border_color = env_manager.edit_mode_color if mode == "EDIT" else env_manager.play_mode_color
        pygame.draw.rect(screen, border_color, screen.get_rect(), 5)

        # Draw UI Overlay
        ui_text = f"Mode: {mode} (SPACE swaps. Spawns: {ui_controls_str})"
        text_surface = font.render(ui_text, True, constants.COLOR_TEXT)
        screen.blit(text_surface, (15, 15))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
