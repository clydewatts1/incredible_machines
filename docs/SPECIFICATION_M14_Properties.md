# Specification: Milestone 14 - Instance Property Editing

## Overview
This specification details the technical architecture for Milestone 14, introducing per-instance property overrides and dynamic UI components for text input in the "Incredible Machines" project. This milestone enables users to select individual entities and modify their specific attributes (e.g., mass, custom logic payloads) independently of their base configuration, adhering to the newly established Property Inheritance Model and Input Focus State rules in the Project Constitution.

## Goals
- **Object Selection:** Enable users to select an individual instance in EDIT mode.
- **Dynamic UI Panels:** Dynamically convert the right-side UI panel from an Object Palette to a Properties Panel when an entity is selected.
- **Property Inheritance:** Implement a strict hierarchy where instance-level overrides take precedence over base YAML configurations.
- **Text Input Components:** Build reusable, safe Pygame text inputs (short strings, floats, ints) and text areas (multiline/JSON) that correctly manage input focus.
- **Data Persistence:** Ensure the Level Manager serializes and deserializes these instance-level overrides.

## Technical Implementation Details

### 1. Object Selection & UI Integration
- **Selection Mechanic:** In EDIT mode, left-clicking on a valid Pymunk shape associated with an entity will select that entity (the active instance).
- **Panel Transformation:** 
  - When no entity is selected, the Right Panel displays the standard "Object Palette" (list of spawnable variants).
  - When an entity is selected, the Right Panel switches to a "Properties Panel." This panel will visually display the attributes of the selected instance, including both its active inherited base properties and its explicit instance overrides.

### 2. The Inheritance Precedence Model
The system must resolve properties using a three-tier data hierarchy:
- **Level 1: Type (Base Engine):** The lowest level, defined by hardcoded defaults in the base classes (e.g., `mass=1.0` if totally unspecified).
- **Level 2: Object (entities.yaml):** The base configuration loaded from `config/entities.yaml` for that specific variant key (e.g., `cannon`).
- **Level 3: Instance (Active Object on Canvas):** The highest level. Each instantiated entity will possess an `overrides` dictionary.
- **Resolution Logic:** When the game queries a property (e.g., `entity.get_property("mass")`), it must first check the `overrides` dictionary. If the key exists, that value is returned. If it does not exist, it falls back to parsing the base dictionary from `entities.yaml`.

### 3. Editing & Adding Attributes
- **Adding Attributes:** The Properties Panel must feature an "Add Property" button that prompts the user for a new Attribute Name/Key.
- **Data Types:**
  - **"Short" Values:** Attributes requiring brief inputs (single-line text, floats, ints) will use a standard `UITextInput` field.
  - **"Long" Values:** Attributes requiring multiline strings or JSON payloads (e.g., custom logic scripts) will use a `UITextArea` component.
- **The "Draft" State Flow:**
  - Modifying text within a `UITextInput` or `UITextArea` does *not* instantly mutate the entity's `overrides` dictionary.
  - The edits are maintained in a temporary text buffer (draft state) within the UI component.
  - The user must explicitly click a "Save/Apply" button to parse the string/JSON and commit it to the entity's `overrides` dictionary.
  - A "Cancel" button discards the draft and reverts the UI component to display the current active property.

### 4. Pygame Text Input Manager
- **Component Expansion:** `utils/ui_manager.py` will be expanded to include `UITextInput` (single-line) and `UITextArea` (multi-line) classes.
- **Functionality:** These components must handle internal blinking cursors, backspace deletion, and character rendering. `UITextArea` must support line wrapping and newline generation.
- **Enforcing "Input Focus State":** 
  - The `UIManager` must track which element currently holds focus. 
  - If a `UITextInput` or `UITextArea` is actively selected (has focus), the `UIManager` will process and consume *all* keyboard events.
  - This ensures global game hotkeys (e.g., pressing 'Delete' to remove an object, or 'Space' to toggle play/edit mode) are strictly suspended while the user is actively typing, preventing catastrophic accidental interactions.

### 5. Save/Load System Updates
- **Serialization:** The `LevelManager.save_level()` method must be updated. When iterating over entities, it must extract the custom `overrides` dictionary for each entity and serialize it into the JSON/YAML structure, alongside the standard position and rotation data.
- **Deserialization:** The `LevelManager.load_level()` method must read this `overrides` dictionary. When the engine instantiates the entity during Pass 1, it must inject this dictionary directly into the new entity's state, seamlessly restoring the custom properties.

## Acceptance Criteria
- [ ] Left-clicking an object in EDIT mode successfully targets it as the active selection and swaps the Right Panel to a Properties view.
- [ ] Properties resolve dynamically, with instance overrides taking precedence over `entities.yaml`.
- [ ] Users can edit existing properties or add entirely new custom properties to an instance via the UI.
- [ ] Edits utilize a draft state, confirming changes via "Save/Apply".
- [ ] Multi-line JSON can be inputted comfortably via a `UITextArea`.
- [ ] While a text box is focused, global hotkeys (Space, Delete) do not trigger game actions.
- [ ] Custom property overrides map persistently through a save/load cycle.
- [ ] No Python implementational code is included in this specification document.
