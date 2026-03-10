# SPECIFICATION: Milestone 23 – Data Generators & External Ingestion

**Document Version:** 1.0  
**Status:** Active  
**Date:** March 9, 2026

---

## Overview

Milestone 23 introduces the **DataSource** entity—a stationary ingestion node that pulls data from external sources and packages it into physics payloads, launching them into the game world. Unlike the Cannon (M15), the DataSource has no physical input port; instead, it actively fetches or polls data from configured external engines (CSV files, MCP servers, etc.) on a regular interval.

The DataSource implements an extensible **Generator Engine Registry** (parallel to M22's processing engine registry), allowing new data sources to be plugged in without modifying core DataSource logic. It operates asynchronously to avoid blocking the main render loop, and implements safe cleanup semantics to handle user deletion during background I/O operations.

---

## Goals

1. **External Data Ingestion:** Enable the game world to be populated with data-driven payloads from CSV files, AI services (via MCP), and other pluggable sources.

2. **Non-Blocking I/O:** File and network I/O must not stall the 60 FPS Pygame render loop; all fetch operations occur in background threads with results passed via thread-safe queues.

3. **Extensible Architecture:** Implement a registry-based generator engine system so new data sources (databases, APIs, etc.) can be added without modifying DataSource core.

4. **Audio & Animation States:** Support state-driven animations and sound effects, enabling rich visual and sonic feedback for INITIALIZING, POLLING, EMITTING, EXHAUSTED, and FATAL states.

5. **Graceful Error Handling:** Network timeouts, MCP connection drops, and malformed CSV files must transition the entity to FATAL and spawn diagnostic floating labels rather than crashing.

6. **Safe Lifecycle:** If the user deletes a DataSource while it is mid-fetch, background threads must cleanly discern the destroy flag and exit without attempting to queue stale results or lock up MCP sessions.

---

## Technical Implementation Details

### 1. DataSource Entity – Physical & Directional Shape

#### 1.1 Body Configuration
- **Shape:** Rectangular, static or kinematic body (no gravity response).
- **Collision Type:** Sensor body (no bouncing; may receive collisions for monitoring purposes only).
- **Default Dimensions:** 96px width × 96px height (configurable via YAML).

#### 1.2 Directional Output Port
- **Single Active Port:** Exactly one emission direction per DataSource instance.
- **Active Side:** Configured in YAML as `active_side: "Top" | "Bottom" | "Left" | "Right"`.
- **Port Position:** Located at the geometric center of the named edge.

#### 1.3 Emission Parameters
Each DataSource YAML variant MUST explicitly define:

```yaml
data_source:
  # ... entity base properties ...
  active_side: "Bottom"        # Top, Bottom, Left, or Right
  exit_velocity: 150.0         # Initial speed (pixels/sec)
  exit_angle: 0.0              # degrees, 0° points right, measured counter-clockwise
  emit_interval: 2.0           # seconds between emissions
  engine_type: "csv"           # "csv", "mcp", or custom
  instructions: { ... }        # Engine-specific config
  animations: { ... }          # State -> sprite name
  sounds: { ... }              # State -> audio file
```

---

### 2. State Machine

#### 2.1 State Definitions

| State | Meaning | Transitions | Actions |
|-------|---------|-------------|---------|
| **OFF** | Entity disabled, no polling. | → INITIALIZING on activation | None; awaiting user enable. |
| **INITIALIZING** | Engine resources being set up (connections, file handles, etc.). | → POLLING on success; → FATAL on init error | Play init animation; may trigger init sound. |
| **IDLE** | Engine ready, waiting for next tick interval. | → POLLING on tick | Play idle animation; awaits next emit window. |
| **POLLING** | Background thread fetching next data item. | → EMITTING on data received; → EXHAUSTED if source empty; → FATAL on error | Transitional; animation reflects "loading" state. |
| **EMITTING** | Physical payload being spawned and launched. | → IDLE after launch | Spawn ball physics; apply velocity; play emit sound. |
| **EXHAUSTED** | Source is depleted (e.g., CSV EOF reached with loop=false). | → OFF | Play exhausted animation; stop polling. |
| **FATAL** | Unrecoverable error (MCP connection lost, bad CSV format, timeout). | → OFF | Play fatal animation; spawn red floating error label. |

#### 2.2 State Transitions & Events
- **On Entry to any state:** If `sounds: { "STATE": "filename.wav" }` is defined in YAML, play the associated audio file immediately.
- **Animation Texture Loading:** Textures are mapped via `animations: { "STATE": "sprite_name" }`, resolved to `assets/sprites/sprite_name.png`.
- **Tick Interval:** Every `emit_interval` seconds (in IDLE or EXHAUSTED states), advance to POLLING if not exhausted.

---

### 3. Payload Initialization & Structure

#### 3.1 Payload Dictionary
Every emitted ball's payload is initialized as a dictionary with the following **required** keys:

```python
payload = {
    "data": { ... },              # Raw data from engine (CSV row, MCP response, etc.)
    "score": 100,                 # Gamification health; downstream processors may modify
    "cost": 100,                  # Energy cost for downstream factories (M22)
    "start_time": <float>,        # time.time() at emission, enables age tracking
    "routing_depth": 0,           # Incremented by each processor; triggers BOTTOM eject at MAX
    "ttl": 50,                    # Time-to-live hops; decremented per processor
    "drop_dead_age": 10.0,        # Seconds of age before forced EXHAUSTED route
    "processing_history": [],     # List of (processor_uuid, score_delta) tuples
}
```

#### 3.2 Payload Birth Process
1. **Engine Yields Data:** Background thread's `fetch_next(instructions)` returns raw data dict (or None on empty/error).
2. **Construct Payload:** Main thread (on poll) wraps the raw data into the payload structure above.
3. **Spawn Ball:** Create a new `GamePart` entity (physics body) with the initialized payload attached.
4. **Apply Velocity:** Compute world-space velocity from `exit_velocity` and `exit_angle` relative to `active_side`.
5. **Position at Port:** Place ball at the output port position (center of active edge).
6. **Transition to EMITTING:** Change visual state and play EMITTING sound.

#### 3.3 Angle Computation
- **Angle Reference Frame:** 0° points right (east), 90° points up (north), 180° points left (west), 270° points down (south).
- **Per-Side Adjustment:**
  - **Top:** Final angle = exit_angle + 90° (pointing upward from the side).
  - **Bottom:** Final angle = exit_angle + 270° (pointing downward).
  - **Left:** Final angle = exit_angle + 180° (pointing left).
  - **Right:** Final angle = exit_angle + 0° (pointing right).

---

### 4. Generator Engine Registry & Interface

#### 4.1 Base Generator Class

All generator engines inherit a common interface:

```
Class: BaseGenerator
  - Method: fetch_next(instructions: dict) -> dict | None
    - Fetches one data item from the source.
    - Returns a dictionary of data (e.g., CSV row as {"name": "Alice", "age": 30}).
    - Returns None if the source is empty or in an "empty" state (e.g., MCP status="empty").
    - Raises Exception (McpError, IOError, etc.) on unrecoverable errors.
```

#### 4.2 Registry Integration
The existing `EngineRegistry` (from M22's `utils/engines.py`) is extended to include generator engines:

- **Registration:** New generators are added to the registry under a `generators` key or separate registry.
- **Factory Constructor:** `get_engine(engine_type="csv", ...)`  or `get_generator(engine_type="csv", ...)` returns an instantiated generator.
- **Fallback:** If engine_type is unknown, a `NullGenerator` is returned (no-op; always returns None).

---

### 5. Concrete Generator Engines

#### 5.1 CSVEngine

**Purpose:** Load rows from a CSV file, one per fetch.

**Instructions Schema:**
```yaml
engine_type: "csv"
instructions:
  filepath: "data/users.csv"     # Relative to game root
  loop: false                     # If true, restart from top at EOF; if false, exhaust
  delimiter: ","                  # Optional; default is ","
  skip_header: true              # Optional; default is true (skip first row)
```

**Behavior:**
- On first `fetch_next()` call, opens the file and initializes a CSV reader.
- Each subsequent call yields one row as a dict (keys from header or auto-named).
- On EOF:
  - If `loop=true`, resets reader to top and continues.
  - If `loop=false`, returns None (signals EXHAUSTED state).
- **Error Handling:** File not found, malformed CSV, IO errors → raises IOError (DataSource transitions to FATAL).

**Example Output:**
```python
{
  "name": "Alice",
  "age": "30",
  "email": "alice@example.com"
}
```

#### 5.2 MCPEngine (Model Context Protocol Client)

**Purpose:** Connect to an MCP server and invoke a tool to fetch data.

**Instructions Schema:**
```yaml
engine_type: "mcp"
instructions:
  transport: "sse" | "stdio"     # Connection type
  # For SSE (Server-Sent Events):
  url: "http://localhost:8000/sse"
  # For stdio (local process):
  command: "mcp-server-binary"
  args: ["--config", "path/to/config.json"]
  tool_name: "get_incredible_machine_data"
  timeout: 5                      # Seconds; defaults to 5
```

**Behavior:**

1. **Initialization:** `fetch_next()` is called the first time. Engine establishes an `mcp.client.session.ClientSession` connecting via the specified transport (SSE or stdio).

2. **Tool Invocation:** On each `fetch_next()` call, the engine invokes the MCP tool `tool_name` (e.g., `"get_incredible_machine_data"`) with no arguments (or with arguments parsed from instructions if extended).

3. **Response Schema:** The MCP tool must return a JSON string in its `text` content block adhering to:
   ```json
   {
     "status": "success" | "empty" | "error",
     "data": { ... }
   }
   ```

4. **Response Handling:**
   - **"success":** The `data` object becomes the payload's data field. Engine returns this dict.
   - **"empty":** The AI service has no new data to provide. Engine returns None (DataSource stays IDLE, waits for next tick).
   - **"error":** The tool encountered an error. Engine raises an exception (DataSource transitions to FATAL).

5. **Error Conditions:**
   - Connection timeout (exceeds `timeout` seconds).
   - MCP server drops connection mid-session.
   - Tool call raises `McpError`.
   - Malformed JSON in tool response.
   - All errors → raise Exception (caught by DataSource, transition to FATAL).

6. **Cleanup:** On DataSource destruction or FATAL, the engine must cleanly close the MCP session to release connections.

**Example Tool Implementation (pseudo-code):**
```
Tool: get_incredible_machine_data
  Returns: {"status": "success", "data": {...}}
           or {"status": "empty"}
           or {"status": "error", "message": "..."}
```

---

### 6. Asynchronous Architecture & Thread Safety

#### 6.1 Threading Model
- **Main Thread:** Pygame render loop (60 FPS), physics updates, entity state draws.
- **Background Thread:** `fetch_next()` execution. Blocks on I/O (file read, network poll) without affecting main loop.
- **Queue Handoff:** Results passed via `queue.Queue()` (thread-safe).

#### 6.2 Polling Interval
- DataSource maintains `next_emit_time` (float, seconds since epoch).
- In `update_logic()` each frame, if `current_time >= next_emit_time` and not in POLLING or EMITTING:
  - Transition to POLLING.
  - Start background thread to call `fetch_next()`.
  - Set `next_emit_time = current_time + emit_interval`.

#### 6.3 Result Queue & Main-Thread Polling
- Background thread places results on `self.queue: queue.Queue()`.
- Each frame, `poll_results()` checks the queue (non-blocking via `queue.get_nowait()`).
- If a result is available:
  - If `_is_destroyed=True`, discard the result.
  - If data is not None, spawn the ball and transition to EMITTING.
  - If data is None (empty signal), transition to IDLE.
  - If Exception was queued (error path), transition to FATAL and spawn error label.

#### 6.4 Safe Cleanup
- **Destruction Flag:** `_is_destroyed` boolean.
- **On Cleanup:** Set `_is_destroyed = True` and drain the queue.
- **Background Thread Guard:** Before queuing a result, check `if not self._is_destroyed: queue.put(...)`.
- **MCP Session Close:** Engine's cleanup() method is called during DataSource destruction; engine cleanly closes MCP session without waiting for in-flight requests.

---

### 7. Audio & Animation Integration

#### 7.1 Animation Textures
Configured in `config/entities.yaml`:
```yaml
data_source:
  animations:
    INITIALIZING: "data_source_init"
    IDLE: "data_source_idle"
    POLLING: "data_source_polling"
    EMITTING: "data_source_emit"
    EXHAUSTED: "data_source_empty"
    FATAL: "data_source_error"
```

Textures resolved to `assets/sprites/{name}.png` and loaded on-demand.

#### 7.2 Sound Effects
Configured in `config/entities.yaml`:
```yaml
data_source:
  sounds:
    INITIALIZING: "init.wav"
    IDLE: null                    # No sound on IDLE entry
    POLLING: "poll.wav"
    EMITTING: "emit.wav"
    EXHAUSTED: "exhausted.wav"
    FATAL: "error.wav"
```

**Sound Playback Logic:**
- On state transition, check `sounds.get(new_state)`.
- If defined and not null, play the audio file immediately via the game's audio manager.
- If undefined or null, no sound plays.

---

### 8. YAML Configuration Example

```yaml
# In config/entities.yaml
data_source_csv_variant:
  type: "data_source"
  width: 96
  height: 96
  x: 0
  y: 0
  active_side: "Bottom"
  exit_velocity: 150.0
  exit_angle: 0.0
  emit_interval: 2.0
  engine_type: "csv"
  instructions:
    filepath: "data/sample.csv"
    loop: false
    skip_header: true
  animations:
    INITIALIZING: "data_source_init"
    IDLE: "data_source_idle"
    POLLING: "data_source_polling"
    EMITTING: "data_source_emit"
    EXHAUSTED: "data_source_empty"
    FATAL: "data_source_error"
  sounds:
    POLLING: "poll.wav"
    EMITTING: "emit.wav"
    FATAL: "error.wav"

data_source_mcp_variant:
  type: "data_source"
  width: 96
  height: 96
  x: 200
  y: 0
  active_side: "Top"
  exit_velocity: 120.0
  exit_angle: 45.0
  emit_interval: 3.0
  engine_type: "mcp"
  instructions:
    transport: "sse"
    url: "http://localhost:8000/sse"
    tool_name: "get_incredible_machine_data"
    timeout: 5
  animations:
    INITIALIZING: "data_source_init"
    IDLE: "data_source_idle"
    POLLING: "data_source_polling"
    EMITTING: "data_source_emit"
    EXHAUSTED: "data_source_empty"
    FATAL: "data_source_error"
  sounds:
    INITIALIZING: "init.wav"
    EMITTING: "emit.wav"
    FATAL: "error.wav"
```

---

### 9. Error & Edge Cases

#### 9.1 CSV Errors
- **File Not Found:** DataSource transitions to FATAL, spawns floating label "CSV file not found".
- **Malformed Row:** Row with missing columns or parse error → skip row, log warning, continue (configurable).
- **Permission Denied:** Transition to FATAL.

#### 9.2 MCP Errors
- **Connection Refused:** Transition to FATAL, spawn label "MCP connection failed".
- **Timeout (5s default):** Transition to FATAL, spawn label "MCP request timeout".
- **Malformed JSON Response:** Transition to FATAL, spawn label "MCP JSON parse error".
- **Tool Not Found:** Transition to FATAL, spawn label "Tool not found".

#### 9.3 Empty Queue vs. Exhaustion
- **MCP Returns {"status": "empty"}:** DataSource returns to IDLE; tries again next tick (AI may have new data later).
- **CSV Reaches EOF with loop=false:** Transition to EXHAUSTED; stop polling.
- **CSV Reaches EOF with loop=true:** Rewind and continue indefinitely.

#### 9.4 User Deletion During Fetch
- Background thread checks `_is_destroyed` before queuing.
- MCP session is closed gracefully in cleanup without blocking.
- No crash; no orphaned threads or dangling connections.

---

## Acceptance Criteria

### Phase 1: DataSource Entity Core
- [ ] DataSource class created with rectangular kinematic body.
- [ ] `active_side` property correctly positions the output port.
- [ ] State machine transitions work: OFF → INITIALIZING → IDLE → POLLING → EMITTING → IDLE (repeat) or EXHAUSTED/FATAL.
- [ ] Emit interval is respected; ball is spawned every N seconds.
- [ ] Exit velocity and angle are applied correctly to spawned balls.

### Phase 2: Payload Initialization
- [ ] Every spawned ball carries a payload dict with `data`, `score=100`, `cost=100`, `start_time`, `routing_depth=0`, `ttl=50`, `drop_dead_age=10.0`, `processing_history=[]`.
- [ ] Raw data from engine is nested in `payload["data"]`.
- [ ] Payload can be consumed by downstream M22 factories without error.

### Phase 3: Generator Engine Registry
- [ ] BaseGenerator interface is defined.
- [ ] Engine registry (or separate generator registry) allows dynamic engine lookup.
- [ ] Unknown engine type falls back to NullGenerator (no-op).
- [ ] Engine instances are created via factory method.

### Phase 4: CSVEngine Implementation
- [ ] CSVEngine reads CSV files and yields rows as dicts.
- [ ] Header row is skipped if `skip_header=true`.
- [ ] Loop behavior is respected (EOF rewinds or signals exhaustion).
- [ ] CSV parsing errors transition DataSource to FATAL.
- [ ] File-not-found errors transition to FATAL.

### Phase 5: MCPEngine Implementation
- [ ] MCPEngine connects via SSE or stdio transport.
- [ ] Tool is invoked with correct name.
- [ ] Response JSON is parsed and checked for `status` field.
- [ ] `status="success"` → data is extracted and returned.
- [ ] `status="empty"` → None is returned (DataSource stays IDLE).
- [ ] `status="error"` → Exception is raised (DataSource goes FATAL).
- [ ] Connection errors, timeouts, malformed JSON all transition to FATAL.
- [ ] MCP session is cleanly closed on cleanup.

### Phase 6: Threading & Safety
- [ ] Fetch operations do not block the main Pygame loop.
- [ ] Results are passed via thread-safe queue.
- [ ] `_is_destroyed` flag prevents stale queue processing.
- [ ] Background threads exit cleanly on DataSource deletion.
- [ ] No zombie threads or orphaned connections remain after destruction.

### Phase 7: Animation & Audio
- [ ] State textures are loaded via `animations` dict in YAML.
- [ ] Correct texture is drawn for each state.
- [ ] Sound files are played on state transitions via `sounds` dict.
- [ ] Missing sound files do not crash; no sound plays.
- [ ] Missing animation textures fall back to default sprite without crash.

### Phase 8: Configuration & YAML
- [ ] YAML variants for `data_source_csv` and `data_source_mcp` are defined.
- [ ] All required fields (`active_side`, `exit_velocity`, `exit_angle`, `emit_interval`, `engine_type`, `instructions`) are validated on load.
- [ ] Missing fields raise clear error messages (or use sensible defaults).

### Phase 9: Integration with Existing Systems
- [ ] DataSource spawned balls can be consumed by M22 factories.
- [ ] Ball physics (gravity, collisions) work normally.
- [ ] Balls can be saved/loaded with level state.
- [ ] DataSource can be deleted and recreated without residual errors.

### Phase 10: Error Handling & UX
- [ ] FATAL state spawns a red floating error label with descriptive reason.
- [ ] Error labels are transient and disappear after timeout.
- [ ] All error paths are covered and tested.
- [ ] No unhandled exceptions bubble up to the game loop.

---

## Notes & Future Extensions

1. **Additional Generators:** The architecture supports easy addition of new engines (e.g., DatabaseEngine, APIEngine, RandomGenerator).

2. **Batching:** If high throughput is needed, `fetch_next()` could be extended to return multiple items per call; DataSource could queue multiple balls in one emission cycle.

3. **MCP Server Pooling:** If many DataSources connect to the same MCP server, global session pooling could reduce overhead.

4. **Data Validation:** A post-fetch validation step (JSON schema, type coercion) could ensure data conforms to expected structure before spawning.

5. **Rate Limiting:** The emit interval can be made dynamic (adjusted by game state) if load balancing becomes necessary.

---

**End of Specification**
