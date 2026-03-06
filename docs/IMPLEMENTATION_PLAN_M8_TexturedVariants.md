# Milestone 8: Implementation Plan (Entity Variants & Textured Sprites)

This document outlines the sequential steps to implement texture caching, Pymunk-synchronized rotation, and input-based variant spawning for "The Incredible Machine Clone" per the M8 Specification.

## Phase 1: Sprite Configuration & Caching

### Task 1: Define YAML Variants
**Objective:** Add specific variants the system will spawn, demonstrating single-class reusability with distinct properties.
**Actions:**
1. Open `config/entities.yaml`.
2. Add a `texture_path` key to the existing `default_properties` block, mapped to `""` (empty string) to prevent errors.
3. Rename the `static_ramp` key to `long_ramp`. Update its dimensions (e.g., length 200, thickness 10). Add `texture_path: "assets/images/wood_texture.png"`.
4. Create a new `small_ramp` block. Set smaller dimensions (e.g., length 50, thickness 5). Do *not* assign a texture, verifying the primitive fallback logic per the specification.

**Validation (QA Rule):**
Attempt to run Python in the terminal and parse `config/entities.yaml` manually to ensure the `long_ramp` has the `texture_path` key and values map correctly.

### Task 2: Base Entity Texture Caching
**Objective:** Update the base `GamePart` to load and cache the texture immediately, avoiding expensive disk reads during the render loop.
**Actions:**
1. Open `entities/base.py`.
2. In the `GamePart.__init__` method, retrieve `texture_path` from `self.properties`.
3. If the path exists and is not an empty string, attempt to load the image (`pygame.image.load`).
4. **Cache the Surface:** Store the loaded `pygame.Surface` on the instance as `self.base_texture`. 
5. **Fail Loudly Fallback:** Wrap the image loading in a `try/except FileNotFoundError` block. If it fails, print a loud warning to the console and cleanly set `self.base_texture = None` so the draw loop drops sequentially to the primitive rendering.

**Validation (QA Rule):**
In `main.py` add `test_r = Ramp(space, "long_ramp", 100, 100)` outside the loop. Launch the game and see if the console prints the "Fail Loudly" warning since `wood_texture.png` isn't created yet. Remove the test code after.

## Phase 2: Drawing and Transformation Hooks

### Task 3: Handle Pygame Transform Orientation
**Objective:** Implement the Constitution's `-math.degrees(self.body.angle)` instruction securely inside the entity's rendering logic.
**Actions:**
1. In `entities/base.py`, introduce a generic `draw_texture(self, surface)` method.
2. In `draw_texture`, check if `self.base_texture` exists.
3. If the texture exists, fetch the Pymunk body angle and invert it using `angle_degrees = -math.degrees(self.body.angle)`.
4. Call `pygame.transform.rotate(self.base_texture, angle_degrees)` to generate a *new*, temporary rotated surface. (This overhead is unavoidable for 2D sprites dynamically rotating in arbitrary physics structures).
5. Fetch the `rect` of the newly rotated surface. Center `rect.center` precisely at `(int(self.body.position.x), int(self.body.position.y))` to tie the visual natively to the center-of-mass of the physics body.
6. `surface.blit(rotated_surface, rect)`.

**Validation (QA Rule):**
N/A (Covered strictly in final integration).

### Task 4: Subclass Implementation hook
**Objective:** Update the specific entity to prioritize the texture, and scale the `base_texture` natively to match its actual YAML Pymunk size upon initialization.
**Actions:**
1. Open `entities/ramp.py`.
2. Update the `__init__` signature to accept a `variant_key`. Pass this `variant_key` explicitly to `super().__init__(space, variant_key)`.
3. In `__init__`, if `self.base_texture` exists, stretch it *once* to precisely match `length * 2` and `thickness`. Store this stretched version over `self.base_texture`.
4. In `draw(self, surface)`, change the logic: If `self.base_texture` is *not* `None`, call `self.draw_texture(surface)`. If it *is* `None`, execute the old `pygame.draw.line` primitive code.

**Validation (QA Rule):**
N/A (Covered strictly in final integration).

## Phase 3: Integration and Testing

### Task 5: Main Input Hooks
**Objective:** Hook the specific `small_ramp` and `long_ramp` keys to the simulation loop.
**Actions:**
1. Open `main.py`.
2. Modify the keydown events in EDIT mode.
3. Hook `pygame.K_1` to spawn `Ramp(space, "small_ramp", m_x, m_y)`.
4. Hook `pygame.K_2` to spawn `Ramp(space, "long_ramp", m_x, m_y)`.

**Validation (QA Rule):**
Pressing `1` and `2` spawns lines of distinct sizes.

### Task 6: Execute Manual Test Validation
**Objective:** Ensure rendering rotation and fallback rules are solid.
**Actions:**
1. Drop a dummy texture file in `assets/images/`.
2. Launch the game. Press `1` to spawn a small ramp. Press `2` to spawn a long ramp.
3. Check the lengths.
4. Rotate the `long_ramp` with the mouse wheel. Prove the texture tilts and tracks tightly with the Pymunk boundaries.
5. Exit game, rename the texture file, and run again. Assert that pressing `2` explicitly logs an error to the terminal, avoids crashing the physics space, and cleanly paints a solid geometric ramp instead.
