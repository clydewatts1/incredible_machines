import math

def get_diamond_vertices(width, height):
    """
    Returns a list of vertices for a centered diamond polygon.
    """
    w = width / 2.0
    h = height / 2.0
    return [(0, -h), (w, 0), (0, h), (-w, 0)]

def get_arc_vertices(radius, start_angle, end_angle, segments=15):
    """
    Returns a list of vertices approximating an arc, closing at the origin (0,0) with counter-clockwise winding.
    """
    vertices = [(0.0, 0.0)]
    angle_step = (end_angle - start_angle) / segments
    for i in range(segments + 1):
        angle = start_angle + i * angle_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append((x, y))
    # Reverse to ensure counter-clockwise winding order for pymunk (by default if angle is increasing, then it's CCW usually, but let's be careful)
    # Actually Pymunk prefers CCW vertices
    if end_angle > start_angle:
        vertices.reverse()
    return vertices
