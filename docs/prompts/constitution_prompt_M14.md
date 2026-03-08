Role: Chief Architect

Context: We are preparing for Milestone 14: Instance Property Editing. This milestone introduces per-instance property overrides and Pygame text input components.

Task: Please update docs/CONSTITUTION.md to accommodate these structural changes.

Requirements for the update:

Update Section 3 (Data-Driven Design): Add a subsection defining the "Property Inheritance Model". Explicitly state that while entities.yaml is the source of truth for base definitions, instantiated entities are permitted to hold an overrides dictionary (e.g., custom mass, custom JSON payloads) that takes precedence over the base definition.

Update Section 11 (User Interface Standards): Add a rule titled "Input Focus State". Mandate that when a UITextInput or UITextArea component has active focus, the UIManager must consume all keyboard events, and all global game hotkeys (e.g., 'Delete' for object removal, 'Space' for play/edit toggle) must be strictly suspended to prevent accidental game actions while typing.

Output: Provide the completely updated CONSTITUTION.md text.