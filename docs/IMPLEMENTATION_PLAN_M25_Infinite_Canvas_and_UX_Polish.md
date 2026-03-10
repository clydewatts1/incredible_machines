# Implementation Plan: Milestone 25 - The Infinite Canvas & UX Polish

## Overview

This document breaks down the Milestone 25 specification into six sequential implementation phases. Each phase is a coherent unit of work that can be developed, tested, and verified independently before moving to the next phase.

The architecture strictly adheres to the separation of concerns defined in Constitution Sections 13-16:
- **Main Thread**: Owns all Pymunk physics mutations, Pygame rendering, and input events.
- **Camera System**: Manages viewport offset calculations for coordinate translation.
- **Render Layers**: Separated into background/grid (camera offset), world entities (camera offset), and UI (NO camera offset).

---

## Phase 1: The 2D Camera System

**Objective**: Create a Camera class that manages viewport positioning and coordinate translation.

**Files to Create**:
- `utils/camera.py`

**Files to Modify**: None

**Detailed Tasks**:

1. **Create the Camera class** with the following properties and methods:
   - Properties: `offset_x` (float), `offset_y` (float) — tracks camera position in world space
   - Method: `world_to_screen(world_x, world_y)` → returns `(world_x - offset_x, world_y - offset_y)`
   - Method: `screen_to_world(screen_x, screen_y)` → returns `(screen_x + offset_x, screen_y + offset_y)`
   - Method: `pan(dx, dy)` → adjusts `offset_x` and `offset_y` by the given deltas
   - Method: `clamp_offset(world_width, world_height, screen_width, screen_height)` → prevents camera from panning beyond world boundaries

2. **Implement panning input handling**:
   - Add internal state tracking for Middle Mouse Button (MMB) drag state: `is_panning` (bool), `pan_start_x`, `pan_start_y`
   - Add methods to detect MMB press, MMB release, and mouse movement during pan
   - Alternatively, provide helper methods that the main game loop can call to handle panning input

3. **Implement keyboard-based camera panning**:
   - Add methods to handle WASD / Arrow Key inputs (e.g., `handle_pan_input(key_pressed_dict)`)
   - Pan at a fixed speed per frame (e.g., 200 pixels/second)

4. **Add boundary validation**:
   - Store world dimensions and screen dimensions as instance variables
   - Ensure `offset_x` and `offset_y` never go negative (camera can't pan to negative world space)
   - Ensure camera doesn't pan beyond the far edge of the world (offset cannot exceed `world_width - screen_width`)

**Testing / Acceptance Criteria**:
- [ ] Create a Camera instance with a 5000x5000 world and 1200x800 screen
- [ ] Verify `world_to_screen(2500, 2500)` returns `(2500 - offset_x, 2500 - offset_y)` based on current offset
- [ ] Verify `screen_to_world(600, 400)` (screen center) returns the correct world coordinate
- [ ] Simulate MMB drag by calling pan() and verify offset changes correctly
- [ ] Verify boundary clamping prevents offset from going negative or exceeding max bounds

---

## Phase 2: World Boundaries & Render Separation

**Objective**: Expand the Pymunk physics world boundaries, then refactor the main render loop to separate entities into camera-dependent and camera-independent layers.

**Files to Modify**:
- `main.py` (Pymunk space initialization, draw loop)

**Detailed Tasks**:

1. **Expand Pymunk static boundaries**:
   - Locate the code in `main()` that creates the static floor and walls (typically `pymunk.Body` with `pymunk.Segments`)
   - Increase the world size from the current screen dimensions (e.g., 1200x800) to a massive size (e.g., 5000x5000)
   - Update floor y-position, ceiling y-position, left wall x-position, and right wall x-position to match the new world size
   - Store world dimensions as constants (e.g., `WORLD_WIDTH = 5000`, `WORLD_HEIGHT = 5000`)

2. **Create the Camera instance**:
   - Instantiate a Camera object in `main()` with the world and screen dimensions
   - Store it as a global or pass it through the game loop as needed

3. **Refactor the draw loop into three distinct layers**:
   - **Layer 1 - Background & Grid** (camera offset):
     - Draw the background image/color using camera-adjusted coordinates
     - Draw the grid overlay (implemented in Phase 4)
   
   - **Layer 2 - World Entities** (camera offset):
     - For each entity in `entities`:
       - Calculate the entity's body position in world space
       - Convert to screen space via `camera.world_to_screen()`
       - Blit the entity's sprite at the screen-space coordinates
       - For sensors/connectors, apply the same offset transformation
   
   - **Layer 3 - UI Layer** (NO camera offset):
     - Call the UIManager to render all UI panels, buttons, and text
     - These must be rendered using ABSOLUTE screen coordinates (no camera transform)

4. **Verify the layer separation contains no cross-contamination**:
   - Ensure Layer 1 draws are fully resolved before Layer 2 starts
   - Ensure Layer 2 (entity transforms) happen BEFORE Layer 3 (UI)
   - Document the render order clearly in comments

**Testing / Acceptance Criteria**:
- [ ] Run the game and verify the physics floor/ceiling/walls are at the expanded world coordinates (e.g., 5000x5000)
- [ ] Drop a ball from above and verify it falls and collides with the expanded floor
- [ ] Verify UI panels remain in their original screen positions when the camera is at offset (0, 0)
- [ ] Inspect the rendered output: UI should be crisp and pixel-perfect; entities should render at correct offsets if camera is panned

---

## Phase 3: Coordinate Translation for Interactions

**Objective**: Update all interaction event handlers (mouse clicks, dragging, placement) to use `screen_to_world()` so objects can be accurately targeted regardless of camera pan.

**Files to Modify**:
- `main.py` (event loop, mouse handlers, placement logic)

**Detailed Tasks**:

1. **Update mouse event handling**:
   - Locate the `pygame.MOUSEBUTTONDOWN` event handler
   - When the user clicks, convert `event.pos` (screen space) to world space via `camera.screen_to_world(event.pos[0], event.pos[1])`
   - Use the world-space coordinates for all physics raycasts and entity hover detection

2. **Update object dragging logic**:
   - When dragging an entity, track the initial click position in world space (not screen space)
   - As the mouse moves, convert the new mouse position to world space via `camera.screen_to_world()`
   - Calculate the delta in world space and apply it to the entity's body position
   - Dragging should feel natural regardless of where the camera is panned

3. **Update object placement logic**:
   - When placing a new object from the Right Panel inventory, convert the target screen coordinate to world space
   - Use the world-space position to create the entity's Pymunk body and GamePart instance
   - If grid snapping is enabled (Phase 4), snap the world-space coordinates before placing

4. **Update raycast / collision detection**:
   - For any hoverover checks (identifying which entity the cursor is over), perform raycasts in world space
   - Ensure the raycast origin is computed from the camera-adjusted mouse position

**Testing / Acceptance Criteria**:
- [ ] Pan the camera to offset (1000, 500)
- [ ] Click on an entity in the viewport; verify it is selected/highlighted correctly (not a different entity off-screen)
- [ ] Click and drag that entity; verify it moves in world space correctly, not jumps to an unexpected location
- [ ] Place a new entity via the Right Panel while the camera is panned; verify it appears at the correct world location
- [ ] Un-pan the camera (reset offset to 0,0); verify all entities are in their expected positions

---

## Phase 4: Grid Snapping Overlay

**Objective**: Add a visual grid background (in EDIT mode) and implement optional grid snapping for precise placement and alignment.

**Files to Modify**:
- `main.py` (draw loop, placement logic, event handling)
- `constants.py` (grid configuration)

**Detailed Tasks**:

1. **Add grid configuration constants** (in `constants.py`):
   - `GRID_SIZE` (int, e.g., 40 pixels) — the size of each grid cell
   - `GRID_COLOR` (RGB tuple, e.g., (100, 100, 100)) — the grid line color
   - `GRID_ALPHA` (int, e.g., 50) — transparency level (0-255, lower = more transparent)
   - `SNAP_TO_GRID_ENABLED` (bool) — toggle for snap behavior (can also be toggled via UI button in Phase 5)

2. **Implement grid drawing in the render loop**:
   - In the Layer 1 (Background & Grid) section of the draw loop, after drawing the background:
     - Calculate the camera-adjusted grid origin: `grid_origin_x = -(camera.offset_x % GRID_SIZE)`, `grid_origin_y = -(camera.offset_y % GRID_SIZE)`
     - Draw vertical lines at intervals of `GRID_SIZE` across the screen, starting from `grid_origin_x`
     - Draw horizontal lines at intervals of `GRID_SIZE` across the screen, starting from `grid_origin_y`
     - Use `pygame.draw.line` with color `GRID_COLOR` and a custom per-line alpha if Pygame supports it (or create a semi-transparent grid surface)
   - Only draw the grid when `game_mode == "EDIT"`

3. **Implement grid snapping logic**:
   - In the object placement step (Phase 3), after converting screen-to-world but before creating the entity:
     - If `SNAP_TO_GRID_ENABLED` is True:
       - Snap the world-space x-coordinate: `snapped_x = round(world_x / GRID_SIZE) * GRID_SIZE`
       - Snap the world-space y-coordinate: `snapped_y = round(world_y / GRID_SIZE) * GRID_SIZE`
       - Use `snapped_x, snapped_y` to place the entity
     - Otherwise, place the entity at the exact world-space coordinates

4. **Add a grid snap toggle button** (in Phase 5):
   - This will be a small button in the Top Panel or Left Panel
   - When clicked, toggle `SNAP_TO_GRID_ENABLED`
   - Update the button's visual state (e.g., highlight or color change) to reflect the toggle state

**Testing / Acceptance Criteria**:
- [ ] Run the game in EDIT mode and verify a faint grid appears across the viewport
- [ ] Pan the camera; verify the grid pans WITH the camera (grid lines remain aligned to the world grid)
- [ ] Enable "Snap to Grid" toggle
- [ ] Place an entity at an arbitrary screen coordinate; verify it snaps to the nearest grid intersection
- [ ] Place another entity at adjacent grid cells; verify precise alignment
- [ ] Disable "Snap to Grid" and place an entity at the same screen coordinate; verify it places at the exact screen-world coordinate (not snapped)

---

## Phase 5: Inventory Categories & UI Transparency

**Objective**: Add category metadata to entities, generate dynamic category filter tabs, and apply alpha-blending to UI panels.

**Files to Modify**:
- `config/entities.yaml` (add `category` field to all variants)
- `main.py` (initialize category tabs, handle tab click events)
- `utils/ui_manager.py` (apply `set_alpha()` to panel surfaces)

**Detailed Tasks**:

1. **Update entities.yaml with categories**:
   - Add a `category` string field to every entity variant definition
   - Suggested categories:
     - `"blocks"` — static blocks, ramps, platforms
     - `"active"` — motors, cannons, conveyors, etc.
     - `"logic"` — logic factories, data sources, data sinks
     - `"payload"` — bouncy balls and other physics objects
   - Example: Add `category: "blocks"` under the `bouncy_ball` variant definition

2. **Generate Category Tab Buttons**:
   - In `main()`, after loading `entities.yaml`:
     - Extract the unique `category` values across all entity variants
     - Sort them alphabetically and prepend an `"All"` category
     - Store the category list: `categories = ["All", "active", "blocks", "logic", "payload"]`
   - Add a horizontal row of toggle buttons above the Right Panel's UIScrollPanel:
     - Each button displays the category name
     - One button is always "active" (highlighted color)
     - Buttons should be small (e.g., 60px wide) and arranged in a left-to-right row
     - Add click handlers to each button

3. **Implement Category Filtering Logic**:
   - When a category tab is clicked:
     - If "All" is selected, populate the Right Panel with ALL entity variants
     - Otherwise, filter the entity list to only variants matching the selected category
     - Clear the UIScrollPanel and re-populate it with the filtered entity buttons
   - Keep track of the currently selected category in a variable (e.g., `active_category`)

4. **Apply Alpha Transparency to UI Panels**:
   - In `utils/ui_manager.py`, locate each UIPanel class (Left, Right, Top, Bottom panels)
   - For each panel's background surface:
     - Create the background surface normally
     - Call `background_surface.set_alpha(220)` to set 220/255 ≈ 86% opacity
     - Blit this semi-transparent surface to the screen
   - This allows the game background and entities to show through the UI panels subtly
   - Ensure UI text/buttons remain fully opaque for readability

5. **Add a "Snap to Grid" Toggle Button** (from Phase 4):
   - Place this toggle button in the Top Panel or Left Panel
   - When clicked, toggle the `SNAP_TO_GRID_ENABLED` constant (or update a corresponding flag)
   - Visually indicate the toggle state (e.g., button color green when enabled, gray when disabled)

**Testing / Acceptance Criteria**:
- [ ] Load the game and verify the Right Panel shows category tabs (All, blocks, active, logic, payload)
- [ ] Click the "blocks" tab; verify the Right Panel now only shows block-type entities
- [ ] Click the "logic" tab; verify it shows logic entities (factories, sources, sinks)
- [ ] Click "All"; verify all entities are visible again
- [ ] Verify the UI panels have the game background visible through them (semi-transparent bleed-through effect)
- [ ] Verify text and buttons in the UI are still legible despite the transparency
- [ ] Click "Snap to Grid" toggle; verify it highlights/changes color to indicate state

---

## Phase 6: Drag-to-Trash UX

**Objective**: Implement a contextual "Trash Can" icon that appears during object dragging and triggers safe deletion when an object is released over it.

**Files to Modify**:
- `main.py` (dragging state tracking, trash detection)
- `utils/ui_manager.py` (render trash can icon)

**Detailed Tasks**:

1. **Define the Trash Can UI Element**:
   - Add a new UIElement subclass or button variant called `UITrashCan`
   - Position it at the bottom center of the screen (e.g., screen center x, 50px from bottom)
   - Visual: A simple trash can icon (can reuse or generate a placeholder sprite)
   - Initially, set `visible = False` (hidden)

2. **Implement Drag State Tracking**:
   - In `main()`, maintain a dragging state variable: `is_dragging = False`, `dragged_entity = None`
   - When the user clicks an entity in EDIT mode:
     - Set `is_dragging = True`
     - Store the entity reference in `dragged_entity`
     - Show the Trash Can icon: `trash_can.visible = True`
   - When the user releases the mouse button:
     - Set `is_dragging = False`
     - Hide the Trash Can icon: `trash_can.visible = False`

3. **Implement Trash Overlap Detection**:
   - During dragging, after each mouse move:
     - Get the current mouse position in screen space: `mouse_x, mouse_y = pygame.mouse.get_pos()`
     - Check if the mouse position overlaps the Trash Can's UI bounding box
     - Update a flag: `cursor_over_trash = trash_can.rect.collidepoint(mouse_x, mouse_y)`
     - Optional: Change the Trash Can's visual appearance (e.g., highlight/glow) when the cursor hovers over it

4. **Implement Safe Deletion on Release**:
   - When the user releases the mouse button (MOUSEBUTTONUP):
     - If `cursor_over_trash` is True and `dragged_entity` is not None:
       - Call the entity's `cleanup()` method if it exists (from M11/M13 safe deletion)
       - Remove the entity from `entities` list
       - Remove the entity from `active_instances` dict
       - Remove the entity's body and shapes from the Pymunk space
     - If `cursor_over_trash` is False:
       - Finalize the drag by updating the entity's position to the final world-space coordinates

5. **Visual Feedback During Drag**:
   - Optional: Enhance the UX by:
     - Semi-highlighting the dragged entity (e.g., increased alpha or color tint)
     - Showing a "ghost" or trail of the entity being dragged
     - Playing a subtle sound effect when the cursor enters/exits the Trash Can area

**Testing / Acceptance Criteria**:
- [ ] Click and drag an entity in EDIT mode; verify the Trash Can appears at the bottom center
- [ ] While dragging, move the cursor over the Trash Can; verify it highlights/changes appearance
- [ ] Drag an entity over the Trash Can and release; verify the entity is safely deleted (removed from space, entities list, active_instances)
- [ ] Drag an entity away from the Trash Can and release; verify it stays in the world at the final position
- [ ] Verify deleted entities do not reappear if the game simulation continues (no ghost bodies or phantom physics)
- [ ] Verify the Trash Can icon disappears immediately after release

---

## Design Constraints & Dependencies

**Constitutional Adherence**:
- All Pymunk mutations (deletion, placement, movement) occur exclusively on the main Pygame thread
- Background threads (if any) only perform I/O and do not access Pymunk space or Entity state
- The Camera system is purely a rendering/event-translation utility; it does not hold game state

**Layer Separation**:
- Render Layer 1 (Background & Grid): Camera offset applied
- Render Layer 2 (Entities): Camera offset applied via `world_to_screen()`
- Render Layer 3 (UI): NO camera offset; absolute screen coordinates

**Coordinate Systems**:
- World Space: Pymunk physics coordinates (unbounded, ~5000x5000)
- Screen Space: Pygame display coordinates (1200x800)
- Camera Offset: Maps world → screen via subtraction

---

## Implementation Order & Milestone Completion

Implement in phase order: **1 → 2 → 3 → 4 → 5 → 6**

Each phase is gated by the previous phase's acceptance criteria. Upon completion of all six phases:

- ✅ The game supports an infinite canvas (5000x5000 or larger)
- ✅ The camera can be panned via Middle Mouse Button or WASD/Arrow Keys
- ✅ All interactions (clicking, dragging, placing) work accurately regardless of camera position
- ✅ A visual grid overlay guides precise placement
- ✅ Grid snapping is optional and togglable
- ✅ Inventory is organized by categories for easier navigation
- ✅ UI panels have a polished, semi-transparent appearance
- ✅ Drag-to-Trash provides an intuitive, satisfying deletion mechanic

**Milestone M25 is complete** when all acceptance criteria are verified and the game is playable with all features integrated.

---

## Rollback & Debugging Guide

- **Grid not rendering**: Verify `GRID_SIZE`, `GRID_COLOR`, `GRID_ALPHA` constants are set. Check that the grid drawing code is in Layer 1 (before entities) and only active in EDIT mode.
- **Camera panning is jerky**: Verify that pan speed (pixels/frame) is proportional to frame delta time, not frame count.
- **Objects appear in wrong location when placed**: Debug the `screen_to_world()` conversion. Print the screen/world coordinates before and after conversion.
- **UI elements move when camera pans**: Ensure UI rendering happens in Layer 3 with NO camera offset. Check that all UIManager drawing uses absolute screen coordinates.
- **Dragging feels slow or offset**: Verify the dragging delta is computed in world space, and the final position accounts for any grid snapping.
- **Trash Can never triggers deletion**: Check the collision rect of the Trash Can icon against the current mouse position. Verify the deletion logic runs only when `cursor_over_trash` is True.
