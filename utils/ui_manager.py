import pygame

class UIElement:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.is_visible = True

    def draw(self, surface):
        pass

    def handle_event(self, event):
        return False

import textwrap

class UITextInput(UIElement):
    def __init__(self, rect, font, text="", color=(255, 255, 255), bg_color=(30, 30, 30), active_color=(60, 60, 60)):
        super().__init__(rect)
        self.font = font
        self.text = text
        self.color = color
        self.bg_color = bg_color
        self.active_color = active_color
        self.is_active = False

    def draw(self, surface):
        if not self.is_visible: return
        color = self.active_color if self.is_active else self.bg_color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200) if self.is_active else (100, 100, 100), self.rect, 1)
        
        text_surf = self.font.render(self.text, True, self.color)
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))
        
        if self.is_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.rect.x + 5 + text_surf.get_width()
            pygame.draw.line(surface, self.color, (cursor_x, self.rect.y + 5), (cursor_x, self.rect.bottom - 5))

    def handle_event(self, event):
        if not self.is_visible: return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_active = True
                return True
            else:
                self.is_active = False
                
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != pygame.K_RETURN:
                self.text += event.unicode
            return True
        return False

class UITextArea(UITextInput):
    def __init__(self, rect, font, text="", color=(255, 255, 255), bg_color=(30, 30, 30), active_color=(60, 60, 60)):
        super().__init__(rect, font, text, color, bg_color, active_color)

    def draw(self, surface):
        if not self.is_visible: return
        color = self.active_color if self.is_active else self.bg_color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200) if self.is_active else (100, 100, 100), self.rect, 1)
        
        # Word wrap rendering
        x, y = self.rect.x + 5, self.rect.y + 5
        lines = self.text.split('\n')
        wrapped_lines = []
        for line in lines:
            if not line:
                wrapped_lines.append("")
                continue
            words = line.split(" ")
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if self.font.size(test_line)[0] < self.rect.width - 10:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    current_line = word + " "
            wrapped_lines.append(current_line)
            
        for i, line in enumerate(wrapped_lines):
            text_surf = self.font.render(line, True, self.color)
            surface.blit(text_surf, (x, y + i * self.font.get_height()))

        if self.is_active and pygame.time.get_ticks() % 1000 < 500:
            if wrapped_lines:
                last_line = wrapped_lines[-1]
                cursor_x = x + self.font.size(last_line)[0]
                cursor_y = y + (len(wrapped_lines) - 1) * self.font.get_height()
            else:
                cursor_x = x
                cursor_y = y
            pygame.draw.line(surface, self.color, (cursor_x, cursor_y), (cursor_x, cursor_y + self.font.get_height()))

    def handle_event(self, event):
        if not self.is_visible: return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_active = True
                return True
            else:
                self.is_active = False
                
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.text += '\n'
            else:
                self.text += event.unicode
            return True
        return False


class UIPanel(UIElement):
    def __init__(self, rect, color=(40, 40, 40), alpha=220):
        """
        Initialize a UI panel.
        
        M25 Phase 5: Added alpha parameter for semi-transparent panels.
        
        Args:
            rect: Pygame Rect for panel position and size
            color: RGB color tuple
            alpha: Alpha transparency (0-255, where 255 is opaque)
        """
        super().__init__(rect)
        self.color = color
        self.alpha = alpha

    def draw(self, surface):
        if self.is_visible:
            # M25 Phase 5: Create semi-transparent panel surface
            panel_surface = pygame.Surface((self.rect.width, self.rect.height))
            panel_surface.set_alpha(self.alpha)
            panel_surface.fill(self.color)
            surface.blit(panel_surface, self.rect.topleft)


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


class UIScrollPanel(UIPanel):
    def __init__(self, rect, color=(40, 40, 40), alpha=220, scroll_speed=24):
        super().__init__(rect, color=color, alpha=alpha)
        self.children = []
        self.content_height = 0
        self.scroll_y = 0
        self.scroll_speed = scroll_speed

    def add_child(self, element):
        self.children.append(element)
        return element

    def clear_children(self):
        self.children.clear()
        self.content_height = 0
        self.scroll_y = 0

    def get_active_child(self):
        for child in self.children:
            if isinstance(child, (UITextInput, UITextArea)) and child.is_active:
                return child
        return None

    def deactivate_text_children(self):
        for child in self.children:
            if isinstance(child, (UITextInput, UITextArea)):
                child.is_active = False

    def _clamp_scroll(self):
        min_scroll = min(0, self.rect.height - self.content_height)
        if self.scroll_y > 0:
            self.scroll_y = 0
        if self.scroll_y < min_scroll:
            self.scroll_y = min_scroll

    def draw(self, surface):
        if not self.is_visible:
            return

        super().draw(surface)

        # CRITICAL: clip child rendering to panel bounds.
        previous_clip = surface.get_clip()
        surface.set_clip(self.rect)
        try:
            for child in self.children:
                original_rect = child.rect.copy()
                child.rect.y = original_rect.y + self.scroll_y
                child.draw(surface)
                child.rect = original_rect
        finally:
            # CRITICAL: restore prior clipping state after drawing children.
            surface.set_clip(previous_clip)

    def handle_event(self, event):
        if not self.is_visible:
            return False

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            active_child = self.get_active_child()
            if active_child:
                return active_child.handle_event(event)
            return False

        if event.type == pygame.MOUSEWHEEL and hovered:
            self.scroll_y += event.y * self.scroll_speed
            self._clamp_scroll()
            return True

        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            if not hasattr(event, "pos"):
                return False

            if not self.rect.collidepoint(event.pos):
                return False

            # CRITICAL: offset child event Y by scroll_y so hit tests align with drawn children.
            adjusted_pos = (event.pos[0], event.pos[1] - self.scroll_y)
            adjusted_event = pygame.event.Event(event.type, {**event.dict, "pos": adjusted_pos})

            consumed = False
            for child in reversed(self.children):
                if child.handle_event(adjusted_event):
                    consumed = True
                    break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not consumed:
                self.deactivate_text_children()
            return consumed

        return False


class UIManager:
    def __init__(self):
        self.elements = []
        self.focused_element = None

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
                if isinstance(element, (UITextInput, UITextArea)) and event.type == pygame.MOUSEBUTTONDOWN:
                    if self.focused_element and self.focused_element != element:
                        self.focused_element.is_active = False
                    self.focused_element = element if element.is_active else None
                elif isinstance(element, UIScrollPanel) and event.type == pygame.MOUSEBUTTONDOWN:
                    active_child = element.get_active_child()
                    if self.focused_element and self.focused_element != active_child:
                        self.focused_element.is_active = False
                    self.focused_element = active_child
                break
                
        # Handle clicking outside any text input to unfocus
        if not consumed and event.type == pygame.MOUSEBUTTONDOWN:
            if self.focused_element:
                self.focused_element.is_active = False
                self.focused_element = None
                
        # If we have a focused element, we should consume all keyboard events to prevent global hotkey triggers
        if self.focused_element and event.type in (pygame.KEYDOWN, pygame.KEYUP):
            return True
                
        # If it wasn't a button click, we should still prevent clicking *through* a UIPanel
        # Only consume left mouse button (button 1) - allow middle/right buttons for camera panning
        if not consumed and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for element in self.elements:
                if isinstance(element, UIPanel) and element.rect.collidepoint(event.pos):
                    # We clicked on a background panel, consume the click
                    consumed = True
                    break

        return consumed
