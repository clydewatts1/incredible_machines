Role: Specification Design Agent

Context: We are beginning Milestone 17: Logic Wiring & Signals. We need to allow players to logically connect entities together (e.g., connecting a Basket to a Cannon so that when the Basket ingests an item, it sends a "signal" to the Cannon to fire).

Task: Generate the specification document docs/SPECIFICATION_M17_LogicWiring.md.

Requirements for the Specification:

The Wire Tool (UI & Interaction):

Specify a new tool state (e.g., WIRE_TOOL).

Detail the interaction: The user clicks a source entity (Sender), then clicks a target entity (Receiver) to create a logical link.

Specify that the link must map the source's UUID to the target's UUID.

Visualizing Connections:

Detail how these connections should be drawn in EDIT mode (e.g., drawing an anti-aliased line pygame.draw.aaline between the center coordinates of the connected entities).

Detail visual feedback for PLAY mode: When a signal is sent, the connection line should flash or briefly change color to show the flow of logic.

Signal Logic (Sender to Receiver):

Specify an interface or method (e.g., receive_signal(payload)) that active entities like the Cannon must implement.

Specify that the Basket (when it successfully ingests an accepted type) must look up its connected UUIDs and trigger their receive_signal() methods.

Important: Ensure this logic is decoupled from Pymunk's physics step to prevent simulation lockups (e.g., queue the signals and process them in the main update loop).

Save/Load System Updates:

Detail how the utils/level_manager.py must be updated to serialize a connections: [] list alongside the entities, saving the pairs of linked UUIDs.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria.

CRITICAL CONSTRAINT: Do NOT generate any Python code. Your job is exclusively to define the architectural specification and plan.