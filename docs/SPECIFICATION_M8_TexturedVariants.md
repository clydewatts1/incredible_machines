# Milestone 8 Specification: Entity Variants & Textured Sprites

## Overview
This specification details the implementation of Entity Variants and Sprite-based rendering, adhering to the newly updated Section 10 of the Constitution. The goal is to allow multiple variants of the same base logic (e.g., small and long ramps) strictly defined via `config/entities.yaml`, and to seamlessly integrate textured sprites that follow Pymunk's physics rotation.

## 1. Feature Requirements
### YAML Variants
* Extend `config/entities.yaml` to define distinct variants representing the same underlying Python class.
* Introduce `small_ramp` and `long_ramp` blocks. Both will utilize the `Ramp` Python class but will supply different dimensional properties (e.g., `length` and `thickness`).

### Sprite Feature Integration
* Introduce a `texture_path` key within the YAML definitions (e.g., `texture_path: "assets/images/ramp_texture.png"`).
* The base `GamePart` (Entity) class must evaluate this property. If present, it must load the image into a `pygame.Surface` and cache it to avoid I/O bottlenecks during the physics loop.

### Rotation Handling (The Constitution Rule)
* Per Section 10 of the Constitution, sprite rendering must strictly sync with Pymunk's physics logic. 
* The `draw()` method must compute the rotation using: `-math.degrees(self.body.angle)`. This resolves the mathematical inversion between Pygame's drawing coordinates and Pymunk's physics coordinate planes.

### Fallback Logic
* If an entity declares a `texture_path` but the file is missing from the disk, the engine MUST catch the `FileNotFoundError` explicitly, failing loudly via a console warning, and safely fall back to rendering its standard primitive shape (e.g., the `pygame.draw.line` or `pygame.draw.polygon`).

## 2. Technical Considerations
* **Key Bindings:** The `main.py` input logic will be updated. Pressing the `1` key will spawn a `small_ramp` and `2` will spawn a `long_ramp`.
* **Image Scaling/Repeating:** For scalable objects like ramps, `pygame.transform.scale` should be used to stretch the texture to match the entity's physical dimensions defined in YAML.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating Variants and Sprite Rotation
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Verify Entity Variants via Keybinds**
1. Ensure the placeholder texture (e.g., `assets/images/ramp_texture.png`) is generated.
2. Launch the application (starts in `Mode: EDIT`).
3. Press `1` and click/move the mouse to spawn and drop a "Small Ramp".
4. Press `2` to spawn a "Long Ramp" next to it.
5. **Success Check 1:** Verify the two ramps have visibly distinct physical lengths, despite being spawned by the same base Python `Ramp` class.

**Step 2: Verify Texture Stretching and Rotation**
1. While still in `Mode: EDIT`, grab the Long Ramp and rotate it using the mouse scroll wheel (or Q/E keys).
2. **Success Check 2:** Verify that the rendered texture accurately tilts to identically match the Pymunk physics bounding box boundaries.

**Step 3: Test Primitive Fallback Logic**
1. Close the game.
2. Open `config/entities.yaml` and modify the `long_ramp`'s `texture_path` to an invalid string (e.g., `"missing_texture.png"`).
3. Relaunch the game. Press `2` to spawn a "Long Ramp".
4. **Success Check 3:** The game MUST NOT crash. A clear warning must print to the console, and the Long Ramp must seamlessly render using its fallback primitive geometry (the solid colored line/polygon).

**Sign-off:** The feature is complete when the user can spawn distinct YAML variants, observe mathematically accurate sprite rotation, and rely cleanly on primitive fallbacks.
