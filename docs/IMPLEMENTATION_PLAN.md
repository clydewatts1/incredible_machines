# Milestone 1: Implementation Plan

This document outlines the step-by-step technical roadmap for building Milestone 1 of "The Incredible Machine Clone", strictly adhering to the Project Constitution and Specification.

## Phase 1: Foundation and Engine Setup

### Task 1: Setup Constants and Engine Window
**Objective:** Establish the foundational definitions and initialize the Pygame and Pymunk environments.
**Actions:**
1. Create `constants.py` to define screen dimensions (e.g., 800x600), fixed time steps (`1/60.0`), colors, and basic physics properties (default gravity).
2. Create `main.py` to initialize `pygame`, create the display window, and initialize `pymunk.Space`.
3. Implement the basic empty game loop with event handling (quit event), display update, and a frame rate clock.

**Validation:** Run `main.py`. A blank window of the specified dimensions should appear and stay open until manually closed. No errors should be thrown.

### Task 2: Implement Game State Manager
**Objective:** Create the State Machine to toggle between Edit Mode and Play Mode.
**Actions:**
1. Define an `Enum` or state variable for `GameState` (`EDIT`, `PLAY`).
2. Modify the main loop:
   * In `PLAY` mode: Call `space.step(constants.PHYSICS_STEP)`.
   * In `EDIT` mode: Do not step the physics space.
3. Add a keyboard listener (e.g., SPACEBAR) to toggle between the states. Visual indicator (e.g., text on screen) should show the current mode.

**Validation:** Run the game. Pressing the spacebar should toggle the text on the screen between "Edit Mode" and "Play Mode". The console can log the physics step execution to verify it only runs in Play Mode.

## Phase 2: Architecture and Base Classes

### Task 3: Implement Base `GamePart` Entity
**Objective:** Create the strict OOP foundation ensuring separation of concerns and the "Pymunk Rule".
**Actions:**
1. Create `entities/base.py` containing a `GamePart` class.
2. The class must hold references to its `pymunk.Body`, `pymunk.Shape`, and some representation of its visual (color/size).
3. Implement an `update_visual()` method that reads the `pymunk.Body` position and rotation, and translates it for Pygame rendering (handling Y-axis inversion if necessary).
4. **"Fail Loudly" Rule:** Implement an `assert` or exception inside the update/render method to raise an error if a physics body is missing or mismatched with its visual counterpart.

**Validation:** Instantiate a dummy `GamePart` object lacking a physics body in the main loop and verify the game crashes explicitly with our custom "Fail Loudly" error message. Remove the dummy object after test passes.

## Phase 3: World Building

### Task 4: Static Boundaries & The Ramp
**Objective:** Create the environment boundaries and the first static entity type.
**Actions:**
1. Create screen edges using `pymunk.Segment` with a static body (`space.static_body`) around the borders based on `constants.py`.
2. Create `entities/ramp.py` inheriting from `GamePart`.
3. The `Ramp` initializes a static Pymunk line segment (infinite mass/inertia) and implements a Pygame `draw.line` method synchronized to the physics segment.
4. Add instances of these to the space and draw them in the main loop.

**Validation:** Run the game. The screen borders should exist (even if invisible to physics, they can be drawn for debugging), and a static line (Ramp) should be visible on the screen.

### Task 5: Dynamic Entity: Bouncy Ball
**Objective:** Add the first dynamic entity to interact with the environment.
**Actions:**
1. Create `entities/ball.py` inheriting from `GamePart`.
2. The `Ball` initializes a dynamic `pymunk.Body` (calculating mass and moment) and a `pymunk.Circle` shape. Set high elasticity for bouncing.
3. Implement Pygame `draw.circle` in its visual update taking position from the physics body.
4. Hardcode one ball to spawn at a specific height above the ramp on startup.

**Validation:** 
* Start in Edit Mode: The ball should hang frozen in mid-air.
* Toggle to Play Mode: The ball should fall, bounce off the static ramp accurately based on Pymunk math, and eventually settle.
* Toggle back to Edit Mode: The ball should freeze in its current state.

## Phase 4: Interactions

### Task 6: Edit Mode Interactions (Spawning & Moving)
**Objective:** Allow users to build scenes in Edit Mode.
**Actions:**
1. Implement input handling to spawn entities (e.g., press 'B' for Ball, 'R' for Ramp at mouse coordinates).
2. Implement basic object picking in Edit Mode using `space.point_query` to detect if the mouse clicks on a Pymunk shape.
3. Allow dragging the selected object's body position directly with the mouse *only* while in Edit Mode.

**Validation:**
1. In Edit Mode, press 'B' and 'R' to continuously spawn objects at the mouse position.
2. Click and drag objects around the screen successfully.
3. Switch to Play Mode: Verify that dragging objects with the mouse no longer works, and gravity takes over all dynamically spawned balls.

## Final Review
* Run a full suite test ensuring all tasks integrate seamlessly.
* Perform a code review against the Project Constitution (No direct visual coordinate updates in Play Mode, Fail Loudly intact, strict OOP).
