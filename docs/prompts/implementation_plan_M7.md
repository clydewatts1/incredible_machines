Role: Lead System Architect

Context: Please read CONSTITUTION.md (specifically Section 10) and docs/SPECIFICATION_M7_BackgroundAesthetics.md.

Task: Generate a sequential technical implementation plan for Milestone 7.

Operational Constraints:

Naming Convention: Per Section 7 of the Constitution, name the file docs/IMPLEMENTATION_PLAN_M7_BackgroundAesthetics.md.

Architecture: Ensure the plan strictly separates the loading logic (Environment Manager) from the main game loop rendering.

Fail Loudly: The plan must include explicit tasks for implementing the "Fail Loudly" requirement—if a YAML path is invalid, the terminal MUST output a clear error before falling back to the solid color.

Validation Steps: Every task in the plan MUST include a "Validation" step. This step should describe exactly how to verify the task works (e.g., "Change the YAML color and check if the border color updates").

Required Tasks to include in the plan:

Setup the directory structure (assets/images/) and the initial config/environment.yaml.

Implement a EnvironmentManager or update utils/config_loader.py to handle background image loading and scaling.

Implement the mode-specific border logic (Edit vs Play) using the colors defined in the YAML.

Refactor the main.py draw loop to prioritize the background layer.

Final execution of the Manual Test Script defined in the Specification.

Final Action: Output the Markdown file for my review. Do not write any Python code yet.