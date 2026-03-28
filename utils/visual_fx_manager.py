import pygame
import random
import math
import time
from collections import deque
from typing import List, Tuple, Optional
from utils.visual_utils import get_wire_curve_point

class Particle:
    """Represents a single visual particle in the system."""
    def __init__(self, x, y, dx, dy, color, lifetime, shape="circle", size=4, gravity=0.1, friction=1.0, alpha_fade=True, size_growth=0.0, max_alpha=255, text=None, text_color=(0,0,0)):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.max_life = lifetime
        self.life = lifetime
        self.shape = shape # "circle", "rect", "flare", "balloon"
        self.size = size
        self.gravity = gravity
        self.friction = friction
        self.alpha_fade = alpha_fade
        self.size_growth = size_growth
        self.max_alpha = max_alpha
        self.text = text
        self.text_color = text_color
        self.spawn_time = time.time()
        
        # Sub-effect state (e.g., for fireworks)
        self.has_exploded = False
        self.angle = random.uniform(0, math.pi * 2)
        self.spin_speed = random.uniform(-0.1, 0.1)

    def update(self, dt):
        self.life -= dt
        self.dx *= self.friction
        self.dy *= self.friction
        self.dy += self.gravity
        self.x += self.dx * dt * 60 # Scale to roughly 60fps
        self.y += self.dy * dt * 60
        self.size += self.size_growth * dt * 60
        self.angle += self.spin_speed

    def is_dead(self):
        return self.life <= 0

class VisualFXManager:
    """
    Enhanced Visual FX Manager.
    Supports legacy stigmergy traces AND a high-performance particle system.
    """
    def __init__(self, max_points=2000, max_particles=1000):
        self.max_points = max_points
        self.trace_buffer = deque(maxlen=max_points)
        self.trace_lifetime = 5.0
        
        self.max_particles = max_particles
        self.particles: List[Particle] = []
        
        # Initialize font for particle text
        try:
            self.font = pygame.font.SysFont(None, 20, bold=True)
        except:
            self.font = None

    def add_trace(self, x, y, color):
        self.trace_buffer.append((x, y, color, time.time()))

    # --- EFFECT EMITTERS (Milestone 41) ---

    def spawn_confetti(self, x, y):
        """Instant explosion of spinning rectangles."""
        for _ in range(30):
            dx = random.uniform(-4, 4)
            dy = random.uniform(-10, -5)
            color = random.choice([(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255)])
            self._add_particle(Particle(x, y, dx, dy, color, 2.0, shape="rect", size=random.randint(4, 8), gravity=0.2, friction=0.98))

    def spawn_firework(self, x, y):
        """Single rocket that explodes into a radial burst."""
        # The rocket itself is a particle that explodes on death (if we flag it) or we can implement two stages
        color = (255, 255, 200)
        p = Particle(x, y, random.uniform(-1, 1), random.uniform(-12, -8), color, 1.2, shape="rocket", size=4, gravity=0.15)
        self._add_particle(p)

    def _explode_firework(self, x, y):
        """Radial burst triggered by rocket apex."""
        color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        for i in range(40):
            angle = (math.pi * 2 / 40) * i
            speed = random.uniform(3, 6)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self._add_particle(Particle(x, y, dx, dy, color, 1.5, shape="circle", size=3, gravity=0.1, friction=0.96))

    def spawn_flare(self, x, y):
        """Intense fountain of sparks (additive)."""
        for _ in range(3):
            dx = random.uniform(-2, 2)
            dy = random.uniform(-8, -4)
            color = (255, random.randint(100, 200), 50)
            self._add_particle(Particle(x, y, dx, dy, color, 0.5, shape="flare", size=random.randint(2, 5), gravity=0.05))

    def spawn_glitter(self, x, y):
        """Slow-falling spray of tiny golden squares."""
        for _ in range(2):
            dx = random.uniform(-3, 3)
            dy = random.uniform(-2, 2)
            color = random.choice([(255, 215, 0), (255, 255, 255), (255, 250, 205)])
            self._add_particle(Particle(x, y, dx, dy, color, 3.0, shape="rect", size=3, gravity=0.05, friction=0.92))

    def spawn_balloon(self, x, y):
        """Swaying upward circles with strings."""
        color = random.choice([(255, 80, 80), (80, 255, 80), (80, 80, 255), (255, 200, 50)])
        self._add_particle(Particle(x, y, random.uniform(-0.5, 0.5), -2.0, color, 4.0, shape="balloon", size=15, gravity=-0.02, friction=0.99))

    def spawn_fart(self, x, y):
        """Puff of expanding green smoke that falls downwards."""
        for _ in range(15):
            dx = random.uniform(-2.5, 2.5)
            dy = random.uniform(1.0, 4.0) # Falling
            # Shades of green/yellow-green
            color = (random.randint(40, 80), random.randint(160, 220), random.randint(40, 60))
            self._add_particle(Particle(
                x, y, dx, dy, color, 
                lifetime=random.uniform(1.2, 2.0), 
                shape="circle", 
                size=random.randint(5, 12), 
                gravity=0.1,    # Gravity pulls it down
                friction=0.96,  # Air resistance
                size_growth=random.uniform(0.15, 0.4), 
                max_alpha=random.randint(80, 140), 
                text="fart",
                text_color=(160, 120, 80) # Light brown
            ))

    def _add_particle(self, particle: Particle):
        if len(self.particles) < self.max_particles:
            self.particles.append(particle)

    def update(self, dt):
        now = time.time()
        remaining = []
        for p in self.particles:
            p.update(dt)
            
            # Firework logic
            if p.shape == "rocket" and p.life <= 0.1 and not p.has_exploded:
                p.has_exploded = True
                self._explode_firework(p.x, p.y)
                
            if not p.is_dead():
                remaining.append(p)
        self.particles = remaining

    def draw(self, surface, camera=None):
        now = time.time()
        sw, sh = surface.get_size()
        viewport_rect = pygame.Rect(-100, -100, sw + 200, sh + 200)

        # 1. Draw Traces (Legacy)
        for x, y, color, timestamp in self.trace_buffer:
            age = now - timestamp
            if age > self.trace_lifetime: continue
            
            life_ratio = 1.0 - (age / self.trace_lifetime)
            radius = max(1, int(10 * life_ratio))
            alpha = int(120 * life_ratio)
            
            sx, sy = camera.world_to_screen(x, y) if camera else (x, y)
            if viewport_rect.collidepoint(sx, sy):
                trace_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(trace_surf, (*color, alpha), (radius, radius), radius)
                surface.blit(trace_surf, (int(sx - radius), int(sy - radius)))

        # 2. Draw Particles
        for p in self.particles:
            sx, sy = camera.world_to_screen(p.x, p.y) if camera else (p.x, p.y)
            if not viewport_rect.collidepoint(sx, sy): continue
            
            alpha = p.max_alpha
            if p.alpha_fade:
                alpha = int(p.max_alpha * (p.life / p.max_life))
            
            if p.shape == "circle" or p.shape == "rocket":
                pygame.draw.circle(surface, (*p.color, alpha), (int(sx), int(sy)), int(p.size))
            elif p.shape == "rect":
                # Spinning rectangle
                size = p.size
                rect_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
                pygame.draw.rect(rect_surf, (*p.color, alpha), (0, 0, size, size*1.5))
                rotated = pygame.transform.rotate(rect_surf, math.degrees(p.angle))
                surface.blit(rotated, rotated.get_rect(center=(int(sx), int(sy))))
            elif p.shape == "flare":
                # Glow effect with additive-like blending simulation
                flare_size = int(p.size * (1.5 if random.random() > 0.5 else 1.0))
                flare_surf = pygame.Surface((flare_size*2, flare_size*2), pygame.SRCALPHA)
                pygame.draw.circle(flare_surf, (*p.color, alpha), (flare_size, flare_size), flare_size)
                surface.blit(flare_surf, (int(sx - flare_size), int(sy - flare_size)), special_flags=pygame.BLEND_RGB_ADD)
            elif p.shape == "balloon":
                # Circle + string
                radius = int(p.size)
                # Sway
                sx += math.sin(time.time() * 3 + p.spawn_time) * 15
                pygame.draw.circle(surface, (*p.color, alpha), (int(sx), int(sy)), radius)
                pygame.draw.line(surface, (100, 100, 100, alpha), (int(sx), int(sy + radius)), (int(sx), int(sy + radius + 20)))
            elif p.shape == "fart":
                # Transparent green circle
                radius = int(p.size)
                fart_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(fart_surf, (*p.color, alpha), (radius, radius), radius)
                surface.blit(fart_surf, (int(sx - radius), int(sy - radius)))

            # 3. Draw Particle Text (Rotating)
            if p.text and self.font:
                text_surf = self.font.render(p.text, True, p.text_color)
                text_surf.set_alpha(alpha)
                # Rotate text slowly
                rotated_text = pygame.transform.rotate(text_surf, math.degrees(p.angle))
                text_rect = rotated_text.get_rect(center=(int(sx), int(sy)))
                surface.blit(rotated_text, text_rect)

    def draw_connections(self, surface, camera, entities, active_instances, active_signals, show_all=False):
        """
        Milestone 44: Wiring 2.0
        Draws visible splines between connected entities and racing signal 'pulses'.
        """
        for entity in entities:
            if not hasattr(entity, "connected_uuids") or not entity.connected_uuids:
                continue
            
            if not entity.body:
                continue

            # Start point (Source)
            start_world = entity.body.position
            start_screen = camera.world_to_screen(start_world.x, start_world.y)
            
            for target_uuid in entity.connected_uuids:
                target = active_instances.get(target_uuid)
                if not target or not target.body:
                    continue
                
                # End point (Target)
                end_world = target.body.position
                end_screen = camera.world_to_screen(end_world.x, end_world.y)
                
                # Milestone 44 Fix: All connector lines must wiggle (gentle wind sway)
                if show_all:
                    points = [get_wire_curve_point(start_screen, end_screen, i / 25.0) for i in range(26)]
                    int_points = [(int(p.x), int(p.y)) for p in points]
                    
                    # Draw Connection Spline (Dark teal/grey)
                    color = (60, 100, 110)
                    pygame.draw.aalines(surface, color, False, int_points)
                
                # 2. Draw Active Signal Pulses
                for sig in active_signals:
                    if sig.get("sender_uuid") == entity.uuid and sig.get("target_uuid") == target_uuid:
                        prog = sig.get("progress", 0.0)
                        # Phase 11 Fix: Signals also follow the wiggle curve
                        pt = get_wire_curve_point(start_screen, end_screen, prog)
                        px, py = pt.x, pt.y
                        
                        # Draw glowing pulse
                        pulse_color = (100, 255, 255) # Cyan glow
                        pygame.draw.circle(surface, pulse_color, (int(px), int(py)), 6)
                        # Optional outer glow
                        glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*pulse_color, 100), (10, 10), 10)
                        surface.blit(glow_surf, (int(px - 10), int(py - 10)), special_flags=pygame.BLEND_RGB_ADD)

    def clear(self):
        self.trace_buffer.clear()
        self.particles.clear()

# Global singleton
visual_fx_manager = VisualFXManager()
