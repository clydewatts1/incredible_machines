import pygame

class ControllerManager:
    """
    Milestone 42: Unified Gamepad Manager.
    Maps joystick inputs to system mouse movement, camera panning, and avatar control.
    """
    def __init__(self):
        self.joystick = None
        
        # Default Mappings (will be overridden by env_manager)
        self.deadzone = 0.15
        self.mouse_speed = 15.0
        self.scroll_speed = 10.0
        
        self.AXIS_MOUSE_X = 0
        self.AXIS_MOUSE_Y = 1
        self.AXIS_AVATAR_X = 2
        self.AXIS_AVATAR_Y = 3
        self.AXIS_ZOOM_OUT = 4 # L2 / LT
        self.AXIS_ZOOM_IN = 5  # R2 / RT
        
        self.BTN_LEFT_CLICK = 0
        self.BTN_RIGHT_CLICK = 1
        self.BTN_NEXT_PALETTE = 5
        self.BTN_PREV_PALETTE = 4
        
        self.init_joystick()
        self.reload_config()

    def reload_config(self):
        """Load mappings from EnvironmentManager."""
        from utils.environment_manager import env_manager
        cfg = env_manager.get_config("controller", {})
        if not cfg: return
        
        self.deadzone = cfg.get("deadzone", self.deadzone)
        self.mouse_speed = cfg.get("mouse_speed", self.mouse_speed)
        self.scroll_speed = cfg.get("scroll_speed", self.scroll_speed)
        
        self.AXIS_MOUSE_X = cfg.get("axis_mouse_x", self.AXIS_MOUSE_X)
        self.AXIS_MOUSE_Y = cfg.get("axis_mouse_y", self.AXIS_MOUSE_Y)
        self.AXIS_AVATAR_X = cfg.get("axis_avatar_x", self.AXIS_AVATAR_X)
        self.AXIS_AVATAR_Y = cfg.get("axis_avatar_y", self.AXIS_AVATAR_Y)
        self.AXIS_ZOOM_OUT = cfg.get("axis_zoom_out", self.AXIS_ZOOM_OUT)
        self.AXIS_ZOOM_IN = cfg.get("axis_zoom_in", self.AXIS_ZOOM_IN)
        
        self.BTN_LEFT_CLICK = cfg.get("btn_left_click", self.BTN_LEFT_CLICK)
        self.BTN_RIGHT_CLICK = cfg.get("btn_right_click", self.BTN_RIGHT_CLICK)
        self.BTN_NEXT_PALETTE = cfg.get("btn_next_palette", self.BTN_NEXT_PALETTE)
        self.BTN_PREV_PALETTE = cfg.get("btn_prev_palette", self.BTN_PREV_PALETTE)

    def init_joystick(self):
        try:
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print(f"Controller: Initialized '{self.joystick.get_name()}'")
            else:
                print("Controller: No joystick detected at startup.")
        except pygame.error as e:
            print(f"Controller: Joystick initialization failed internally: {e}")
            self.joystick = None

    def update(self, dt):
        """Handle continuous polling (Virtual Mouse & Zoom)."""
        if not self.joystick:
            return

        # 1. Virtual Mouse (Stick -> Cursor Pos)
        mx = self.joystick.get_axis(self.AXIS_MOUSE_X)
        my = self.joystick.get_axis(self.AXIS_MOUSE_Y)
        
        if abs(mx) > self.deadzone or abs(my) > self.deadzone:
            m_pos = list(pygame.mouse.get_pos())
            m_pos[0] += mx * self.mouse_speed
            m_pos[1] += my * self.mouse_speed
            pygame.mouse.set_pos(m_pos)

        # 2. Camera Zoom (Triggers)
        # Triggers in pygame usually range from -1 (unpressed) to 1 (pressed)
        # but some controllers use 0 to 1. We check if > -0.8 to be safe.
        z_out = self.joystick.get_axis(self.AXIS_ZOOM_OUT)
        z_in = self.joystick.get_axis(self.AXIS_ZOOM_IN)
        
        if z_out > -0.5: # Pressed
            self._post_mouse_event(pygame.MOUSEBUTTONDOWN, 5) # Scroll Down / Zoom Out
        if z_in > -0.5: # Pressed
            self._post_mouse_event(pygame.MOUSEBUTTONDOWN, 4) # Scroll Up / Zoom In

    def process_event(self, event, callbacks=None):
        """Translates joystick events into simulated mouse or UI actions."""
        if not self.joystick:
            return False

        # 1. Button -> Mouse Clicks
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == self.BTN_LEFT_CLICK: # Changed from BUTTON_A
                # Simulate Left Click
                m_pos = pygame.mouse.get_pos()
                click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
                    'pos': m_pos,
                    'button': 1  # Left Click
                })
                pygame.event.post(click_event)
                return True
        
        if event.type == pygame.JOYBUTTONUP:
            if event.button == self.BTN_LEFT_CLICK: # Changed from BUTTON_A
                m_pos = pygame.mouse.get_pos()
                up_event = pygame.event.Event(pygame.MOUSEBUTTONUP, {
                    'pos': m_pos,
                    'button': 1
                })
                pygame.event.post(up_event)
                return True

        # 2. D-Pad -> Transport Controls
        if event.type == pygame.JOYHATMOTION and callbacks:
            # event.value is (x, y) where x is horizontal, y is vertical
            hx, hy = event.value
            if hx == 1: # Right -> Play
                if "play" in callbacks: callbacks["play"]()
            elif hx == -1: # Left -> Slow Mo
                # Assuming index 0 of transport or a specific callback
                pass 
            elif hy == 1: # Up -> Fast Forward
                pass
            elif hy == -1: # Down -> Stop/Edit
                if "edit" in callbacks: callbacks["edit"]()
                
        return False

    def get_movement_vector(self):
        """Returns standard (x, y) normalized for the Player Avatar."""
        if not self.joystick:
            return 0.0, 0.0
            
        ax = self.joystick.get_axis(self.AXIS_AVATAR_X)
        ay = self.joystick.get_axis(self.AXIS_AVATAR_Y)
        
        if abs(ax) < self.deadzone: ax = 0.0
        if abs(ay) < self.deadzone: ay = 0.0
        
        return ax, ay

    def rumble(self, low=0.5, high=0.5, duration=200):
        """Milestone 42: Haptic Feedback."""
        if self.joystick and hasattr(self.joystick, 'rumble'):
            try:
                self.joystick.rumble(low, high, duration)
            except:
                pass

controller_manager = ControllerManager()
