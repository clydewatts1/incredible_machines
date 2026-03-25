import uuid

import pygame

import constants


class FloatingTextLabel:
    """Lightweight floating label used for diagnostics."""

    def __init__(self, x: float, y: float, text: str, color=(255, 60, 60), lifetime=2.0):
        self.uuid = str(uuid.uuid4())
        self.x = float(x)
        self.y = float(y)
        self.text = str(text)
        self.color = color
        self.lifetime = float(lifetime)
        self.elapsed = 0.0
        self.to_delete = False
        self.is_hovered = False
        
        # Milestone 38: MockBody for system compatibility (prevents crashes in test runner/renderer)
        class MockPos:
            def __init__(self, owner): self.owner = owner
            @property
            def x(self): return self.owner.x
            @x.setter
            def x(self, val): self.owner.x = float(val)
            @property
            def y(self): return self.owner.y
            @y.setter
            def y(self, val): self.owner.y = float(val)
        
        class MockBodyObj:
            def __init__(self, owner):
                self.position = MockPos(owner)
                self.angle = 0.0
                self.velocity = (0, 0)
                self.angular_velocity = 0.0
                self.constraints = []
                self.body_type = 1 # Static
                
        self.body = MockBodyObj(self)
        self.shape = None
        self.shapes = []
        self.connected_uuids = []

    def update_logic(self, dt: float, game_state, entities, active_instances=None):
        self.elapsed += dt
        self.y -= constants.FLOATING_LABEL_RISE_SPEED * dt
        if self.elapsed >= self.lifetime:
            self.to_delete = True

    def update_visual(self, surface, camera=None, **kwargs):
        alpha_ratio = max(0.0, 1.0 - (self.elapsed / max(self.lifetime, 0.001)))
        alpha = int(255 * alpha_ratio)
        font = pygame.font.SysFont(None, 18)
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)

        if camera:
            screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        else:
            screen_x, screen_y = self.x, self.y

        rect = text_surf.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(text_surf, rect)