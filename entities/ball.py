import pygame
import pymunk
import math
from entities.base import GamePart
import constants

class Ball(GamePart):
    def __init__(self, space, x, y):
        super().__init__(space, "bouncy_ball")
        
        # --- Stigmergic Trace Properties ---
        self.trace_history = [] # Format: [(x, y, timestamp_added), ...]
        self.trace_timer = 0.0
        self.show_traces = False
        
        # Configuration Constraints
        self.TRACE_LIFETIME = 5.0    # Fades completely after 5 seconds
        self.MAX_TRACE_POINTS = 100  # Accumulative to a maximum
        self.TRACE_INTERVAL = 0.05   # Drop interval
        
        mass = self.properties.get("mass", 1.0)
        self.radius = 15.0
        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0, 0))
        self.body = pymunk.Body(mass, inertia, body_type=pymunk.Body.DYNAMIC)
        self.body.position = (x, y)
        self.shape = pymunk.Circle(self.body, self.radius, (0, 0))
        self.shape.elasticity = self.properties.get("elasticity", 0.8)
        self.shape.friction = self.properties.get("friction", 0.5)
        self.shape.collision_type = 1
        
        # Add to space
        self.space.add(self.body, self.shape)

    def update_logic(self, dt, game_state, entities, active_instances=None):
        super().update_logic(dt, game_state, entities, active_instances)
        
        # Sync toggle state from UI
        self.show_traces = game_state.get("show_traces", False)
        current_time = pygame.time.get_ticks() / 1000.0
        
        if game_state.get("mode") == "PLAY" and self.show_traces:
            if not getattr(self, "is_hidden", False) and self.body:
                self.trace_timer += dt
                # Drop a coordinate "breadcrumb" on interval
                if self.trace_timer >= self.TRACE_INTERVAL:  
                    self.trace_history.append((self.body.position.x, self.body.position.y, current_time))
                    self.trace_timer = 0.0
                    
            # Rule 1: Purge points older than 5 seconds
            self.trace_history = [p for p in self.trace_history if current_time - p[2] <= self.TRACE_LIFETIME]
            
            # Rule 2: Cap at maximum accumulative points
            if len(self.trace_history) > self.MAX_TRACE_POINTS:
                self.trace_history = self.trace_history[-self.MAX_TRACE_POINTS:]
                
        elif not self.show_traces and self.trace_history:
            self.trace_history.clear() # Wipe memory instantly when toggled off

    def draw(self, surface, camera=None):
        """
        Draws the ball using Pymunk physics position.
        Called strictly by GamePart.update_visual() to ensure Fail Loudly assertions run.
        M25 Phase 2: Applies camera offset if provided.
        """
        if not self.body:
            return

        # Get world-space position
        world_x, world_y = self.body.position.x, self.body.position.y
        
        # Apply camera transformation if provided
        if camera:
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        else:
            screen_x, screen_y = world_x, world_y
        
        x, y = int(screen_x), int(screen_y)
        color = constants.COLOR_BALL
        current_time = pygame.time.get_ticks() / 1000.0

        # --- Rule 3: Draw Glowing Trace Trail (Underneath the ball) ---
        if self.show_traces and self.trace_history:
            for p in self.trace_history:
                age = current_time - p[2]
                
                # Clamp age for safety bounds
                if age < 0: age = 0
                if age > self.TRACE_LIFETIME: age = self.TRACE_LIFETIME
                
                # Life ratio goes from 1.0 (just spawned) down to 0.0 (5 seconds old)
                life_ratio = 1.0 - (age / self.TRACE_LIFETIME)
                
                # Shrink radius as it fades out
                trail_radius = max(1, int(self.radius * 0.8 * life_ratio))
                
                # Cap max opacity at ~120/255 (less than 50%) so it doesn't overdisplay
                alpha = int(120 * life_ratio) 
                
                sx, sy = camera.world_to_screen(p[0], p[1]) if camera else (p[0], p[1])
                
                trace_surf = pygame.Surface((trail_radius * 2, trail_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(trace_surf, (*color[:3], alpha), (trail_radius, trail_radius), trail_radius)
                surface.blit(trace_surf, (int(sx - trail_radius), int(sy - trail_radius)))

        # 1. Main Base Sprite
        pygame.draw.circle(surface, color, (x, y), int(self.radius))
        
        # 2. Glossy Highlight (Brings visual in line with PayloadBall)
        pygame.draw.circle(surface, (255, 255, 255), (int(x - self.radius*0.3), int(y - self.radius*0.3)), int(self.radius*0.3))
        
        # Draw a line from center to edge to visually confirm it is rolling
        end_x = x + math.cos(self.body.angle) * self.radius
        end_y = y + math.sin(self.body.angle) * self.radius
        pygame.draw.line(surface, (0, 0, 0), (x, y), (int(end_x), int(end_y)), 2)