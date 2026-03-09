# Specification: Milestone 15 - Directional Active Entities & Filtering

## Overview
In Milestone 12, we introduced "Active Entities" (the Cannon and the Basket) built as composite U-shapes. In Milestone 15, we are redesigning these entities to be more robust, performant, and highly configurable. Both the Basket and the Cannon will transition to standard rectangular physics bodies. Instead of relying on complex geometric enclosures to dictate directionality, their behavior will be driven by configurable "Active Sides" and strict type-filtering logic defined in `entities.yaml`.

## Goals
1. Transition active entities from composite U-shapes to primitive Rectangles to improve physics stability.
2. Introduce directional sensing by allowing config to define which specific sides of a rectangle trigger actions.
3. Implement Entity Filtering so receptacles (Baskets) only accept specific object types.
4. Expand Emitter configurability so Cannons can dictate exactly what they shoot, how fast, and at what angle.
5. Adhere to the M14 Property Inheritance Model, ensuring all these new properties can be overridden on a per-instance basis.

## Technical Implementation Details

### 1. The Basket Redesign (Directional Ingestion & Filtering)
*   **Shape Transition:** The Basket will no longer generate left/right/bottom walls. It will be a single static (or dynamic, if configured) rectangular `pymunk.Poly`.
*   **Active Sides Definition:** The `entities.yaml` definition for a basket will include a new property:
    *   `active_sides: ["top", "left", "right", "bottom"]`
    *   This defines which of the 4 standard local edges act as the sensor.
*   **Type Filtering:** A new property will define what the basket can ingest:
    *   `accepts_types: ["bouncy_ball", "data_ball"]` (or `"all"`)
*   **Collision Logic:** 
    *   When another entity collides with the Basket, the collision handler must calculate which local side of the Basket was hit.
    *   If the hit side is *not* in `active_sides`, the Basket acts as a normal solid wall (bouncing the object away based on elasticity/friction).
    *   If the hit side *is* in `active_sides`, the handler must then check the incoming entity's `entity_id` against the `accepts_types` list.
    *   If the type matches (or `accepts_types` is `"all"`), the incoming entity is ingested (deleted) and the basket's action is triggered.
    *   If the type does not match, the basket acts as a normal solid wall.

### 2. The Cannon Redesign (Directional Emitter)
*   **Shape Transition:** The Cannon will also become a standard rectangular `pymunk.Poly`.
*   **Active Side:** The Cannon will define an `active_side` (e.g., `"right"`) to determine which local edge the projectile spawns from.
*   **Configurable Trajectory & Ammo:** The following properties will be added to the Cannon's YAML configuration:
    *   `ammo_id: "bouncy_ball"` (Declares which `entity_id` the cannon shoots).
    *   `exit_velocity: 800.0` (The scalar speed of the projectile).
    *   `exit_angle: 0.0` (The angle in degrees, relative to the Cannon's current rotation, that the projectile fires).
*   **Spawning Logic:** When the cannon triggers, it must calculate the world-space center of its `active_side`, spawn an instance of `ammo_id` at that location, and apply an impulse corresponding to the `exit_velocity` and the combined world-rotation + `exit_angle`.

### 3. Data-Driven Rules
*   All new properties (`active_sides`, `accepts_types`, `ammo_id`, `exit_velocity`, `exit_angle`) must be defined in `config/entities.yaml` under their respective entity definitions.
*   Because of the M14 Inheritance logic, users must be able to left-click an instance of a Cannon or Basket in EDIT mode and modify these values via the Properties Panel (e.g., changing a Cannon's `ammo_id` from "bouncy_ball" to "bowling_ball").

## Acceptance Criteria
- [ ] Baskets and Cannons are rendered and simulated as standard rectangles without internal composite U-shapes.
- [ ] A Basket configured with `active_sides: ["top"]` acts as a solid platform on its bottom, left, and right sides, but ingests objects that land on its top.
- [ ] A Basket configured with `accepts_types: ["red_diamond"]` will bounce away a bouncy ball but ingest a red diamond.
- [ ] A Cannon's spawned projectile type, speed, and angle are driven strictly by variables accessible via `entities.yaml` or instance overrides.
- [ ] Using the M14 Properties Panel, a user can override a Cannon's `ammo_id` and have it immediately shoot the new object type.
