# Implementation Plan: Standardized Flow Signaling & Routing

**Branch**: `004-standardized-flow` | **Date**: 2026-03-28 | **Spec**: [004-standardized-flow/spec.md](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/specs/004-standardized-flow/spec.md)
**Input**: Feature specification from `specs/004-standardized-flow/spec.md`

## Summary
Centralize backpressure signaling and routing logic in the `FlowEntity` base class. This improves simulation reliability by ensuring all machine types (including Data Pipes) propagate "JAMMED" states and simplifies configuration by allowing wildcard "any" routing for direct pipe connections. We also optimize `GuardPart` to skip rule evaluations when the source is empty.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: pygame, pymunk, rule-engine  
**Storage**: N/A (Project-based YAML project saves)  
**Testing**: Manual Visual Verification; Headless Test Mode (`--test`)  
**Target Platform**: Desktop (Windows/Linux)
**Project Type**: Simulation Engine  
**Performance Goals**: Reduce CPU overhead for idle Guard nodes by >90% (SC-003).  
**Constraints**: Zero Rule (errors <= 0); Kinematic Pipes.

## Constitution Check
- [x] **FlowEntity Pattern**: Yes, refactoring `DataPipePart` to inherit from `FlowEntity`.
- [x] **Zero Rule / Routing**: Yes, `resolve_exit_path` centrally handles wildcard routing with "any".
- [x] **Handshake / Backpressure**: Yes, move `receive_signal`/`broadcast_status` to base class with conservative signal policy.
- [x] **Data Mutation (M40)**: N/A.
- [x] **Visual FX (M41)**: N/A.
- [x] **Deletion Pipeline/Kill Z**: N/A (existing pipeline used).
- [x] **Configuration Isolation**: Yes, wildcard routes triggered via "any" logic in `resolve_exit_path`.
- [x] **Entity Documentation**: All entities documented in `docs/entity/`.

## Project Structure

### Documentation (this feature)
```text
specs/004-standardized-flow/
├── plan.md              # This file
├── spec.md              # Requirement definition
├── tasks.md             # Task breakdown
├── data-model.md        # Entity definitions
├── quickstart.md        # Verification guide
└── checklists/
    └── requirements.md   # Quality validation
```

### Source Code (repository root)
```text
entities/
├── base.py              # FlowEntity (receive_signal, resolve_exit_path)
├── data_pipe.py         # DataPipePart (FlowEntity inheritance)
├── warehouse.py         # WarehousePart (last_state tracking)
└── guard.py             # GuardPart (Aura awareness/optimization)
agent_engine.py          # FactoryPart (Routing simplification)
```

## Proposed Changes

### [Core Framework]
#### [MODIFY] [entities/base.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/base.py)
- **Signaling (FR-001)**: robustify `receive_signal` and `broadcast_status`. Implement **Conservative Signal Policy**: any "JAMMED" status from any path takes precedence.
- **Routing (FR-002)**: Update `resolve_exit_path` to match pipes with `route_state: "any"` as a fallback. If multiple wildcards exist, pick the first encountered.

### [Data Pipes]
#### [MODIFY] [entities/data_pipe.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py)
- **Inheritance (FR-003)**: Change base class to `FlowEntity`.
- **Threshold Signaling**: Implement delta thresholds; only broadcast `broadcast_status` when crossing IDLE/JAMMED boundary.

### [Factories]
#### [MODIFY] [agent_engine.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/agent_engine.py)
- Simplify `poll_results` to use base `resolve_exit_path` and remove redundant state management.

### [Warehouses & Guards]
#### [MODIFY] [entities/warehouse.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py)
- **State Exposure (FR-004)**: Implement `last_state` property returning `IDLE` (empty) or `ACTIVE` (populated).
- **Passive Broadcast**: Notify all connected Guard listeners of state changes.

#### [MODIFY] [entities/guard.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/guard.py)
- **Wake-up Logic (FR-005)**: In `update_logic`, check `source_node.last_state`. If `IDLE`, skip scanning.
- **Manual Overrides**: REFRESH signals and manual triggers force a scan regardless of state.

## Verification Plan

### Manual Verification
1. **Backpressure**: Connect Factory -> Pipe. Block pipe output. Factory must turn **JAMMED (Red)**.
2. **"any" Routing**: Set Pipe to `route_state: "any"`. Factory must successfully hand off payloads.
3. **Guard Slumber**: Observe radar beam behavior on Guard when Warehouse is empty/filled.
4. **Signal Precedence**: Connect one Factory to two pipes (one JAMMED, one IDLE). Factory should remain JAMMED.
