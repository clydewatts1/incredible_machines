import pygame

class ControllerManager:
    """
    Milestone 42: Unified Gamepad Manager.
    Maps joystick inputs to system mouse movement and transport controls.
    """
    def __init__(self):
        self.joystick = None
        self.deadzone = 0.15
        self.mouse_speed = 10.0
        
        # Mapping for generic Xbox/PS controllers
        self.BUTTON_A = 0    # Cross / A
        self.BUTTON_B = 1    # Circle / B
        self.BUTTON_X = 2    # Square / X
        self.BUTTON_Y = 3    # Triangle / Y
        
        self.AXIS_LX = 0
        self.AXIS_LY = 1
        self.AXIS_RX = 2
        self.AXIS_RY = 3
        
        self.init_joystick()

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
        """Handle continuous polling (e.g. stick-to-mouse movement)."""
        if not self.joystick:
            return

        # 1. Virtual Mouse (Right Stick)
        rx = self.joystick.get_axis(self.AXIS_RX)
        ry = self.joystick.get_axis(self.AXIS_RY)
        
        if abs(rx) > self.deadzone or abs(ry) > self.deadzone:
            m_pos = list(pygame.mouse.get_pos())
            m_pos[0] += rx * self.mouse_speed
            m_pos[1] += ry * self.mouse_speed
            pygame.mouse.set_pos(m_pos)

    def process_event(self, event, callbacks=None):
        """
        Translates joystick events into simulated mouse or transport events.
        'callbacks' is the dictionary from main.py (play, stop, pause, etc.)
        """
        if not self.joystick:
            return False

        # 1. Button -> Mouse Clicks
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == self.BUTTON_A:
                # Simulate Left Click
                m_pos = pygame.mouse.get_pos()
                click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {
                    'pos': m_pos,
                    'button': 1  # Left Click
                })
                pygame.event.post(click_event)
                return True
        
        if event.type == pygame.JOYBUTTONUP:
            if event.button == self.BUTTON_A:
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
            
        lx = self.joystick.get_axis(self.AXIS_LX)
        ly = self.joystick.get_axis(self.AXIS_LY)
        
        if abs(lx) < self.deadzone: lx = 0.0
        if abs(ly) < self.deadzone: ly = 0.0
        
        return lx, ly

controller_manager = ControllerManager()
