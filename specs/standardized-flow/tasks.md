# Tasks: Standardized Flow Signaling & Routing

**Input**: Design documents from `/specs/standardized-flow/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Foundational (Core Signaling & Routing)

**Purpose**: Update the base class to support universal signaling and wildcard routing.

- [ ] T001 [P] Update `FlowEntity` in `entities/base.py` to support `route_state: "any"` in `resolve_exit_path`.
- [ ] T002 [P] Standardize `receive_signal` in `FlowEntity` (in `entities/base.py`) to ensure all subclasses update `downstream_status` identically.

## Phase 2: Refactoring (Data Pipes & Factories)

**Purpose**: Move Data Pipes into the FlowEntity hierarchy and simplify Factory routing.

- [ ] T003 Refactor `DataPipePart` in `entities/data_pipe.py` to inherit from `FlowEntity`.
- [ ] T004 Implement signal broadcasting in `DataPipePart.update_logic` based on transit queue capacity.
- [ ] T005 [P] Simplify `FactoryPart.poll_results` in `agent_engine.py` to rely entirely on `self.resolve_exit_path`.

## Phase 3: Optimizations (Warehouses & Guards)

**Purpose**: Improve performance by making Guards aware of upstream Warehouse state.

- [ ] T006 Update `WarehousePart` in `entities/warehouse.py` to track and expose `last_state` (IDLE/ACTIVE).
- [ ] T007 Update `GuardPart` in `entities/guard.py` to check `source_node.last_state` and skip scanning if IDLE.
- [ ] T008 [P] Remove redundant `receive_signal` from `WarehousePart` (use base class version).

## Phase 4: Verification

**Purpose**: Manual validation of the standardized flow logic.

- [ ] T009 Verify Factory-Pipe backpressure (Factory turns JAMMED when pipe is full).
- [ ] T010 Verify "any" routing (Factory hands off to pipe without explicit route integer).
- [ ] T011 Verify Guard optimization (Radar beam turns Blue/IDLE when Warehouse is empty).
