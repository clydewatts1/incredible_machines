Role: Lead System Architect

Context: Please read CONSTITUTION.md (specifically Sections 9 and 10) and our current config/entities.yaml. We are moving into Milestone 8: The Template-Variant Inheritance System.

Task: Generate Specification
Create a new specification file: docs/SPECIFICATION_M8_EntityTemplates.md.

1. Data Architecture Requirements:

YAML Structure: The entities.yaml must be split into templates (the base DNA) and variants (the actual game objects).

Inheritance Logic: When a variant is spawned, the system must perform a "Deep Merge": Start with the template's properties and overwrite them with the variant's specific overrides (e.g., mass, friction, length, texture_path).

2. Geometric Template Requirements:
Define the technical physics and visual requirements for the following base templates:

Square & Rectangle: Using pymunk.Poly.create_box.

Circle: Using pymunk.Circle.

Diamond: A polygon defined by four points [(0, -h), (w, 0), (0, h), (-w, 0)].

Half-Circle & Quarter-Circle: To be implemented as pymunk.Poly approximations (providing a list of vertices that form the arc).

3. Visual & Texture Requirements (Per Section 10):

Every template/variant must support an optional texture_path.

If a texture is present, the draw() method must use pygame.transform.rotate using the -math.degrees(self.body.angle) formula.

Sprites must be scaled to the bounding box of the physics shape.

4. Mandatory Quality Assurance (Per Section 6):
Include a "Manual Test Script" that verifies:

Inheritance: Spawning a "Red Diamond" (Variant) which inherits mass from "Diamond Template" but overrides the color to Red.

Geometry: Verify the collision boundaries of the Half-Circle and Quarter-Circle match their visual arc.

Texture Sync: Spawning a "Textured Rectangle" and verifying the image tilts perfectly with the physics body in Play Mode.

Constraint: Do not write any Python code yet. Provide the Specification for my review.