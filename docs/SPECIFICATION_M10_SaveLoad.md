# Specification: Milestone 10 - Save and Load System

## Overview
This specification details the technical plan for Milestone 10: replacing the "Save" and "Load" UI stubs with a fully functional serialization and deserialization system. This will allow players to save the current state of their canvas (including all dynamically placed parts) to a file and restore it later.

## Goals
- Implement a flexible data serialization format (YAML) for saving level layouts.
- Establish a dedicated local directory (`saves/`) for storing these layout files.
- Enable "Quick Save" and "Quick Load" buttons to rapidly persist and restore canvas state to a default file.
- Enable explicit "Save" and "Load" buttons that utilize native OS file dialog boxes (e.g., via `tkinter`) allowing the user to browse and specify a particular filename for persisting and restoring the canvas state.
- Automatically switch the game mode back to "EDIT" whenever a layout is loaded (either via Quick Load or Explicit Load).
- Ensure the save/load mechanism gracefully handles the Pymunk physics space state.

## Technical Implementation Details

### 1. Data Serialization Format
- **Format:** YAML format will be used for saving layouts to align with our `entities.yaml` standard.
- **Payload Structure:** The saved file will contain a parent dictionary with a high-level `entities` list.
- **Entity Record required fields:**
  - `entity_id` (string): The identifier used to look up the entity in `entities.yaml` (e.g., "bouncy_ball", "wooden_ramp").
  - `position` (object): The (x, y) coordinates of the entity's Pymunk body.
    - `x` (float)
    - `y` (float)
  - `rotation` (float): The angle of the entity's Pymunk body (in radians, matching Pymunk's internal representation).
- **Extensibility:** The schema should optionally allow for arbitrary additional metadata per entity (e.g., specific joint connections or localized state depending on the entity type).

### 2. File I/O and Storage
- **Directory:** A new directory named `saves/` will be created in the project root to store level layouts.
- **Saving Mechanisms:** 
  - **Quick Save/Load:** Rapidly writes/reads to a hardcoded file: `saves/quicksave.yaml`.
  - **Explicit Save/Load:** Triggers a separate, native GUI dialog box allowing the user to browse their directories and provide a custom filename (e.g., `saves/my_level.yaml`) without relying on the terminal prompt.
- **Error Handling:** The system must handle cases where the directory does not exist (creating it automatically) or the file cannot be read/written gracefully, catching exceptions and printing standard error logs instead of crashing.

### 3. The "Save" and "Quick Save" Actions
- **Trigger:** Clicking the "Save" or "Quick Save" `UIButton`s in the Top Bar (replaces current stubs). "Save" must summon a separate GUI dialog box for file selection, whereas "Quick Save" bypasses prompts entirely.
- **Data Extraction Logic:**
  - The callback function will iterate through the `entities` list managed in `main.py`.
  - For each `GamePart` (or subclass instance), extract its variant key or `entity_id`.
  - Access the underlying `pymunk.Body` of the object to retrieve its exact current `position` (x, y) and `angle` (rotation).
  - Construct a Python dictionary matching the payload structure defined above.
- **Serialization:** Dump the aggregated list of entity dictionaries into the specified YAML file (`saves/[filename].yaml` or `saves/quicksave.yaml`) using Python's standard or third-party `yaml` module.

### 4. The "Load" and "Quick Load" Actions
- **Trigger:** Clicking the "Load" or "Quick Load" `UIButton`s in the Top Bar. "Load" must summon a separate GUI dialog box for file selection, whereas "Quick Load" bypasses prompts entirely and attempts to load `quicksave.yaml`.
- **Mode Reset:** Upon triggering either load action, the game state `mode` MUST be explicitly set back to `"EDIT"`.
- **State Cleanup:**
  - Before loading, the existing canvas must be cleared exactly like a full restart.
  - Iterate through the active `entities` list. For each entity, safely remove its `Shape` and `Body` from the `pymunk.Space` (handling static vs dynamic body differences appropriately).
  - Clear the `entities` rendering list.
- **Instantiation Process:**
  - Open and parse the target YAML file. If the file doesn't exist, log an error and abort gracefully.
  - Iterate through the `entities` array in the loaded data.
  - For each record, read the `entity_id`, `position`, and `rotation`.
  - Instantiate a new `GamePart` (or appropriate sub-class) using the `entity_id`, placing it at the specified (x, y) coordinates.
  - Explicitly set the new object's body `angle` to the saved `rotation` value.
  - Reindex the Pymunk space for any static bodies as necessary (`space.reindex_static()`).
  - Append the newly spawned objects to the `entities` list.

## Acceptance Criteria
- [ ] A `saves/` directory is utilized for storing layout data.
- [ ] Clicking "Quick Save" or "Quick Load" accurately persists/restores layout state to/from `saves/quicksave.yaml` without user dialogs.
- [ ] Clicking "Save" or "Load" summons a separate, native OS file dialog box to specify a filename to persist/restore layout state to/from a custom file.
- [ ] On any successful successful Load action, the application automatically ensures the mode returns to EDIT.
- [ ] The "Load" action safely destroys all currently spawned dynamic objects from the Pymunk space and Pygame rendering list.
- [ ] Data is serialized correctly in YAML format.
- [ ] The save and load actions are bound to their respective UI buttons in the Top Bar.
- [ ] No Python implementation code is included in this specification document.
