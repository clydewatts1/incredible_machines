# Implementation Plan: Milestone 26 - The Infinite Canvas & UX Polish

## Overview

This document provides a detailed, phase-by-phase implementation plan for Milestone 26: The Infinite Canvas & UX Polish. The goal is to transform the game from a single-screen experience into an expansive, navigable world with sophisticated UX improvements.

**Core Objectives:**
- Implement a 2D camera system with coordinate translation
- Expand the physics world to 5000x5000 pixels
- Maintain strict UI layer separation (frozen on screen while world pans)
- Add grid snapping for precise mechanical alignment
- Implement category-based inventory filtering
- Polish the UI with transparency and drag-to-trash deletion

**Constitutional Compliance:**
- **Section 11 (UI Standards)**: UI elements MUST render last with NO camera offset applied
- **Section 13 (Thread Safety)**: All Pymunk mutations remain on the main thread
- **Coordinate Translation**: Strict separation between screen space (UI) and world space (physics)

---

## Phase 1: The 2D Camera System

**Objective**: Create a foundational camera system that tracks viewport position and provides coordinate translation utilities.

**Files to Create**:
- `utils/camera.py` (new file)

**Files to Modify**:
- `constants.py` (add camera-related constants)

**Detailed Tasks**:

1. **Define Camera Constants**:
   - Add `CAMERA_PAN_SPEED = 300.0` to `constants.py` (pixels per second for keyboard panning)
   - Add `WORLD_WIDTH = 5000` and `WORLD_HEIGHT = 5000` to define the expanded physics space

2. **Create the Camera Class**:
   - Create `utils/camera.py` with a Camera class
   - **Properties**:
     - `offset_x: float` - Camera's X position in world coordinates
     - `offset_y: float` - Camera's Y position in world coordinates
     - `world_width: int` - Total width of the physics world
     - `world_height: int` - Total height of the physics world
     - `screen_width: int` - Width of the visible screen
     - `screen_height: int` - Height of the visible screen
     - `is_panning: bool` - Flag tracking if middle mouse button is dragging
     - `pan_start_x, pan_start_y: int` - Mouse position when panning started
     - `pan_start_offset_x, pan_start_offset_y: float` - Camera offset when panning started

3. **Implement Coordinate Translation Methods (CRITICAL)**:
   - `world_to_screen(world_x: float, world_y: float) -> Tuple[float, float]`:
     - Formula: `return (world_x - self.offset_x, world_y - self.offset_y)`
     - Used by the rendering loop to convert Pymunk body positions to screen pixels
   - `screen_to_world(screen_x: float, screen_y: float) -> Tuple[float, float]`:
     - Formula: `return (screen_x + self.offset_x, screen_y + self.offset_y)`
     - Used by the event loop to determine which physics object the user clicked

4. **Implement Panning Methods**:
   - `pan(dx: float, dy: float)`:
     - Adjust `offset_x` and `offset_y` by the delta values
     - Call `_clamp_offset()` to prevent panning beyond world boundaries
   - `begin_pan(mouse_x: int, mouse_y: int)`:
     - Store current mouse position and camera offset
     - Set `is_panning = True`
   - `update_pan(mouse_x: int, mouse_y: int)`:
     - Calculate delta from `pan_start_x/y` to current mouse position
     - Update camera offset based on delta
     - Call `_clamp_offset()`
   - `end_pan()`:
     - Set `is_panning = False`

5. **Implement Keyboard Panning**:
   - `handle_keyboard_pan(keys, dt: float)`:
     - Check for WASD or Arrow Key presses
     - Calculate movement based on `CAMERA_PAN_SPEED * dt`
     - Call `pan()` with calculated delta
     - Call `_clamp_offset()`

6. **Implement Boundary Clamping**:
   - `_clamp_offset()`:
     - Ensure `offset_x` stays within `[0, max(0, world_width - screen_width)]`
     - Ensure `offset_y` stays within `[0, max(0, world_height - screen_height)]`
     - Prevents the camera from showing areas outside the defined world boundaries

**Acceptance Criteria**:
- Camera class instantiates without errors
- `world_to_screen()` and `screen_to_world()` return mathematically correct inverse transforms
- Camera offset can be modified via `pan()` method
- Offset clamps correctly at world boundaries

**Manual Verification**:
- Create a test script that instantiates a Camera and verifies:
  - `screen_to_world(world_to_screen(x, y)) == (x, y)` (inverse operation)
  - Clamping prevents offset from going negative or beyond world bounds

---

## Phase 2: World Boundaries & Render Separation

**Objective**: Expand the Pymunk physics world to 5000x5000 and restructure the main render loop into three distinct layers with selective camera offset application.

**Files to Modify**:
- `main.py` (render loop restructuring, boundary creation)
- `constants.py` (world dimension constants)

**Detailed Tasks**:

1. **Expand Physics World Boundaries**:
   - Locate the `create_boundaries()` function in `main.py`
   - Replace screen dimension references (`WINDOW_WIDTH`, `WINDOW_HEIGHT`) with `WORLD_WIDTH` and `WORLD_HEIGHT`
   - The static Pymunk walls (floor, ceiling, left, right) should now define a 5000x5000 pixel arena
   - **Critical**: These boundaries are invisible; they exist only in physics space

2. **Instantiate the Camera**:
   - Import the Camera class: `from utils.camera import Camera`
   - In `main()`, after screen initialization, create:
     ```python
     camera = Camera(
         world_width=constants.WORLD_WIDTH,
         world_height=constants.WORLD_HEIGHT,
         screen_width=constants.WINDOW_WIDTH,
         screen_height=constants.WINDOW_HEIGHT
     )
     ```

3. **Refactor the Render Loop into 3 Layers**:
   - **Layer 1: Background & Grid** (camera offset applied)
     - Clear the screen with background color
     - Draw background image/texture (if any) offset by camera position
     - Reserve space for grid overlay (implementation comes in Phase 4)
   
   - **Layer 2: World Entities** (camera offset applied)
     - Iterate through all `entities` and `active_instances`
     - For each entity, call its `draw(surface, camera)` method
     - Pass the `camera` object as a parameter
     - **Entity rendering responsibility**: Each entity must internally call `camera.world_to_screen()` to convert its Pymunk body position to screen coordinates before blitting sprites
   
   - **Layer 3: UI Overlay** (NO camera offset - absolute screen coordinates)
     - Draw the mode indicator border around the playable area
     - Call `ui_manager.draw(screen)`
     - **Constitutional Mandate**: UI elements MUST use absolute screen coordinates; they remain frozen on screen while the world pans beneath them

4. **Update Entity Draw Methods (Preparation)**:
   - All entity classes (`entities/base.py`, `entities/ball.py`, `entities/ramp.py`, etc.) must accept an optional `camera` parameter in their `draw()` methods
   - If `camera` is provided, use `camera.world_to_screen(body.position.x, body.position.y)` to get the screen position
   - If `camera` is None (backward compatibility), use the raw body position directly

**Acceptance Criteria**:
- The physics world boundaries expand to 5000x5000
- The main render loop has three distinct, commented sections
- Camera object instantiates successfully
- Entities can access the camera object during rendering (even if not yet using it)

**Manual Verification**:
- Run the game and verify it starts without crashes
- Observe that objects still render (even if camera isn't panning yet)
- Use print statements to confirm `create_boundaries()` is creating walls at 5000x5000 dimensions

---

## Phase 3: Coordinate Translation for Interactions

**Objective**: Update all mouse interaction code to use `camera.screen_to_world()` so clicking, dragging, placing, and rotating objects works accurately regardless of camera position.

**Files to Modify**:
- `main.py` (event loop: MOUSEBUTTONDOWN, MOUSEMOTION, MOUSEWHEEL)
- `entities/base.py` (entity draw methods to use camera offset)
- `entities/ball.py`, `entities/ramp.py`, etc. (camera-aware rendering)

**Detailed Tasks**:

1. **Update Mouse Click Handler (MOUSEBUTTONDOWN, button 1)**:
   - When the user left-clicks, capture `event.pos` (screen coordinates)
   - Convert to world coordinates: `world_click_pos = camera.screen_to_world(event.pos[0], event.pos[1])`
   - Use `world_click_pos` for:
     - Pymunk point queries: `space.point_query_nearest(world_click_pos, ...)`
     - Object spawning: `create_part(space, world_click_pos[0], world_click_pos[1], variant_key)`
   - **Critical**: This ensures clicks target the correct physics object even when the camera is panned away from the origin

2. **Update Mouse Drag Handler (MOUSEMOTION)**:
   - When `grabbed_body` is not None (user is dragging an object):
     - Convert `event.pos` to world coordinates: `world_drag_pos = camera.screen_to_world(event.pos[0], event.pos[1])`
     - Set `grabbed_body.position = world_drag_pos`
     - Reset velocity: `grabbed_body.velocity = (0, 0)` and `grabbed_body.angular_velocity = 0`
     - Call `space.reindex_shapes_for_body(grabbed_body)` to update spatial hash

3. **Update Mouse Wheel Handler (MOUSEWHEEL for rotation)**:
   - When detecting the object under the mouse cursor for rotation:
     - Convert `pygame.mouse.get_pos()` to world coordinates
     - Use world coordinates for the Pymunk point query
     - Apply rotation to the detected body

4. **Update Right-Click Deletion (MOUSEBUTTONDOWN, button 3)**:
   - Convert `event.pos` to world coordinates
   - Use world coordinates for the Pymunk point query to find the object to delete

5. **Update Hover Detection**:
   - In the main loop, when checking for hover highlights:
     - Convert `pygame.mouse.get_pos()` to world coordinates
     - Use world coordinates for the Pymunk point query

6. **Add Middle Mouse Button Panning**:
   - **MOUSEBUTTONDOWN, button 2** (middle mouse button):
     - Call `camera.begin_pan(event.pos[0], event.pos[1])`
   - **MOUSEBUTTONUP, button 2**:
     - Call `camera.end_pan()`

7. **Add Keyboard Panning**:
   - In the main loop, after the event loop:
     - Get the current key state: `keys = pygame.key.get_pressed()`
     - Calculate delta time: `dt = clock.get_time() / 1000.0`
     - Call `camera.handle_keyboard_pan(keys, dt)`

8. **Update MOUSEMOTION for Camera Panning**:
   - At the top of the MOUSEMOTION handler:
     - Check if `camera.is_panning` is True
     - If yes, call `camera.update_pan(event.pos[0], event.pos[1])`

9. **Update All Entity Draw Methods**:
   - Modify `entities/base.py`:
     - `draw(surface, camera=None)` method
     - If `camera` is not None, convert `self.body.position` to screen coordinates using `camera.world_to_screen()`
     - Use screen coordinates for all `pygame.draw` or `surface.blit()` calls
   - Repeat for all entity subclasses:
     - `entities/ball.py`
     - `entities/ramp.py`
     - `entities/active.py` (FactoryPart, FloatingTextLabel)
     - `entities/source.py`, `entities/sink.py`

**Acceptance Criteria**:
- Clicking on an object selects it correctly, even when the camera is panned far from origin
- Dragging an object updates its position accurately relative to the mouse cursor
- Spawning new objects places them at the correct world position
- Right-clicking deletes the correct object under the cursor
- Middle mouse button panning moves the camera smoothly
- WASD/Arrow keys pan the camera at a constant speed

**Manual Verification**:
- Pan the camera to the far corner of the 5000x5000 world
- Place a new object → it should appear exactly where you clicked
- Drag an object → it should follow the mouse cursor smoothly
- Right-click an object → the correct object should be deleted (not one offset by the camera)
- Verify that the UI buttons remain clickable and don't move when panning

---

## Phase 4: Grid Snapping Overlay

**Objective**: Render a faint visual grid in EDIT mode and implement toggleable grid snapping for precise mechanical alignment.

**Files to Modify**:
- `main.py` (grid rendering, snap logic, toggle button)
- `constants.py` (grid constants)

**Detailed Tasks**:

1. **Define Grid Constants**:
   - Add to `constants.py`:
     - `GRID_SIZE = 40` (pixels between grid lines)
     - `GRID_COLOR = (100, 100, 100)` (gray)
     - `GRID_ALPHA = 50` (low opacity for subtle visibility)

2. **Add Grid Toggle to Game State**:
   - In `main()`, update the `game_state` dictionary:
     - `"snap_to_grid": False` (default off)
     - `"show_grid": True` (default visible in EDIT mode)

3. **Implement Grid Rendering (Layer 1)**:
   - In the main render loop, in Layer 1 (after background, before entities):
   - Check if `current_mode == "EDIT"` and `game_state["show_grid"]` is True
   - Create a semi-transparent surface:
     ```python
     grid_surface = pygame.Surface((screen_width, screen_height))
     grid_surface.set_alpha(GRID_ALPHA)
     ```
   - Calculate the starting position for grid lines based on camera offset:
     - `start_x = -(camera.offset_x % GRID_SIZE)`
     - `start_y = -(camera.offset_y % GRID_SIZE)`
   - Draw vertical lines:
     - Loop from `start_x` to `screen_width` with step `GRID_SIZE`
     - Draw line from `(x, 0)` to `(x, screen_height)` in `GRID_COLOR`
   - Draw horizontal lines:
     - Loop from `start_y` to `screen_height` with step `GRID_SIZE`
     - Draw line from `(0, y)` to `(screen_width, y)` in `GRID_COLOR`
   - Blit the grid surface to the screen

4. **Create Snap-to-Grid Helper Function**:
   - In `main.py`, before the main loop, define:
     ```python
     def snap_to_grid(x: float, y: float) -> Tuple[float, float]:
         snapped_x = round(x / GRID_SIZE) * GRID_SIZE
         snapped_y = round(y / GRID_SIZE) * GRID_SIZE
         return (snapped_x, snapped_y)
     ```

5. **Apply Snapping on Object Placement**:
   - In the MOUSEBUTTONDOWN handler (left-click):
     - After converting to world coordinates, check if `game_state["snap_to_grid"]` is True
     - If yes, call `snap_to_grid(world_click_pos[0], world_click_pos[1])`
     - Use the snapped coordinates for `create_part()`

6. **Apply Snapping on Object Dragging**:
   - In the MOUSEMOTION handler:
     - After converting to world coordinates, check if `game_state["snap_to_grid"]` is True
     - If yes, call `snap_to_grid(world_drag_pos[0], world_drag_pos[1])`
     - Set `grabbed_body.position` to the snapped coordinates

7. **Add Grid Snap Toggle Button**:
   - In the Top Panel button creation section of `main()`:
     - Define a callback:
       ```python
       def toggle_snap_to_grid():
           game_state["snap_to_grid"] = not game_state.get("snap_to_grid", False)
           # Update button visual to show state (requires rebuilding top panel)
       ```
     - Add a toggle button labeled "Snap: ON" or "Snap: OFF" (or use symbols like "⊞" / "☐")
     - The button text/color should reflect the current state

8. **Implement Top Panel Rebuild on Toggle**:
   - Create a `build_top_panel()` helper function that clears and rebuilds all top panel buttons
   - Call `build_top_panel()` inside `toggle_snap_to_grid()` to update the button appearance

**Acceptance Criteria**:
- Grid overlay renders in EDIT mode as a faint, semi-transparent pattern
- Grid moves correctly with the camera (proving offset calculation is accurate)
- Grid does not render in PLAY mode
- Clicking the snap toggle button switches the state
- When snap is ON, placed objects align to grid intersections
- When snap is ON, dragged objects snap to grid positions
- Button visual updates to reflect the current snap state

**Manual Verification**:
- Enter EDIT mode and pan the camera → grid should scroll smoothly
- Toggle snap ON → place objects → they should align perfectly to grid lines
- Toggle snap OFF → place objects → they should land exactly where you click (no rounding)
- Drag an object with snap ON → it should "magnetize" to grid intersections

---

## Phase 5: Inventory Categories & UI Transparency

**Objective**: Organize the growing entity inventory with category filters and add visual polish with semi-transparent UI panels.

**Files to Modify**:
- `config/entities.yaml` (add category field to all variants)
- `main.py` (category tab generation, filter logic)
- `utils/ui_manager.py` (alpha transparency for UIPanel)

**Detailed Tasks**:

1. **Add Category Field to All Variants in entities.yaml**:
   - Open `config/entities.yaml`
   - For each variant under the `variants:` section, add a `category: "..."` field
   - Suggested categories:
     - `"payloads"`: bouncy_ball, data payloads
     - `"blocks"`: long_ramp, diamond, half_circle, quarter_circle, square_block, spring, shoot_block, textured_rectangle
     - `"active"`: cannon, basket, conveyor_belt, motor
     - `"logic"`: logic_factory
     - `"sources"`: data_source, data_source_csv, data_source_mcp
     - `"sinks"`: data_sink, data_sink_csv, data_sink_json, data_sink_yaml, data_sink_mcp
   - Ensure every variant has a category (default to `"other"` if uncertain)

2. **Extract Unique Categories in main()**:
   - After loading `all_variants` from the YAML:
     - Create a set to store unique categories
     - Iterate through `all_variants.items()` and extract the `category` field from each variant
     - Convert the set to a sorted list
     - Prepend `"all"` to the list (to show all entities)
   - Store in a variable: `categories_list = ["all", "active", "blocks", "logic", ...]`

3. **Add Selected Category to Game State**:
   - In the `game_state` dictionary, add:
     - `"selected_category": "all"` (default to showing all entities)

4. **Create Category Tab UI Elements**:
   - Define a list to track category tab buttons: `category_tab_elements = []`
   - Define a function `build_category_tabs()`:
     - Clear any existing category tab elements from `ui_manager.elements`
     - Calculate the position for the tabs (above the Right Panel scroll area)
     - For each category in `categories_list`:
       - Create a small UIButton (e.g., 70x25 pixels)
       - Arrange in a 2-column grid layout
       - Text: `cat.title()` (capitalize the category name)
       - Highlight the selected category with a different background color (e.g., green)
       - Callback: Set `game_state["selected_category"] = category`, rebuild category tabs and right panel
     - Add all buttons to `ui_manager.elements` and `category_tab_elements`

5. **Update build_right_panel() to Filter by Category**:
   - In the `build_right_panel()` function:
     - Retrieve `selected_category = game_state.get("selected_category", "all")`
     - When iterating through `all_variants.items()`:
       - Extract the variant's category: `variant_category = variant_data.get("category", "other")`
       - If `selected_category != "all"` and `variant_category != selected_category`, skip this variant (continue to next iteration)
       - Otherwise, create the entity button as usual
     - Adjust the starting Y position to account for the category tabs (add ~140 pixels offset)

6. **Call build_category_tabs() at Initialization**:
   - In `main()`, after defining `build_category_tabs()`, call it once before the main game loop starts

7. **Implement UI Panel Transparency**:
   - Open `utils/ui_manager.py`
   - Locate the `UIPanel` class
   - Modify `__init__()` to accept an `alpha` parameter (default: 220, which is ~86% opacity)
   - Store `self.alpha = alpha`
   - Modify the `draw()` method:
     - Instead of drawing directly to the surface with `pygame.draw.rect(surface, self.color, self.rect)`
     - Create a temporary surface:
       ```python
       temp_surface = pygame.Surface((self.rect.width, self.rect.height))
       temp_surface.fill(self.color)
       temp_surface.set_alpha(self.alpha)
       surface.blit(temp_surface, (self.rect.x, self.rect.y))
       ```
   - **Result**: UI panels will have a subtle transparency, allowing the game background to bleed through

**Acceptance Criteria**:
- All variants in `entities.yaml` have a `category` field
- Category tabs render above the Right Panel in a 2-column grid
- Clicking a category tab filters the entity list to show only matching entities
- The "All" category shows all entities
- Selected category tab is visually highlighted
- UI panels have a semi-transparent appearance (background slightly visible through them)

**Manual Verification**:
- Click each category tab → verify that only entities from that category appear in the Right Panel
- Click "All" → verify that all entities are shown
- Observe the UI panels → the game background should be faintly visible through the panels
- Pan the camera with entities behind the UI → transparency effect should be subtle but noticeable

---

## Phase 6: Drag-to-Trash UX

**Objective**: Implement a contextual "Trash Can" icon that appears during object dragging and triggers safe deletion when an object is released over it.

**Files to Modify**:
- `main.py` (dragging state tracking, trash detection)
- Optionally: `utils/ui_manager.py` (if creating a UITrashCan element)

**Detailed Tasks**:

1. **Define Trash Can State Variables**:
   - In `main()`, before the main game loop:
     - `trash_can_visible = False` (trash can is hidden by default)
     - `trash_can_rect = pygame.Rect(w // 2 - 40, h - 100, 80, 80)` (bottom center, 80x80 pixels)
     - `cursor_over_trash = False` (flag to track if mouse is hovering over trash)

2. **Show Trash Can When Dragging Starts**:
   - In the MOUSEBUTTONDOWN handler (left-click):
     - When setting `grabbed_body` to a valid physics body:
       - Set `trash_can_visible = True`

3. **Track Cursor Position Over Trash Can**:
   - In the MOUSEMOTION handler:
     - If `trash_can_visible` is True:
       - Check if the mouse cursor overlaps the trash can rect:
         ```python
         cursor_over_trash = trash_can_rect.collidepoint(event.pos[0], event.pos[1])
         ```

4. **Implement Safe Deletion on Release Over Trash**:
   - In the MOUSEBUTTONUP handler (left-click):
     - Check if `grabbed_body` is not None AND `cursor_over_trash` is True
     - If both conditions are met:
       - **Find the entity associated with `grabbed_body`**:
         - Iterate through `entities` to find the entity where `entity.body == grabbed_body`
       - **Trigger Safe Deletion (from M11/M13)**:
         - Call `entity.cleanup()` if the method exists (clears threads, timers, etc.)
         - Remove the entity from `active_instances` dict (if it has a UUID)
         - Remove the entity from the `entities` list
         - Remove any Pymunk constraints attached to the body:
           - Iterate through `entity.body.constraints` and remove from `space.constraints`
         - Remove the body's shapes from the space:
           - `space.remove(*entity.shape.body.shapes)`
         - Remove the body itself from the space (if not static_body):
           - `space.remove(entity.shape.body)`
     - **Always** (whether deletion occurred or not):
       - Set `grabbed_body = None`
       - Set `trash_can_visible = False`

5. **Render the Trash Can Icon (Layer 3)**:
   - In the main render loop, in Layer 3 (after `ui_manager.draw(screen)`):
     - Check if `trash_can_visible` is True AND `current_mode == "EDIT"`
     - If yes:
       - Draw a background rectangle for the trash can:
         - Color: Red `(150, 50, 50)` if `cursor_over_trash` (highlight), else gray `(80, 80, 80)`
         - Draw with rounded corners: `pygame.draw.rect(screen, color, trash_can_rect, border_radius=10)`
       - Draw a border:
         - `pygame.draw.rect(screen, (200, 200, 200), trash_can_rect, 3, border_radius=10)`
       - Draw a trash can icon (simple text emoji or custom sprite):
         - Render a large emoji (e.g., "🗑") or symbol
         - Center it in the `trash_can_rect`

6. **Visual Feedback for Hover State**:
   - When `cursor_over_trash` is True, the trash can background should change to a red/warning color
   - This provides immediate visual feedback that releasing the mouse will delete the object

**Acceptance Criteria**:
- Trash can icon does not appear when nothing is being dragged
- Trash can appears at the bottom center when the user starts dragging an object
- Trash can changes color when the cursor hovers over it
- Releasing a dragged object over the trash can triggers safe deletion
- The deleted object is completely removed from the game (physics space, entities list, active_instances)
- Trash can disappears when the drag operation ends (whether deleted or not)

**Manual Verification**:
- Enter EDIT mode and click-drag an object → trash can should appear at bottom center
- Hover over the trash can while dragging → it should highlight (red warning color)
- Release the object over the trash can → the object should vanish completely
- Release the object elsewhere → the object remains in the world
- Verify no orphaned physics bodies or memory leaks by checking `len(entities)` and `len(space.bodies)`

---

## Integration & Final Testing

After completing all six phases, perform comprehensive integration testing:

1. **Camera System Validation**:
   - Pan the camera to all four corners of the 5000x5000 world
   - Verify that objects render correctly at extreme positions
   - Verify that the UI remains frozen on screen during panning

2. **Interaction Accuracy**:
   - At various camera positions, click, drag, place, rotate, and delete objects
   - Verify that all interactions target the correct world coordinates

3. **Grid Snapping**:
   - Enable snap → place/drag objects → verify perfect grid alignment
   - Disable snap → place/drag objects → verify free-form positioning

4. **Category Filtering**:
   - Click through all category tabs
   - Verify that each category shows the correct subset of entities
   - Verify "All" shows everything

5. **Drag-to-Trash**:
   - Drag multiple types of objects to the trash can
   - Verify safe deletion for static bodies, dynamic bodies, and active entities

6. **Performance Testing**:
   - Create a dense arrangement of 50+ objects across the expanded world
   - Pan the camera rapidly → verify smooth 60 FPS performance
   - Verify no memory leaks or frame drops

7. **Constitutional Compliance Check**:
   - Verify Section 11 compliance: UI layer renders absolutely last with NO camera offset
   - Verify Section 13 compliance: All Pymunk mutations occur on the main thread only
   - Verify coordinate translation is mathematically correct (no off-by-one errors)

---

## Rollback & Debugging Guide

**Common Issues & Solutions**:

- **Grid not rendering**:
  - Verify `GRID_SIZE`, `GRID_COLOR`, `GRID_ALPHA` constants are defined
  - Check that grid drawing code is in Layer 1 (before entities)
  - Ensure grid is only drawn when `current_mode == "EDIT"`

- **Camera panning is jerky**:
  - Verify that `handle_keyboard_pan()` uses `dt` (delta time) for frame-rate independent movement
  - Check that pan speed is scaled by frame delta, not frame count

- **Objects appear in wrong location when placed**:
  - Debug `screen_to_world()` conversion
  - Print both screen coordinates and world coordinates before/after conversion
  - Verify camera offset values are reasonable (not NaN or infinity)

- **UI elements move when camera pans**:
  - Ensure UI rendering happens in Layer 3 with NO camera offset
  - Check that `ui_manager.draw()` uses absolute screen coordinates
  - Verify UIPanel, UIButton positions are not modified by camera offset

- **Dragging feels slow or offset**:
  - Verify dragging delta is computed in world space, not screen space
  - Check that `grabbed_body.position` is set to the snapped/unsnapped world coordinates
  - Ensure `space.reindex_shapes_for_body()` is called after position update

- **Trash Can never triggers deletion**:
  - Check the collision rect of the trash can against mouse position (use screen coordinates, not world)
  - Verify `cursor_over_trash` flag updates correctly in MOUSEMOTION
  - Ensure deletion logic runs only when both `grabbed_body` and `cursor_over_trash` are True

---

## Completion Checklist

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

**Milestone M26 is complete** when all acceptance criteria are verified and the game is playable with all features integrated.
