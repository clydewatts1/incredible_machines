import pygame
import pymunk
from entities.base import GamePart
from utils.controller import controller_manager

class AvatarPart(GamePart):
    """
    Milestone 42: Player Avatar.
    A physics-driven entity controlled by the gamepad's Left Stick.
    """
    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        
        # Physics setup
        self.move_speed = 300.0
        
        if self.body:
            self.body.body_type = pymunk.Body.DYNAMIC
            # Give it some weight but also high damping so it doesn't drift forever
            self.body.mass = 5.0
            self.body.moment = pymunk.moment_for_circle(5.0, 0, 20)
            
        if self.shape:
            self.shape.friction = 1.0  # High friction to stop quickly
            self.shape.elasticity = 0.2
            import constants
            self.shape.collision_type = constants.COLLISION_TYPE_AVATAR
        # Visuals
        self.color = (50, 200, 50) # Player Green
        self.width = float(self.get_property("width", 40))
        self.height = float(self.get_property("height", 40))

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        if game_state.get("mode") != "PLAY":
            # In EDIT mode, the avatar stays put or is handled by EditorUI if moved
            return

        # Read Right Stick from global controller manager (M42 Redux)
        ax, ay = controller_manager.get_avatar_movement()
        
        if self.body:
            # milestone 42: Direct velocity modification for "snappy" control
            # We preserve some momentum but mostly follow the stick
            target_vx = ax * self.move_speed
            target_vy = ay * self.move_speed
            
            # Simple lerp-like approach to avoid infinite acceleration
            self.body.velocity = (target_vx, target_vy)
            self.body.angular_velocity *= 0.9 # Keep it upright

    def draw(self, surface, camera=None):
        if not self.body: return
        
        pos = self.body.position
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)
        
        radius = int(self.width / 2)
        
        # Draw body
        pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), radius)
        # Draw "visor" to show orientation or just a border
        pygame.draw.circle(surface, (255, 255, 255), (int(screen_x), int(screen_y)), radius, 2)
        
        # Subtle glow if moving
        if self.body.velocity.length > 10:
            glow_radius = radius + 4
            pygame.draw.circle(surface, (50, 255, 50, 100), (int(screen_x), int(screen_y)), glow_radius, 1)

    def cleanup(self):
        super().cleanup()
