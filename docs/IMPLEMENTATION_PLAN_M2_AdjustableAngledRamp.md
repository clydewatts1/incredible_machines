# Milestone 2: Implementation Plan (Adjustable Angled Ramp)

This document outlines the step-by-step technical roadmap for integrating the Adjustable Angled Ramp feature natively into the "The Incredible Machine Clone" architecture.

## Phase 1: Interaction Engine (Edit Mode)

### Task 1: Add Rotation Controls to Event Loop
**Objective:** Capture keyboard inputs to adjust the rotation angle of a grasped object in Edit Mode.
**Actions:**
1. Modify the Pygame event loop in `main.py`.
2. Map rotation keys (e.g., `Q` for counter-clockwise, `E` for clockwise).
3. If an object is currently being dragged/grasped (`grabbed_body` is not None) *and* the game mode is `EDIT`:
   * Update the `angle` property of the `grabbed_body`.
   * Apply a fixed rotation step (e.g., +/- 0.1 radians per key press) directly to `grabbed_body.angle`.

**Validation (QA Rule):** 
1. Run `python main.py`. 
2. Spawn a Ramp (`R`). 
3. Grab it with the mouse. While holding the mouse button, press `Q` and `E`. 
4. The ramp should instantly visually rotate around its center.

## Phase 2: Visual Synchronization

### Task 2: Pymunk-to-Pygame Rotation Rendering (The Pymunk Rule)
**Objective:** Ensure Pygame correctly draws the angle specified by the Pymunk static body, adhering strictly to the separation of concerns.
**Actions:**
1. Update `entities/ramp.py`.
2. The current drawing logic draws from `self.shape.a` to `self.shape.b` translated by `self.body.local_to_world()`. Because `local_to_world()` automatically factors in the body's `angle`, the underlying math for the segment endpoints is already correct.
3. *Critical Verification*: Ensure the `draw` method is purely reading `self.body.local_to_world()` and passing those integer coordinates to `pygame.draw.line()`.
4. Ensure the `Ball` also updates its visual if necessary, though circles look identical regardless of rotation unless marked.
5. Apply the "Fail Loudly" bounds check inside `update_visual` in `entities/base.py` to ensure rotation properties exist.

**Validation (QA Rule):** 
1. Re-run the test from Task 1.
2. The visual Pygame line MUST perfectly mirror the bounds of the invisible physics segment. (You can test this by dropping balls on it while rotated and seeing if they hit exactly where the line is drawn).

## Phase 3: Physics Calibration (Play Mode)

### Task 3: Guarantee Rolling Mechanics
**Objective:** The ball must physically *roll* down the incline using torque, gravity, friction, and inertia—not statically slide.
**Actions:**
1. Adjust the friction properties of the `Ball` shape in `entities/ball.py` (e.g., set `friction = 0.7`).
2. Adjust the friction properties of the `Ramp` shape in `entities/ramp.py` (e.g., set `friction = 0.7`).
3. Lower the elasticity (bounciness) slightly on both if necessary so the ball quickly settles onto the ramp rather than bouncing infinitely.

**Validation (QA Rule):** 
1. Run `python main.py`. 
2. Spawn a ramp, angle it using `E` to approx 45 degrees, and place a ball slightly above it. 
3. Press `SPACE` to enter `PLAY` mode.
4. The ball should fall, strike the ramp, settle quickly, and roll down the incline to the floor. (Note: Because the ball is a solid color, rolling torque might be confirmed via print statements of `ball.body.angular_velocity` in the console during testing, or you can temporarily draw a line on the ball in `entities/ball.py`'s draw method from center to edge to visually confirm rotation).
