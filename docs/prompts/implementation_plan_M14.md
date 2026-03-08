Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 14: Instance Property Editing. The details of what needs to be built are located in SPECIFICATION_M14_Properties.md.
The architectural rules for property inheritance and input focus are defined in the updated CONSTITUTION.md (Sections 3 and 11).

Task:
Generate the document IMPLEMENTATION_PLAN_M14_Properties.md. This document must break down the specification into logical, actionable implementation phases.

Requirements for the Implementation Plan:

Sequential Phases: Divide the work into distinct phases that build upon each other so the codebase remains stable. A recommended breakdown:

Phase 1: Text Input & Focus Management (Expanding utils/ui_manager.py with UITextInput and UITextArea, and implementing the global hotkey suspension logic when a text box has focus).

Phase 2: Inheritance & Draft State Data Structure (Updating the base Entity class to handle the overrides dictionary, UUID tracking, and a temporary draft_overrides state for unapplied edits).

Phase 3: Properties Panel UI Integration (Modifying main.py so clicking an object in EDIT mode swaps the Right Panel to a property editor populated with the selected instance's data).

Phase 4: Save/Load Serialization (Updating the Level Manager to accurately serialize and deserialize the UUIDs and custom overrides dictionaries into the level save files).

File Targeting: For every step, explicitly state which file(s) are being modified or created (e.g., utils/ui_manager.py, entities/base.py, main.py, utils/level_manager.py).

Actionable Details: Keep the plan high-level but clearly state the goal of each phase. Leave the granular Python/Pygame algorithms up to the coding agent.

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that typing in a text box does not trigger the 'Spacebar' play/edit toggle").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the plan/task list. The code will be written by the Implementation Agent in the next step.