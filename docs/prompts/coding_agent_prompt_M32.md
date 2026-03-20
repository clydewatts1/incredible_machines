Please implement the Unified Flow Architecture (Milestone 32) to standardize all I/O nodes and signal behaviors.

Objective: Refactor all processing entities into a single inheritance hierarchy using a new FlowEntity base class. This centralizes animation, signaling, backpressure, and routing, making the system modular and extensible.

Step 1: The FlowEntity Base Class (entities/base.py)

Create FlowEntity(GamePart) to act as the template for all Sources, Sinks, and Factories.

Animation State Machine:

Implement list-based frame loading for states: OFF, INITIALIZING, IDLE, INGESTING, WRITING, FATAL, JAMMED.

Add an animation_timer and current_frame index to cycle through frames based on animation_speed.

Procedural Fallback: If a sprite file is missing, generate a pygame.Surface with a Light Gray (#E0E0E0) background, a 1px Black border, and the state name rendered in Black text (centered).

Standardized Signaling:

Implement receive_signal(sender, signal_data) to handle backpressure.

Implement broadcast_status(active_instances) to notify neighbors of IDLE, FULL, or JAMMED status.

Parameter Refresh Hook:

Implement refresh_parameters(updates_dict) to merge new properties into self.properties at runtime (supporting future stigmergic optimization).

Step 2: Hybrid Routing & The "Zero Rule"

Implement resolve_exit_path(payload_entity, state_result, entities) in the base class:

Normalization: If state_result <= 0, it MUST be treated as an error. Force the lookup for a routing rule where max_state: 0.

Precedence Rule: 1.  Pipe First: Search for a DataPipePart where source_uuid == self.uuid and route_state == normalized_state. If found and the pipe accepts the ball, transit is logical.
2.  Vector Fallback: If no pipe exists, use the matching routing rule's velocity, angle, and output_side.
3.  Error Default: If state_result <= 0 AND no pipe/rule exists, default to physical ejection from the "bottom" at tired_velocity.

Step 3: Refactor Specialized Nodes

Refactor the following files to inherit from FlowEntity and remove all redundant animation/physics/signaling code:

entities/source.py: Set can_provide_output = True. Emission is gated by downstream signals.

entities/sink.py: Set can_accept_input = True. Broadcasts FULL signal while consuming a payload.

entities/active.py (Factory) & entities/brain.py (Brain): Set both I/O flags to True.

Override process_payload(entity) to handle their specific logic (Regex, AI, etc.).

Ensure any processing failure returns a state of 0 or less.

Step 4: Final Cleanup

Ensure the CollisionManager in utils/physics_events.py calls entity.ingest_payload(ball) uniformly for all FlowEntity subclasses.

Verify that if a node is JAMMED (due to a full pipe), it properly halts the processing of its next payload.

Please provide the full code for entities/base.py and the refactored versions of the four node files.