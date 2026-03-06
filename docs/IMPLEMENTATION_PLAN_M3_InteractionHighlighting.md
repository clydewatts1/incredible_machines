# Milestone 3: Implementation Plan (Interaction Highlighting)

This document details the step-by-step technical roadmap for integrating the Universal Interaction Highlighting feature into "The Incredible Machine Clone", ensuring all interactive objects visibly respond to mouse hover states during the Edit phase.

## Phase 1: Engine and Base Class Integration

### Task 1: Update Base `GamePart` with Hover State
**Objective:** Add state tracking to the foundation class so every entity intrinsically understands if it is being interacted with.
**Actions:**
1. Open `entities/base.py`.
2. Add a new boolean property `self.is_hovered = False` inside the `GamePart.__init__` method.
3. Add a universal visual hook to `update_visual()`. If `self.is_hovered` is True, it should draw a standardized outline or visual element *after* calling the subclass's `draw()` method, or pass a flag to the subclass. However, `pymunk` shapes can be easily outlined by Pygame using their mathematical coordinates. For simplicity, we can pass the `is_hovered` state to the subclass `draw` methods so they can render their specific outlines (e.g., a white circle for Ball, a white thicker line for Ramp).

**Validation (QA Rule):** 
1. Run `python main.py`. 
2. The game must launch without crashing. (No highlights will appear yet because nothing toggles the boolean, but defining the property ensures the architecture is sound).

## Phase 2: Spatial Querying

### Task 2: Pymunk Cursor Detection in Main Loop
**Objective:** Use Pymunk's physics engine to determine precisely which shape the mouse is hovering over, maintaining strict separation from visual bounding boxes.
**Actions:**
1. Open `main.py`.
2. In the `EDIT` mode section of the event/frame loop (specifically during or right after `pygame.MOUSEMOTION` or just once per frame in the update loop), get the current mouse position.
3. Reset `is_hovered = False` for *all* entities.
4. Call `space.point_query_nearest(mouse_pos, 0, pymunk.ShapeFilter())` to find the exact Pymunk shape under the cursor.
5. If a shape is found (and it's not the static boundary `space.static_body`), find the corresponding `GamePart` entity locally and set its `is_hovered = True`.

**Validation (QA Rule):** 
1. Temporarily add a `print("Hovering!")` statement in the `main.py` when `is_hovered` is set to True.
2. Run `python main.py`, spawn a Ball (`B`) and a Ramp (`R`).
3. Wiggle the mouse over them and ensure the console prints accurately and *only* when the cursor is mathematically touching the objects. Remove the print statement once verified.

## Phase 3: Visual Implementation

### Task 3: Render Subclass Visual Feedback
**Objective:** Make the `Ball` and `Ramp` classes react visually to the boolean set by the main loop.
**Actions:**
1. Open `entities/ball.py`. In its `draw()` method, if `self.is_hovered` is True, draw a slightly larger `pygame.draw.circle` underneath it, or draw a 3-pixel white outline over it using `pygame.draw.circle(..., width=3)`.
2. Open `entities/ramp.py`. In its `draw()` method, if `self.is_hovered` is True, draw a slightly thicker, bright-colored line underneath the main ramp line to act as a glow/outline.

**Validation (QA Rule):** 
1. Run `python main.py`.
2. Spawn a Ball and a Ramp.
3. Move the mouse over the Ball: It must visually highlight. Move away: It must return to normal.
4. Move the mouse over the Ramp: It must visually highlight. Move away: It must return to normal.
