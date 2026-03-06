# Milestone 7 Specification: Background & Aesthetic Enhancements

## Overview
This specification details the implementation of the Visual Asset and Aesthetic Standards introduced in Section 10 of the Constitution. The goal is to migrate visual environment properties (background images, edit mode indicators, and fallback colors) to an external YAML configuration, allowing dynamic styling without touching Python code.

## 1. Feature Requirements
### Environment Config (`config/environment.yaml`)
* A new file (`config/environment.yaml`) MUST be created to centralize aesthetic configurations.
* Required properties include:
  * `background_image`: Path to the image file to load (e.g., `assets/images/bg.png`).
  * `fallback_color`: The RGB tuple or hex color to use if the background image is missing.
  * `edit_mode_color`: The RGB color used for the visual border/overlay when in EDIT mode.
  * `play_mode_color`: The RGB color used for the visual border/overlay when in PLAY mode.

### Background Loading & Scaling
* The system must load the background image using Pygame (`pygame.image.load`).
* It must automatically scale the loaded image to fit `constants.WINDOW_WIDTH` and `constants.WINDOW_HEIGHT` using `pygame.transform.scale` or `pygame.transform.smoothscale`.
* **Fail Loudly & Fallback:** If the `background_image` path is invalid or the file is missing, the system must print an explicit error to the console (failing loudly) and immediately fall back to drawing the `fallback_color` as the screen background.

### State Visualization (Edit vs Play Modes)
* Beyond simply reading "Mode: EDIT" in the console or small UI text, a clear visual difference must indicate the current mode.
* Implement a colored border around the window or a subtle screen overlay that changes color depending on `mode` (using `edit_mode_color` and `play_mode_color` from the YAML file). For instance, a green border for PLAY mode and a yellow border for EDIT mode.

### No Hardcoding
* Hardcoded colors (like the background fill or border indicators) in `main.py` must be completely replaced by queries fetching data from `config/environment.yaml`.

## 2. Technical Considerations
* **Asset Location:** Images should be organized into an `assets/images/` directory.
* **Property Loading:** The `utils/config_loader.py` logic can be extended or reused to load `environment.yaml`.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating YAML Aesthetic Loading and Visual State Indicators
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Verify Initial YAML Load and State Indicators**
1. Provide a temporary placeholder background image (e.g., `assets/images/bg.png`) and define it in `config/environment.yaml`.
2. Launch the application (starts in `Mode: EDIT`).
3. **Success Check 1:** Obtain visual confirmation that the background image loads and scales to correctly fill the window (800x600).
4. **Success Check 2:** Obtain visual confirmation that the screen displays the "EDIT mode" visual indicator (e.g., a colored border).
5. Press `SPACE` to switch to `PLAY` mode.
6. **Success Check 3:** Obtain visual confirmation that the indicator changes immediately to the "PLAY mode" color/style.

**Step 2: Dynamic Updates Verification (Config Changes)**
1. While the game is closed, edit `config/environment.yaml` to change the `edit_mode_color` to a wildly different, noticeable color (e.g., bright purple `[255, 0, 255]`).
2. Launch the game.
3. **Success Check 4:** The EDIT mode visual indicator must now display the newly assigned color based solely on the YAML change.

**Step 3: Test "Fallback & Fail Loudly" Logic**
1. Close the game.
2. Open `config/environment.yaml` and set the `background_image` property to an invalid path (`assets/images/nonexistent_bg.png`).
3. Launch the game.
4. **Success Check 5:** The game MUST NOT crash. It must log a clear warning in the terminal (fail loudly), and fallback to rendering the solid `fallback_color` securely across the 800x600 window.

**Sign-off:** The feature is complete when the user can explicitly see mode changes instantly, configure the background image externally, and rely safely on YAML-driven fallbacks for visual assets.
