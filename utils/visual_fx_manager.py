import pygame
from collections import deque
import time

class VisualFXManager:
    """
    Milestone 34: Global Visual FX Budget.
    Manages stigmergy traces using a global ring buffer to cap memory and render overhead.
    """
    def __init__(self, max_points=5000):
        self.max_points = max_points
        # Each point: (x, y, color, timestamp)
        self.trace_buffer = deque(maxlen=max_points)
        self.points_per_second = 20
        self.trace_lifetime = 5.0

    def add_trace(self, x, y, color):
        """Adds a new trace point to the global buffer."""
        self.trace_buffer.append((x, y, color, time.time()))

    def update(self, dt):
        """
        Optional: Purge expired points. 
        Note: Since we use deque(maxlen), we only need to purge if we care about 
        points disappearing before the buffer is full.
        """
        now = time.time()
        # Ring buffer purges by index naturally, but we might want to skip drawing old ones.
        pass

    def draw(self, surface, camera=None):
        """Renders all active traces in the global buffer."""
        now = time.time()
        
        # Performance: Pre-calculate camera viewport bounds if camera exists
        if camera:
            # Simple bounding box for the viewport (plus padding)
            from constants import WINDOW_WIDTH, WINDOW_HEIGHT
            # we don't have direct access to constants here without import
            # but we can just use the provided surface size
            sw, sh = surface.get_size()
            viewport_rect = pygame.Rect(-50, -50, sw + 100, sh + 100)

        for x, y, color, timestamp in self.trace_buffer:
            age = now - timestamp
            if age > self.trace_lifetime:
                continue
            
            life_ratio = 1.0 - (age / self.trace_lifetime)
            radius = max(1, int(12 * 0.8 * life_ratio)) # Using 12 as a base radius
            alpha = int(120 * life_ratio)
            
            if camera:
                sx, sy = camera.world_to_screen(x, y)
                if not viewport_rect.collidepoint(sx, sy):
                    continue
            else:
                sx, sy = x, y
            
            # Simple optimization: Use a single trace surface if color/radius are same? 
            # Not really possible for stigmergy color variations.
            trace_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trace_surf, (*color, alpha), (radius, radius), radius)
            surface.blit(trace_surf, (int(sx - radius), int(sy - radius)))

    def clear(self):
        """Wipes all traces."""
        self.trace_buffer.clear()

# Global singleton
visual_fx_manager = VisualFXManager()
