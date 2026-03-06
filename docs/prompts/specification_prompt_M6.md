Role: Lead Audio Designer

Context: Please read docs/CONSTITUTION.md (specifically Section 8 and 9) and our current config/entities.yaml. Milestone 5 is complete; we are now moving to Milestone 6: Universal Audio System.

Task: Generate Specification
Create a new specification file following our naming conventions: docs/SPECIFICATION_M6_AudioSystem.md.

Requirements for M6:

Sound Manager: Create a centralized system to load sounds into memory (Pygame mixer) at startup to prevent lag during collisions.

YAML Integration: The system must look for a collision_sound key in the entities.yaml for each entity.

The Fallback Rule: Per Section 8 of the Constitution, if an entity's YAML entry doesn't specify a sound, or the file is missing, it must play a default_collision.wav.

Collision Logic: Implement a Pymunk collision handler that triggers the appropriate sound based on the collision impulse (strength).

Mandatory Quality Assurance:
Per Section 6, include a "Manual Test Script" with these steps:

Launch the game and spawn a ball.

Drop the ball onto a ramp and verify a sound plays on impact.

Edit entities.yaml to change the collision_sound path to a different file and verify the sound changes in-game without restarting.

Delete the sound path from YAML and verify the "Fallback" sound plays instead.

Constraint: Do not write code yet. Provide the M6 Specification for my review.