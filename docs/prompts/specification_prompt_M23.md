Role: Specification Design Agent

Context: We are beginning Milestone 23: Data Generators & External Ingestion. We need to create a "DataSource" entity. This is an ingestion node (similar to the Cannon from M15, but with no physical input port) that pulls data from external sources (like a CSV file or an MCP server), packages it into a physics payload, and shoots it into the game world.

Task: Generate the document docs/SPECIFICATION_M23_DataGenerators.md.

Requirements for the Specification:

The DataSource Entity (States, Audio & Emitter):

Shape & Ports: A rectangular static or kinematic body. It has exactly ONE active directional output port where payloads are emitted.

Emission Parameters: The YAML configuration MUST explicitly specify the active_side (Top, Bottom, Left, Right), the exit_velocity (float), and the exit_angle (degrees or radians relative to the side) for the spawned payloads.

Tick Rate: It operates on a configurable interval (e.g., emit 1 payload every 2.0 seconds).

Expanded State Machine: OFF, INITIALIZING, IDLE, POLLING (fetching data), EMITTING, EXHAUSTED (source is empty), FATAL (connection error).

Animation Handling: Mapped via the animations dictionary in config/entities.yaml.

Audio Handling: Each state can optionally map to a sound file via a sounds dictionary in config/entities.yaml (e.g., sounds: { "EMITTING": "pop.wav", "FATAL": "error.wav" }). When the entity transitions into a new state, the game must play the associated sound effect. If no sound file is specified for a state, no sound is made.

Payload Initialization (The Birth of Data):

Detail exactly how this node constructs a brand new payload.

Crucial Metrics: Every emitted ball must have its payload dictionary strictly initialized with:

data: The raw data retrieved from the engine (e.g., a CSV row or JSON from MCP).

score: 100 (Initializing the payload's health/gamification metric).

cost: A default starting energy value (e.g., 100).

start_time: The current timestamp (time.time()) to enable the Age/TTL mechanics downstream.

routing_depth: 0.

Extensible Generator Engines (Registry Pattern):

The Interface: Specify a base generator class that implements a fetch_next(instructions) method.

The Registry: Integrate this into the existing EngineRegistry system.

Concrete Engines & Detailed Requirements:

CSVEngine: Expects instructions: {"filepath": "data/users.csv", "loop": false}. Reads the file and yields one row (as a dictionary) per call. Triggers EXHAUSTED state when EOF is reached.

MCPEngine (Model Context Protocol Client): Must utilize the official Python mcp library (pip install mcp) to connect to an MCP server.

Config: Expects instructions defining the transport and tool. Example: {"transport": "sse", "url": "http://localhost:8000/sse", "tool_name": "get_incredible_machine_data", "timeout": 5} (Must also support stdio transport).

Tool Execution: The engine must establish an MCP client session (mcp.client.session.ClientSession) and execute call_tool requesting the tool get_incredible_machine_data.

Required Return Schema: The MCP tool must return a JSON string (in its text content block) adhering to this schema: {"status": "success|empty", "data": { ... }}.

Response Handling: If status is "success", the data object becomes the core of the physical payload.

Empty Queues: If the tool returns {"status": "empty"} (indicating the AI has no new data to provide right now), the node must NOT spawn a ball. It quietly returns to IDLE and waits for the next tick interval.

Error Handling: If the MCP server connection drops, the tool call throws an McpError, or it times out, the DataSource must transition to FATAL and spawn a red floating error label (e.g., "MCP Tool Failed").

Asynchronous Architecture & Thread Safety:

File I/O (CSV reading) and Network I/O (MCP server polling) MUST NOT block the 60 FPS Pygame render loop.

Similar to M22, the fetch_next() operation must occur in a background threading.Thread (or handled via asyncio running in a background thread, as the mcp library is heavily async).

The generated data must be passed back to the main thread via a thread-safe queue.Queue(). The main loop polls this queue to physically spawn the ball.

Safe Cleanup: Must implement _is_destroyed checks. If the user deletes the DataSource node while it is awaiting an MCP response, the thread silently discards the data and cleanly closes the MCP session without crashing the game.

Output Format:

Produce a well-structured Markdown document containing an Overview, Goals, Technical Implementation Details, and Acceptance Criteria. Do NOT generate any Python code.