import pygame
import pymunk

from entities.base import GamePart
from utils.asset_manager import asset_manager


class PayloadBallPart(GamePart):
    """A dynamic ball that leaves glowing stigmergic traces and changes color based on payload score."""

    def __init__(self, space: pymunk.Space, x: float, y: float, property_key: str):
        super().__init__(space, x, y, property_key)
        
        # --- Stigmergic Trace Properties ---
        self.trace_history = [] # Format: [(x, y, timestamp_added), ...]
        self.trace_timer = 0.0
        self.show_traces = False
        
        # Configuration Constraints
        self.TRACE_LIFETIME = 5.0    # Fades completely after 5 seconds
        self.MAX_TRACE_POINTS = 100  # Accumulative to a maximum (prevents memory bloat)
        self.TRACE_INTERVAL = 0.05   # How often to drop a point (20 points per second)
        
        # Milestone 32 Fix: Duplicate body/shape creation removed. 
        # GamePart.__init__ already instantiates and registers the main physics body and shape 
        # based on the "Circle" template in entities.yaml.

    def get_color_for_score(self, score: int):
        """Map score to a smooth color gradient."""
        if score >= 100:
            t = max(0.0, min(1.0, (score - 100) / 100.0))
            r = int(0 + t * (0 - 0))
            g = int(255 + t * (255 - 255))
            b = int(255 + t * (0 - 255))
            return (r, g, b)
        else:
            t = max(0.0, min(1.0, (score + 50) / 50.0))
            r = 255
            g = int(255 + t * (0 - 255))
            return (r, g, 0)

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
        if not self.body:
            return

        pos = self.body.position
        screen_x, screen_y = camera.world_to_screen(pos.x, pos.y) if camera else (pos.x, pos.y)

        score = 100
        if hasattr(self, 'payload') and isinstance(self.payload, dict):
            score = self.payload.get('score', 100)
        else:
            score = self.get_property('score', 100)

        color = self.get_color_for_score(score)
        radius = float(self.get_property('radius', 15.0))
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
                trail_radius = max(1, int(radius * 0.8 * life_ratio))
                
                # Cap max opacity at ~120/255 (less than 50%) so it doesn't overdisplay
                alpha = int(120 * life_ratio) 
                
                sx, sy = camera.world_to_screen(p[0], p[1]) if camera else (p[0], p[1])
                
                trace_surf = pygame.Surface((trail_radius * 2, trail_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(trace_surf, (*color, alpha), (trail_radius, trail_radius), trail_radius)
                surface.blit(trace_surf, (int(sx - trail_radius), int(sy - trail_radius)))

        # 1. Main Base Sprite
        pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), int(radius))
        
        # 2. Glossy Highlight
        pygame.draw.circle(surface, (255, 255, 255), (int(screen_x - radius*0.3), int(screen_y - radius*0.3)), int(radius*0.3))