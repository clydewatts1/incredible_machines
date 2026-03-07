# Specification: Milestone 12 - Active Entities (Cannon & Basket)

## Overview
This specification details the technical plan for introducing "Active Entities" to the Incremental Machines project. Specifically, we will implement a "Cannon" (a spawner) and a "Basket" (an ingester). Both will utilize complex, multi-shape geometries to form a U-shape container/barrel, operating only when the game is in the "PLAY" state.

## Goals
- Construct a parameterized, composite U-shaped geometry in Pymunk for both the Cannon and Basket entities.
- Implement the "Cannon" to spawn specified projectiles at a set frequency and velocity while the game plays.
- Implement the "Basket" to ingest (destroy) specific entities that fall into it using an invisible Pymunk sensor.
- Maintain total compliance with the project's data-driven architecture by exposing all configuration values in `entities.yaml`.

## Technical Details

### 1. Geometry & U-Shapes
- **Composite Bodies:** Instead of a single primitive shape (like a box or circle), the Cannon and Basket require a single rigid `pymunk.Body` (likely kinematic or static depending on placement needs) with multiple attached `pymunk.Shape` instances.
- **Construction:** The U-shape will be formed by attaching three rectangular shapes (e.g., `pymunk.Poly` or thick `pymunk.Segment`s) to the central body:
  - A bottom "base" wall.
  - A left "side" wall.
  - A right "side" wall.
- **Orientation:** The open "mouth" of the U-shape will face "up" by default (relative to the entity's rotation angle).

### 2. The Cannon (Spawner)
- **YAML Parameters:** The `entities.yaml` configuration for the Cannon must explicitly declare:
  - `shoot_velocity`: A tuple `[x, y]` representing the initial impulse or velocity in local space.
  - `shoot_frequency`: A float representing the delay (in seconds) between shots.
  - `max_count`: An integer capping the total number of projectiles the Cannon can spawn (e.g., `max_count: 5`). Leave as `null` or `-1` for infinite.
  - `projectile_id`: A string matching a valid `variant_key` (e.g., `"ball"`) defining what entity to spawn.
- **Update Logic:**
  - The Cannon instance must have an `update(dt)` loop hook.
  - It will maintain an internal timer and increment it by `dt`.
  - **Crucially**, this timer only increments, and spawning only occurs, if the global game state is `"PLAY"`.
  - When the timer exceeds `shoot_frequency` (and `max_count` is not reached), the Cannon instantiates the new `projectile_id` entity.
  - The projectile must spawn precisely at the Cannon's open mouth, inheriting the Cannon's exact spatial rotation so it shoots "forward" out of the barrel.
- **Ingestion/Reflection Logic:**
  - The Cannon must possess an inner collision sensor inside its U-shape, similar to the Basket.
  - When a valid projectile lands in the Cannon's sensor, it must be ingested (destroyed) and immediately trigger a new projectile to be shot back out.

### 3. The Basket (Ingester)
- **YAML Parameters:** While largely borrowing the U-shape physical properties, the Basket may specify optional filters, like `ingest_types: ["ball"]`.
- **Collision Sensor:** 
  - In addition to the three physical walls forming the U-shape, a fourth `pymunk.Shape` must be added bridging the open gap.
  - This shape must have its `.sensor = True` property set so physics objects pass through it without bouncing, triggering collision callbacks instead.
  - The shape should be assigned a specific `collision_type` integer identifying it as an Ingester Sensor.
- **Collision Handling:**
  - Establish a Pymunk collision handler (e.g., `space.add_collision_handler(projectile_type, sensor_type)`).
  - Inside the handler's `begin` or `post_solve` methods, identify the incoming projectile entity.
  - Flag the incoming entity for safe destruction (removing it from both the Pygame rendering list and Pymunk space, identical to the cleanup logic created in M11).

### 4. Data-Driven Architecture Conformance
- Ensure the base `GamePart` (or a subclass) can ingest lists of composite shapes via the YAML configuration or a dedicated factory function mapped via `entities.yaml` templates.
- Ensure all logic avoids hardcoded physics offsets, relying on `entities.yaml` width/height definitions to place the walls and sensors procedurally.

## Acceptance Criteria
- [ ] A Cannon entity exists in the sidebar, configurable via `entities.yaml` (velocity, rate, type).
- [ ] A Basket entity exists in the sidebar, configurable via `entities.yaml`.
- [ ] Both entities render visually as U-shapes and block physics properly on their solid walls.
- [ ] In PLAY mode, the Cannon fires projectiles according to its defined logic. It ceases firing in EDIT mode.
- [ ] In PLAY mode, the Basket captures and cleanly destroys valid physics objects that fall into its sensor zone without crashing.
- [ ] No Python implementational code is included in this specification document.
