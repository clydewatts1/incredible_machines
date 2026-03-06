# Milestone 8 Specification: Template-Variant Inheritance System

## Overview
This specification redefines the Entity creation pipeline, introducing a powerful Template-Variant inheritance model as mandated by the updated Section 9 of the Constitution. It also standardizes the geometric definitions of core primitives and solidifies the visual/texture handling pipeline.

## 1. Data Architecture Requirements
### YAML Structure
* `config/entities.yaml` must be refactored into two distinct sections:
    * `templates`: The base "DNA" definitions (e.g., `Circle`, `Rectangle`, `Diamond`).
    * `variants`: The actual instantiated game objects (e.g., `bouncy_ball`, `long_ramp`, `red_diamond`).

### Inheritance Logic (Deep Merge)
* When the game requests to spawn a variant, the `EnvironmentManager` or `ConfigLoader` must perform a dictionary "Deep Merge".
* Example: A `red_diamond` variant specifies its `template: "Diamond"`. The system loads the `Diamond` template properties, then recursively overwrites any matching keys with the specific `red_diamond` properties (like changing `color: [255, 0, 0]` or altering `mass`).

### Key Bindings & Dynamic UI
* Variants may optionally define a `key_bind` property in the YAML (e.g., `'1'`, `'2'`, `'Q'`).
* The render loop (`main.py`) MUST dynamically read these assigned keys from the loaded variants and build the on-screen UI overlay text dynamically. 
* The UI text must accurately reflect the specific spawn key and variant label (e.g., `Mode: EDIT (1: Bouncy Ball, 2: Red Diamond, 3: Half-Circle... )`) so the human player knows what keys trigger which shape.

## 2. Geometric Template Requirements
Entities will no longer have hardcoded physics shapes in their `__init__`. Instead, the base class will construct the `pymunk.Shape` dynamically based on the inherited template geometry.

* **Square & Rectangle:** 
  * YAML requires `width` and `height`.
  * Implementation: `pymunk.Poly.create_box(body, size=(width, height))`.
* **Circle:**
  * YAML requires `radius`.
  * Implementation: `pymunk.Circle(body, radius)`.
* **Diamond:**
  * YAML requires `width` (w) and `height` (h).
  * Implementation: A `pymunk.Poly` defined by the vertices `[(0, -h), (w, 0), (0, h), (-w, 0)]`.
* **Half-Circle & Quarter-Circle:**
  * YAML requires `radius` and `resolution` (number of segments).
  * Implementation: A loop generating vertices along the mathematical arc (using Sine/Cosine) passed into `pymunk.Poly`.

## 3. Visual & Texture Requirements (Per Section 10)
* **Optional Textures:** Every template or variant can optionally define a `texture_path`.
* **Rotation Sync:** If a texture exists, the `draw()` method must use `pygame.transform.rotate(image, -math.degrees(self.body.angle))` to correctly sync Pygame's drawing orientation with Pymunk's physics step.
* **Scaling:** Sprites must be scaled (stretched) during initialization to precisely fit the bounding box (width/height or radius*2) of the generated collision shape.
* **Primitive Fallback:** If `texture_path` is missing or the file is not found, the `draw()` method must fall back to drawing a primitive Pygame shape (e.g., `pygame.draw.polygon`) using the object's specified `color`.

## 4. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating Inheritance, Geometry, and Texture Sync
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Verify Inheritance (Deep Merge)**
1. Ensure the YAML defines a `Diamond Template` (with default mass 1.0) and a `red_diamond` Variant (overriding color to `[255, 0, 0]` and mass to `50.0`).
2. Launch the application in EDIT mode.
3. Spawn the `red_diamond`.
4. **Success Check 1:** Verify visually the diamond is red, proving it successfully inherited the shape geometry from the template but merged the color override.
5. Drop it to test physics. It should exhibit heavy mass behavior, proving physics data merged correctly.

**Step 2: Verify Complex Geometry**
1. Ensure the YAML defines a generic `half_circle` Variant.
2. Spawn the `half_circle` and drop a standard Ball directly on its curved edge.
3. **Success Check 2:** Verify the ball rolls perfectly smoothly over the mathematical arc geometry, proving the vertex generation for the Pymunk Polygon is accurate.

**Step 3: Verify Texture Sync**
1. Ensure the YAML defines a `textured_rectangle` Variant with a valid grid or wood `texture_path`.
2. Spawn the `textured_rectangle` and drop it into a dynamic collision (e.g., tumbling down a ramp).
3. **Success Check 3:** Verify that as the rectangle physically tumbles, its rendered image rotates perfectly in sync, with the texture borders aligning exactly with the Pygame physics bounds.

**Sign-off:** The feature is complete when the user proves the data inheritance merges correctly, new geometries respond accurately to collisions, and textures track physics rotation flawlessly.
