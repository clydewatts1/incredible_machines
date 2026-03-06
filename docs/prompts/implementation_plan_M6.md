Role: Lead Audio & Systems Architect

Context: Please read docs/CONSTITUTION.md, config/entities.yaml, and the newly finalized docs/SPECIFICATION_M6_AudioSystem.md.

Task: Generate a sequential technical implementation plan for Milestone 6.

Operational Constraints:

Naming Convention: Per Section 7 of the Constitution, name the file docs/IMPLEMENTATION_PLAN_M6_AudioSystem.md.

Architecture: Use a singleton or centralized SoundManager to ensure sounds are loaded once and stored in memory, as mandated by Section 8.

YAML Integration: The plan must detail how the base Entity class retrieves sound file paths from the properties dictionary (loaded from YAML).

Validation Steps: Every task MUST include a specific "Validation" step. Since audio can be tricky, include steps to verify file loading success before attempting to play them.

Required Tasks to include in the plan:

Initialize the pygame.mixer and create the SoundManager utility.

Implement the "Fallback Logic": define a global default sound and ensure the code uses it if a YAML-specified file is missing or invalid.

Set up a Pymunk collision handler (PostSolve) to calculate collision impulse and trigger sounds based on impact strength.

Update the base class to handle "one-shot" sound triggering for interaction events (spawning, highlighting, etc.).

Perform the final Manual Test Script validation.

Final Action: Output the Markdown file for my review. Do not write any Python code yet.