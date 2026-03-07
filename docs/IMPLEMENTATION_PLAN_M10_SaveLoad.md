# Implementation Plan: Milestone 10 - Save and Load System

## Overview
This document outlines the step-by-step implementation plan for adding a functioning save and load system to "Incredible Machines," based on the specifications in `docs/SPECIFICATION_M10_SaveLoad.md` and architectural rules in `docs/CONSTITUTION.md`.

## Implementation Phases

### Phase 1: Level Manager Setup
**Goal:** Establish the saving directory and the core level manager utility class that handles JSON file interactions.
**Target Files:** `utils/level_manager.py` (New File)
- Import the standard `yaml` and `os` libraries.
- Create a `LevelManager` class.
- In the constructor (or initialization method), ensure a `saves/` directory exists in the project root: `os.makedirs("saves", exist_ok=True)`.
- Define the default save path as `saves/quicksave.yaml`.
- Create empty stub methods: `save_level(entities)` and `load_level()`.
**Testing/Acceptance:** Instantiate the `LevelManager` in a test script or `main.py` setup, run the game, and verify that the `saves/` folder is automatically created in the project root.

### Phase 2: Implementing 'Save' and 'Quick Save'
**Goal:** Implement the logic to extract entity data from the active Pymunk/Pygame instances and write it to the YAML file.
**Target Files:** `utils/level_manager.py`
- Complete the `save_level(entities, filepath=None)` method.
- Initialize an empty list called `level_data`.
- Iterate through each `entity` in the provided `entities` list.
- For each entity, construct a dictionary containing:
  - `"entity_id"`: Access `entity.variant_key` (or equivalent identifier).
  - `"position"`: Dictionary containing `"x": entity.body.position.x` and `"y": entity.body.position.y`.
  - `"rotation"`: Access `entity.body.angle`.
- Append this dictionary to `level_data`.
- Open the specified filepath (or the default `quicksave.yaml`) in write mode (`"w"`) and use `yaml.dump` to serialize `{"entities": level_data}` to the file.
**Testing/Acceptance:** Construct a mock list containing a dummy entity with a specific position/angle, pass it to `save_level()`, and verify the YAML file contains the expected output format.

### Phase 3: Implementing 'Load' and 'Quick Load'
**Goal:** Implement the logic to safely clear the Pymunk Space, read the YAML file, and return the data needed to recreate the entities.
**Target Files:** `utils/level_manager.py`, `main.py`
- Complete the `load_level(filepath=None)` method in `LevelManager`.
- Use `os.path.exists()` to check if the target block exists. If not, return an empty list or `None`.
- Open the file in read mode (`"r"`) and parse it with `yaml.safe_load`. Return the `"entities"` list.
- In `main.py` (or the equivalent logic managing the space), implement a `clear_canvas(space, entities)` function:
  - Iterate through `entities` and remove their respective shapes and bodies from the `pymunk.Space`.
  - Clear the `entities` Python list.
- Implement the spawning logic following a load:
  - Iterate through the returned `level_data`.
  - Use the `"entity_id"` to instantiate a new `GamePart`.
  - Place it at the specified `"position"` (x, y) coordinates.
  - Set its `body.angle` to the `"rotation"`.
  - Reindex the space if necessary via `space.reindex_static()`.
**Testing/Acceptance:** Create a manual call to the load logic with a pre-written JSON file, and ensure the game screen clears and the objects spawn exactly as defined in the test file.

### Phase 4: UI Integration
**Goal:** Connect the UI buttons to the newly written backend functions.
**Target Files:** `main.py`
- Import the newly created `LevelManager`.
- Import `tkinter` and `tkinter.filedialog` to support native OS dialogs.
- Instantiate `LevelManager` globally alongside `UIManager`.
- Locate the stub callbacks in the Top Panel creation loop (`add_top_btn("Save", ...)`).
- Replace the "Save" stub callback with a function that calls `level_manager.save_level(entities)`.
- Replace the "Load" stub callback with a function that calls the `clear_canvas` logic, then fetches data via `level_manager.load_level(filepath)`, and spawns the parts.
- Ensure any successful 'Load' or 'Quick Load' explicitly sets the global `game_state['mode'] = 'EDIT'`.
- Ensure the UI has four active buttons for this functionality:
  - `Quick Save`: Calls `save_level()` without arguments to overwrite `quicksave.yaml`.
  - `Quick Load`: Calls `load_level()` without arguments to read `quicksave.yaml` and switches to EDIT mode.
  - `Save`: Creates a hidden `tk.Tk()` window, calls `filedialog.asksaveasfilename()`, cleans up the window, and calls `save_level(filepath)`.
  - `Load`: Creates a hidden `tk.Tk()` window, calls `filedialog.askopenfilename()`, cleans up the window, calls `load_level(filepath)`, and switches to EDIT mode.
**Testing/Acceptance:** Run the game normally. Place several ramps and objects via the sidebar palettes. Click the "Quick Save" UI button. Verify `quicksave.yaml` updates dynamically on disk. Click "Quick Load" and verify the canvas is rebuilt and the game enters EDIT mode. Click "Save" and verify a native file dialog appears. Click "Load" and verify it reads the selected file properly to reconstruct the board and resets to EDIT mode.
