# Implementation Plan: Milestone 11 - Object Deletion & Canvas Clearing

## Overview
This document provides a high-level sequence of actionable phases for implementing the object deletion mechanics specified in `docs/SPECIFICATION_M11_ObjectDeletion.md`. As per architectural guidelines, these phases grant autonomy to the implementing agent regarding the exact algorithms and filtering methods used.

## Implementation Phases

### Phase 1: Entity Cleanup Logic
**Goal:** Establish a robust mechanism for safely removing physics bodies, shapes, and rendering instances for dynamically placed objects.
**Target Files:** `main.py` (or a dedicated physics utility)
- Identify the most effective method to segregate user-placed entities from static environment boundaries (e.g., floor, walls).
- Create a dedicated cleanup function (or method) that accepts an entity and completely obliterates its presence from `pymunk.Space` and the global Pygame `entities` rendering list.
- Ensure the method fails gracefully if an invalid or already-deleted entity is passed.
**Testing/Acceptance:** Code inspection verifies that the cleanup effectively wipes a target without removing static UI boundaries.

### Phase 2: Right-Click Detection
**Goal:** Map the right mouse button (mouse button 3) during "EDIT" mode to trigger the deletion of an object underneath the cursor.
**Target Files:** `main.py`
- Update the main event loop to listen for right-click events (`MOUSEBUTTONDOWN` with button 3).
- Implement a spatial query (e.g., using `space.point_query` or iterating over entity rectangles) to determine if a valid user-placed object exists at the mouse coordinates.
- If a valid object is found and the game is in "EDIT" mode, pass that object to the cleanup logic established in Phase 1.
**Testing/Acceptance:** Run the game, place various objects in EDIT mode, and verify that right-clicking exactly on an object removes it without crashing. Verify clicking empty space does nothing.

### Phase 3: UI Integration
**Goal:** Introduce a "Clear" button in the Top UI Bar that obliterates all user-placed objects simultaneously.
**Target Files:** `main.py`
- Modify the UI setup logic to include a new Top Panel button labeled "Clear".
- Write a callback function for this button that loops through all user-placed objects in the canvas and processes them through the cleanup logic defined in Phase 1.
- Ensure this bulk deletion respects the "EDIT" mode safety constraints.
**Testing/Acceptance:** Run the game, clutter the screen with shapes, and click the "Clear" button in EDIT mode. Verify the canvas is reset cleanly while boundary walls remain intact.
