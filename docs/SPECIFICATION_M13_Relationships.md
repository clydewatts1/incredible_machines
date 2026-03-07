# Specification: Milestone 13 - Object Relationships & Constraints

## Overview
This specification details the technical architecture for supporting advanced object relationships and constraints (such as Pymunk joints, pulleys, ropes, and hinges) in the Incredible Machines project. This milestone introduces the foundational structure required to link entities together, strictly adhering to the Relational Architecture rules defined in Section 12 of the Project Constitution.

## Goals
- **Instance Tracking:** Implement a robust identification system to uniquely track every spawned entity on the canvas.
- **Relational Data Structure:** Design a clear, data-driven YAML format for defining connections between distinct entities.
- **Two-Pass Instantiation:** Architect a two-phase loading and spawning sequence to ensure bodies exist before constraints are applied.
- **Cascading Deletion:** Ensure the object deletion system safely cleans up attached constraints to prevent physics engine instability.

## Technical Details

### 1. Instance Identity (UUIDs)
To allow constraints and save/load files to target specific instances on the canvas, every entity must have a guaranteed unique identifier.
- **UUID Assignment:** Upon instantiation, every entity (e.g., within the base `GamePart` initialization) must generate and store a Unique Identifier (UUID) using a standard generator (such as Python's `uuid` module).
- **Entity Management:** The global game state or entity manager must track these active instances using a dictionary or hash map, mapping each UUID string directly to its corresponding active Entity instance. This allows $O(1)$ lookup when a constraint needs to finding its target bodies.

### 2. Relational YAML Structure
Constraints must be defined in a data-driven manner, compatible with `config/entities.yaml` (for predefined composite parts) and level save files.
- **Structure:** Relationships should be defined in a dedicated list (e.g., under a `constraints` key) rather than nested within individual entity definitions. 
- **Required Properties per Constraint:**
  - `type`: The type of Pymunk constraint to create (e.g., "PivotJoint", "SlideJoint", "PinJoint").
  - `target_uuid_a`: The UUID of the first connected entity.
  - `target_uuid_b`: The UUID of the second connected entity.
  - `anchor_a`: The local coordinate offset $(x, y)$ on the first entity where the joint attaches.
  - `anchor_b`: The local coordinate offset $(x, y)$ on the second entity where the joint attaches.
  - *(Optional)* Additional parameters specific to the constraint type, such as `min_dist` and `max_dist` for a SlideJoint.

### 3. Two-Pass Instantiation System
To adhere to the Two-Pass Instantiation Rule, the engine's main spawning and level loading logic must be refactored into distinct phases.
- **Pass 1 - Entity Spawning:** Iterate through the level data and instantiate all standard entities (bodies and shapes). Add them to the Pymunk space and the Pygame rendering list. During this pass, record each entity in the UUID dictionary.
- **Pass 2 - Constraint Linking:** Iterate through the defined relationships/constraints data. For each relationship definition:
  - Look up the two required entity instances using `target_uuid_a` and `target_uuid_b` against the UUID dictionary.
  - If both entities exist, extract their Pymunk `Body` objects.
  - Instantiate the appropriate Pymunk Constraint using the bodies and the provided `anchor` coordinate offsets.
  - Add the newly created constraint to the Pymunk space.

### 4. Cascading Deletion (Safe Cleanup)
The object deletion system established in Milestone 11 must be updated to prevent crashes caused by deleting a body that is still referenced by an active Pymunk constraint.
- **Constraint Tracking:** Pymunk bodies maintain a list of constraints attached to them.
- **Deletion Sequence (Cascading Deletion Rule):** 
  - When an entity is flagged for deletion (e.g., via right-click or ingestion), the system must first retrieve the Pymunk `Body` associated with that entity.
  - Before removing the shapes or the body, iterate through any Pymunk Constraints attached to that body.
  - Remove each attached constraint from the Pymunk space entirely.
  - Only after all constraints are successfully removed from the space may the system proceed to remove the entity's shapes, the body itself, and finally the entity from the main rendering list and UUID dictionary.

## Acceptance Criteria
- [ ] Every entity on the canvas possesses a unique UUID accessible via its properties.
- [ ] A global dictionary successfully maps UUIDs to active entity instances.
- [ ] The loading logic executes a strict two-pass sequence: spawning all bodies first, followed by instantiating any defined constraints.
- [ ] Level save data and configuration structures support a defined schema for linking `target_uuid_a` to `target_uuid_b` with anchor points.
- [ ] Deleting an entity that has active constraints securely removes the constraints from the Pymunk space prior to removing the body, preventing any `AssertionError` or segmentation faults.
- [ ] No Python implementational code is included in this specification document.
