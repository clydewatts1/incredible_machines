import math


def find_route(state_value: float, routing_list: list) -> dict:
    if not isinstance(routing_list, list):
        return None

    for rule in routing_list:
        if not isinstance(rule, dict):
            continue

        try:
            if float(state_value) <= float(rule.get("max_state")):
                return rule
        except (TypeError, ValueError):
            continue

    return None


def calculate_ejection_kinematics(entity, edge: str, route_rule: dict, default_velocity: float, default_angle: float, entities: list = None) -> tuple:
    width = float(entity.get_property("width", 96))
    height = float(entity.get_property("height", 96))
    half_w = width / 2.0
    half_h = height / 2.0
    margin = 25.0

    fx = entity.body.position.x
    fy = entity.body.position.y

    if edge == "bottom":
        eject_x, eject_y = fx, fy + half_h + margin
    elif edge == "top":
        eject_x, eject_y = fx, fy - half_h - margin
    elif edge == "left":
        eject_x, eject_y = fx - half_w - margin, fy
    elif edge == "right":
        eject_x, eject_y = fx + half_w + margin, fy
    else:
        eject_x, eject_y = fx, fy

    active_rule = route_rule if isinstance(route_rule, dict) else {}
    target_value = active_rule.get("target")
    if not target_value:
        target_value = entity.get_property("target", None)

    if target_value and entities is not None:
        for other in entities:
            if getattr(other, "uuid", None) == target_value or other.get_property("name") == target_value:
                dx = other.body.position.x - eject_x
                dy = other.body.position.y - eject_y
                dist = math.hypot(dx, dy)
                speed = float(active_rule.get("velocity", default_velocity))
                if dist > 0.0:
                    return (eject_x, eject_y), ((dx / dist) * speed, (dy / dist) * speed)
                return (eject_x, eject_y), (0.0, 0.0)

    angle_deg = float(active_rule.get("angle", default_angle))
    velocity = float(active_rule.get("velocity", default_velocity))
    angle_rad = math.radians(angle_deg)
    vx = velocity * math.cos(angle_rad)
    vy = velocity * -math.sin(angle_rad)
    return (eject_x, eject_y), (vx, vy)