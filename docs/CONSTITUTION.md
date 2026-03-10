# **Incredible Machines: Project Constitution**

This document defines the core principles, architectural constraints, and coding standards for the "Incredible Machines" project. All AI agents and developers must adhere to these rules to maintain project integrity.

## **1\. Project Identity**

* **Name:** Incredible Machines  
* **Genre:** 2D Physics-based puzzle game (inspired by The Incredible Machine)  
* **Core Loop:** Place parts \-\> Run simulation \-\> Achieve goal \-\> Next level  
* **Vibe:** Tinkering, experimentation, playful physics, mechanical logic.

## **2\. Core Technologies**

* **Language:** Python 3.x  
* **Rendering & Input:** Pygame Community Edition (CE) is highly recommended over standard Pygame for better performance and modern features.  
* **Physics Engine:** Pymunk (2D physics library)  
* **Configuration:** YAML (for levels, parts, environment settings)

## **3\. Architectural Principles**

* **Separation of Concerns:**  
  * *Physics (Pymunk):* Handles all collision, gravity, mass, and movement. Visuals must *follow* physics, not dictate them.  
  * *Rendering (Pygame):* Only reads physics state to draw the screen.  
  * *Game Logic:* State machine managing transitions (Edit Mode vs. Play Mode).  
* **Data-Driven Design:** Hardcoding values (mass, friction, sprite paths) in Python is strictly prohibited. All entity definitions must live in config/entities.yaml.  
  * **Property Inheritance Model:** While `entities.yaml` is the source of truth for base definitions, instantiated entities are permitted to hold an overrides dictionary (e.g., custom mass, custom JSON payloads) that takes precedence over the base definition.
* **Modularity:** New parts/entities should be easily added by creating a new class inheriting from a base Entity class and adding a YAML entry.

## **4\. Physics Engine (Pymunk) Mandates**

* **The Single Source of Truth:** Pymunk's Space is the absolute authority on object position and rotation.  
* **Coordinate Systems:** Pygame's origin (0,0) is top-left. Pymunk's origin can be bottom-left (standard) or top-left depending on setup. *Mandate:* Explicitly define and document the coordinate conversion functions and use them universally.  
* **Units:** 1 Pymunk unit \= 1 pixel (unless a specific scale factor is explicitly decided and documented). Keep mass and forces within reasonable, stable ranges.  
* **Time Step:** The physics simulation must use a fixed time step (e.g., 60Hz) to ensure deterministic behavior across different machines. Do *not* use variable delta-time for physics step().

## **5\. Coding Standards (Python)**

* **Style:** PEP 8 compliant. Use type hinting (e.g., def calculate\_force(mass: float) \-\> float:) for all function signatures.  
* **Naming Conventions:**  
  * Classes: PascalCase  
  * Variables/Functions: snake\_case  
  * Constants: UPPER\_SNAKE\_CASE  
* **Error Handling:** Fail gracefully. If a sprite is missing, draw a magenta placeholder rectangle and log a warning; do not crash.

## **6\. The State Machine**

The game must clearly distinguish between:

1. **Edit Mode:** Physics simulation is *paused*. Players can place, move, and configure parts.  
2. **Play Mode:** Physics simulation is *running*. Player input is restricted to interactive parts (e.g., flipping a switch). Parts cannot be added or moved freely.

## **7\. Version Control & AI Interaction**

* **Incremental Commits:** Code changes must be small, focused, and tied to a specific milestone.  
* **Agent Roles:** Respect the defined roles of the Speckit AI agents (Plan, Specify, Implement, Checklist, Review). Do not merge steps.

## **8\. YAML Configuration Standards**

* All configurations (entities, levels) must be validated upon loading.  
* Structure must be clean and self-documenting.  
* Example:  
  ball\_bowling:  
    type: dynamic  
    mass: 10  
    radius: 15  
    elasticity: 0.1  
    friction: 0.8  
    visual: "bowling\_ball.png"

## **9\. Performance Constraints**

* Target Framerate: 60 FPS.  
* Object limits: The game should comfortably handle at least 100 physics objects simultaneously without dropping frames.  
* Avoid loading assets (images, sounds) during the main loop. Pre-load everything during initialization.

## **10\. Milestone Progression**

* Work must proceed strictly according to the defined milestones.  
* No "feature creep." Do not implement features from Milestone 4 while working on Milestone 2\.

## **11\. User Interface (UI) Standards**

* **Playable Area Boundary:** The UI acts as a physical picture frame. The Pymunk physics boundaries (static lines for floor/walls/ceiling) must be inset to match the playable\_rect. Objects must never spawn, fall, or bounce *behind* the UI elements.  
* **Separation of Input:** The game must distinguish between "UI Clicks" and "World Clicks." The main event loop must process UI collisions first. If a click falls on a UI element, it MUST NOT accidentally interact with the physics space behind it.  
* **Lightweight UI:** Avoid heavy external UI libraries (like pygame\_gui) unless absolutely necessary. Maintain a simple, custom UI manager (utils/ui\_manager.py) focusing on clear, basic components like buttons and panels.  
* **Data-Driven Toolbars:** Object palettes (side panels) must populate dynamically based on the variants loaded from config/entities.yaml. Avoid hardcoding object buttons. Icons should be auto-generated by drawing the entity onto a temporary surface.  
* **Graceful Stubs:** If a UI element represents a feature that does not yet exist (e.g., "Save", "Load", "Challenges"), it must render visually but safely log a "Not Implemented" message to the console when clicked, preventing game crashes.  
* **Clear State Indication:** The UI must provide immediate, obvious visual feedback of the current game state (e.g., highlighting whether the game is currently in PLAY or EDIT mode, and indicating the active tool via a "ghost" cursor).
* **Input Focus State:** When a UITextInput or UITextArea component has active focus, the UIManager must consume all keyboard events, and all global game hotkeys (e.g., 'Delete' for object removal, 'Space' for play/edit toggle) must be strictly suspended to prevent accidental game actions while typing.

## **12. Relational Architecture & Constraints**

* **Two-Pass Instantiation Rule:** The engine must spawn all bodies/shapes first, and then apply constraints/joints in a second pass.  
* **Instance Identity Rule:** Every spawned entity must have a Unique Identifier (UUID) to allow constraints and save/load files to target specific instances on the canvas.  
* **Cascading Deletion Rule:** If an entity is deleted, the system must safely remove any associated Pymunk constraints attached to it before removing the body.

## **13. Thread Safety & Asynchronous Processing**

* **The Main Thread Dictates Physics:** The Pymunk `space` object and all physics body modifications (creating, destroying, applying forces) **MUST** occur exclusively on the main Pygame execution thread. Pymunk is **NOT thread-safe**. Any attempt to modify physics bodies from a background thread will cause race conditions, data corruption, or crashes.

* **Background Processing Mandate:** Any long-running, blocking, or external I/O operations **MUST** be executed in a background thread or asynchronous worker pool to prevent frame-rate jitter in the Pygame render loop. Examples include:
  * Simulated LLM or AI engine evaluations (e.g., Factory processing logic)
  * File I/O operations (asset loading, save/load on disk)
  * Network communication or external API calls
  * Heavy CPU-intensive calculations (e.g., pathfinding, signal routing across complex networks)

* **Thread-Safe Handoffs:** Background threads must communicate results back to the main thread using **thread-safe** structures only:
  * **Recommended:** Python's `queue.Queue()` for passing data structures or status flags.
  * **Pattern:** The main Pygame loop polls the queue during each frame, retrieves results, and executes the physical manifestation (e.g., updating a Pymunk body's velocity, spawning a new entity, applying a signal).
  * **No Direct Modifications:** Background threads **MUST NOT** directly write to `entities` lists, `active_instances` dicts, or any game state variables. All state changes must be queued and applied by the main thread.

* **Graceful Timeouts:** Background tasks must include timeout mechanisms. If a computation takes longer than a reasonable threshold (e.g., 5 seconds), the system must either:
  * Abort the computation and log a warning.
  * Return a sensible default result.
  * Fail gracefully without crashing the game or blocking the UI.

* **Resource Cleanup:** Background threads must be properly joined or terminated before the game exits. Use Python's threading context managers (e.g., `ThreadPoolExecutor`) or explicitly manage thread lifecycle to prevent orphaned threads.

## **14. Extensible Plugin Architecture**

* **The Registry Mandate:** When introducing processing engines, factories, logical transformers, or other extensible components, implement a **Registry Pattern** where:
  * A central dictionary (or class-based registry) maps configuration strings to their corresponding Python classes or factory functions.
  * Example: `ENGINE_REGISTRY = { "boolean_logic": BooleanEngine, "arithmetic": ArithmeticEngine, "string_concat": StringEngine }`
  * Registry is initialized once at startup and remains immutable during gameplay.

* **No Hardcoded Logic Gates:** Core game entities (e.g., Factory, Processor, Router) must remain **completely agnostic** to the specific engine implementations. They must:
  * Query their YAML configuration for an `engine_type` or `processor_type` string.
  * Dynamically instantiate the required class from the Registry: `engine_class = ENGINE_REGISTRY[self.engine_type]`.
  * Use the instantiated engine's standard interface (e.g., `engine.process(payload)`) without knowledge of internal logic.
  * **Fail gracefully** if the requested engine type is not registered, logging a warning and using a null/passthrough engine instead of crashing.

* **Standard Interface Contract:** All engines/processors registered in the Registry must implement a consistent interface:
  * **Constructor:** Accept configuration from YAML (e.g., `__init__(self, config_dict)`).
  * **Process Method:** `def process(self, payload: dict) -> dict` or similar, returning a modified payload or result.
  * **Validation Method:** `def validate_config(self) -> bool` to allow setup-time checks.

* **Plugin Hot-Loading (Optional Future Enhancement):** The architecture must support the ability to register new engines at runtime (e.g., loading custom engine modules from a plugins directory) without requiring code recompilation or game restart. Design the Registry to support dynamic imports.

## **15. Physical Data Degradation & Time-To-Live (TTL)**

* **Preventing Infinite Loops:** Because Milestone 22+ simulates computational logic using physical data payloads routing between nodes, infinite loops and cyclic routing are critical crash risks. The system must implement TTL or degradation mechanics to guarantee termination.

* **Payload Metrics (Mandatory):** Every data payload flowing through the simulation must carry:
  * **TTL (Time-To-Live):** An integer countdown. Nodes decrement this counter with each processing step. When TTL reaches zero, the payload must be safely ejected or archived.
  * **Cost (Energy):** A float representing the "fuel" or energy budget of the payload. Processing operations consume cost. When cost is depleted, the payload fails gracefully.
  * **drop_dead_age:** An absolute age limit (in frames or seconds). Once a payload exceeds this age, it must be rejected automatically, regardless of TTL or cost.
  * **Routing Depth:** A counter tracking how many nodes the payload has visited. If depth exceeds a hardcoded limit (e.g., 1000), reject the payload to prevent circular routing.

* **Audit & Rejection Logic:** Before processing a payload, every node must check these metrics:
  ```
  if payload.ttl <= 0 or payload.cost <= 0 or payload.age > payload.drop_dead_age or payload.routing_depth > MAX_DEPTH:
      safely_eject_or_archive_payload(payload)
      return  # Do not process further
  ```

* **Safe Floating Mechanics (No Negative Mass):** To simulate expired or "floating" payloads awaiting destruction:
  * **Never** assign negative mass to a Pymunk body. Physics engines crash or produce unstable behavior with negative mass.
  * **Instead:** Flag the body as "floating" (e.g., `body.floating = True`). During the main physics update step, apply a continuous upward anti-gravity force:
    ```
    if body.floating:
        body.apply_force_at_world_point((0, -body.mass * UPWARD_ACCELERATION), body.position)
    ```
  * This mechanism allows expired payloads to visually float away before being deleted, providing clear feedback without physics instability.

* **Archive & Recycling (Optional):** Ejected payloads can be archived to a separate "trash" list for deferred cleanup, reducing per-frame garbage collection pressure. Archived payloads are removed during an idle cleanup phase.

## **16. Payload Scoring & Health System**

* **Data Gamification:** Data payloads flowing through the system carry a **score** parameter, representing the payload's cumulative "health" or success metric. This adds a strategic and visual layer to data routing and signal processing.

* **Payload Health Metrics:**
  * **score:** An integer or float (default: 0, max: typically 100) tracking the payload's quality or success state.
  * **processing_history:** A list of (node_uuid, score_delta) tuples recording which nodes processed the payload and the score changes applied.
  * **final_destination_bonus:** A bonus score granted if the payload reaches a designated final sink node successfully.

* **Node Processing Rules:**
  * Routing nodes may modify a payload's score based on processing outcomes:
    * **Success:** `payload.score += success_bonus` (e.g., +10 for correct logic calculation).
    * **Partial Success:** `payload.score += partial_bonus` (e.g., +5 for partial routing).
    * **Failure:** `payload.score += failure_penalty` (e.g., -10 for incorrect result), but score is clamped to a minimum of 0.
  * Nodes record the modification in `processing_history` for debugging and scoring.

* **Visual Score Feedback:**
  * Payloads should render with a visual indicator of their health (e.g., color gradient from green (high score) to red (low score), or a small text label showing the score).
  * This allows players to see at a glance which payloads are succeeding vs. failing as they route through the simulation.

* **Final Scoring & Victory Conditions:**
  * When a payload reaches a predefined "sink" or "output" node, its final score is recorded.
  * Challenge levels can define victory conditions such as:
    * "All payloads must reach the output with a score >= 80."
    * "Achieve a combined score of 500 across all payloads."
    * "Route at least 5 payloads successfully without any drooping below 50 score."
  * The game loop polls sink nodes and accumulates final scores, triggering level victory checks.

* **Integration with Payload TTL:** Score and TTL interact:
  * High-scoring payloads may have extended TTL (e.g., +50 frames per 10 score points).
  * Low-scoring payloads degrade faster (e.g., -2 TTL per 10 frames).
  * This creates emergent gameplay where successful routing chains grant longer viability.