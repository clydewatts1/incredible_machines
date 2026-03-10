# Specification: Milestone 25 - The Infinite Canvas & UX Polish

## 1. Overview

Milestone 25 completely transforms the scale and feel of the game. It breaks the game out of the constraints of a single-screen window by introducing a 2D Camera System, allowing for massive, sprawling Rube Goldberg machines on an expanded canvas.

Simultaneously, this milestone implements major Quality of Life (QoL) and UX improvements, including Grid Snapping for precise mechanical alignment, Category Tabs to organize the growing inventory of parts, and visual polish to soften the UI.

## 2. Goals

- **2D Camera System**: Implement a pannable camera that allows the player to navigate a world much larger than the game window.
- **Screen vs. World Space**: Implement coordinate translation so mouse clicks accurately interact with the physics world regardless of camera position, while UI elements remain fixed to the screen.
- **Expanded World Boundaries**: Expand the Pymunk static boundaries (floor/walls) from the screen edges to define a massive logical world size (e.g., 5000 x 5000 pixels).
- **Grid Snapping Overlay**: Add a visual grid background in EDIT mode and a toggleable "Snap to Grid" mechanic for perfect part alignment.
- **Inventory Category Tabs**: Add filter tabs to the Right Panel (e.g., All, Blocks, Active, Logic) to easily navigate the growing list of entities.
- **Aesthetic Polish**: Introduce alpha-blended (semi-transparent) UI backgrounds and a "Drag to Trash" contextual icon for satisfying object deletion.

## 3. Technical Implementation Details

### 3.1 The 2D Camera System (utils/camera.py)

Create a new Camera class to manage the viewport offset.

**Properties:**
- `offset_x`, `offset_y` (floats tracking the camera's position in the world).

**Panning Controls:**
- Allow the user to pan the camera by holding the Middle Mouse Button and dragging, or by using the WASD / Arrow Keys.

**Coordinate Translation Methods (CRITICAL):**

- `world_to_screen(world_x, world_y)`: Returns `(world_x - offset_x, world_y - offset_y)`. Used by the Pygame render loop to figure out where to draw Pymunk bodies.
- `screen_to_world(screen_x, screen_y)`: Returns `(screen_x + offset_x, screen_y + offset_y)`. Used by the Pygame event loop to figure out what physics object the user actually clicked on.

### 3.2 Main Render Loop Adjustments (main.py)

**Separation of Render Layers:**

- **Background & Grid**: Draw the background image/color and the grid overlay relative to the camera.
- **World Entities**: Iterate through all physics entities. Apply `camera.world_to_screen()` to their Pymunk coordinates before blitting their sprites.
- **UI Layer**: Draw the UIManager elements absolutely last, with NO camera offset applied. They must remain static on the screen.

### 3.3 Grid Snapping & Overlay

**Visual Overlay:**
In EDIT mode, draw a faint grid (e.g., using `pygame.draw.line` with a low alpha color) across the screen, offset by the camera. The `grid_size` should be configurable (e.g., 40 pixels).

**Snap Logic:**
When placing or dragging an object in EDIT mode, if "Snap to Grid" is enabled (via a toggle button in the UI), mathematically round the target `world_x` and `world_y` coordinates to the nearest multiple of `grid_size`.

Formula: `snapped_x = round(world_x / grid_size) * grid_size`

### 3.4 Category Tabs (Inventory Filtering)

**Data-Driven Categories:**
Update `config/entities.yaml` so every entity definition includes a `category` string (e.g., `category: "logic"`, `category: "blocks"`).

**UI Tabs:**
Above the 3-column UIScrollPanel in the Right Panel, generate a horizontal row of small toggle buttons representing the unique categories found in the YAML.

**Filter Logic:**
Clicking a category tab clears the UIScrollPanel and re-populates it only with buttons for entities matching that category.

### 3.5 Drag-to-Trash & Visual Polish

**Thematic Blending:**
Update `utils/ui_manager.py` so UIPanel backgrounds utilize `pygame.Surface.set_alpha()` (e.g., 85% opacity), allowing the game background to subtly bleed through the UI.

**Drag-to-Trash UX:**
- Add a "Trash Can" icon to the bottom center of the screen that is normally hidden.
- When the user clicks and drags an object in EDIT mode, reveal the Trash Can.
- If the user releases the mouse button while the cursor overlaps the Trash Can UI element, trigger the safe deletion flow (from M11/M13) and destroy the object.

## 4. Acceptance Criteria

- [ ] The camera can be smoothly panned around a large physics space using the middle mouse button or keyboard.
- [ ] The UI panels (Left, Right, Top, Bottom) remain completely stationary on the screen while the camera pans.
- [ ] Clicking and dragging objects in EDIT mode works perfectly, regardless of where the camera is currently positioned (proving `screen_to_world` translation is correct).
- [ ] Entities render at the correct visual offsets based on the camera position (proving `world_to_screen` translation is correct).
- [ ] Category tabs successfully filter the Right Panel's 3-column scrollable grid.
- [ ] When Grid Snapping is enabled, objects snap rigidly to intersection points when placed or dragged.
- [ ] Releasing a dragged object over the new Trash Can icon safely deletes it from the Pymunk space and Render list.
