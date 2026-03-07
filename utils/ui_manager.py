import pygame

class UIElement:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.is_visible = True

    def draw(self, surface):
        pass

    def handle_event(self, event):
        return False


class UIPanel(UIElement):
    def __init__(self, rect, color=(40, 40, 40)):
        super().__init__(rect)
        self.color = color

    def draw(self, surface):
        if self.is_visible:
            pygame.draw.rect(surface, self.color, self.rect)


class UILabel(UIElement):
    def __init__(self, rect, text, font, color=(255, 255, 255)):
        super().__init__(rect)
        self.text = text
        self.font = font
        self.color = color
        self._rendered_text = self.font.render(self.text, True, self.color)

    def set_text(self, text):
        self.text = text
        self._rendered_text = self.font.render(self.text, True, self.color)

    def draw(self, surface):
        if self.is_visible:
            # Center text in rect
            text_rect = self._rendered_text.get_rect(center=self.rect.center)
            surface.blit(self._rendered_text, text_rect)


class UIButton(UIElement):
    def __init__(self, rect, callback=None, text=None, font=None, icon_surface=None, 
                 bg_color=(70, 70, 70), hover_color=(100, 100, 100), text_color=(255, 255, 255),
                 click_sound=None):
        super().__init__(rect)
        self.callback = callback
        self.text = text
        self.font = font
        self.icon_surface = icon_surface
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.click_sound = click_sound
        
        self.is_hovered = False

    def draw(self, surface):
        if not self.is_visible:
            return

        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 1) # Border

        if self.icon_surface and self.text and self.font:
            # Both icon and text: Stack them vertically
            text_surf = self.font.render(self.text, True, self.text_color)
            
            # Calculate total height to center the group vertically
            total_height = self.icon_surface.get_height() + text_surf.get_height()
            
            # Start Y position for the block
            start_y = self.rect.centery - (total_height // 2)
            
            icon_rect = self.icon_surface.get_rect(centerx=self.rect.centerx, top=start_y)
            text_rect = text_surf.get_rect(centerx=self.rect.centerx, top=icon_rect.bottom + 2)
            
            surface.blit(self.icon_surface, icon_rect)
            surface.blit(text_surf, text_rect)
            
        elif self.icon_surface:
            # Just icon: Center it
            icon_rect = self.icon_surface.get_rect(center=self.rect.center)
            surface.blit(self.icon_surface, icon_rect)
            
        elif self.text and self.font:
            # Just text: Center it
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if not self.is_visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            # We don't necessarily consume mouse motion, but we update state
            return False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.click_sound:
                    from utils.sound_manager import sound_manager
                    sound_manager.play_sound(self.click_sound)
                if self.callback:
                    self.callback()
                return True # Consumed
                
        return False


class UIManager:
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)
        return element

    def update(self):
        # Could be used for animations or continuous checks later
        pass

    def draw(self, surface):
        for element in self.elements:
            element.draw(surface)

    def process_event(self, event):
        """
        Passes event downward. Returns True if *any* element consumed it.
        UI Panels also consume clicks so you can't click through them.
        """
        consumed = False
        
        # We process elements in reverse order so elements drawn last (on top) get clicks first
        for element in reversed(self.elements):
            if element.handle_event(event):
                consumed = True
                break
                
        # If it wasn't a button click, we should still prevent clicking *through* a UIPanel
        if not consumed and event.type == pygame.MOUSEBUTTONDOWN:
            for element in self.elements:
                if isinstance(element, UIPanel) and element.rect.collidepoint(event.pos):
                    # We clicked on a background panel, consume the click
                    consumed = True
                    break

        return consumed
