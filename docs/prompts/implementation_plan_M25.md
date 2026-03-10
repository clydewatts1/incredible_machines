Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 26: The Infinite Canvas & UX Polish. The details of what needs to be built are located in docs/SPECIFICATION_M26_InfiniteCanvas.md.
The architectural rules for UI overlay and physics separation are defined in docs/CONSTITUTION.md.

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M26_InfiniteCanvas.md. This document must break down the specification into logical, actionable implementation phases.

Requirements for the Implementation Plan:

Highly Granular Sequential Phases: Divide the work into distinct, bite-sized phases:

Phase 1: The 2D Camera System (Create utils/camera.py with world_to_screen and screen_to_world methods. Implement panning via Middle Mouse Button or WASD).

Phase 2: World Boundaries & Render Separation (Expand the static Pymunk walls to a massive size like 5000x5000. Update the main draw() loop to apply the camera offset to entities, but NOT to the UI layer).

Phase 3: Coordinate Translation for Interactions (Update the Pygame event loop so mouse clicks, object dragging, and placing use camera.screen_to_world() to accurately target physics objects regardless of camera pan).

Phase 4: Grid Snapping Overlay (Draw a faint background grid offset by the camera. Implement a toggle button and the math to round placement coordinates to the nearest grid_size).

Phase 5: Inventory Categories & UI Transparency (Update entities.yaml with categories, generate the category tab buttons above the Right Panel's scroll grid, and apply set_alpha to UI panel backgrounds for a thematic bleed-through).

Phase 6: Drag-to-Trash UX (Implement the hidden Trash Can icon that appears during dragging and triggers safe deletion upon release).

File Targeting: Explicitly state which file(s) are being modified or created (e.g., utils/camera.py, main.py, utils/ui_manager.py).

Actionable Details: Mention specific Pygame/math constraints (e.g., rounding math for grid snapping, set_alpha for transparency).

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that UI buttons stay firmly in place while the camera pans the physics objects").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the detailed plan/task list.