Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md

docs/SPECIFICATION_M15_DirectionalEntities.md

docs/IMPLEMENTATION_PLAN_M15_DirectionalEntities.md

Task: Implement Milestone 15: Directional Active Entities & Filtering. Execute the phased steps outlined in the implementation plan.

Critical Instructions:

Allow autonomy in execution: Rely on your own expertise to translate local "active sides" (Top, Bottom, Left, Right) into precise Pymunk segment sensors attached to the main rectangular body.

Conditional Collisions: In Pymunk, returning False from a begin or pre_solve collision handler tells the engine to ignore the collision (allowing overlap/ingestion). Returning True tells the engine to resolve it physically (bouncing). Use this mechanic to implement the Basket's type filter. If the type is not in the accepted list, return True so it bounces off the sensor like a normal wall.

Vector Math: Ensure the Cannon's exit_velocity and exit_angle calculations correctly account for the Cannon's current rotation in the world space.

Inheritance Compatibility: Ensure these new configurable properties fully support the Instance Property Overrides established in M14, so users can edit a Cannon's angle or a Basket's filter directly in the game UI.