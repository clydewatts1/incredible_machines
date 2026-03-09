# Implementation Plan: Milestone 15 - Directional Active Entities & Filtering

## Phase 1: YAML Configuration Updates
**Goal:** Modify the base definitions of the Basket and Cannon to support the new rectangular schemas and directional attributes.
**Target Files:** `config/entities.yaml`
**Actions:**
- Redefine both `basket` and `cannon` to use `template: "Rectangle"` rather than `UShape`.
- Define `active_sides` (e.g., `["top"]`) for the basket.
- Define `accepts_types` (e.g., `["bouncy_ball", "data_ball"]`) for the basket.
- Define `active_side` (e.g., `"right"`) for the cannon.
- Define `ammo_id`, `exit_velocity`, and `exit_angle` for the cannon.
**Verification:** Run the application and verify no parsing errors occur during startup, and the Basket/Cannon objects render as standalone rectangles.

## Phase 2: Directional Sensors in Pymunk
**Goal:** Equip rectangular bodies with specific logical sensors based on their active side configurations.
**Target Files:** `entities/base.py` (or specific `entities/active.py` if splitting logic)
**Actions:**
- During `GamePart.__init__`, if `active_sides` or `active_side` is present, construct an additional `pymunk.Segment` shape along the specified local edge (Top, Bottom, Left, or Right).
- Assign these segments a specific `collision_type` (e.g., 2 for Basket Sensor, 3 for Cannon Sensor).
- Mark these segments as `sensor = True` so they don't produce physical bounce.
**Verification:** Use Pygame drawing or Pymunk debug draw to visually verify a small sensor line appears exactly on the designated active side of the entity.

## Phase 3: Basket Type Filtering Logic
**Goal:** Ensure the Basket only ingests specific entity types.
**Target Files:** `main.py` (Collision Handlers)
**Actions:**
- Update the Basket's `on_collision` handler.
- Extract the colliding `GamePart` from the arbiter.
- Query the Basket's `get_property("accepts_types")`.
- If the colliding entity's ID is in the accepted list (or if the list is `"all"`), flag the entity for deletion (ingestion).
- If it is *not* in the list, return `True` from the handler to enforce a physical bounce.
**Verification:** Spawn a Basket that only accepts Red Diamonds. Drop a Bouncy Ball onto it—it should bounce. Drop a Red Diamond onto it—it should be destroyed.

## Phase 4: Cannon Emitter Logic
**Goal:** Update the Cannon to fire its strictly configured ammo type with respect to its rotation and exit parameters.
**Target Files:** `main.py` (or `entities/active.py`'s `update_logic` method)
**Actions:**
- Modify the Cannon's spawning logic so it only fires `get_property("ammo_id")`.
- Calculate the correct world-space spawn position by translating the local coordinates of the `active_side` using the Cannon body's current world `position` and `angle`.
- Apply an instantaneous central impulse (`apply_impulse_at_local_point`) based on the Cartesian decomposition of `get_property("exit_velocity")` and the Cannon's world `angle` + `get_property("exit_angle")`.
**Verification:** Spawn a Cannon configured to shoot Bouncy Balls at an angle of 45 degrees relative to its nose. Trigger the Cannon and verify the ball arcs out at the expected speed and angle.
