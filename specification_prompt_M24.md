Specification: Milestone 24 - Data Sinks & External Egestion

1. Overview

Milestone 24 introduces the DataSink entity, the mechanical opposite of the DataSource built in M23. This ingestion node serves as the final destination for physical data payloads in the visual ETL pipeline. It captures physical objects (Balls), extracts their internal payload['data'], and asynchronously pushes that data out of the game engine into external systems—either writing to local rotating files (CSV, JSON, YAML) or transmitting via the Model Context Protocol (MCP) to an external AI server.

This milestone reinforces the Constitution's mandates for Thread Safety (Section 13) and the Extensible Plugin Architecture (Section 14), while adding strict Data Integrity rules for safe shutdown and flushing.

2. Goals

Establish the DataSink Entity: Create a physical ingestion node that uses a Pymunk sensor to consume specific payload types.

Implement File Rotation Mechanics: Safely write to local disk (CSV, JSON, YAML) with automated file rotation based on item limits or time limits to prevent massive file lockups.

Integrate Outgoing MCP Requests: Use the official Python mcp library to establish a client session and call_tool to post data to an external AI server.

Ensure Data Integrity (Flushing): Guarantee that queued payloads are fully flushed to disk/network if the node is deleted or the game shuts down.

Maintain Asynchronous Safety: Execute all I/O operations in a background thread fed by a queue.Queue(), keeping the Pygame 60 FPS loop unblocked.

Provide AV UX Feedback: Wire up a visual and auditory state machine (IDLE, INGESTING, WRITING, FATAL) to give immediate tactile feedback.

3. Technical Implementation Details

3.1 The DataSink Entity & Ingestion Physics

Shape & Sensor: A rectangular static or kinematic body featuring a Pymunk sensor (similar to the M15 Basket).

Type Filtering: Must parse an accepts_types array from its YAML configuration (e.g., ["data_ball"]). If a colliding entity matches, it is ingested.

Ingestion Logic: Upon a valid sensor collision, the game MUST extract the payload dictionary, place it into the DataSink's thread-safe queue.Queue(), and safely schedule the colliding Pymunk body and Pygame sprite for deletion in the main update() loop.

3.2 Visual & Audio State Machine

States: The node manages OFF, INITIALIZING, IDLE, INGESTING (brief transition when a ball enters), WRITING (active I/O processing), and FATAL (I/O error).

AV Mapping: Data-driven mapping via animations and sounds dictionaries in config/entities.yaml. A sound (e.g., a "gulp" or "printing" noise) plays instantly on state transition.

FATAL Feedback: If a file lock occurs or the MCP server drops connection, the node transitions to FATAL and spawns a floating red error label (e.g., "File Lock Error" or "MCP Disconnected"), reusing the M18 payload visualization logic.

3.3 Extensible Exporter Architecture (Registry Pattern)

The Registry: Expand the Plugin Architecture by creating an ExporterRegistry mapping string types to Python classes.

File Exporters (CSVExporter, JSONExporter, YAMLExporter):

Configuration: Require directory, file_prefix, and file_type parameters.

Rotation Logic (CRITICAL): Must implement internal tracking to close the current file handle and open a new file (appending a timestamp or incrementing ID to the file_prefix) when either:

The file contains max_objects entries (default: 10).

The rotation_timer expires (default: 180 seconds).

Network Exporter (MCPExporter):

Must utilize the official mcp Python library.

Establishes a ClientSession.

Executes an outgoing tool call (e.g., post_incredible_machine_data), packaging the ingested payload['data'] as the tool arguments.

3.4 Asynchronous Processing & Safe Flushing

Background Worker: All exporter write/post actions MUST happen in a background threading.Thread (or asyncio event loop for MCP) polling the Queue.

Safe Session Cleanup & Data Integrity (Ghost Thread Prevention): * The DataSink must track its lifecycle via an _is_destroyed flag.

If the user deletes the node from the canvas in EDIT mode, the cleanup() or destroy() method is invoked.

CRITICAL REQUIREMENT: The background thread MUST NOT be brutally killed. It must be signaled to enter a "flush" state. It must iterate through the remainder of its Queue, write/post all remaining payloads, and then cleanly close any open file handles or active MCP client sessions before terminating.

4. Acceptance Criteria

The DataSink successfully ingests balls matching its accepts_types and rejects all others.

Ingested bodies and sprites are safely removed without crashing the Pymunk simulation step.

The background thread processes the queue without causing stutter in the main Pygame render loop.

CSVExporter (and similar file exporters) successfully rotate and split files exactly when max_objects is reached or rotation_timer expires.

MCPExporter successfully establishes a connection and executes the outgoing tool call to pass data to an external server.

Deleting a DataSink node with balls still in its queue successfully triggers the "Flush" mechanism, guaranteeing no data is lost before the file handle/network session is closed.

Network timeouts or file permission errors instantly trigger the FATAL visual state and sound effect, displaying the descriptive red error label.