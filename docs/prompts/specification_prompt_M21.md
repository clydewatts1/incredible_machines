Role: Specification Design Agent

Context: We are beginning Milestone 21: Canvas Properties & Environments. We need the ability to configure global physics properties (gravity, damping) and visual properties (background image/color) on a per-level basis, and save these configurations inside our level YAML files.

Task: Generate the specification document docs/SPECIFICATION_M21_CanvasProperties.md.

Requirements for the Specification:

Global Physics Properties:

Detail how to configure Pymunk's space.gravity (an x, y tuple) and space.damping (a float between 0.0 and 1.0) dynamically.

Visual Backgrounds:

Detail the addition of a background_image or background_color property.

Specify how Pygame should render this background. It must be drawn first in the render loop, strictly contained within the playable_rect (scaled to fit or tiled).

Level Settings UI:

Specify adding a "Level Settings" button to the Top Bar.

When clicked, the Right Panel should populate with input fields for Gravity X, Gravity Y, Damping, and Background Image Name, utilizing the text input system built in M14.

Serialization (Save/Load Updates):

Detail how utils/level_manager.py must be updated. The YAML save format should now include a root-level canvas_settings block alongside the entities list.

Example:

canvas_settings:
  gravity: [0, 900]
  damping: 0.99
  background: "yorkie_light_blue.jpeg"
entities:
  # ... existing entity data ...


Detail how the Load function must parse these settings and apply them to the Pymunk Space and Pygame render loop before spawning entities. If canvas_settings is missing, it must fall back to hardcoded defaults.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.