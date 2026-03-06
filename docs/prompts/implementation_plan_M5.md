Role: Lead System Architect

Context: Please read docs/CONSTITUTION.md and docs/SPECIFICATION_M5_YamlMetadataSystem.md.

Task: Generate a sequential, step-by-step implementation plan for Milestone 5.

Operational Constraints:

Naming Convention: Per Section 7 of the Constitution, name the file docs/IMPLEMENTATION_PLAN_M5_YamlMetadataSystem.md.

Refactoring Priority: This plan must focus on moving hardcoded values (mass, friction, elasticity) into a central configuration without breaking existing functionality.

Validation Steps: Every task MUST include a specific "Validation" step (human-testable) to ensure we "Fail Loudly" if the YAML data is malformed or missing.

Scalability: Ensure the base class is designed so that Milestone 6 (Audio) can easily add a sound_file property to the YAML later without needing another major refactor.

Required Tasks to include in the plan:

Setup the config/ directory and create the initial entities.yaml.

Implement a YAML loader utility (using PyYAML).

Modify the Entity base class to accept a property_key (e.g., "bouncy_ball") and fetch its data from the loaded YAML.

Update BouncyBall and StaticRamp to stop passing hardcoded numbers to the parent constructor.

Verify that changing the elasticity in the YAML file correctly updates the behavior of all spawned objects in the next run.

Final Action: Output the Markdown file for my review. Do not write any Python code yet.