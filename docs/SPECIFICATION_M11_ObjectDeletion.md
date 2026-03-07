# Specification: Milestone 11 - Object Deletion & Canvas Clearing

## Overview
This specification outlines the technical plan for Milestone 11: Object Deletion & Canvas Clearing. In addition to placing new objects, players require the ability to remove objects to fix mistakes or reset the entire level. Deletion mechanisms must strictly adhere to the Pymunk authority principles, guaranteeing synchronization between the physics simulation and the visual rendering state.

## Goals
- Provide an intuitive method for removing individual user-placed objects via a secondary mouse click.
- Implement a global "Clear" mechanism within the UI to instantly wipe all dynamic objects from the canvas.
- Ensure that the deletion process safely decouples and removes entities from both the `pymunk.Space` and the Pygame rendering lists to prevent memory leaks or ghost collisions.
- Guarantee that essential game boundaries (static environment walls) are completely immune to deletion.

## Technical Details

### 1. Right-Click Deletion
- **Trigger:** A right-click (mouse button 3) event within the playable area.
- **Mode Requirement:** Deletion is strictly tied to "EDIT" mode. In "PLAY" mode, right-clicking should have no deletion effect.
- **Target Identification:** 
  - Upon a right-click, a Pymunk point query or equivalent spatial check determines if a user-placed object lies at the mouse coordinates.
  - If a shape is found, it must be verified as a valid deleting target (see Safety Constraints below).
  - If empty space is clicked (no shape found), the event must simply be ignored and safely discarded without raising an error.
- **Cleanup Sequence:**
  - **Physics Space Removal:** The entity's associated `pymunk.Shape`(s) and `pymunk.Body` must be formally removed from the active `pymunk.Space` using `space.remove()`.
  - **Render List Removal:** The `GamePart` (or subclass instance) must be permanently deleted from the global `entities` list managed by `main.py` so that it is no longer processed or drawn.

### 2. Clear Canvas Button
- **UI Integration:** A new `UIButton` labeled "Clear" must be added to the Top Panel UI.
- **Mode Requirement:** Similar to individual deletion, the "Clear" button should only execute its logic when the game is in "EDIT" mode.
- **Bulk Cleanup Sequence:**
  - Iterate through the entire `entities` list.
  - For every entity, apply the Physics Space Removal logic (removing shapes and bodies from the `pymunk.Space`).
  - Once the Pymunk space is cleared of these dynamic objects, call `entities.clear()` to wipe the rendering list in a single atomic action.

### 3. Safety Constraints
- **Protecting Environment Boundaries:** 
  - The static Pymunk segments representing the floor, ceiling, and walls (created during Milestone 9) must NOT be deleted.
  - *Implementation strategy:* When identifying an object for deletion (especially during the bulk "Clear Canvas" loop or a spatial query), the logic must definitively verify that the object's body is distinct from the `space.static_body` that owns the UI boundary segments. Only objects inheriting from `GamePart` that represent user-placed tools should be allowed to be destroyed.
- **Graceful Failure:** Any intersection query that returns `None` or an unmanaged entity must abort the deletion routine cleanly.

## Acceptance Criteria
- [ ] A "Clear" button is visible and accessible in the Top Bar UI.
- [ ] In EDIT mode, right-clicking an object perfectly removes it from both the visual screen and the physics simulation.
- [ ] In EDIT mode, clicking "Clear" successfully removes all user-placed objects simultaneously.
- [ ] Right-clicking in empty space produces no errors or crashes.
- [ ] The core bounding walls (floor, ceiling, left, right limits) cannot be deleted under any circumstances (neither via individual click nor via the Clear button).
- [ ] Deletion actions (right-click or Clear button) are disabled or ignored when the game is in PLAY mode.
- [ ] No Python implementation code is included in this specification document.
