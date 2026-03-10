Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

docs/CONSTITUTION.md (Pay close attention to Section 11 regarding UI layout, input separation, and focus states)

docs/SPECIFICATION_M25_UIPolish.md

docs/IMPLEMENTATION_PLAN_M25_UIPolish.md

Task: Implement Milestone 25: UI Polish & Scrollable Grid Palettes. You will consolidate the object palettes into a 3-column scrollable grid on the right, repurpose the left panel as a dedicated Inspector, and adjust the playable canvas layout. Execute the 5 phased steps exactly as outlined in the implementation plan.

Critical Execution Instructions:

UIScrollPanel Logic (CRITICAL):

Create the UIScrollPanel in utils/ui_manager.py.

Rendering: You MUST use pygame.Surface.set_clip(self.rect) before iterating through and drawing the child elements to ensure buttons don't bleed out of the panel. Remember to reset it with set_clip(None) afterward.

Input Offsets: When handling process_event for mouse clicks or hover states, you must offset the mouse y coordinate by self.scroll_y before passing the event down to the child buttons.

Panel Reallocation & Playable Area:

Stop generating spawnable object buttons for the Left Panel. Ensure the M14 Property Editor components render strictly within the Left Panel when an object is selected.

Expand the Right Panel width to easily fit 3 columns of buttons (e.g., 300px to 320px).

Physics Boundaries: Update the playable_rect math in main.py. The left boundary is LeftPanel.rect.right and the right boundary is RightPanel.rect.left. You MUST update the underlying Pymunk static boundary lines to match this new inner rectangle so physics objects don't fall behind the UI.

3-Column Grid Math:

When dynamically parsing entities_config to build the buttons for the Right Panel, use the following logic to place them:
col = index % 3
row = index // 3

Calculate the x and y offsets using the button width/height and padding, then add the buttons as children to the new UIScrollPanel.

Top Bar Regrouping:

Refactor the placement of the Top Bar buttons. Stop spacing them uniformly across the entire screen width.

Group them visually using explicit x coordinates: Play | Edit | Clear on the far left, File operations (Save, Load) in the center, and Meta actions (Challenges, Settings) on the right.