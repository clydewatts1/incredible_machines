import pygame
import pymunk
import math
from entities.base import GamePart
import constants
from utils.asset_manager import asset_manager
from typing import Dict, List

class ConveyorBeltPart(GamePart):
    """A conveyor belt that moves objects along its surface using Pymunk's surface_velocity, with animated visuals."""

    def __init__(self, space, x, y, property_key):
        super().__init__(space, x, y, property_key)
        self.scroll_offset = 0.0

        # Conveyors absolutely must have high friction to grip objects effectively!
        if self.shape:
            self.shape.friction = float(self.get_property("friction", 2.0))
            self.shape.elasticity = 0.1  # Low elasticity so objects don't bounce off

        # Generate animated frames for the sprite
        width = float(self.get_property("width", 120.0))
        height = float(self.get_property("height", 20.0))
        self.frames = self._generate_belt_frames(width, height)

    def _generate_belt_frames(self, width: float, height: float) -> List[pygame.Surface]:
        """Generates a sequence of images to animate the conveyor belt."""
        frames = []
        num_frames = 8
        segment_length = 20  # Width of each alternating color piece
        
        color1 = (45, 45, 45)  # Dark gray belt
        color2 = (75, 75, 75)  # Lighter gray belt
        wheel_color = (90, 90, 90)
        wheel_hub = (160, 160, 160)
        
        for i in range(num_frames):
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            
            # The offset makes the belt look like it's shifting forward
            offset = (i / num_frames) * segment_length * 2
            
            # 1. Draw alternating belt pieces
            start_x = int(-segment_length * 2)
            end_x = int(width + segment_length)
            for x in range(start_x, end_x, segment_length):
                c = color1 if (x // segment_length) % 2 == 0 else color2
                pygame.draw.rect(surf, c, (x + offset, 0, segment_length, height))
                
            # 2. Draw small wheels inside the belt
            num_wheels = max(2, int(width // 20))
            spacing = width / num_wheels
            for w in range(num_wheels):
                wx = w * spacing + spacing / 2
                wy = height / 2
                radius = int(height / 2 - 2)
                pygame.draw.circle(surf, wheel_color, (int(wx), int(wy)), radius)
                pygame.draw.circle(surf, wheel_hub, (int(wx), int(wy)), int(radius / 2.5))
            
            # 3. Draw a border casing around the belt
            pygame.draw.rect(surf, (30, 30, 30), (0, 0, width, height), 2, border_radius=3)
            
            frames.append(surf)
            
        return frames

    def update_logic(self, dt: float, game_state: Dict, entities: List[GamePart], active_instances: Dict = None):
        super().update_logic(dt, game_state, entities, active_instances)

        if game_state.get("mode") == "PLAY":
            if self.shape and self.body:
                raw_speed = float(self.get_property("speed", 100.0))
                direction = str(self.get_property("direction", "right")).lower()
                
                # Reverse speed if direction is "left"
                speed = raw_speed if direction == "right" else -raw_speed
                
                angle = self.body.angle

                # Apply surface velocity in the direction of the conveyor's physical rotation
                self.shape.surface_velocity = (speed * math.cos(angle), speed * math.sin(angle))
                
                # Advance the animation frame based on the speed
                self.scroll_offset += speed * dt

                # === GAMEPLAY ASSIST ===
                # Forcefully push dynamic objects touching the belt to overcome free-rolling ball physics
                width = float(self.get_property("width", 120.0))
                height = float(self.get_property("height", 20.0))
                max_dist = max(width, height) + 50.0

                for entity in entities:
                    # Ignore self, static geometry, and tools
                    if entity.uuid == self.uuid or not getattr(entity, 'body', None):
                        continue
                    if entity.body.body_type != pymunk.Body.DYNAMIC:
                        continue
                    
                    # Quick bounding box cull for performance
                    dx = entity.body.position.x - self.body.position.x
                    dy = entity.body.position.y - self.body.position.y
                    if math.hypot(dx, dy) > max_dist:
                        continue

                    # Precise Pymunk contact check
                    is_touching = False
                    target_shapes = getattr(entity, 'shapes', [getattr(entity, 'shape', None)])
                    for t_shape in target_shapes:
                        if not t_shape: 
                            continue
                        try:
                            contact = self.shape.shapes_collide(t_shape)
                            if contact and len(contact.points) > 0:
                                is_touching = True
                                break
                        except Exception:
                            pass
                    
                    if is_touching:
                        # 1. Apply a strong artificial drag force along the belt vector
                        push_force = speed * entity.body.mass * 12.0
                        entity.body.apply_force_at_world_point(
                            (push_force * math.cos(angle), push_force * math.sin(angle)),
                            entity.body.position
                        )
                        # 2. Dampen the angular velocity significantly so the ball grips the belt instead of spinning
                        entity.body.angular_velocity *= 0.85

    def draw(self, surface, camera=None):
        if not self.body:
            return

        pos = self.body.position
        if camera:
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
        else:
            screen_x, screen_y = pos.x, pos.y

        # Determine which animation frame to use based on scroll_offset
        segment_length = 20
        cycle_length = segment_length * 2
        
        # Calculate progress through the cycle
        progress = (self.scroll_offset % cycle_length) / cycle_length
        frame_idx = int(progress * len(self.frames)) % len(self.frames)
        
        current_frame = self.frames[frame_idx]
        
        # Rotate the frame to match the physics body's angle
        rotated_frame = pygame.transform.rotate(current_frame, math.degrees(-self.body.angle))
        rect = rotated_frame.get_rect(center=(int(screen_x), int(screen_y)))
        
        # Draw the generated sprite directly to the screen (replacing the old gray box)
        surface.blit(rotated_frame, rect)