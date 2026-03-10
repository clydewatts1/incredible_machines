# IMPLEMENTATION PLAN: Milestone 24 - Data Sinks & External Egestion

**Document Version:** 1.0  
**Status:** Active  
**Date:** March 10, 2026  
**Related Specification:** `docs/SPECIFICATION_M24_DataSinks.md`  
**Constitution Scope:** Sections 13-16 (Thread Safety, Plugin Architecture, Data Degradation, Payload Scoring)

---

## Overview

This implementation plan breaks Milestone 24 into five safe, sequential phases focused on physics stability and data integrity. The core principle is strict separation of responsibilities:

- Main Pygame thread handles physics, collisions, entity lists, and state transitions.
- Background worker thread handles exporter I/O only.
- Queue-based handoff (`queue.Queue`) ensures thread-safe communication.

The DataSink must never lose data during deletion/shutdown; flush semantics are mandatory.

---

## Phase 1: Exporter Architecture & File Rotation

### Objective
Create a registry-based exporter system with file exporters that support strict rotation by object count and time window.

### Files to Create
- `utils/exporters.py`

### Files to Modify
- `constants.py` (M24 defaults)
- `requirements.txt` (if needed for YAML dependency checks)

### Detailed Tasks

1. Create `BaseExporter` interface in `utils/exporters.py`.
- Required methods:
  - `export(data_item: dict) -> None`
  - `flush() -> None`
  - `cleanup() -> None`
  - Optional `validate_config() -> bool`
- Ensure all exporters share consistent constructor contract: `__init__(config: dict)`.

2. Create `NullExporter` fallback implementation.
- Behaves as no-op for unknown exporter types.
- Prevents runtime crashes when configuration is invalid.

3. Implement `EXPORTER_REGISTRY` in `utils/exporters.py`.
- Map:
  - `csv -> CSVExporter`
  - `json -> JSONExporter`
  - `yaml -> YAMLExporter`
  - `mcp -> MCPExporter` (stub in this phase, full implementation in Phase 2)
  - `null -> NullExporter`
- Add helper constructor (e.g., `get_exporter(exporter_type, config)`).

4. Implement file exporter base behavior shared by CSV/JSON/YAML.
- Internal state tracking:
  - active file handle/path
  - current object count
  - file open timestamp
  - rotation index/counter
- Rotation checks before every write:
  - rotate if `object_count >= max_objects`
  - rotate if `(now - file_start_time) >= rotation_seconds`
- Rotation behavior:
  - flush + close existing handle
  - open new file with unique suffix (timestamp + index)

5. Implement `CSVExporter`.
- Write one row per item.
- Handle nested dictionaries safely (stringify nested values as JSON strings).
- Ensure header management is deterministic across rotation files.

6. Implement `JSONExporter`.
- Prefer JSONL (one JSON object per line) for append-safe streaming.
- Avoid whole-file read/overwrite patterns.

7. Implement `YAMLExporter`.
- Use append-safe YAML strategy with item delimiters or compact document boundaries.
- Avoid expensive full-file reconstruction per write.

8. Add M24 constants in `constants.py`.
- Suggested defaults:
  - `SINK_ROTATION_MAX_OBJECTS = 10`
  - `SINK_ROTATION_SECONDS = 180`
  - `SINK_EXPORT_DIR = "exports"`

9. Validate exporter config and fail gracefully.
- Missing directory/prefix/file_type should raise clear initialization errors.
- Invalid directory permissions should raise explicit exceptions for FATAL handling upstream.

### Constraints to Enforce
- Registry pattern required (Constitution §14).
- Exporters must not mutate entities/physics/game state (Constitution §13).
- Rotation must trigger exactly on threshold conditions, not eventually.

### Manual Verification (Phase 1)
- Verify CSV exporter creates files and rotates exactly at `max_objects` boundary.
- Verify rotation also occurs at `rotation_seconds` threshold even with low item count.
- Verify JSON/YAML exporters write valid output and rotate similarly.
- Verify unknown exporter type returns `NullExporter` without crash.
- Verify permission error raises a deterministic exception message.

---

## Phase 2: MCP Exporter Implementation

### Objective
Implement MCP network exporter using official Python `mcp` library with both SSE and stdio transport.

### Files to Modify
- `utils/exporters.py`
- `requirements.txt` (ensure `mcp` is present and pinned compatibly)

### Detailed Tasks

1. Implement `MCPExporter` class in `utils/exporters.py`.
- Include session lifecycle state:
  - transport config
  - `ClientSession` reference
  - connection initialized flag
  - timeout settings

2. Add transport support.
- SSE transport config:
  - `transport: "sse"`
  - `url`
- stdio transport config:
  - `transport: "stdio"`
  - `command`
  - `args`

3. Initialize official MCP session.
- Use `mcp.client.session.ClientSession` with configured transport.
- Ensure initialization occurs once and is reused.

4. Implement outgoing tool call.
- On each `export(data_item)`:
  - Build tool args from `data_item["data"]` plus optional metadata (score/history if needed).
  - Call configured tool (default: `post_incredible_machine_data`).
- Validate response status and raise exception on failure.

5. Add timeout handling and error mapping.
- Handle:
  - connection timeout
  - disconnect
  - `McpError`
  - malformed response
- Raise clear exceptions so DataSink can enter FATAL with user-readable label.

6. Implement `flush()` and `cleanup()`.
- `flush()` should ensure in-flight exports are completed/awaited.
- `cleanup()` must close session/transport safely.

### Constraints to Enforce
- Official `mcp` library required.
- Network calls must never run on main thread (Constitution §13).
- MCP failures should bubble as controlled exceptions, not hard crashes.

### Manual Verification (Phase 2)
- Verify SSE config initializes and can call `post_incredible_machine_data`.
- Verify stdio config initializes and can call the same tool.
- Verify timeout/disconnect forces exporter exception.
- Verify cleanup closes session cleanly with no orphan transport process.

---

## Phase 3: DataSink Entity & Ingestion Sensor

### Objective
Create the DataSink entity with Pymunk-safe ingestion behavior, payload extraction, and queue handoff.

### Files to Create
- `entities/sink.py`

### Files to Modify
- `entities/base.py` (collision type support if needed)
- `main.py` (entity factory routing + collision handler wiring)
- `config/entities.yaml` (DataSink variants and AV mappings)
- `constants.py` (sink collision constants)

### Detailed Tasks

1. Create `DataSink` entity class in `entities/sink.py`.
- Inherit from `GamePart` or equivalent active-entity class pattern.
- Add state model:
  - `OFF`, `INITIALIZING`, `IDLE`, `INGESTING`, `WRITING`, `FATAL`
- Load `accepts_types`, `exporter_type`, exporter config from YAML.

2. Configure ingestion sensor geometry.
- Use rectangular sensor shape.
- Ensure collision type is unique and routed through main collision callbacks.

3. Implement type filtering.
- Parse `accepts_types` from YAML.
- In collision callback, accept only matching entity variants/types.

4. Implement ingestion extraction logic.
- On accepted collision:
  - Extract payload safely (`payload = entity.payload or {}`)
  - Build queue item with at least:
    - `data`
    - `score`
    - `processing_history`
    - `ingested_at`
  - Enqueue for background export

5. Implement safe deletion marking.
- In callback, do not remove body/shape immediately.
- Set `entity.to_delete = True` and let main update loop perform actual removal.

6. Wire DataSink creation in `main.py`.
- Extend `create_part(...)` dispatcher for DataSink variants.
- Ensure DataSink instances are tracked in `entities` and `active_instances`.

7. Add collision handler wiring in `main.py`.
- Route sink collision events to DataSink ingestion method.
- Guard against duplicate ingestion of same object during repeated overlap frames.

8. Add YAML variants in `config/entities.yaml`.
- `data_sink_csv`, `data_sink_json`, `data_sink_yaml`, `data_sink_mcp`.
- Include required fields:
  - `accepts_types`
  - `exporter_type`
  - `export` config
  - `animations`
  - `sounds`

### Constraints to Enforce
- Pymunk mutation only in main thread and not inside worker thread (Constitution §13).
- Sensor callback must remain lightweight; only queueing and flags.
- Payload metadata should be preserved (Constitution §§15-16 compatibility).

### Manual Verification (Phase 3)
- Verify sink ingests accepted ball types and ignores others.
- Verify ingested balls are removed safely via `to_delete` path, no physics crash.
- Verify sink queue grows as collisions occur.
- Verify no duplicate enqueue spam from persistent overlap.

---

## Phase 4: Async Worker & Safe Flush Lifecycle

### Objective
Implement background export worker with mandatory flush-on-destroy behavior and safe termination.

### Files to Modify
- `entities/sink.py`
- `main.py` (cleanup hooks during delete/clear/load/exit)
- `utils/level_manager.py` (persist only sink entity state, never transient labels)

### Detailed Tasks

1. Add background worker thread in `DataSink`.
- Worker loop polls `queue.Queue`.
- Each dequeued item calls `exporter.export(...)`.
- Signal state changes (`WRITING` while active).

2. Add lifecycle flags.
- `_is_destroyed`
- `_flush_requested`
- `_worker_running`
- Optional `_accept_ingestion` gate to stop new queue items during teardown.

3. Implement mandatory flush mode (CRITICAL).
- `cleanup()` / `destroy()` must:
  - set `_is_destroyed=True`
  - disable further ingestion
  - set `_flush_requested=True`
  - wait for worker to drain queue
  - call exporter `flush()` then `cleanup()`
- Use bounded wait timeout + warning logs, but prioritize data flush completion.

4. Prevent ghost thread behavior.
- Worker must exit only after:
  - queue fully drained
  - exporter flushed
  - exporter/session cleaned up
- Never force-kill the thread with abrupt process-level termination.

5. Hook cleanup into all destructive paths.
- Right-click delete in edit mode.
- Level clear/load replace.
- Game shutdown.

6. Ensure queue safety and race handling.
- Main thread only enqueues.
- Worker thread only dequeues/exports.
- No cross-thread direct writes to physics/entity containers.

### Constraints to Enforce
- Thread-safe queue handoff required (Constitution §13).
- No data loss allowed on deletion with pending queue items.
- Worker shutdown must be orderly and deterministic.

### Manual Verification (Phase 4)
- Spawn sink, ingest many balls rapidly, then delete sink mid-processing.
- Verify queued items are fully exported before sink disappears.
- Verify files are closed and no handle leaks remain.
- Verify MCP session closes cleanly after flush.
- Verify no lingering worker thread after cleanup completes.

---

## Phase 5: AV State Machine & UX Feedback

### Objective
Finalize visual/audio feedback for sink lifecycle and robust fatal diagnostics.

### Files to Modify
- `entities/sink.py`
- `config/entities.yaml`
- `main.py` (if global audio triggers/helpers are required)

### Detailed Tasks

1. Implement state transition helper.
- Centralize `_set_state(new_state)`.
- Trigger animation texture selection.
- Trigger optional sound playback by state key.

2. Wire state transitions through runtime flow.
- `INITIALIZING` during exporter setup.
- `IDLE` when ready and queue empty.
- `INGESTING` immediately on accepted collision.
- `WRITING` while worker actively exporting.
- `FATAL` on exporter errors.

3. Integrate sound mapping.
- Use existing sound manager and per-state `sounds` dict.
- Missing sound should fail silently.

4. Reuse floating text diagnostics.
- Spawn red floating label (M18/M22 pattern) for fatal errors:
  - file lock
  - permission denied
  - MCP disconnect/timeout
- Ensure labels are transient and excluded from save data.

5. Add optional cooldown/debounce around `INGESTING` visual transitions.
- Prevent noisy flicker during high-frequency collisions.

6. Ensure fatal mode behavior is deterministic.
- In `FATAL`, stop accepting new ingestion work unless explicitly reset.

### Constraints to Enforce
- AV feedback must not block game loop.
- Error labels must not mutate physics world.
- Fatal transitions must preserve already queued data until flush/cleanup.

### Manual Verification (Phase 5)
- Verify all states render with correct animation mapping.
- Verify sounds play on state transitions when configured.
- Trigger file lock and confirm FATAL + red label appears.
- Trigger MCP disconnect and confirm FATAL + red label appears.
- Confirm sink remains stable and no crash occurs in repeated fatal scenarios.

---

## Integration Test Pass (Post-Phase)

### End-to-End Scenarios

1. **File sink happy path**
- DataSource emits balls -> DataSink ingests -> CSV/JSON/YAML files receive records.

2. **Rotation boundaries**
- Confirm exact split when object/time threshold reached.

3. **MCP sink happy path**
- DataSink exports payload data via `post_incredible_machine_data`.

4. **Delete-with-pending-queue**
- Delete sink while queue non-empty, verify flush-before-close behavior.

5. **Error handling UX**
- Simulate file permission error and MCP timeout, verify FATAL state + label + sound.

6. **Performance sanity**
- Run with frequent ingestion and confirm no visible render stutter.

### Final Acceptance Checklist
- [ ] Ingestion filtering works by `accepts_types`.
- [ ] Safe main-thread deletion path for ingested entities is stable.
- [ ] Exporter worker runs asynchronously and does not block Pygame loop.
- [ ] File rotation is exact and deterministic.
- [ ] MCP exporter can initialize and post data.
- [ ] Flush lifecycle guarantees no queued data loss on destroy/shutdown.
- [ ] FATAL UX feedback is immediate and descriptive.

---

## Implementation Order Dependencies

1. Build exporters first (Phase 1) to establish sink output contract.
2. Add MCP exporter next (Phase 2) to complete registry coverage.
3. Implement DataSink ingestion shell (Phase 3) once exporters are available.
4. Add worker and flush lifecycle (Phase 4) before any heavy playtesting.
5. Add AV polish and fatal UX last (Phase 5) after core correctness is proven.

This order minimizes physics risk while prioritizing data integrity guarantees.

---

**End of Implementation Plan**
