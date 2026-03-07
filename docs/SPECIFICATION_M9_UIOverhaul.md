# Specification: Milestone 9 - UI Overhaul & Interaction Systems

## Overview
This specification details the technical plan for transitioning "Incredible Machines" from a debug-text overlay to a professional, structured graphical user interface (GUI). Adhering to the project's Architectural Constitution (specifically Section 11), this overhaul implements a custom GUI system that neatly frames the gameplay area while separating UI event handling from physics interactions.

## Goals
- Replace the debug-text overlay with structured UI panels (Top Bar, Bottom Bar, Side Panels).
- Establish a strict `playable_rect` that represents the screen space inside the UI frames.
- Re-align Pymunk static boundaries so physical objects cannot enter the UI space.
- Implement a lightweight, custom UI manager (`utils/ui_manager.py`) without relying on heavy external libraries like `pygame_gui`.
- Provide data-driven dynamic object palettes on the side panels that auto-generate icons from `config/entities.yaml`.
- Ensure robust click filtering so the user cannot accidentally interact with the game world when clicking UI elements.
- Implement visual state feedback, including an active tool selection and a ghost cursor for part placement.

## Technical Implementation Details

### 1. Layout Requirements
- **Top Bar (Operations):** Spans the top of the screen (e.g., 50px high). It will contain functional buttons: Play, Edit, Save, Load, Challenges, and Help.
- **Side Panels (Object Palettes):** Spans the left and right sides of the screen (e.g., 100px wide each). These will be used for selecting parts to place in the world.
- **Bottom Bar (Information):** Spans the bottom of the screen (e.g., 40px high). It will display placeholder text for the current Score and Timer.

### 2. Playable Area & Physics Boundaries
- **`playable_rect` Definition:** The game will calculate a `pygame.Rect` called `playable_rect` which defines the active simulation space, strictly bounded by the inner edges of the Top, Bottom, and Side UI panels.
- **Pymunk Boundary Adjustment:** The Pymunk static boundaries (floor, ceiling, walls) currently aligned to the screen edges must be moved inward to exactly match the `playable_rect`. This guarantees that physics objects cannot spawn, bounce, or fall behind the UI components.

### 3. Lightweight UI Manager
- **Module:** Create a new module at `utils/ui_manager.py`.
- **Class Structure:** Implement a minimal, custom class hierarchy:
  - `UIManager`: Handles the global update and render loops for all UI elements, and routes events.
  - `UIPanel`: Represents a background area (like the Top Bar or Side Panels).
  - `UIButton`: Interactive elements that can render text or icons, respond to mouse clicks, and play distinct 'clunk' sounds based on their UI layer (e.g., top, side, bottom). For object palettes, these must be small, uniform squares (e.g., 60x60 or 80x80 pixels) with the icon centered and the object's label text rendered directly below the icon.
- **Dependencies:** The manager must rely strictly on standard Pygame drawing primitives (rectangles, text rendering, surfaces) and avoid external GUI libraries.

### 4. Dynamic Object Palettes (Data-Driven)
- **Data Integration:** Instead of hardcoded buttons, the side panels will read entity variants directly from `config/entities.yaml` to dynamically populate the available parts list.
- **Auto-Generating Icons:** The UI system will create temporary Pygame `Surface` objects. It will instantiate each entity and use the entity's underlying geometric template (e.g., Square, Diamond, Half-Circle from `utils/geometry_utils.py`) to draw itself onto the temporary surface. The shapes drawn on the UI buttons must perfectly visually match the physics shapes spawned in the game world.

### 5. Interaction & State Feedback
- **Click Filtering:** The main event loop in `main.py` must pass standard event structures to `UIManager` first. If `UIManager` determines the interaction targets a UI element (e.g., a click inside a UI panel), it will claim the click and return a consumed state. The game logic must skip physics/world interactions (spawning/grabbing) for claimed events.
- **Active Tool Selection:** Clicking an object's button in the side panel assigns its corresponding entity type to an `active_tool` state variable managed in `main.py`. This deprecates keyboard shortcut reliance for part selection.
- **Ghost Cursor:** During `EDIT` mode, when an `active_tool` is set, a semi-transparent representation of the tool must be rendered at the current mouse coordinates, but only if the mouse is hovering over the `playable_rect`.

### 6. Graceful Stubs
- Features that are included in the UI design but not yet implemented (e.g., Save, Load, Challenges) must be constructed using placeholder callback functions.
- These placeholder callbacks will simply print "Not Implemented: [Feature Name]" to the console without causing the game to crash or state to corrupt.

## Acceptance Criteria
- [ ] The screen is divided cleanly into a top bar, bottom bar, two side panels, and a central playable area.
- [ ] UI buttons play distinct clunk sounds when clicked depending on what layer they are in (Top, Side, Bottom).
- [ ] Physics objects are perfectly contained within the `playable_rect` and do not overlap with UI panels.
- [ ] `utils/ui_manager.py` manages UI components without external GUI dependencies.
- [ ] Side panels auto-populate buttons with dynamically generated graphic icons reflecting the `entities.yaml` data.
- [ ] Clicking a UI button handles the click cleanly without affecting the underlying game world (e.g., no accidental spawning).
- [ ] Selecting an object changes the `active_tool` and displays a transparent ghost cursor when hovering over the playable area in `EDIT` mode.
- [ ] Unimplemented buttons (e.g., Save, Load) log "Not Implemented" safely when clicked.
