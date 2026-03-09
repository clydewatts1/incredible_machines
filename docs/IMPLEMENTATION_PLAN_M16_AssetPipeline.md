# Implementation Plan: Milestone 16 - Asset Pipeline & Sprite Management

## Phase 1: Asset Manager & Directory Setup
**Goal:** Establish the foundational asset management system and guarantee the necessary directory structure exists.
**Target Files:** `utils/asset_manager.py` (New), `main.py`
**Actions:**
1. Create `utils/asset_manager.py` housing an `AssetManager` class/singleton.
2. During its `__init__`, use `os.makedirs(..., exist_ok=True)` to ensure `assets/sprites/` and `assets/icons/` exist relative to the project root.
3. Initialize an empty dictionary `self.cache` to store `pygame.Surface` objects keyed by their absolute or relative filepath.
**Verification:** Run the application. Check your local file system to confirm that `assets/sprites/` and `assets/icons/` have been created inside the project directory.

## Phase 2: Auto-Generation Fallback Logic
**Goal:** Implement the core mechanics to catch missing files, generate a placeholder, save it, and load it into the cache.
**Target Files:** `utils/asset_manager.py`
**Actions:**
1. Create a `get_image(path, fallback_size=(50, 50), text_label="X")` method.
2. Check if `path` is in `self.cache`; return it if so.
3. Attempt to load using `pygame.image.load(path).convert_alpha()`.
4. Catch `FileNotFoundError`:
    - Create a new placeholder `pygame.Surface(fallback_size, pygame.SRCALPHA)`.
    - Fill it with a visible fallback color (e.g., `(200, 50, 50, 255)` for a red square).
    - Render a simple `pygame.font.SysFont` label containing the `text_label` onto the center of the standard surface.
    - Save this generated surface to the disk at the missing `path` using `pygame.image.save()`.
    - Add it to `self.cache` and return it.
**Verification:** Through a temporary debug script or Python command line, instantiate the AssetManager and request a nonexistent image. Verify the function returns a surface, and that the specified placeholder `.png` has appeared on your hard drive.

## Phase 3: Entity Rendering Update
**Goal:** Transition the world objects from drawing primitive math geometry to blitting fetched sprite textures synced perfectly with Pymunk body orientations.
**Target Files:** `entities/base.py`
**Actions:**
1. In `GamePart.__init__`, utilize the new `AssetManager` to query an image specifically for this entity type (e.g., `f"assets/sprites/{self.variant_key}.png"`). Store the returned surface as `self.base_texture`.
2. Delete the primitive drawing logic (like `pygame.draw.circle` and `pygame.draw.polygon`) from `draw()`.
3. In `draw()` (or `update_visual()`), leverage `pygame.transform.rotate(self.base_texture, angle_degrees)` using the `self.body.angle` (remembering to negate the angle to sync Pymunk standard math with Pygame's inverted Y-axis).
4. Extract a proper center-aligned `pygame.Rect` from the rotated surface and `surface.blit()` it over `self.body.position`.
**Verification:** Launch the game and spawn various entities. They should all appear as generated placeholder blocks containing their name. Rotating or colliding them should spin the image accurately with the underlying invisible physics hitboxes.

## Phase 4: UI Icon Update
**Goal:** Transition the interface buttons to rely on explicitly loaded, stylized `_button.png` images rather than procedurally drawing entities inside tiny surfaces.
**Target Files:** `main.py`, `utils/ui_manager.py`
**Actions:**
1. In `main.py`'s `build_right_panel()` and equivalent UI generation loops, remove the calls to `create_icon_surface(...)`.
2. Instead, construct a file path for the specific tool (e.g., `f"assets/icons/{variant_key}_button.png"`).
3. Request this path from the `AssetManager`, providing a fallback size of `(60, 60)` and a label of `variant_key`.
4. Pass the returned surface directly into the `UIButton` constructor. Modify `UIButton` if necessary to skip internal text rendering if an `icon_surface` fully covers the button space.
**Verification:** Launch the game. The sidebars should populate with auto-generated placeholder buttons labeled with the names of the tools. Verify that interacting with these tools still successfully spawns the corresponding entities in the world.
