# Implementation Plan: Milestone 12 - Active Entities (Cannon & Basket)

## Overview
This document outlines the high-level implementation sequence for introducing Active Entities (the Cannon and the Basket) into "Incredible Machines," as defined in `docs/SPECIFICATION_M12_ActiveEntities.md`. It grants the Implementation Agent autonomy over granular algorithmic and mathematical decisions.

## Implementation Phases

### Phase 1: YAML Configuration
**Goal:** Define the raw data parameters for the new Cannon and Basket entities.
**Target Files:** `config/entities.yaml`
- Add a new entry for the Cannon specifying properties such as `shoot_velocity`, `shoot_frequency`, `max_count`, and `projectile_id`.
- Add a new entry for the Basket.
- Ensure both entities use a template identifier (e.g., `"UShape"`) to indicate they require composite geometry parsing.
**Testing/Acceptance:** The YAML configuration successfully parses on game launch without errors, and the new tools appear in the sidebar UI (even if their advanced logic is not yet functional).

### Phase 2: Composite Geometry Parsing
**Goal:** Modify the entity creation logic to support constructing bodies with multiple attached shapes (U-shapes) instead of simple primitives.
**Target Files:** `entities/base.py` (or similar factory module)
- Expand the geometry generation system to detect the `"UShape"` template.
- Implement the mathematical logic to attach three rectangular walls (base, left side, right side) to a single `pymunk.Body` based on the entity's defined width and height.
- Ensure these parts inherit the body's transform correctly when rendering.
**Testing/Acceptance:** Spawning a Cannon or Basket visually renders a U-shape, and other physics objects realistically collide with and rest inside the walls of the U-shape.

### Phase 3: Cannon Spawning Logic
**Goal:** Empower the Cannon to act as an active spawner during PLAY mode.
**Target Files:** `entities/base.py`, `main.py`
- Add an `update(dt)` hook to the entity system that is called on every dynamic body every frame.
- Implement the Cannon's specific logic: Increment an internal timer by `dt`.
- When the timer exceeds the `shoot_frequency`, and if the global game state is `"PLAY"`, instantiate a new entity based on the `projectile_id`.
- Apply the `shoot_velocity` impulse to the spawned projectile based on the Cannon's current rotation angle.
- Add an invisible sensor shape to the Cannon's opening (similar to the Basket). Establish a collision handler so that any valid entity landing in the Cannon is destroyed and immediately triggers the Cannon to fire a new projectile.
- Ensure the Cannon ceases firing immediately when entering "EDIT" mode.
**Testing/Acceptance:** In PLAY mode, the Cannon autonomously spawns projectiles at the specified rate that shoot out of its opening.

### Phase 4: Basket Ingestion Logic
**Goal:** Grant the Basket the ability to detect and destroy incoming entities.
**Target Files:** `entities/base.py`, `main.py`
- During Phase 2's geometry construction for the Basket, add a fourth `pymunk.Shape` across the U-shape's opening with its `sensor` property set to `True` and a specific collision type integer assigned.
- Establish a Pymunk collision handler in the main space mapping the sensor's collision type to generic dynamic object collision types.
- Inside this handler, identify the incoming body and flag it for deletion (utilizing the cleanup logic developed in Milestone 11).
**Testing/Acceptance:** Dropping a ball or block into the Basket causes that object to securely vanish from the physics space and screen.
