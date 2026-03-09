Role: Specification Design Agent

Context: We are beginning Milestone 15: Directional Active Entities & Filtering. We are redesigning the "Cannon" and "Basket" entities introduced in M12. They will transition from composite U-shapes to standard Rectangles with highly configurable directional behaviors and entity filtering.

Task: Generate the specification document docs/SPECIFICATION_M15_DirectionalEntities.md.

Requirements for the Specification:

The Basket Redesign (Directional Ingestion & Filtering):

Shape Transition: The Basket must become a standard rectangular physics body.

Active Sides: Specify how the YAML config can define which side(s) of the rectangle (Top, Bottom, Left, Right) act as the ingestion sensor.

Type Filtering: Detail a new YAML parameter (e.g., accepts_types: ["bouncy_ball", "data_ball"]).

Collision Logic: If an object collides with an active side, the collision handler must check the object's type against the accepts_types list. If it matches (or if the list is "all"), it is ingested/destroyed. If it does not match, it must act as a normal solid wall and bounce the object away.

The Cannon Redesign (Directional Emitter):

Shape Transition: The Cannon must also become a standard rectangular physics body.

Active Side: Specify how the YAML config can define which side the projectile spawns from.

Configurable Trajectory: Detail YAML parameters for exit_velocity (float) and exit_angle (degrees/radians relative to the Cannon's rotation).

Configurable Ammo: Ensure the Cannon can define exactly which entity_id it shoots out.

Data-Driven Rules:

Ensure all new properties (active sides, accepted types, exit velocity, exit angle) are strictly defined in config/entities.yaml or as instance overrides (following the M14 inheritance rules).

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.