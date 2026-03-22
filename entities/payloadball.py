import pygame
import pymunk
import math

from entities.base import GamePart
from utils.asset_manager import asset_manager
from utils.visual_fx_manager import visual_fx_manager


class PayloadBallPart(GamePart):
    """A dynamic ball that leaves glowing stigmergic traces and changes color based on payload score."""

    def __init__(self, space: pymunk.Space, x: float, y: float, property_key: str):
        super().__init__(space, x, y, property_key)
        
        # --- Visual Stigmergy Settings ---
        self.trace_timer = 0.0
        self.idle_timer = 0.0 # Milestone 34: Stuck ball protection
        
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
        
        # Global Visual FX Budget (Phase 14)
        if game_state.get("mode") == "PLAY" and game_state.get("show_traces", False):
            if not getattr(self, "is_hidden", False) and self.body:
                self.trace_timer += dt
                if self.trace_timer >= 0.05: # Interval: 20 points per sec
                    score = self.payload.get("score", 100) if hasattr(self, "payload") else 100
                    color = self.get_color_for_score(score)
                    visual_fx_manager.add_trace(self.body.position.x, self.body.position.y, color)
                    self.trace_timer = 0.0

        # Rule 4: Stale Payload Timeout (Milestone 34)
        if game_state.get("mode") == "PLAY" and self.body:
            vx, vy = self.body.velocity
            if math.hypot(vx, vy) < 5.0:  # Near stationary
                self.idle_timer += dt
                if self.idle_timer > 30.0:
                    self.to_delete = True
            else:
                self.idle_timer = 0.0

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

        # --- Global Trace Trail (Phase 14: Handled by visual_fx_manager) ---

        # 1. Main Base Sprite
        pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), int(radius))
        
        # 2. Glossy Highlight
        pygame.draw.circle(surface, (255, 255, 255), (int(screen_x - radius*0.3), int(screen_y - radius*0.3)), int(radius*0.3))