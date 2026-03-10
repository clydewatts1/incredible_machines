Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

docs/CONSTITUTION.md (Pay close attention to Section 11 regarding UI separation)

docs/SPECIFICATION_M26_InfiniteCanvas.md

docs/IMPLEMENTATION_PLAN_M26_InfiniteCanvas.md

Task: Implement Milestone 26: The Infinite Canvas & UX Polish. Execute the phased steps exactly as outlined in the implementation plan to break the game out of a single-screen window.

Critical Execution Instructions:

Camera Translation Math (CRITICAL):

Create utils/camera.py.

When rendering Pymunk physics bodies, you MUST translate their coordinates using world_to_screen(world_x, world_y).

When handling Pygame mouse events (clicking, dragging, deleting physics objects), you MUST translate event.pos using screen_to_world(screen_x, screen_y). Failure to do this will cause the player to click on the wrong objects when panned!

Render Layer Separation:

Ensure your Pygame draw() loop strictly isolates the UI. The UI components (UIManager, Left/Right panels, Top/Bottom bars) MUST be rendered absolutely last, and they MUST NOT have the camera offset applied to them.

Expanded Physics World:

Redefine the static Pymunk boundaries (the 4 walls). Instead of mapping them to the screen dimensions, push them out to create a massive logical space (e.g., 5000 x 5000 pixels).

Grid Snapping:

When Grid Snapping is toggled ON, apply rounding math (round(val / grid_size) * grid_size) to the target coordinates whenever an object is placed or released from a drag in EDIT mode.

Category Tabs & Scroll Filtering:

Update config/entities.yaml to assign categories to objects.

Add a row of filter buttons above the Right Panel's 3-column UIScrollPanel. Clicking a tab must rebuild the scrollable grid with only the matched entities.

UI Polish & Drag-to-Trash:

Apply a slight alpha transparency to the UIPanel backgrounds.

Render a Trash Can UI element ONLY when an object is actively being dragged. If the drag is released over the Trash Can's rect, trigger the safe to_delete cascading cleanup flow.