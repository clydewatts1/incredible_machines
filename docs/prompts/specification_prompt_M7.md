Role: Creative Lead & UI/UX Designer

Context: Please read CONSTITUTION.md (specifically Section 10). We are starting Milestone 7: Background & Aesthetic Enhancements.

Task: Generate Specification
Create a new specification file: docs/SPECIFICATION_M7_BackgroundAesthetics.md.

Requirements for M7:

Environment Config: Create config/environment.yaml to store background settings (image path, fallback background color).

Background Loading: Implement logic to load a background image and scale it to fit the 800x600 window.

State Visualization: Add a simple visual indicator (e.g., a "PAUSED/EDITING" overlay or a color-coded border) that changes depending on whether the game is in Edit Mode or Play Mode.

No Hardcoding: All asset paths and colors must come from the YAML file.

Mandatory Quality Assurance:
Per Section 6, include a "Manual Test Script". The test must verify:

The human can change the background image path in environment.yaml and see the new background on launch.

The human can see a clear visual difference between "Edit Mode" and "Play Mode" beyond just the console output.

The game "Fails Loudly" if the background image file is missing.

Constraint: Do not write code yet. Provide the M7 Specification for my review.