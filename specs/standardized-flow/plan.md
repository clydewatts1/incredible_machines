# Implementation Plan: Standardized Flow Signaling & Routing

**Branch**: `###-standardized-flow` | **Date**: 2026-03-28 | **Spec**: [spec.md](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/specs/standardized-flow/spec.md)
**Input**: Feature specification from `specs/standardized-flow/spec.md`

## Summary
Centralize signaling (backpressure) and routing logic in the `FlowEntity` base class. This ensures consistent behavior across all machine types, enables wildcard routing for simplified pipe connections, and optimizes the `GuardPart` to skip expensive scanning when upstream warehouses are empty.

## Technical Context
**Language/Version**: Python 3.11
**Primary Dependencies**: pygame, pymunk, rule-engine
**Storage**: N/A
**Testing**: Manual Visual Verification (using defect_warehouse_brain.yaml)
**Target Platform**: Desktop (Pygame)
**Project Type**: Desktop-app / Engine
**Performance Goals**: Reduce CPU overhead for idle Guard scanning.
**Constraints**: Adhere to the "Zero Rule" (errors <= 0).

## Constitution Check
- [x] **FlowEntity Pattern**: Yes, `DataPipePart` will be refactored to inherit from `FlowEntity`.
- [x] **Zero Rule / Routing**: Yes, `resolve_exit_path` will be updated to support wildcard routing.
- [x] **Handshake / Backpressure**: Yes, signals will be standardized across `FlowEntity` subclasses.
- [x] **Data Mutation (M40)**: N/A (no new mutations, using existing structure).
- [x] **Visual FX (M41)**: N/A.
- [x] **Deletion Pipeline/Kill Z**: N/A (using existing pipeline).
- [x] **Configuration Isolation**: Yes, wildcard routes are triggered by "any" in `route_state`.
- [x] **Entity Documentation**: N/A (modifying existing entities).

## Project Structure

### Documentation (this feature)
```text
specs/standardized-flow/
├── plan.md              # This file
├── spec.md              # Requirement definition
└── tasks.md             # Task breakdown
```

### Source Code (repository root)
```text
entities/
├── base.py              # FlowEntity & resolve_exit_path
├── data_pipe.py         # Refactor DataPipePart
├── warehouse.py         # WarehousePart last_state tracking
├── guard.py             # GuardPart aura awareness
agent_engine.py          # FactoryPart routing simplification
```

## Proposed Changes

### [Core Framework]
#### [MODIFY] [entities/base.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/base.py)
- Update `resolve_exit_path` to check for `matching_pipe.get_property("route_state") == "any"` as a fallback if no exact numeric match is found.
- Standardize `receive_signal` to consistently update `downstream_status`.

### [Data Pipes]
#### [MODIFY] [entities/data_pipe.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py)
- Change inheritance to `FlowEntity`.
- Implement `update_logic` to set `logic_signal = "JAMMED"` when full and broadcast.

### [Factories]
#### [MODIFY] [agent_engine.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/agent_engine.py)
- Remove redundant state checks in `poll_results` and rely on the base `resolve_exit_path`.

### [Warehouses & Guards]
#### [MODIFY] [entities/warehouse.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py)
- Expose `last_state` (IDLE if empty, ACTIVE if has items).

#### [MODIFY] [entities/guard.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/guard.py)
- In `update_logic`, check `source_node.last_state`. If `IDLE`, set own visual state to `IDLE` and abort scanning.

## Verification Plan

### Manual Verification
1. **Backpressure Test**: Connect a Factory to a Data Pipe. Stop the downstream end of the pipe. Factory should turn **JAMMED (Red)**.
2. **Wildcard Routing**: Define a Data Pipe with `route_state: "any"`. Factory should hand off all processed payloads to it.
3. **Guard Optimization**: Attach a Guard to an empty Warehouse. Verify no rule-engine logs are generated and radar beam is Blue.
