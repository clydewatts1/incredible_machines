# Tasks: Standardized Flow Signaling & Routing

**Input**: Design documents from `/specs/004-standardized-flow/`
**Prerequisites**: plan.md (required), spec.md (required)

## Phase 1: Setup (Project structure)

**Purpose**: Initialize the feature environment.

- [ ] T001 Create project documentation structure in `specs/004-standardized-flow/`
- [ ] T002 [P] Verify feature branch `004-standardized-flow` is active

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update base class to support signaling and routing for all user stories.

- [x] T003 Update `FlowEntity` in `entities/base.py` to support `route_state: "any"` in `resolve_exit_path`.
- [x] T004 Robustify `FlowEntity.receive_signal` and `broadcast_status` in `entities/base.py` to implement conservative "JAMMED wins" logic.

## Phase 3: User Story 1 - Standardized Backpressure (Priority: P1)

**Goal**: Enable reliable signaling from downstream pipes to upstream factories.

**Independent Test**: Connect Factory -> Pipe. Block pipe end. Verify Factory turns logic-state JAMMED (Red).

- [x] T005 [P] [US1] Refactor `DataPipePart` in `entities/data_pipe.py` to inherit from `FlowEntity`.
- [x] T006 [US1] Implement delta-threshold signaling in `DataPipePart.update_logic` in `entities/data_pipe.py` (broadcast only on Full/Not Full change).
- [x] T007 [US1] Update `FactoryPart.poll_results` in `agent_engine.py` to rely on the base class signaling and state-setting.

## Phase 4: User Story 2 - Wildcard Pipe Routing (Priority: P2)

**Goal**: Simplified factory-to-pipe handoff using "any" route.

**Independent Test**: Connect Factory to "any" Data Pipe. Verify processed payloads enter the pipe without explicit route integer.

- [x] T008 [P] [US2] Ensure `resolve_exit_path` in `entities/base.py` correctly resolves the first encountered "any" pipe as fallback.
- [ ] T009 [US2] Remove complex routing tables from test entities if applicable to simplify configurations.

## Phase 5: User Story 3 - Aware Guards (Priority: P3)

**Goal**: Optimize Guard scanning by checking upstream Warehouse state.

**Independent Test**: Observe Guard radar beam on empty Warehouse (Blue/IDLE). Add payload. Verify beam briefly turns Yellow (Scanning).

- [x] T010 [P] [US3] Update `WarehousePart` in `entities/warehouse.py` to expose `last_state` property (IDLE/ACTIVE).
- [x] T011 [P] [US3] Implement passive status broadcast in `WarehousePart.update_logic` in `entities/warehouse.py`.
- [x] T012 [US3] Update `GuardPart.update_logic` in `entities/guard.py` to check source `last_state` and honor Manual/REFRESH overrides.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and documentation.

- [x] T013 Update `docs/entity/` documentation to reflect new signaling behaviors.
- [x] T014 [P] Remove redundant `receive_signal` overrides from `WarehousePart` in `entities/warehouse.py`.
- [x] T015 Run `quickstart.md` validation scenarios.
- [x] T016 [US1] Stress Test: Verify 100% signal propagation under high-frequency (60/s) payload bursts.


## Dependencies & Execution Order

### Phase Dependencies

- **Phase 2 (Foundational)**: MUST complete before Phase 3, 4, or 5.
- **Phase 3 (US1)**: Priority MVP.
- **Phase 4 & 5**: Can run in parallel with each other if Phase 2 is complete.

### Parallel Opportunities
- T005, T008, T010, T011 are all [P] as they touch independent files or class definitions.
