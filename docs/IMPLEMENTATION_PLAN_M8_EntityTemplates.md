# Milestone 8: Implementation Plan (Entity Templates & Variant Inheritance)

This document provides a sequential roadmap for implementing deep-merge configuration inheritance, dynamic geometric templates, and sprite rotation scaling per the M8 Specification.

## Phase 1: Data Architecture & Inheritance

### Task 1: Refactor `config/entities.yaml`
**Objective:** Restructure the YAML file to explicitly separate base definitions from distinct game objects.
**Actions:**
1. Open `config/entities.yaml`.
2. Create a top-level `templates:` dictionary.
3. Define base templates: `Square`, `Rectangle`, `Circle`, `Diamond`, `Half-Circle`, `Quarter-Circle` with default properties (e.g., `mass`, `friction`).
4. Create a top-level `variants:` dictionary.
5. Move existing objects (e.g., `bouncy_ball`, `long_ramp`) into `variants`.
6. Add `template: [TemplateName]` to each variant, removing redundant properties to rely on the template.
7. Create the `red_diamond` test variant referencing the `Diamond` template with an explicit `color` override.

**Validation (QA Rule):**
Attempt to run Python in the terminal and parse `yaml.safe_load("config/entities.yaml")`. Assert both `templates` and `variants` keys successfully parse.

### Task 2: Implement "Deep Merge" in `config_loader.py`
**Objective:** Re-write the property retrieval utility to support variant-to-template inheritance.
**Actions:**
1. Open `utils/config_loader.py`.
2. Retrieve the raw YAML dictionary.
3. Fetch the requested `variant_key` from the `variants` block.
4. Extract its `template` string. Fetch that base dictionary from the `templates` block.
5. **Fail Loudly:** If the variant or its defined template does not exist, explicitly print an error and `sys.exit(1)` or `raise ValueError` to prevent the engine from running blindly.
6. Perform a Deep Merge: Copy the template dictionary, then iterate over the variant dictionary keys. Overwrite the template's keys with the variant's specific values. Return the merged dictionary.

**Validation (QA Rule):**
Write a temporary test block in `config_loader.py` that loads `red_diamond`. Programmatically assert its color is red, but its mass inherited the value from `Diamond`. Run the file directly to prove the logic.

## Phase 2: Physics Geometry & Visuals

### Task 3: Create Geometry Utility (`utils/geometry.py`)
**Objective:** Isolate complex mathematical vertex generation to keep the base entity class clean.
**Actions:**
1. Create `utils/geometry.py`.
2. Implement `get_diamond_vertices(width, height) -> list[tuple]`.
3. Implement `get_arc_vertices(radius, start_angle, end_angle, segments=15) -> list[tuple]`. Use `math.cos` and `math.sin` to generate points along the curve. Combine endpoints back to `(0,0)` to close the polygon for `Half-Circle` and `Quarter-Circle`.

**Validation (QA Rule):**
Call `get_diamond_vertices(10, 20)` manually and assert the returned point list matches `[(0, -20), (10, 0), (0, 20), (-10, 0)]`.

### Task 4: Refactor Entity Base Class for Templates & Sprites
**Objective:** The base `GamePart` must dynamically generate Pymunk shapes from the Deep Merged dictionary and handle texture rotation correctly.
**Actions:**
1. Open `entities/base.py`.
2. Inside `__init__`, evaluate `self.properties["template"]`. 
3. Dynamically create the `self.shape`:
   * If `Circle` -> `pymunk.Circle`
   * If `Rectangle` -> `pymunk.Poly.create_box`
   * If `Diamond/Half-Circle` -> Call `utils.geometry` and pass vertices to `pymunk.Poly`.
4. Implement Texture Loading & Scaling: Pre-scale `self.base_texture` to exactly bound the generated shape's extreme dimensions.
5. **Fail Loudly:** If `texture_path` fails to find the image, explicitly `print()` the error and set `self.base_texture = None`.
6. Refactor `draw()` (or `draw_texture()`): Call `pygame.transform.rotate` using exactly `-math.degrees(self.body.angle)`.

**Validation (QA Rule):**
Temporarily hack `main.py` to instantiate `GamePart(space, "red_diamond", 100, 100)`. Launch the game. Ensure it doesn't crash, proving geometric dynamic initialization works.

## Phase 3: Final Integration

### Task 5: Dynamic Key Mapping in `main.py`
**Objective:** Allow human-in-the-loop manual testing by hooking keyboard events to spawn variants dynamically based on YAML keys, updating the UI to match.
**Actions:**
1. Open `main.py`.
2. On initialization, iterate through the loaded `variants` from `config_loader.py`.
3. Extract `key_bind` and `label` properties to build the UI overlay string (e.g., `1: Bouncy Ball, 2: Long Ramp...`).
4. In the EDIT mode event loop, evaluate `event.unicode` against the loaded `key_bind` mappings.
5. Spawn the matched variant via `GamePart(space, m_x, m_y, mapped_variant_key)` natively, eliminating specific hardcoded subclasses or hardcoded `if event.key == pygame.K_1` logic.

**Validation (QA Rule):**
Execute the formal "Manual Test Script" defined in `docs/SPECIFICATION_M8_EntityTemplates.md`. Pressing the dynamically assigned keys MUST drop visually distinct shapes that inherit properly, collide gracefully, and rotate synchronously. The on-screen UI text MUST display exactly the keys mapped in the YAML file.
