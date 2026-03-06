Since we have established that Milestone 5 (YAML Metadata & Property System) is the next priority to create the data structure for everything else (including sounds), we need to get the agent to execute the Implementation Plan we just discussed.

Here is the professional-grade prompt to trigger the actual coding for Milestone 5.

Copy and paste this into Antigravity:
Role: Senior Systems Programmer

Context: > Please read:

docs/CONSTITUTION.md (Specifically Section 9: Data Management & Property Standards).

docs/SPECIFICATION_M5_YamlMetadataSystem.md.

docs/IMPLEMENTATION_PLAN_M5_YamlMetadataSystem.md.

Task: > Implement the YAML-based Property System as defined in the plan. This is a foundational refactor to remove hardcoded physics values.

Execution Requirements:

Dependencies: Install PyYAML in the terminal first.

Refactor Logic: >    - Create config/entities.yaml.

Modify the Entity (or GamePart) base class constructor to load its properties (elasticity, friction, mass, etc.) from the YAML file using a key.

Ensure BouncyBall and StaticRamp use this system.

The "Fail Loudly" Guard: Implement a check that raises an AttributeError or KeyError with a clear message if a required property is missing from the YAML file.

Naming: Ensure any new utility files follow the snake_case rule from Section 7 of the Constitution.

Final Action & Quality Assurance:

Run the code to ensure the game still launches and physics work correctly.

Lead Developer Validation: Once running, provide a confirmation message that the system is ready for me to perform the "Manual Test Script" (changing a YAML value and observing the change in-game).