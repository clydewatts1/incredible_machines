# Implementation Plan: Milestone 14 - Instance Property Editing

## Phase 1: UI Proportions & Canvas Expansion
**Goal:** Increase the overall Pygame window base resolution to provide a larger playable canvas and reduce the width of the Left and Right UI panels.
**Target Files:** `main.py`, `constants.py` (if applicable)
**Actions:**
- Update window resolution constants to a larger size (e.g., 1280x720).
- Modify the sidebar width constants (e.g., `UI_SIDE_WIDTH`) in `main.py` to be narrower.
- Scale down the object selector `UIButton` sizes and `create_icon_surface` dimensions to fit the narrower panels.
**Verification:** Launch the game and verify the window covers more screen space while the side panels look slimmer and less intrusive.

## Phase 2: Text Input & Focus Management
**Goal:** Implement robust UI text input components and strict input focus management.
**Target Files:** `utils/ui_manager.py`, `main.py`
**Actions:**
- Create `UITextInput` and `UITextArea` classes in `utils/ui_manager.py` capable of handling character input, backspace, and cursor blinking.
- Update `UIManager` to track the currently `focused_element`.
- In `main.py`'s event loop, route events to `ui_manager` first. If a text field has focus, consume all keyboard events to suspend global hotkeys.
**Verification:** Click a dummy text field, type some text including 'Q', 'E', 'Space', and 'Delete', and verify that no game actions are triggered.

## Phase 3: Inheritance & Draft State Data Structure
**Goal:** Equip instances with the ability to override base properties and securely hold draft edits.
**Target Files:** `entities/base.py`
**Actions:**
- Add an `overrides` dictionary to the `GamePart` initialization.
- Implement a `get_property(key)` method that checks `self.overrides` before safely falling back to the base `self.properties` from `entities.yaml`.
- Refactor existing property accesses (e.g., mass, friction, radius) to route through `get_property`.
- Create an `apply_draft_overrides(new_dict)` method to safely cast incoming strings to numbers and update the actual Pymunk physics properties.
**Verification:** Programmatically inject an override (like extreme mass) into an instance and observe its altered physical behavior in the simulation compared to a standard instance.

## Phase 4: Properties Panel UI Integration
**Goal:** Swap the right-hand object palette to a contextual Property Editor when an instance is selected.
**Target Files:** `main.py`
**Actions:**
- Add click detection logic in EDIT mode. When the user clicks a valid shape, assign its root `GamePart` to `game_state["selected_instance"]`.
- Create a `build_right_panel()` function that dynamically clears the right side UI elements.
- If an instance is selected, iteratively render `UILabel` and `UITextInput`/`UITextArea` components pre-filled with the instance's active `get_property()` values.
- Include "Save" and "Cancel" buttons to execute `apply_draft_overrides` and deselect the instance.
**Verification:** Spawn an object, click it, modify a property in the newly generated right panel, click Save, and observe the immediate change.

## Phase 5: Save/Load Serialization
**Goal:** Persist custom instance properties between sessions.
**Target Files:** `utils/level_manager.py`, `main.py`
**Actions:**
- Modify `LevelManager.save_level()` to query each entity's `overrides` dictionary and append it to the serialized JSON/YAML block.
- Modify `LevelManager.load_level()` to safely unpack the `overrides` dict if it exists.
- In `main.py`'s loading loop, pass the unpacked `overrides` into the newly spawned `GamePart` before it completes physics indexing.
**Verification:** Customize an object's properties, save the level, clear the board, load the level, and verify the object retains its custom properties.
