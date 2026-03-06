Role: Lead System Architect

Context: Please read CONSTITUTION.md (specifically Sections 9 and 10) and the recently finalized docs/SPECIFICATION_M8_EntityTemplates.md.

Task: Generate a sequential technical implementation plan for Milestone 8.

Operational Constraints:

Naming Convention: Per Section 7 of the Constitution, name the file docs/IMPLEMENTATION_PLAN_M8_EntityTemplates.md.

Deep Merge Logic: Detail how the ConfigLoader will deep-merge properties from a template into a variant.

Geometry Math: Plan the creation of a utility for generating vertices for the Diamond, Half-Circle, and Quarter-Circle shapes.

Sprite Architecture: Detail the refactor of the Entity base class to handle texture loading, scaling to physics bounds, and the rotation math required by Section 10.

Validation Steps: Every task MUST include a specific "Validation" step to ensure we "Fail Loudly" if the YAML data or geometric math is incorrect.

Required Tasks to include in the plan:

Update config/entities.yaml to the Template/Variant structure.

Refactor utils/config_loader.py to handle inheritance.

Create a geometry utility for complex point lists.

Update the Entity base class to support sprite rendering and cached textures.

Map keys 1-6 in main.py to the new variant objects.

Final Action: Output the Markdown file for my review. Do not write any Python code yet.