

Role: Lead System Architect

Context: Please read CONSTITUTION.md. We are starting Milestone 8: Entity Variants & Textured Sprites.

Task: Generate Specification
Create docs/SPECIFICATION_M8_TexturedVariants.md.

Requirements for M8:

YAML Variants: Update config/entities.yaml to support "variants". For example, define small_ramp and long_ramp. They should both use the same Python logic but have different length and width properties.

Sprite Feature: Add a texture_path property to the YAML for each entity.

Base Class Update: The base Entity class must check for texture_path. If it exists, it should load the image once and use it in the draw() method.

Rotation Handling: Implement the rotation math from Section 10 of the Constitution so textures tilt correctly as the physics body tilts.

Mandatory Quality Assurance:
Include a "Manual Test Script" to verify:

Spawning a "Small Ramp" (Key: 1) vs a "Long Ramp" (Key: 2).

Verifying the "Long Ramp" displays a repeating or stretched texture image.

Verifying that if the texture file is missing, the object falls back to its original primitive shape (line/polygon).

Constraint: Do not write code yet.