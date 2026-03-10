# SPECIFICATION: Milestone 24 - Data Sinks & External Egestion

**Document Version:** 1.0  
**Status:** Active  
**Date:** March 10, 2026

---

## Overview

Milestone 24 introduces the **DataSink** entity, the mechanical opposite of DataSource (M23). DataSink acts as the terminal node of the visual ETL pipeline: it ingests physical payload carriers (balls), extracts `payload["data"]`, and asynchronously exports data to external targets.

Supported export targets in this milestone are:
- Local rotating files (`csv`, `json`, `yaml`)
- MCP tool calls to external AI/server systems using the official Python `mcp` client library

This milestone enforces Constitution Sections **13-16** by design:
- Section 13: strict main-thread physics ownership and background I/O
- Section 14: registry-based plugin architecture for exporters
- Section 15: payload integrity and safe degradation handling during sink ingestion
- Section 16: score/history preservation and sink finalization semantics

---

## Goals

1. **Establish DataSink Entity**
Create a rectangular static/kinematic ingestion node with sensor-based collision capture and payload type filtering.

2. **Implement Rotating File Exporters**
Write outgoing data to disk with bounded file sizes/time windows via automatic file rotation.

3. **Integrate Outgoing MCP Export**
Use official `mcp` Python library to post exported payload data via `ClientSession.call_tool(...)`.

4. **Guarantee Data Integrity on Shutdown/Delete**
On DataSink deletion or game shutdown, queued items must be flushed before exporter/session shutdown.

5. **Maintain Non-Blocking Runtime**
All file/network I/O must run in a background worker thread with queue handoff, keeping 60 FPS render loop responsive.

6. **Provide AV State Feedback**
Data-driven animation/sound mappings for `OFF`, `INITIALIZING`, `IDLE`, `INGESTING`, `WRITING`, `FATAL`.

---

## Technical Implementation Details

### 1. DataSink Entity - Physics, Capture, and Deletion

#### 1.1 Body and Sensor
- Shape: Rectangle (`template: "Rectangle"`), static or kinematic.
- Collision style: Sensor-based ingestion zone (no bounce impulse transfer).
- Dimensions: YAML-configurable (`width`, `height`).

#### 1.2 Type Filtering
Each DataSink variant must define an `accepts_types` list in YAML.

Example:
```yaml
accepts_types: ["bouncy_ball", "data_ball"]
```

Rules:
- If colliding entity type is not in `accepts_types`, DataSink ignores it.
- If accepted, DataSink extracts payload and enqueues export work.

#### 1.3 Ingestion Pipeline
On valid sensor contact:
1. Read collision target's payload dict.
2. Validate payload has `data` key; if missing, fallback to empty object and mark warning metadata.
3. Enqueue export item to DataSink's internal `queue.Queue()`.
4. Mark colliding entity for safe deletion in main loop (`to_delete=True`), never removing body from physics space inside callback.
5. Transition sink state to `INGESTING` (brief) then `WRITING` as worker processes queue.

This preserves Pymunk safety by deferring body removal to main-thread update flow.

---

### 2. Visual and Audio State Machine

#### 2.1 States
DataSink state set:
- `OFF`
- `INITIALIZING`
- `IDLE`
- `INGESTING`
- `WRITING`
- `FATAL`

#### 2.2 Transition Semantics
- `OFF -> INITIALIZING`: Sink spawned or enabled.
- `INITIALIZING -> IDLE`: Exporter initialized successfully.
- `IDLE -> INGESTING`: Accepted payload collision.
- `INGESTING -> WRITING`: Export item enqueued and worker active.
- `WRITING -> IDLE`: Queue drained and no active write.
- `* -> FATAL`: unrecoverable I/O/export error.

#### 2.3 AV Mapping via YAML
Each state maps to optional animation and optional sound.

```yaml
animations:
  OFF: "sink_off"
  INITIALIZING: "sink_initializing"
  IDLE: "sink_idle"
  INGESTING: "sink_ingesting"
  WRITING: "sink_writing"
  FATAL: "sink_fatal"
sounds:
  INGESTING: "gulp.wav"
  WRITING: "printing.wav"
  FATAL: "error.wav"
```

Rules:
- On every state transition, if `sounds[new_state]` exists and is non-null, play immediately.
- Missing/invalid sound files must fail silently and not crash gameplay.

#### 2.4 FATAL UX Feedback
On fatal exporter failures (file lock, MCP disconnect, timeout, permission denied):
- Transition to `FATAL`
- Spawn a floating red label near node (M18-style), e.g. `"File Lock Error"`, `"MCP Disconnected"`

---

### 3. Exporter Plugin Architecture (Registry Pattern)

### 3.1 Registry Mandate
Define an `EXPORTER_REGISTRY` mapping exporter keys to classes.

Example:
```python
EXPORTER_REGISTRY = {
  "csv": CSVExporter,
  "json": JSONExporter,
  "yaml": YAMLExporter,
  "mcp": MCPExporter,
  "null": NullExporter,
}
```

DataSink must only select exporters by `exporter_type` string from YAML config. No hardcoded `if/elif` branching in DataSink core logic.

### 3.2 Standard Exporter Interface
All exporters implement:
- `__init__(config_dict)`
- `export(data_item: dict) -> None`
- `flush() -> None`
- `cleanup() -> None`
- optional `validate_config() -> bool`

Contract:
- Raise exceptions for unrecoverable write/post failures.
- Do not mutate Pygame/Pymunk state.

---

### 4. File Exporters (CSV/JSON/YAML) and Rotation

#### 4.1 Required Config
```yaml
exporter_type: "csv"   # or json/yaml
export:
  directory: "exports"
  file_prefix: "sink_output"
  file_type: "csv"
  max_objects: 10
  rotation_seconds: 180
```

#### 4.2 Rotation Triggers (CRITICAL)
Rotate active output file when either condition is true:
1. Written objects in current file reaches `max_objects` (default `10`)
2. Current file age exceeds `rotation_seconds` (default `180` seconds)

Rotation behavior:
- Flush and close current file handle.
- Create a new file name with timestamp or incrementing counter.
- Continue writing remaining queue items to new file.

Example names:
- `sink_output_20260310_181522_001.csv`
- `sink_output_20260310_181845_002.csv`

#### 4.3 Format Notes
- CSVExporter: row-per-object flat mapping; nested values should be stringified JSON.
- JSONExporter: newline-delimited JSON objects (JSONL preferred for append safety).
- YAMLExporter: append list entries safely; avoid rewriting massive files each write.

---

### 5. MCPExporter (Outgoing Network Egestion)

#### 5.1 Library Requirement
Must use official Python MCP client library (`mcp`).

#### 5.2 Connection and Tool Invocation
Config example:
```yaml
exporter_type: "mcp"
export:
  transport: "sse"
  url: "http://localhost:8000/sse"
  tool_name: "post_incredible_machine_data"
  timeout: 5
```

Also support stdio transport:
```yaml
transport: "stdio"
command: "mcp-server"
args: ["--config", "server.json"]
```

Exporter behavior:
1. Initialize `ClientSession`.
2. On each export item, call tool `post_incredible_machine_data`.
3. Tool arguments include extracted payload data (typically `payload["data"]`).
4. Parse tool response; treat non-success statuses as errors.

Timeout/disconnect/`McpError` must raise and trigger sink `FATAL`.

---

### 6. Asynchronous Worker and Queue Handoff

#### 6.1 Main-Thread Rules
Main thread responsibilities:
- Detect sensor collisions
- Validate accepted types
- Queue export work
- Mark entities for deletion
- Apply state transitions

Background thread responsibilities:
- Poll sink queue
- Execute exporter `export(...)`
- Emit worker-status results/errors back via thread-safe structures if needed

No background thread may mutate:
- physics space
- `entities` list
- `active_instances` map

#### 6.2 Queue Item Schema
Recommended queue item:
```json
{
  "sink_uuid": "...",
  "payload_uuid": "...",
  "data": { ... },
  "score": 0,
  "processing_history": [],
  "ingested_at": 1710115200.0
}
```

Notes:
- Preserve score/history metadata for final analytics.
- `data` is the exported primary content.

---

### 7. Safe Flushing and Destroy Lifecycle (CRITICAL)

#### 7.1 Destroy Contract
DataSink must track lifecycle with `_is_destroyed` and `_flush_requested` flags.

On `cleanup()` / `destroy()`:
1. Set `_is_destroyed=True`
2. Signal worker to stop accepting new ingestion jobs
3. Enter flush mode: drain all remaining queue items
4. Call exporter `flush()`
5. Call exporter `cleanup()`
6. Mark worker terminated

#### 7.2 No Brutal Termination
Worker must not be force-killed while queue has pending items. Flush is mandatory to avoid data loss.

#### 7.3 Game Shutdown Behavior
Global shutdown path must call DataSink cleanup and wait for exporter shutdown completion (with bounded timeout and warning logs).

---

### 8. Data Integrity and Payload Scoring Compatibility

To remain aligned with Constitution Sections 15 and 16:
- DataSink must preserve `score` and `processing_history` metadata when available.
- Sink may apply optional final destination bonus (future switch), but M24 default is non-mutating pass-through on score.
- Missing payload metrics must not crash sink; they should be defaulted/sanitized in queue item.

Default handling:
- `score`: default `0`
- `processing_history`: default `[]`
- `data`: default `{}` when absent

---

### 9. YAML Configuration Example

```yaml
data_sink_csv:
  template: "Rectangle"
  label: "Data Sink (CSV)"
  width: 96
  height: 96
  is_static: true
  accepts_types: ["bouncy_ball", "data_ball"]
  exporter_type: "csv"
  export:
    directory: "exports"
    file_prefix: "sink_data"
    file_type: "csv"
    max_objects: 10
    rotation_seconds: 180
  animations:
    OFF: "sink_off"
    INITIALIZING: "sink_initializing"
    IDLE: "sink_idle"
    INGESTING: "sink_ingesting"
    WRITING: "sink_writing"
    FATAL: "sink_fatal"
  sounds:
    INGESTING: "gulp.wav"
    WRITING: "printing.wav"
    FATAL: "error.wav"

data_sink_mcp:
  template: "Rectangle"
  label: "Data Sink (MCP)"
  width: 96
  height: 96
  is_static: true
  accepts_types: ["bouncy_ball", "data_ball"]
  exporter_type: "mcp"
  export:
    transport: "sse"
    url: "http://localhost:8000/sse"
    tool_name: "post_incredible_machine_data"
    timeout: 5
  animations:
    OFF: "sink_off"
    INITIALIZING: "sink_initializing"
    IDLE: "sink_idle"
    INGESTING: "sink_ingesting"
    WRITING: "sink_writing"
    FATAL: "sink_fatal"
  sounds:
    INGESTING: "gulp.wav"
    WRITING: "printing.wav"
    FATAL: "error.wav"
```

---

## Acceptance Criteria

1. **Type Filtering and Ingestion**
- DataSink ingests only entities matching `accepts_types`.
- Non-matching entities are ignored without side effects.

2. **Safe Entity Removal**
- Ingested entities are marked and removed in main-thread update loop safely.
- No Pymunk crash due to deletion during collision callback.

3. **Async Worker Performance**
- Export operations run in background thread.
- Render loop remains smooth without stutter from file/network I/O.

4. **File Rotation Correctness**
- CSV/JSON/YAML exporters rotate exactly when `max_objects` reached or `rotation_seconds` elapsed.
- Rotated files are uniquely named and valid.

5. **MCP Export Success Path**
- MCPExporter initializes session and successfully invokes outgoing tool call.
- Payload data is transmitted as tool arguments.

6. **Flush-on-Destroy Integrity**
- Deleting DataSink with pending queue triggers flush mode.
- All queued items are written/posted before exporter/session closes.

7. **Fatal Error UX**
- File lock/network timeout/permission/MCP disconnect transitions sink to `FATAL`.
- Correct sound plays if configured.
- Red floating label with descriptive message is displayed.

8. **Constitution Compliance**
- No background mutation of physics/game collections.
- Registry pattern is used for exporter resolution.
- Payload integrity metadata is preserved/sanitized.

---

## Out of Scope (M24)

- Reliable retry queues persisted across game restarts
- Exactly-once external delivery guarantees
- Compression/encryption of output files
- Batch network streaming over persistent channels

These may be addressed in future milestones.

---

**End of Specification**
