Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md (Specifically Sections 9 and 10).

docs/SPECIFICATION_M8_EntityTemplates.md.

docs/IMPLEMENTATION_PLAN_M8_EntityTemplates.md.

Task: Implement Milestone 8: The Template-Variant Inheritance System and Advanced Geometry.

Execution Requirements:

Data Inheritance: >    - Restructure config/entities.yaml to include templates and variants.

Refactor utils/config_loader.py to implement Deep Merge logic: a variant must inherit all properties from its parent template, overwriting only the specific keys defined in the variant block.

Geometry Utility:

Create utils/geometry_utils.py to generate vertex lists for:

Diamond: Centered diamond based on width/height.

Half-Circle & Quarter-Circle: Vertex approximations (using ~12 segments) for smooth physics arcs.

Sprite Refactor (Section 10):

Update the Entity base class to check for texture_path.

Caching: Load and scale the texture to the physics bounds exactly once during initialization.

Rotation: Implement the mandated rotation formula: pygame.transform.rotate(self.image, -math.degrees(self.body.angle)).

Input Integration:

Map keys 1 through 6 in main.py to spawn: Square, Rectangle, Circle, Diamond, Half-Circle, and Quarter-Circle variants respectively.

Final Action & Quality Assurance:

Run the game to ensure all new shapes spawn at the mouse position.

Lead Developer Validation: Confirm the system is ready for the "Manual Test Script" to verify that textured objects rotate correctly and variants properly inherit friction/elasticity from their templates.