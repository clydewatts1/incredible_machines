Milestone 28: Universal Routing Module

Objective

To eliminate the massive code duplication across FactoryPart, BrainPart, WarehousePart, and DataSource by centralizing payload ejection math and route resolution into a single utils/routing.py module. This ensures all entities behave identically when targeting UUIDs, applying ejection angles, and calculating velocity.

Core Mechanics

1. The utils/routing.py Module

Create a new utility file exposing two primary helper functions:

find_route(state_value: float, routing_list: list) -> dict: Iterates through a standardized routing list and returns the first rule where state_value <= rule.get("max_state").

calculate_ejection_kinematics(entity, edge: str, route_rule: dict, entities_list: list = None) -> tuple:

Takes the emitting entity, the string edge ("top", "bottom", "left", "right"), the active route rule, and the global entities list.

Calculates Position: Determines the exact (eject_x, eject_y) coordinate just outside the entity's bounding box based on the edge.

Calculates Velocity: Checks if the route rule defines a specific string target (UUID or Name). If so, calculates the exact trigonometric (vx, vy) needed to shoot directly at that target. If no target exists, falls back to the route rule's angle and velocity to compute the vector.

Returns: ((eject_x, eject_y), (vx, vy))

2. Refactoring the Entities

entities/active.py (Factory) & entities/brain.py (Brain): * Delete their internal _find_route methods.

Strip out the heavy math inside their _eject_payload methods. Replace it with a single call to calculate_ejection_kinematics, then apply the returned position and velocity to the payload's Pymunk body.

entities/source.py (Data Source):

Replace _compute_emission_velocity and the positioning math inside _emit_ball with the new universal routing utility.

Benefits

DRY Code: Removes hundreds of lines of duplicated trigonometry.

Consistency: Ensures a rule like angle: 45, velocity: 200 behaves exactly the same whether it is defined on a Factory or a Brain.

Maintainability: If we want to add a new routing feature (like homing missiles or wind resistance), we only have to update utils/routing.py.