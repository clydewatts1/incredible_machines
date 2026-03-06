# Milestone 2 Specification Addendum: Adjustable Angled Ramp

## Overview
This addendum expands the Milestone 1 foundational sandbox by introducing an **Adjustable Angled Ramp**. The core goal is to allow users to build more complex physics puzzles by rotating static ramps during the Edit Mode build phase and verifying correct physics interactions (specifically, rolling behavior) during Play Mode.

## 1. Feature Requirements
### Interaction (Edit Mode)
* **Rotation Mechanism:** In addition to moving objects via mouse drag, users must be able to rotate the ramp.
* **Controls:** 
    * When a user grabs a ramp with a mouse click (or hovers over it), holding a specific modifier key (e.g., `Shift` + Mouse Scroll Wheel) or using dedicated keyboard keys (e.g., Left/Right Arrow keys or `Q`/`E`) will rotate the ramp around its center pivot.
* The visual representation must correctly update to match the new physics angle in real-time while in Edit Mode.

### Physics (Play Mode)
* The ramp will remain a **Static Physics Body** (`space.static_body`).
* When a dynamic Ball entity naturally falls or colliding with the ramp, the `pymunk` physics engine's gravity, friction, and moment of inertia properties must dictate the behavior.
* **Crucial:** The ball must functionally *roll* down the incline. It should not merely slide statically without rotation, nor should it bounce indefinitely. Appropriate friction values must be set on both the Ball and the Ramp shapes to ensure rolling torque is generated.

## 2. Technical Considerations
* **The Pymunk Rule (Strict):** Ensure that the `update_visual` method correctly reads `self.body.angle` (which is in radians) from the Pymunk physics body and appropriately translates that into Pygame's visual rotation (which generally requires degrees and adjusting the drawing pivot point).
* **Friction & Elasticity Calibration:** The default values defined in `constants.py` or entity initialization may need to be adjusted:
  * Ball Friction + Ramp Friction must be high enough to cause rolling (e.g., > 0.6).
  * Ball Elasticity should likely be lowered slightly (e.g., from 0.95 to 0.5) so the ball doesn't violently bounce off the ramp constantly but instead settles into a roll.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating Ramp Rotation and Ball Rolling
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Spawn the Adjustable Ramp**
1. Launch the application (Application starts in `Mode: EDIT`).
2. Press `R` to spawn a new Ramp.
3. Verify the ramp appears horizontally on the screen.

**Step 2: Change the Ramp Angle**
1. Select/Grab the ramp with the mouse.
2. Use the designated rotation controls (e.g., `Q`/`E` or `Shift`+Scroll).
3. **Success Check:** The visual line representing the ramp tilts smoothly around its center point. Set the ramp to an approximately 45-degree angle pointing downward from left-to-right.

**Step 3: Position the Ball**
1. Press `B` to spawn a Ball.
2. Use the mouse to grab the ball and drag it high into the air, positioned directly above the higher, left-hand side of the tilted ramp.

**Step 4: Execute Play Mode and Verify Physics**
1. Press the `SPACEBAR` to transition to `Mode: PLAY`.
2. **Success Check (Gravity):** The ball falls downward onto the ramp.
3. **Success Check (Incline Physics):** The ball strikes the ramp and begins to travel down the incline.
4. **Success Check (Rolling, NOT Sliding):** The physical logic shows the ball *rolling* down the ramp. (Note: Since the ball is a solid untextured color, visual rolling might be hard to see natively; the physics test is that it accelerates smoothly rather than awkwardly sticking or skidding without momentum. *Optional Enhancement: Add a visual line/dot to the ball sprite to make the rolling mathematically obvious visually.*)

**Sign-off:** The feature is complete when the ball consistently rolls down the sloped user-created ramp.
