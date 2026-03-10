Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 23: Data Generators & External Ingestion. The details of what needs to be built are located in docs/SPECIFICATION_M23_DataGenerators.md.
The architectural rules for thread safety, plugins, and data degradation are defined in docs/CONSTITUTION.md (Sections 13-16).

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M23_DataGenerators.md. This document must break down the specification into logical, actionable implementation phases. Provide a fine-grained task list to ensure the coding agent handles the complexity safely.

Requirements for the Implementation Plan:

Highly Granular Sequential Phases: Divide the work into distinct, bite-sized phases to protect the physics engine's stability. Use the following breakdown:

Phase 1: Generator Architecture & Engines (Extend the EngineRegistry. Create the base interface, CSVEngine, and MCPEngine using the official Python mcp library, ensuring it handles the get_incredible_machine_data tool call and strictly parses the returned JSON schema).

Phase 2: YAML Configuration & Audio Mapping (Update config/entities.yaml for the DataSource node. Define the visual states, animations, sounds dictionary, and the directional emitter parameters: active_side, exit_velocity, exit_angle).

Phase 3: Thread-Safe Polling & Safe Cleanup (Implement the background threading/asyncio logic for fetch_next(). Use queue.Queue for the state handoff. Crucially, implement the _is_destroyed checks to safely close the MCP session and prevent ghost threads if the node is deleted).

Phase 4: Payload Initialization & Physical Emission (Implement the main loop polling logic. When data is retrieved from the queue, construct the exact payload dictionary (data, score: 100, cost, start_time, routing_depth: 0) and spawn the projectile applying the calculated velocity and angle from the active_side).

Phase 5: UX Feedback & State Polish (Integrate the state transitions (IDLE, POLLING, EMITTING, FATAL), hook up the audio cues for state changes, gracefully handle "empty" MCP responses, and reuse the M18 floating text labels for FATAL connection errors).

File Targeting: For every phase, explicitly state which file(s) are being modified or created (e.g., utils/engines.py, entities/active.py, config/entities.yaml).

Actionable Details: Mention specific constraints and libraries (like threading, asyncio, mcp.client.session, queue, or Pygame audio playback).

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that deleting a polling DataSource cleanly closes the MCP session without crashing").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the detailed plan/task list.