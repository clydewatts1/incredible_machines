import pygame
import math

def get_wire_curve_point(start_pos, end_pos, t):
    """Calculates a point along an elegant S-Curve Bezier for logic wires, with a gentle wind sway."""
    p0 = pygame.math.Vector2(start_pos)
    p3 = pygame.math.Vector2(end_pos)
    
    dx = p3.x - p0.x
    dy = p3.y - p0.y
    dist = p0.distance_to(p3)
    
    time_sec = pygame.time.get_ticks() / 1000.0
    phase = (p0.x + p0.y) * 0.01 
    max_sway = min(25.0, dist * 0.15)
    
    sway1 = math.sin(time_sec * 2.0 + phase) * max_sway
    sway2 = math.sin(time_sec * 2.5 + phase + 1.0) * max_sway
    
    if abs(dx) > abs(dy):
        p1 = p0 + pygame.math.Vector2(dx * 0.5, sway1)
        p2 = p0 + pygame.math.Vector2(dx * 0.5, dy + sway2)
    else:
        p1 = p0 + pygame.math.Vector2(sway1, dy * 0.5)
        p2 = p0 + pygame.math.Vector2(dx + sway2, dy * 0.5)
        
    u = 1 - t
    return (u**3)*p0 + 3*(u**2)*t*p1 + 3*u*(t**2)*p2 + (t**3)*p3
