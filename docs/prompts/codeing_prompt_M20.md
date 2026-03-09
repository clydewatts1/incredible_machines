Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md

docs/SPECIFICATION_M20_AdvancedPhysics.md

docs/IMPLEMENTATION_PLAN_M20_AdvancedPhysics.md

Task: Implement Milestone 20: Advanced Physics Mechanics (Motors & Conveyors). Execute the phased steps outlined in the implementation plan.

Critical Instructions:

Allow autonomy in execution: Rely on your own expertise to implement Pymunk's surface_velocity and SimpleMotor.

Pymunk Surface Velocity: Note that shape.surface_velocity is a tuple. For a flat horizontal conveyor belt, it should be (speed, 0).

Motor Anchoring: A dynamic motor needs to be held in place. Use the Two-Pass Instantiation system (from M13) or simply spawn a static dummy body at the motor's (x, y) coordinates, attach a pymunk.PivotJoint to hold it there, and attach a pymunk.SimpleMotor to spin it.

Edit Mode Overrides: Ensure the speed properties dynamically update if the user changes them in the UI Properties Panel (M14) while in EDIT mode.