Context: Please read docs/CONSTITUTION.md. We are moving into Milestone 5: YAML Metadata & Property System. We have decided to implement Point 9 of the Constitution now to ensure all future features (like Point 8's Audio system) have a consistent data structure to build upon.

Task: Generate Specification
Create a new specification file: docs/SPECIFICATION_M5_YamlMetadataSystem.md.

Requirements for M5:

External Config: Create config/entities.yaml. This file will store the physics properties (mass, friction, elasticity) and metadata for the BouncyBall and StaticRamp.

Base Class Refactor: Refactor the base Entity / GamePart class to load its initial state from this YAML configuration.

Dynamic Updates: Ensure that when a new entity is spawned, it pulls the latest values from the YAML file, allowing behavior changes without modifying Python code.

No Hardcoding: Remove all hardcoded physics values from the individual entity classes.

Mandatory Quality Assurance:
Per Section 6 of the Constitution, include a "Manual Test Script". The test must verify:

The human can edit config/entities.yaml, change the elasticity of the ball, save the file, and then spawn a new ball in-game to see the immediate physical difference.

The game "Fails Loudly" if a required property is missing from the YAML file.

Constraint: Do not write code yet. Provide the M5 Specification for my review.