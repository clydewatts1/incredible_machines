Role: Senior UI/UX Developer

Context: Please perform a comprehensive review of the following documents:

CONSTITUTION.md (Specifically Section 10: Visual Asset & Aesthetic Standards).

docs/IMPLEMENTATION_PLAN_M7_BackgroundAesthetics.md.

Task: Implement Milestone 7: Background & Aesthetic Enhancements.

Execution Requirements:

Data-Driven Visuals: Create config/environment.yaml as defined in the plan. All colors (fallback, edit mode, play mode) and the background image path MUST be loaded from this file.

Environment Manager: >    - Create the directory assets/images/.

Implement logic to load the background image. You MUST use pygame.transform.smoothscale to ensure it fits the 800x600 window exactly.

Fail Loudly: If the image file is missing, print a clear error to the terminal and fall back to the fallback_color from the YAML.

State Indicators: >    - Add a 5-pixel thick border to the main drawing loop.

The color must switch instantly between the YAML-defined edit_mode_color and play_mode_color when the user toggles the simulation state.

Drawing Order: Refactor the main loop in main.py so the background is drawn first, followed by physics entities, then the mode indicator border.

Asset Generation: If assets/images/bg.png does not exist, please generate a simple 800x600 placeholder image (e.g., a dark blue gradient or a grid pattern) and save it to that path so we can verify the loading logic immediately.

Final Action & Quality Assurance:

Run the game to ensure the background displays and the border color changes with the spacebar toggle.

Lead Developer Validation: Confirm that the system is ready for me to perform the "Manual Test Script" defined in the M7 Specification (specifically testing the YAML fallback by renaming the image file).