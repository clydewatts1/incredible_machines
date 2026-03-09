# Milestone 19: Advanced Physics Mechanics (Motors & Conveyors) - Implementation Plan

This document breaks down the specification for Milestone 19 into logical, actionable implementation phases.

## Phase 1: YAML Configuration
**Goal:** Add configuration profiles for Conveyor Belts and Motors to the entity library.
**Target File:** `config/entities.yaml`
**Steps:**
1. Open `config/entities.yaml`.
2. Append a new entity profile for `conveyor_belt`.
   - Set `template` to `Rectangle`.
   - Set `type` to `kinematic` (or `static` if preferred, but kinematic allows for potential moving platforms later).
   - Add a `properties` dictionary with a `speed` attribute (e.g., default `100.0`) and `direction` attribute (e.g., default `"right"`).
   - Define a `color` (e.g., `[100, 100, 100]`).
3. Append a new entity profile for `motor`.
   - Set `template` to `Circle`.
   - Set `type` to `dynamic` (important for rotation).
   - Add a `properties` dictionary with a `motor_speed` attribute (e.g., default `3.14`) and `direction` attribute (e.g., default `"clockwise"`).
   - Define a `color` (e.g., `[200, 100, 50]`).
**Testing:** Boot the game to ensure YAML parsing does not throw errors.

## Phase 2: Conveyor Belt Logic
**Goal:** Implement the physical driving force for Conveyor Belts.
**Target File:** `entities/base.py` (or a dedicated `entities/kinematic.py` if splitting off).
**Steps:**
1. Locate the initialization (`__init__`) or logic update loop (`update_logic` added in previous milestones) inside `GamePart`.
2. Add a condition for `if self.variant_key == "conveyor_belt":`.
3. Fetch the horizontal speed using `self.get_property("speed", 100.0)`.
4. Apply this speed * direction multiplier to the physical Pymunk shape's `surface_velocity`.
   - Read `direction`. If it is `"left"`, multiply speed by `-1`.
   - Example mapping: `self.shape.surface_velocity = (speed, 0)`.
5. Integrate logic signaling (M17): If the entity has an active/inactive state triggered via `receive_signal`, conditionally apply `(speed, 0)` or `(0, 0)`.
**Testing:** Place a Conveyor Belt in the editor, drop a Bouncy Ball onto it in Play mode, and verify the ball is pushed horizontally.

## Phase 3: Motor Logic & Constraints
**Goal:** Ensure Motors stay pinned in space and rotate at a constant velocity.
**Target File:** `entities/base.py` and `main.py`
**Steps:**
1. In `GamePart.__init__`, if `self.variant_key == "motor"`, flag the entity as needing constraints (e.g., `self.needs_motor_constraints = True`).
2. Alternatively, handle this mapping in `main.py` where constraints are built, or inside `level_manager.py` if abstracting. The vital step is ensuring a `pymunk.PivotJoint` and a `pymunk.SimpleMotor` are created tying the motor `body` to `space.static_body`.
3. The `PivotJoint` anchors the motor's center to the space (`body.position`).
4. The `SimpleMotor` drives the relative rotation. Use `self.get_property("motor_speed", 3.14)` for the motor's defined rate. Multiply by `-1` if the `direction` property equals `"counter-clockwise"`.
5. Store references to these constraints on the entity so they can be cleaned up on deletion (M11).
**Testing:** Place a Motor in the editor. Hit Play. Verify it spins steadily and knocks away objects that drop onto its teeth/edges without falling down.

## Phase 4: Property Editor Integration
**Goal:** Allow users to tweak speeds in real-time.
**Target File:** `main.py` (UI Input Handling) & `entities/base.py`
**Steps:**
1. Ensure the M14 Property Editor UI automatically picks up the `speed`/`direction` (Conveyor) and `motor_speed`/`direction` (Motor) variables because they were defined in the `properties` dictionary in Phase 1.
2. In the `GamePart` run loop/update phase (e.g., in a `update_property_overrides` method or just before the `step` call), dynamically read from `self.overrides` (via `self.get_property`).
3. Re-apply the updated values to the Pymunk Engine.
   - For Conveyors: update `self.shape.surface_velocity = (new_speed, 0)`.
   - For Motors: update the `rate` property of the `SimpleMotor` constraint you stored in Phase 3.
**Testing:** Place a Conveyor. Select it in EDIT mode. Change its `speed` in the UI to a negative number. Hit play. Verify objects are now pushed in the opposite direction.
