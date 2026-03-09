# Milestone 21: Canvas Properties & Environments - Implementation Plan

This document breaks down the implementation of global canvas properties (gravity, damping, and backgrounds) into three actionable phases.

## Phase 1: Serialization Updates
**Goal:** Update the level persistence layer to handle a global `canvas_settings` block.
**Target File:** `utils/level_manager.py`
**Steps:**
1.  **Modify `save_level`**: Update the signature to accept an optional `canvas_settings` dictionary.
2.  **Write Settings**: If the dictionary is provided, write it to the top of the YAML output under the key `canvas_settings`.
3.  **Modify `load_level`**: Update the return signature to include `canvas_settings` data as a third return value.
4.  **Default Handling**: Ensure the loader returns sensible defaults (e.g., gravity `[0, 900]`, damping `1.0`) if the `canvas_settings` block is missing from older save files.
**Verification:** Manually save a level and inspect the resulting `.yaml` file to ensure a `canvas_settings` block exists with the expected keys.

## Phase 2: Physics & Render Integration
**Goal:** Apply canvas settings to the Pymunk simulation and render high-quality backgrounds.
**Target File:** `main.py`
**Steps:**
1.  **Physics Application**: Update the `apply_level_data` function to receive the `canvas_settings` block.
2.  **Space Update**: Apply `gravity` and `damping` directly to the `pymunk.Space` instance.
3.  **Background Cache**: Use the `AssetManager` (from Milestone 16) to load and cache the background image specified in the settings. This prevents redundant file I/O every frame.
4.  **Render Pass**: In the main `draw` loop, render the background (scaled to fit the `playable_rect`) before any entities or physics objects are blitted.
**Verification:** Load a level with a custom background string and modified gravity. Hit "Play" and verify that entities react to the new gravity and the background is visible.

## Phase 3: UI Integration
**Goal:** Add a "Level Settings" panel to allow live editing of global environment properties.
**Target File:** `main.py`, `utils/ui_manager.py`
**Steps:**
1.  **Top Bar Button**: Add a "Level Settings" (or "Settings") button to the main UI top bar.
2.  **Panel Population**: Hook the button up to the properties panel logic. When clicked, it should populate the right panel with `UITextInput` fields for Gravity X, Gravity Y, Damping, and Background Image.
3.  **Properties Data Object**: Create a "dummy" or singleton object that holds the current canvas settings to allow the M14 Properties Panel to bind to its attributes.
4.  **Live Updates**: Ensure that changing a value in the UI immediately updates the `canvas_settings` state and the active `pymunk.Space`.
**Verification:** Open the Level Settings panel in EDIT mode, change the Background Image path, and verify the canvas updates instantly without requiring a restart.
