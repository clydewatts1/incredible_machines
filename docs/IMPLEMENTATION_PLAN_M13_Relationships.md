# Implementation Plan: Milestone 13 - Object Relationships & Constraints

## Overview
This document outlines the high-level implementation sequence for introducing the Relational Architecture to "Incredible Machines," as defined in `docs/SPECIFICATION_M13_Relationships.md`. This architecture will support Pymunk joints (pulleys, ropes, hinges) by enforcing UUIDs, two-pass spawning, and cascading deletion logic.

## Implementation Phases

### Phase 1: UUID System & State Tracking
**Goal:** Guarantee that every entity spawned on the canvas receives a unique identifier and is tracked globally for $O(1)$ relationship lookups.
**Target Files:** `entities/base.py`, `main.py`
- Modify the base `GamePart` (or similar base entity class) initialization to automatically generate and assign a standard Python `uuid` string.
- Establish a global dictionary (e.g., `active_instances` in the game state or main loop) that maps these UUID strings to their corresponding active entity objects.
- Ensure entities added via tools/spawning or loaded from files are properly registered in this dictionary.
**Testing/Acceptance:** Instantiate several entities and verify (via logging or debugging) that each possesses a unique `uuid` property and exists within the tracking dictionary.

### Phase 2: Relational YAML Parsing
**Goal:** Prepare the game's data loading functions to read and understand constraint metadata without requiring those constraints to be nested inside an entity block.
**Target Files:** `utils/level_manager.py` (or the equivalent level loader script), `config/entities.yaml`
- Update the level saving and loading schemas to support a separate `constraints` array.
- Parse relationship data out of the config files. This data must detail the constraint type, the two target UUIDs (`target_uuid_a`, `target_uuid_b`), and the local anchor points mapping where the joint attaches.
**Testing/Acceptance:** A dummy YAML file containing a `constraints` array loads into the engine successfully, properly parsing out the relationship metadata strings into memory without crashing.

### Phase 3: Two-Pass Spawning System
**Goal:** Architect a two-phase initialization sequence to safely link physics bodies.
**Target Files:** `utils/level_manager.py`, `main.py`
- Refactor the level loading and tool-spawning functions so they adhere to the Two-Pass Instantiation Rule.
- **Pass 1:** Iterate through the parsed entities and instantiate their bodies/shapes sequentially onto the Pymunk space as usual.
- **Pass 2:** Iterate through the parsed relationships. Retrieve the actual entity instances via the UUID tracking dictionary created in Phase 1. Extract their underlying Pymunk `Body` components and use them to instantiate the requested Pymunk constraints (e.g., `pymunk.PivotJoint`).
**Testing/Acceptance:** Two static bodies defined in a YAML file can be successfully loaded and connected via an active Pymunk joint without throwing an `AssertionError` regarding missing bodies.

### Phase 4: Cascading Deletion
**Goal:** Ensure the removal of connected entities does not destabilize the physical simulation.
**Target Files:** `main.py` (specifically the object deletion logic/event loop)
- Update the right-click deletion and "Basket ingestion" logic established in Milestone 11.
- Before calling `space.remove()` on an entity's bodies or shapes, access the entity's underlying Pymunk body and iterate through its `constraints` property.
- For each attached constraint, safely remove it from the Pymunk space.
- Once all attached constraints are cleanly removed, proceed with deleting the entity's shapes, body, and rendering data as normal. 
**Testing/Acceptance:** Deleting an entity that is actively connected to a Pymunk joint (e.g., via right-click or dropping it in the Basket) securely removes the joint and the entity without causing the game or physics engine to crash.
