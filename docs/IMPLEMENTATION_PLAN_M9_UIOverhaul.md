# Implementation Plan: Milestone 9 - UI Overhaul & Interaction Systems

## Overview
This document outlines the step-by-step implementation plan for transitioning "Incredible Machines" to a structured graphical user interface (GUI), based on the specifications in `docs/SPECIFICATION_M9_UIOverhaul.md` and the architectural rules in Section 11 of `docs/CONSTITUTION.md`. 

## Implementation Phases

### Phase 1: The Core UI Manager
**Goal:** Establish the foundational UI framework without external dependencies.
**Target Files:** `utils/ui_manager.py` (New File)
- Create `utils/ui_manager.py`.
- Implement `UIElement` base class.
- Implement `UIPanel` class (inheriting from `UIElement`) for background areas (Top Bar, Side Panels, Bottom Bar). Include a `draw` method using `pygame.draw.rect`.
- Implement `UIButton` class (inheriting from `UIElement`) for interactive buttons. It must store a `pygame.Rect`, handle hover states, render text and icons (supporting small, uniform squares with the icon centered and text rendered directly below the icon), and execute a callback function when clicked.
- Implement `UILabel` class for rendering text (e.g., Score, Timer).
- Implement `UIManager` class to manage a collection of `UIElement`s, with `update()`, `draw(surface)`, and `handle_event(event)` methods. `handle_event` should return True if the event is consumed by the UI.
**Testing/Acceptance:** Initialize an empty `UIManager` in a test script or temporarily in `main.py` and verify it can draw a simple panel and a button that prints to the console when clicked.

### Phase 2: Physics Boundaries & Playable Area
**Goal:** Restrict the physics simulation to the new visual boundaries so objects don't overlap with the UI.
**Target Files:** `main.py` (and any related setup logic)
- Calculate the `playable_rect` (e.g., `pygame.Rect(100, 50, screen_width - 200, screen_height - 90)` assuming 100px side panels, 50px top bar, 40px bottom bar).
- Modify the Pymunk static body segments (floor, ceiling, walls) initialization in `main.py` (or the specific layout function) to align with the inner edges of the `playable_rect` instead of `(0, 0)` and `(screen_width, screen_height)`.
**Testing/Acceptance:** Spawn a physics object and verify it bounces off the new invisible boundaries defined by the inset `playable_rect`, leaving empty space for the upcoming UI panels.

### Phase 3: Static Layout & Top/Bottom Bars
**Goal:** Instantiate the main UI panels and top/bottom bar static buttons.
**Target Files:** `main.py`
- Import `UIManager`, `UIPanel`, `UIButton`, `UILabel` into `main.py`.
- Instantiate the `UIManager`.
- Create the layout panels: Top Bar, Bottom Bar, Left Panel, Right Panel using `UIPanel`.
- Add placeholder buttons to the Top Bar: "Play", "Edit", "Save", "Load", "Challenges", "Help". Provide them with dummy callback functions that simply `print("Not Implemented: [Feature]")` to the console.
- Add text labels to the Bottom Bar for Score and Timer placeholders.
- Integrate the `UIManager.draw(screen)` call into the main render loop.
**Testing/Acceptance:** Verify the screen visually contains the top, bottom, and side panels. Verify that clicking the 'Save' button prints to the console without spawning an object.

### Phase 4: Dynamic Palettes & Event Filtering
**Goal:** Populate the side panels using data from entities config and intercept UI clicks to prevent game world interactions.
**Target Files:** `main.py`, `utils/ui_manager.py` (for any icon rendering helpers)
- In `main.py`'s event loop (e.g., `pygame.MOUSEBUTTONDOWN`), pass the event to `UIManager.handle_event()`. Wait to process physics/spawning logic ONLY IF the UI did not consume the event.
- Load `config/entities.yaml`.
- Iterate through available entity variants. For each variant:
  - Create a temporary `pygame.Surface` with `pygame.SRCALPHA`.
  - Instantiate the entity (temporarily) and correctly utilize its underlying geometric template (e.g., Square, Diamond, Half-Circle from `utils/geometry_utils.py`) to draw itself onto the surface. This ensures the icon perfectly visually matches the physics shape spawned in the world.
  - Create a `UIButton` on a Side Panel using this surface as the icon.
  - Set the button's callback to change the `active_tool` state in `main.py` to this entity type.
**Testing/Acceptance:** Verify the side panels display graphical icons for each entity variant defined in the YAML. Verify that clicking these buttons in the side bar does NOT spawn an object in the world, and clicking the world space does NOT trigger any UI actions.

### Phase 5: State Integration & Ghost Cursor
**Goal:** Provide visual feedback for the selected tool during EDIT mode.
**Target Files:** `main.py`
- Implement robust state tracking for `active_tool` (e.g., storing the entity type string or dict).
- In the main render loop, check if the game is in `EDIT` mode and an `active_tool` is currently selected.
- If true, retrieve the mouse position (`pygame.mouse.get_pos()`).
- Check if the mouse position is inside the `playable_rect` using `pygame.Rect.collidepoint()`.
- If inside, render a semi-transparent version (ghost cursor) of the `active_tool`'s sprite or shape at the mouse coordinates to preview placement.
**Testing/Acceptance:** Verify that clicking an icon in the sidebar selects the tool. Verify that moving the mouse into the playable area in EDIT mode shows a transparent preview of the selected part, and clicking actually spawns that specific part at the location.
