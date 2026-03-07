Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 9: UI Overhaul & Interaction Systems. The details of what needs to be built are located in docs/SPECIFICATION_M9_UIOverhaul.md.
The architectural rules for the UI are defined in Section 11 of docs/CONSTITUTION.md.

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M9_UIOverhaul.md. This document must break down the specification into logical, actionable implementation phases.

Requirements for the Implementation Plan:

Sequential Phases: Divide the work into distinct phases that build upon each other so the codebase remains stable. A recommended breakdown:

Phase 1: The Core UI Manager (Creating utils/ui_manager.py with base classes UIElement, UIPanel, UIButton, UILabel).

Phase 2: Physics Boundaries & Playable Area (Modifying main.py to adjust Pymunk static walls inward).

Phase 3: Static Layout & Top/Bottom Bars (Instantiating the UI panels and placeholder buttons in main.py, adding the dummy action handlers).

Phase 4: Dynamic Palettes & Event Filtering (Generating sidebar buttons from entities.yaml, filtering Pygame events through the UIManager before physics).

Phase 5: State Integration & Ghost Cursor (Hooking up active_tool, rendering the transparent hover cursor in EDIT mode).

File Targeting: For every step, explicitly state which file(s) are being modified or created (e.g., utils/ui_manager.py, main.py).

Actionable Details: Mention specific classes, functions, or Pygame/Pymunk methods that need to be utilized (e.g., pygame.Rect, collidepoint, pymunk.Segment).

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that clicking the 'Save' button prints to the console without spawning an object").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL: Do NOT generate the actual Python code. Your job is exclusively to write the plan/task list. The code will be written by the Implementation Agent in the next step.