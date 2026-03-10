Role: Specification Design Agent

Context: We are beginning Milestone 25: UI Polish & Scrollable Grid Palettes. We need to overhaul the User Interface layout based on recent feedback. The dual-sidebar object palettes are taking up too much space and becoming cluttered. We need to consolidate the object selection into a single, scrollable 3-column grid on the right, and repurpose the left panel as a dedicated Inspector/Property Editor.

Task: Generate the specification document docs/SPECIFICATION_M25_UIPolish.md.

Requirements for the Specification:

Consolidate Palettes (Right Panel):

Move all dynamically generated object selection buttons exclusively to the Right UI Panel.

Expand the width of the Right Panel (e.g., to 300px or 320px) to comfortably accommodate multiple columns.

Repurpose Inspector (Left Panel):

Clear the Left UI Panel of all object spawning buttons.

Permanently assign the Left Panel to serve as the "Inspector" or "Properties" panel (established in M14). It will only display the Instance Property Editor when an object is actively selected in the canvas.

Refine Playable Area & Boundaries:

Detail how to mathematically recalculate the playable_rect. Its left edge must start exactly at the Right edge of the Left Panel, and its right edge must end exactly at the Left edge of the Right Panel.

Ensure the Pymunk static boundaries (floor, ceiling, left wall, right wall) are automatically repositioned to tightly frame this new central canvas.

Implement UIScrollPanel (utils/ui_manager.py):

Specify a new UI component that inherits from UIPanel or UIElement.

State: Must track content_height and scroll_y.

Input Handling: Must listen for pygame.MOUSEWHEEL events when hovered, updating scroll_y with proper boundary clamping. Click events passed to children must be offset by scroll_y.

Rendering: Detail the use of Pygame's clipping (pygame.Surface.set_clip(self.rect)) to mask buttons that scroll out of bounds, preventing them from overlapping the Top and Bottom bars.

3-Column Grid Algorithm:

Detail the mathematical logic required to arrange the dynamically generated entity buttons into a 3-column grid inside the UIScrollPanel.

Required Math: col = index % 3 and row = index // 3, applying appropriate padding and gap offsets.

Top Bar Regrouping:

Specify that the Top Bar buttons should no longer be uniformly spaced across the entire screen width.

Group them into logical visual clusters using explicit X-coordinate offsets:

Modes: Play, Edit, Clear (Left-aligned).

File Ops: Q.Save, Q.Load, Save, Load (Center-aligned).

Meta: Challenges, Help, Level Settings (Right-aligned).

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.