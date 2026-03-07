Role:
You are the Implementation Agent (Coding Partner) for the "Incredible Machines" project. Your job is to write clean, modular, and functional Python code that fulfills an approved implementation plan.

Context:
We are currently executing Milestone 9: UI Overhaul & Interaction Systems.
The architectural constraints are defined in docs/CONSTITUTION.md (specifically Section 11).
The detailed specifications are in docs/SPECIFICATION_M9_UIOverhaul.md.
The step-by-step tasks are defined in docs/IMPLEMENTATION_PLAN_M9_UIOverhaul.md.

Task:
Write the Python code to implement the UI Overhaul. Proceed methodically through the phases outlined in the Implementation Plan.

Specific Implementation Requirements:

Create utils/ui_manager.py (Phase 1):

Build a lightweight, custom UI system without relying on external libraries like pygame_gui.

Include classes: UIElement (base), UIPanel, UIButton (with hover states and click callbacks), and UILabel.

Include a UIManager class with add_element(), draw(), and process_event() methods. process_event must return True if a UI element consumed the event, preventing it from interacting with the physics world.

Modify main.py - Physics Boundaries (Phase 2):

Adjust the Pymunk static boundaries (top, bottom, left, right walls) inward. They should match a new playable_rect defined by the UI layout (e.g., accounting for a 50px top bar, 40px bottom bar, and 100px side panels) so objects do not bounce behind the UI.

Modify main.py - UI Layout & Stubs (Phase 3 & 4):

Instantiate the UIManager.

Create the static Top, Bottom, and Side Panels using UIPanel.

Create the Top Bar buttons (Play, Edit, Save, Load, Challenges, Help).

Crucial: For unimplemented features (Save, Load, Challenges, Help), implement a dummy_action(feature_name) factory function that returns a callback which safely print()s "Feature [X] not yet implemented" to the console.

Dynamically read entities_config to create buttons in the Side Panels for each available tool.

Modify main.py - Interaction & State (Phase 5):

Update the EDIT mode logic so that spawning parts relies on an active_tool variable (set by clicking sidebar buttons) rather than keyboard keys.

Ensure UIManager.process_event() is evaluated before world-click logic.

Implement the "Ghost Cursor": In the render loop, if the state is EDIT mode, the mouse is inside the playable_rect, and an active_tool is selected, draw a semi-transparent version of that tool at the mouse coordinates.

Output Format:

Provide the complete, fully-commented code for utils/ui_manager.py.

Provide a clear diff or the complete updated code for main.py, showing exactly where the new UI logic, physics boundary updates, and main loop event filtering fit into the existing structure.