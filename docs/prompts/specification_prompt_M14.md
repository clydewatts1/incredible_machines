Role: Specification Design Agent

Context: We are beginning Milestone 14: Instance Property Editing. Please review the updated CONSTITUTION.md (specifically Section 3 regarding the Property Inheritance Model and Section 11 regarding the Input Focus State).

Task: Generate the specification document SPECIFICATION_M14_Properties.md.

Requirements for the Specification:

Object Selection & UI Integration: * Detail how clicking an object in EDIT mode selects it.

Specify how selecting an object changes the Right Panel from the "Object Palette" into a "Properties Panel" for the selected instance, displaying its current attributes.

The Inheritance Precedence Model:

Detail the data hierarchy: Type (base engine) -> Object (entities.yaml) -> Instance (active object on canvas).

Explain how the Instance attributes dictionary overrides the base definitions, and how it falls back to entities.yaml if an attribute isn't overridden.

Editing & Adding Attributes:

Specify UI mechanics for adding a new attribute (requires inputting an Attribute Name/Key).

Differentiate between editing "Short" values (single-line text, floats, ints) and "Long" values (multiline text/JSON payloads).

Detail the "draft" state flow: Edits should be held in a temporary state and only applied to the actual Instance when the user clicks "Save/Apply" (or discarded on "Cancel").

Pygame Text Input Manager:

Detail the expansion of utils/ui_manager.py to include UITextInput and UITextArea components to handle keystrokes, backspaces, and multiline rendering.

Crucial: Enforce the "Input Focus State" rule. Detail how the UIManager will suspend global game hotkeys (like Spacebar or Delete) when a text box is actively selected.

Save/Load System Updates:

Detail how the Level Manager must be updated to ensure Instance overrides (including complex JSON payloads) are serialized into the level save files and deserialized accurately upon loading.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.