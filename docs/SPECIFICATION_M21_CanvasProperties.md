# Milestone 21: Canvas Properties & Environments - Specification

## 1. Overview
Milestone 21 introduces the ability to configure global canvas properties on a per-level basis. This includes both physical environment settings (Gravity, Damping) and visual settings (Background Images/Colors). These configurations will be persisted within the level YAML files, allowing unique "worlds" or "challenges" with different physical rules and aesthetics.

## 2. Goals
- **Global Physics Control**: Allow dynamic adjustment of the Pymunk space gravity and damping.
- **Visual Customization**: Support custom background colors or images for the playable area.
- **Level Settings UI**: Provide a dedicated interface for modifying these global properties during Edit Mode.
- **Enhanced Serialization**: Update the Level Loader/Saver to handle a global `canvas_settings` block.

## 3. Technical Implementation Details

### 3.1 Global Physics Properties
The Pymunk `space` object will be updated dynamically when level settings are modified or loaded.
- **Gravity**: A 2D vector `(x, y)`. Controls the direction and strength of the downward (or sideward) pull.
- **Damping**: A float value (0.0 to 1.0). Controls the global "friction" of the air/environment. A value of 0.9 means objects retain 90% of their velocity per second.

### 3.2 Visual Backgrounds
The background must be rendered as the first layer in the main loop, restricted to the `playable_rect`.
- **Background Color**: A standard RGB tuple.
- **Background Image**: A string filename pointing to an asset. 
  - Pygame should scale the image to fit the `playable_rect` or tile it if preferred (scaling is recommended for simplicity).
  - The background must be drawn *before* any entities or physics debug shapes.

### 3.3 Level Settings UI
A new "Level Settings" interaction mode will be added.
- **Button**: A "Level" or "Settings" button added to the Top Bar.
- **Interaction**: Clicking this button updates the Right Panel to show a specific "Canvas Property Editor".
- **Fields**: Utilizing the M14 text input system, the following fields will be provided:
  - `Gravity X` (Float)
  - `Gravity Y` (Float)
  - `Damping` (Float)
  - `Background` (String/Color)

### 3.4 Serialization (YAML Format)
The `utils/level_manager.py` will be updated to handle a new root-level key.
```yaml
canvas_settings:
  gravity: [0, 900]
  damping: 0.99
  background: "classic_blueprint.png"
entities:
  - uuid: "..."
    entity_id: "bouncy_ball"
    # ...
```
- **Loader**: Must look for the `canvas_settings` block. If missing, it uses defaults from `constants.py`.
- **Saver**: Must extract current space/render properties and write them to the top of the YAML file.

## 4. Acceptance Criteria
- [ ] A "Level Settings" button exists and opens a configuration panel on the right.
- [ ] Changing Gravity X/Y or Damping in the UI immediately updates the Pymunk simulation behavior in Play Mode.
- [ ] Entering a valid image path or color hex code updates the canvas background visually.
- [ ] Saved levels correctly restore their custom gravity, damping, and background settings upon being loaded.
- [ ] Default values are correctly applied to legacy level files missing the `canvas_settings` block.
