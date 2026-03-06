# Milestone 7: Implementation Plan (Background & Aesthetic Enhancements)

This document provides a sequential roadmap for adding YAML-driven visual environment features to "The Incredible Machine Clone" per Section 10 of the Constitution. It specifically isolates asset loading from the rendering loop to ensure optimal performance.

## Phase 1: Environment Logic and Assets

### Task 1: Setup Asset Structure and YAML Config
**Objective:** Establish the directory structure for images and define the initial configuration settings.
**Actions:**
1. Create directory `assets/images/`.
2. Create mapping file `config/environment.yaml`.
3. Populate `environment.yaml` with the required keys:
   * `background_image`: `"assets/images/bg.png"`
   * `fallback_color`: `[50, 50, 50]` (A dark grey)
   * `edit_mode_color`: `[255, 200, 0]` (Yellow/Gold)
   * `play_mode_color`: `[0, 255, 0]` (Green)

**Validation (QA Rule):** 
Attempt to load `config/environment.yaml` manually via a python REPL and assert the 4 keys exist; ensure `yaml.safe_load` parses the color lists correctly.

### Task 2: Implement `EnvironmentManager`
**Objective:** Create a dedicated utility to handle image loading, scaling, and the mandatory "Fail Loudly" fallback, strictly separating this logic from `main.py`.
**Actions:**
1. Create `utils/environment_manager.py`.
2. Implement `EnvironmentManager` class (or singleton) with an `initialize(screen_width, screen_height)` method.
3. It must load `config/environment.yaml` utilizing `yaml.safe_load`.
4. It must attempt to load the `background_image` path via `pygame.image.load()`.
5. **Fail Loudly & Fallback:** Put the image load in a `try/except` block. If it fails (e.g. `FileNotFoundError`), it MUST `print()` an explicit error to the terminal, cache `None` for the image, and save the `fallback_color`.
6. If the image loads successfully, it MUST use `pygame.transform.scale` to fit the image to `(screen_width, screen_height)` and cache it.
7. Implement a `draw_background(surface)` method that blits the cached scaled image, OR `surface.fill(fallback_color)` if the image is `None`.
8. Provide getter methods for `edit_mode_color` and `play_mode_color`.

**Validation (QA Rule):** 
In `main.py`, temporarily call `EnvironmentManager.initialize()` before the game loop. Ensure the debug print triggers if `assets/images/bg.png` doesn't exist yet, proving the fallback branch works safely.

## Phase 2: Main Loop Rendering Integration

### Task 3: Refactor Main Render Loop (Background)
**Objective:** Connect the `EnvironmentManager` to `main.py`'s draw execution.
**Actions:**
1. In `main.py`, call `env_manager.initialize(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT)` right after `pygame.init()`.
2. Replace `screen.fill(constants.COLOR_BACKGROUND)` inside the `while running` loop with `env_manager.draw_background(screen)`.

**Validation (QA Rule):** 
Run the game. The screen should be completely filled with the `fallback_color` (dark grey) from the YAML file, since we haven't created `bg.png` yet.

### Task 4: Implement Mode-Specific Border Logic
**Objective:** Provide a glaringly obvious visual distinction between Edit and Play modes using the YAML colors.
**Actions:**
1. In `main.py`, just before `pygame.display.flip()`, evaluate the current `mode`.
2. Fetch the appropriate color from `EnvironmentManager` (`edit_mode_color` or `play_mode_color`).
3. Draw a thick rectangle border (e.g., width=10) around the perimeter of the screen using `pygame.draw.rect`.

**Validation (QA Rule):** 
Run the game. The border should default to Yellow (Edit mode). Press `SPACE`. Check if the border seamlessly changes to Green (Play mode).

## Phase 3: Final System Testing

### Task 5: Execute Manual Test Script
**Objective:** Formally prove the end-to-end functionality of dynamic aesthetic switching per the M7 Specification.
**Actions:**
1. We will use a python script to quickly generate a dummy `bg.png`. 
2. Launch the game to verify the image successfully replaces the fallback color and scales properly.
3. Edit `environment.yaml` externally to change the `edit_mode_color` to `[255, 0, 255]` (Purple).
4. Launch the game and verify the border is purple.
5. Edit `environment.yaml` to point `background_image` to a broken path. Launch the game and verify the loud terminal error prints and the grey fallback color handles the rendering gracefully.
