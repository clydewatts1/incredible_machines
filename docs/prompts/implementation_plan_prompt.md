Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 20: Advanced Physics Mechanics (Motors & Conveyors). The details are located in docs/SPECIFICATION_M20_AdvancedPhysics.md.

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M20_AdvancedPhysics.md. Break down the specification into logical, actionable implementation phases.

Requirements for the Implementation Plan:

Sequential Phases: Divide the work into distinct phases. A recommended breakdown:

Phase 1: YAML Configuration (Adding conveyor and motor entries to config/entities.yaml with their default speed variables).

Phase 2: Conveyor Belt Logic (Creating a Conveyor entity class that maps its configured speed to its Pymunk shape's surface_velocity).

Phase 3: Motor Logic & Constraints (Creating a Motor entity class that spawns a dynamic body, pins it to a static space point with a PivotJoint, and drives it with a SimpleMotor).

Phase 4: Property Editor Integration (Ensuring the M14 overrides dictionary is checked so users can edit the speed of these objects dynamically in EDIT mode).

File Targeting: Explicitly state which file(s) are being modified or created (e.g., config/entities.yaml, entities/active.py).

Actionable Details: Mention how to handle the surface_velocity tuple (e.g., (speed, 0)).

Testing/Acceptance: Include a brief manual verification step at the end of each phase.

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the plan/task list.