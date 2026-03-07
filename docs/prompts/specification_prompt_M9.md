Role:
You are the Specification Design Agent for the "Incredible Machines" project. Your job is to take the current project state, the architectural rules defined in docs/CONSTITUTION.md, and the current milestone goals to write a clear, technical specification document.

Context:
We are beginning Milestone 9: UI Overhaul & Interaction Systems. We need to transition from the current debug-text overlay to a professional, structured graphical user interface.

Please read the newly added "Section 11: User Interface (UI) Standards" in docs/CONSTITUTION.md before proceeding.

Task:
Generate the specification document docs/SPECIFICATION_M9_UIOverhaul.md. This document must detail the technical plan for building the UI system according to the following requirements:

Layout Requirements:

Top Bar (Operations): Spans the top of the screen (e.g., 50px high). Contains buttons for Play, Edit, Save, Load, Challenges, Help.

Side Panels (Object Palettes): Spans the left and right sides (e.g., 100px wide). Used for selecting parts to place.

Bottom Bar (Information): Spans the bottom of the screen (e.g., 40px high). Contains placeholder text for Score and Timer.

Playable Area & Physics Boundaries:

Define a playable_rect that represents the screen space inside the UI frames.

Specify that the Pymunk static boundaries (floor, ceiling, walls) must be moved inward to align with this playable_rect so objects cannot bounce behind the UI.

Lightweight UI Manager:

Specify the creation of utils/ui_manager.py.

Detail a minimal, custom class structure (e.g., UIManager, UIButton, UIPanel) to handle drawing rectangles, rendering text/icons, and processing mouse clicks, without relying on heavy external libraries like pygame_gui.

Dynamic Object Palettes (Data-Driven):

Specify how the side panels will populate dynamically by reading the variants from config/entities.yaml.

Detail the "Auto-Generating Icons" feature: The UI should create temporary Pygame Surfaces, ask each entity to draw itself onto that surface, and use that surface as the button's icon.

Interaction & State Feedback:

Click Filtering: Detail how the main loop must pass events to the ui_manager first. If the UI claims the click, the game must NOT spawn or grab a physics object.

Active Tool Selection: Clicking an object button sets an active_tool state variable in main.py rather than relying on keyboard shortcuts.

Ghost Cursor: Specify that when in EDIT mode and an active_tool is selected, a semi-transparent version of that tool must be drawn at the mouse coordinates (if hovering over the playable_rect).

Graceful Stubs:

Emphasize that buttons for features that do not exist yet (Save, Load, Challenges) must use placeholder functions that simply print "Not Implemented" to the console.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan. Implementation will be handled by a separate agent.