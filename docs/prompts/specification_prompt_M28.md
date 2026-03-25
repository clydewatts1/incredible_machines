Milestone 38: WOLF (Workflow Object Logic Framework)

Objective

To implement a "Pull-Based" workflow engine on top of the existing physical factory. This introduces two new concepts based on existing architecture: passive "Interactions" (storage) and active "Guards" (query-based routers). It utilizes the rule-engine Python library to safely evaluate complex business logic, prioritizing efficiency via event-driven signals.

Prerequisite

Run pip install rule-engine in your virtual environment.

1. The "Interaction" Node (Passive Storage)

We do not need a completely new class for this. We will upgrade the existing WarehousePart.

The Change: Add a boolean property auto_release (Default: True).

The Logic: If auto_release is False, the Warehouse's release_timer never triggers. It simply accepts payloads, stores their UUIDs in its buffer, and waits. It becomes a pure "Interaction" state.

The API: Add a method extract_payload(uuid) to the Warehouse so external nodes can surgically remove a specific payload out of order.

Event-Driven Signaling: When a new payload is successfully ingested, the Interaction broadcasts a REFRESH signal to any connected Guards to wake them up.

2. The "Guard" Node (Active Filter)

This is a new entity (GuardPart) that inherits from FlowEntity.

Connections: It has a source_uuid (the upstream Interaction) and a target_uuid (the downstream Factory/Interaction). Crucially, the connection between the source (normally a Factory or Interaction) and the Guard must be configured using a Data Pipe.

The Query & Sorting: It has a property called guard_query (e.g., "score >= 50 and type == 'admin'"). It also utilizes sort_by (e.g., "score") and sort_order (e.g., "desc") to establish priority.

The Mechanic (Event-Driven): Instead of polling every frame, the Guard slumbers until it receives a REFRESH signal from the source_uuid. Once awakened, it loops through all stored payloads and evaluates their data dictionaries using the compiled rule-engine Rule.

The Pull (Backpressure-Aware): If payloads match the query, the Guard sorts them based on the priority key to find the most valuable workload. It then checks if its target_uuid is currently FULL. If the target is clear, the Guard calls source.extract_payload(matched_uuid), takes ownership of the payload, and routes it to the target via the configured data pipe.

3. Visuals

The Scanner: To make it obvious that a Guard is "scanning", we can give it a radar-like scanning line in its draw() method, which flashes Green when it successfully pulls a workload.

Query Display: To ensure players can read the factory's logic at a glance, attach a FloatingTextLabel to the Guard that constantly displays its guard_query string floating above the machine.