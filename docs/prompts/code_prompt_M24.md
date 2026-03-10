Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

docs/CONSTITUTION.md (Pay close attention to Sections 13-16 regarding Thread Safety, Plugin Architecture, Data Degradation, and Payload Scoring)

docs/SPECIFICATION_M24_DataSinks.md

docs/IMPLEMENTATION_PLAN_M24_DataSinks.md (The 5-Phase Plan)

Task: Implement Milestone 24: Data Sinks & External Egestion. You will build the DataSink entity and the EXPORTER_REGISTRY to safely ingest physical objects and asynchronously write their data to rotating files or an MCP server. Execute the 5 phased steps exactly as outlined in the implementation plan.

Critical Execution Instructions:

Phase 1: Exporters & Rotation (utils/exporters.py):

Implement the BaseExporter interface and EXPORTER_REGISTRY.

For CSVExporter, JSONExporter, and YAMLExporter, you MUST implement the rotation logic. Track the object_count and file_start_time. Before every write, check if object_count >= max_objects OR (now - file_start_time) >= rotation_seconds. If true, flush, close, and open a new file with a timestamp/incrementing suffix. Include a NullExporter fallback.

Phase 2: Official MCP Exporter:

Utilize the official Python mcp library.

Implement MCPExporter supporting both sse and stdio transports based on the YAML config.

Initialize mcp.client.session.ClientSession and execute call_tool for post_incredible_machine_data, passing the payload data. Handle timeouts and McpError by throwing exceptions that the DataSink can catch.

Phase 3: Safe Pymunk Ingestion (entities/sink.py):

Create the DataSink entity with a rectangular sensor shape.

Physics Safety (CRITICAL): Inside the collision callback, filter by accepts_types. If accepted, extract the payload and place it in the thread-safe queue.Queue(). You MUST NOT remove the body or shape from the Pymunk Space inside this callback. Instead, set entity.to_delete = True so the main Pygame update() loop handles the safe removal.

Phase 4: Async Worker & Mandatory Flush (Ghost Thread Prevention):

The background worker thread must ONLY dequeue and export. It must never mutate Pygame/Pymunk state.

Flush Lifecycle (CRITICAL): Implement the cleanup() / destroy() method. It must set _is_destroyed = True and _flush_requested = True, disabling further ingestion. It MUST wait for the worker thread to completely drain the queue, call exporter.flush(), and exporter.cleanup() before the thread terminates. No data loss is permitted on deletion.

Phase 5: AV State Machine & UX Feedback:

Implement _set_state(new_state) managing OFF, INITIALIZING, IDLE, INGESTING, WRITING, FATAL.

Hook up visual animations and play audio from the sounds dictionary on state transitions.

Catch exporter exceptions (like file locks or MCP disconnects), transition to FATAL, and reuse the M18 payload visualization logic to spawn a transient red floating text label detailing the error.