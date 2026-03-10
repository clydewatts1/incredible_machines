"""
Camera System for Infinite Canvas

This module provides a 2D camera for viewport panning across a large world.
The camera translates between world space (Pymunk physics coordinates) and 
screen space (Pygame display coordinates).

Constitutional Adherence:
- Pure rendering/translation utility; holds NO game state
- All coordinate conversions are stateless transformations
- Camera offset changes do NOT trigger Pymunk mutations
"""

from typing import Tuple


class Camera:
    """
    Manages viewport offset for panning across a large 2D world.
    
    Coordinate Systems:
    - World Space: Pymunk physics coordinates (e.g., 5000x5000)
    - Screen Space: Pygame display coordinates (e.g., 1200x800)
    
    The camera maintains an offset (offset_x, offset_y) representing the 
    world-space position of the top-left corner of the screen viewport.
    """
    
    def __init__(self, world_width: int, world_height: int, 
                 screen_width: int, screen_height: int):
        """
        Initialize the camera.
        
        Args:
            world_width: Total width of the game world in pixels
            world_height: Total height of the game world in pixels
            screen_width: Width of the visible screen viewport in pixels
            screen_height: Height of the visible screen viewport in pixels
        """
        self.world_width = world_width
        self.world_height = world_height
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camera offset in world space (top-left corner of viewport)
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        
        # Middle mouse button panning state
        self.is_panning = False
        self.pan_start_screen_x = 0
        self.pan_start_screen_y = 0
        self.pan_start_offset_x = 0.0
        self.pan_start_offset_y = 0.0
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """
        Convert world-space coordinates to screen-space coordinates.
        
        Used by the render loop to determine where to draw Pymunk bodies.
        
        Args:
            world_x: X coordinate in world space
            world_y: Y coordinate in world space
            
        Returns:
            Tuple of (screen_x, screen_y)
        """
        screen_x = world_x - self.offset_x
        screen_y = world_y - self.offset_y
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """
        Convert screen-space coordinates to world-space coordinates.
        
        Used by the event loop to determine what physics object the user clicked.
        
        Args:
            screen_x: X coordinate in screen space (from pygame.mouse.get_pos())
            screen_y: Y coordinate in screen space (from pygame.mouse.get_pos())
            
        Returns:
            Tuple of (world_x, world_y)
        """
        world_x = screen_x + self.offset_x
        world_y = screen_y + self.offset_y
        return (world_x, world_y)
    
    def pan(self, dx: float, dy: float) -> None:
        """
        Pan the camera by the given delta.
        
        Args:
            dx: Change in x offset (positive = pan right)
            dy: Change in y offset (positive = pan down)
        """
        self.offset_x += dx
        self.offset_y += dy
        self._clamp_offset()
    
    def _clamp_offset(self) -> None:
        """
        Ensure camera offset stays within world boundaries.
        
        Prevents panning beyond the edges of the world.
        """
        # Clamp X: Can't go negative or beyond right edge
        max_offset_x = max(0, self.world_width - self.screen_width)
        self.offset_x = max(0.0, min(self.offset_x, max_offset_x))
        
        # Clamp Y: Can't go negative or beyond bottom edge
        max_offset_y = max(0, self.world_height - self.screen_height)
        self.offset_y = max(0.0, min(self.offset_y, max_offset_y))
    
    def begin_pan(self, screen_x: int, screen_y: int) -> None:
        """
        Begin a pan operation (typically from middle mouse button press).
        
        Args:
            screen_x: Initial mouse X position in screen space
            screen_y: Initial mouse Y position in screen space
        """
        self.is_panning = True
        self.pan_start_screen_x = screen_x
        self.pan_start_screen_y = screen_y
        self.pan_start_offset_x = self.offset_x
        self.pan_start_offset_y = self.offset_y
    
    def update_pan(self, screen_x: int, screen_y: int) -> None:
        """
        Update pan position during drag.
        
        Args:
            screen_x: Current mouse X position in screen space
            screen_y: Current mouse Y position in screen space
        """
        if not self.is_panning:
            return
        
        # Calculate how far the mouse has moved
        dx = screen_x - self.pan_start_screen_x
        dy = screen_y - self.pan_start_screen_y
        
        # Pan in the opposite direction (dragging right moves world left)
        self.offset_x = self.pan_start_offset_x - dx
        self.offset_y = self.pan_start_offset_y - dy
        self._clamp_offset()
    
    def end_pan(self) -> None:
        """End the pan operation."""
        self.is_panning = False
    
    def handle_keyboard_pan(self, keys_pressed: dict, pan_speed: float, dt: float) -> None:
        """
        Handle keyboard-based camera panning (WASD / Arrow Keys).
        
        Args:
            keys_pressed: Dictionary from pygame.key.get_pressed()
            pan_speed: Pixels per second to pan
            dt: Delta time in seconds since last frame
        """
        import pygame
        
        pan_distance = pan_speed * dt
        
        # Horizontal panning
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            self.pan(-pan_distance, 0)
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            self.pan(pan_distance, 0)
        
        # Vertical panning
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            self.pan(0, -pan_distance)
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            self.pan(0, pan_distance)
    
    def reset(self) -> None:
        """Reset camera to origin (0, 0)."""
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.is_panning = False
