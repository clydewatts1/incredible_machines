Role:
You are the Specification Design Agent for the "Incredible Machines" project. Your job is to take the current project state, the architectural rules defined in docs/CONSTITUTION.md, and the current milestone goals to write a clear, technical specification document.

Context:
We are beginning Milestone 10: Save and Load System.
In the previous milestone, we implemented a complete UI Overhaul (utils/ui_manager.py) with "Save" and "Load" buttons in the Top Bar that currently act as stubs (printing to the console).
The goal of this milestone is to replace those stubs with actual functionality to serialize the canvas objects (their types, positions, and rotations) to a file, and deserialize them back onto the canvas.

Task:
Generate the specification document docs/SPECIFICATION_M10_SaveLoad.md. This document must detail the technical plan for building the save/load system according to the following requirements:

Data Serialization Format:

Specify the format to be used for saving levels (JSON or YAML is recommended to align with our existing entities.yaml approach).

Define the required payload for each saved entity. At a minimum, it must record:

entity_id (e.g., "bouncy_ball", "wooden_ramp")

position (x, y coordinates)

rotation (angle in degrees or radians)

Any other specific metadata needed to recreate the object.

File I/O and Storage:

Specify a dedicated directory for saving these layouts (e.g., a new saves/ or levels/ folder).

Decide on a saving mechanism: Will it quick-save to a hardcoded file (e.g., saves/quicksave.json), or utilize a basic file dialog to name the save? (Recommend starting with a hardcoded quicksave.json or custom_level.yaml for simplicity in this milestone).

The "Save" Action:

Detail the logic for iterating through all active entities currently in the Pymunk space/Pygame render list.

Explain how to extract their exact Pymunk coordinates and rotations to build the data dictionary.

Specify how to connect this logic to the existing "Save" UIButton in main.py.

The "Load" Action:

Detail the state cleanup process: Before loading a new layout, the game must safely remove all current dynamic and static entities from the Pymunk Space and clear the rendering lists.

Detail the instantiation process: Iterate through the loaded file data, use the entity_id to look up the object in entities.yaml, and spawn it at the specified coordinates and rotation.

Specify how to connect this logic to the existing "Load" UIButton in main.py.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan. Implementation will be handled by a separate agent.