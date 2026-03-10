Role:
You are the Implementation Planning Agent for the "Incredible Machines" project. Your job is to take an approved technical specification and break it down into a clear, sequential, highly detailed, step-by-step implementation plan.

Context:
We have just approved the specification for Milestone 22: Logic Factories & Async Processors. The details of what needs to be built are located in docs/SPECIFICATION_M22_LogicFactories.md.
The architectural rules for thread safety, plugins, and data degradation are defined in docs/CONSTITUTION.md (Sections 13-16).

Task:
Generate the document docs/IMPLEMENTATION_PLAN_M22_LogicFactories.md. This document must break down the specification into logical, actionable implementation phases. Provide a fine-grained task list to ensure the coding agent handles the complexity safely.

Requirements for the Implementation Plan:

Highly Granular Sequential Phases: Divide the work into distinct, bite-sized phases to protect the physics engine's stability. Use the following breakdown:

Phase 1: Engine Architecture & Registry (Create utils/engines.py, define BaseEngine interface, and build the EngineRegistry dictionary).

Phase 2: Regex Engine Implementation (Implement RegexEngine, ensuring it loops over "rules", safely extracts "target_field" from dictionary payloads, and returns discrete states).

Phase 3: Random Engine Implementation (Implement RandomEngine, ensuring it parses "distribution", utilizes Python's random.uniform or random.gauss, and maps outputs using "rules").

Phase 4: YAML Configuration & Animation Mapping (Update config/entities.yaml for the Factory. Define the 7 required visual states and map them to sprite base names via the animations dictionary. Add cost_modifier and tired_velocity).

Phase 5: Thread-Safe Background Processing (Implement the threading.Thread logic inside the Factory. Use queue.Queue for the state handoff. Crucially, implement the cleanup()/destroy() method and the _is_destroyed flag to prevent ghost threads).

Phase 6: Payload Lifecycle Pre-Processing (Age & Cost) (Implement the firewall logic: If cost <= 0, eject Bottom. If expired via drop_dead_age, set floating flag and apply upward anti-gravity force in the main loop).

Phase 7: Routing Table & Health Modifiers (Implement the Left-edge ejection logic. Parse the "routing" array, evaluate <= max_state, extract the "score" modifier, and apply it to the payload's health).

Phase 8: UX Polish & Collision Safety (Integrate the 0.5-second Top sensor cooldown post-emission, and hook up the FATAL state to spawn floating red text labels reusing the M18 payload visualizer).

File Targeting: For every phase, explicitly state which file(s) are being modified or created (e.g., utils/engines.py, entities/active.py, config/entities.yaml).

Actionable Details: Mention specific constraints and libraries (like threading, queue, random, or the specific collision handler overrides needed for the cooldown).

Testing/Acceptance: Include a brief manual verification step at the end of each phase (e.g., "Verify that deleting a processing Factory does not crash the Pygame loop when the thread finishes").

Output Format:

Produce a well-structured Markdown document outlining the step-by-step plan.

CRITICAL CONSTRAINT: Do NOT generate the actual Python code. Your job is exclusively to write the detailed plan/task list.