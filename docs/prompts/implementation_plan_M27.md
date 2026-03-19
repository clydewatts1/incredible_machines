Milestone 27: Data Pipes & Hybrid Routing

Objective

To introduce DataPipePart, a new transit entity that acts as a bridge between the physical simulation and rigid logical automation. Data Pipes allow BrainPart and FactoryPart entities to bypass Newtonian physics entirely for specific evaluated states, transporting payloads directly to a target over a set transit time.

Core Mechanics

1. The DataPipePart Entity

Properties: source_uuid, target_uuid, capacity (default 5), transit_time (default 2.0s), route_state (default 10).

Ingestion: Accepts payloads explicitly passed to it by its source entity.

Transit: Removes the payload from the active physics simulation (is_hidden = True, velocity = 0). It smoothly interpolates the payload's visual position along an S-Curve Bezier from the source to the target over the transit_time.

Ejection: Once progress reaches 1.0 (100%), it attempts to call ingest_payload() on the target entity. If the target is full, the payload pauses at the end of the pipe (Backpressure).

Visuals: Renders as a thick, wavy, translucent glass tube. If len(transit_queue) >= capacity, the tube pulses Red/Orange to indicate a blockage.

2. Upgrading Active Processors (Brain & Factory)

Currently, BrainPart and FactoryPart use _eject_payload to shoot balls into the air. We will update their poll_results logic to support hybrid routing:

Evaluate: Determine the state of the processed payload (e.g., 10).

Scan: Look through all DataPipePart entities in the game where source_uuid == self.uuid and route_state == 10.

Route (Pipe): If a matching pipe is found, attempt to push the payload into the pipe. If the pipe returns False (it is full/blocked), the Brain/Factory changes its state to JAMMED and waits.

Fallback (Physics): If NO matching pipe exists for that state, the Brain/Factory falls back to the legacy _eject_payload() method, shooting the ball into the physical world based on its configured velocity and angle.

Future Integration: Stigmergic Auto-Architect

By keeping the physics fallback, we set the stage for a future milestone where DataSinks analyze the trace list of unrouted physical balls and automatically spawn new DataPipePart connections to optimize the factory dynamically.