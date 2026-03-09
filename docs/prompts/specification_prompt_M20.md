Role: Specification Design Agent

Context: We are beginning Milestone 20: Advanced Physics Mechanics (Motors & Conveyors). We want to add driven, continuous motion to the physics sandbox to allow for more complex Rube Goldberg-style machines that can physically transport our data payloads.

Task: Generate the specification document docs/SPECIFICATION_M20_AdvancedPhysics.md.

Requirements for the Specification:

Conveyor Belts:

Shape & Type: Must be a static or kinematic rectangular body.

Physics Property: Detail the use of Pymunk's surface_velocity attribute on the shape. This natively pushes dynamic objects that rest on it.

Configuration: Specify new YAML parameters for entities.yaml, such as speed (float, determining the horizontal surface velocity).

Instance Overrides: Ensure the speed can be modified on the fly using the M14 Property Editor.

Motors (Spinning Gears/Wheels):

Shape & Type: Must be a dynamic body (like a circle or polygon) that rotates constantly.

Physics Constraint: Detail the use of pymunk.SimpleMotor. If the motor is placed freely on the canvas, it should be pinned to a static background body using a PivotJoint (so it doesn't fall) and driven by a SimpleMotor constraint attached to that same static body.

Configuration: Specify YAML parameters like motor_speed (radians per second).

Instance Overrides: The motor speed must be editable via the M14 Property Editor.

Signal Integration (Optional but Recommended):

Detail how these new active elements can listen to the logic signals established in M17. For example, receiving a signal could toggle the Conveyor/Motor's speed between 0 and its configured speed, allowing them to be turned on/off by Baskets or Processors.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.