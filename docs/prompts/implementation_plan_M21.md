Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 21: Canvas Properties & Environments. The details are located in docs/SPECIFICATION_M21_CanvasProperties.md.

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M21_CanvasProperties.md. Break down the specification into logical, actionable implementation phases.

Requirements for the Implementation Plan:

Sequential Phases: Divide the work into distinct phases. A recommended breakdown:

Phase 1: Serialization Updates (Updating utils/level_manager.py to read/write a canvas_settings dictionary to the root of the save files, with sensible defaults).

Phase 2: Physics & Render Integration (Updating main.py to apply the loaded gravity/damping to the pymunk.Space, and drawing the loaded background image/color over the playable_rect).

Phase 3: UI Integration (Adding the "Level Settings" button to the Top Bar and hooking it up to the M14 Properties Panel so users can edit the global values live in EDIT mode).

File Targeting: Explicitly state which file(s) are being modified or created (e.g., main.py, utils/level_manager.py, utils/ui_manager.py).

Actionable Details: Mention caching the loaded background image in the Asset Manager (from M16) so it isn't re-loaded every frame.

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that saving the game creates a canvas_settings block in the YAML file").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the plan/task list.