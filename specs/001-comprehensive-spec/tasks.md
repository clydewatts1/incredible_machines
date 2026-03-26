# Implementation Tasks: Incredible Machines Baseline

**Feature**: [001-comprehensive-spec]
**Plan**: [plan.md](plan.md)
**Status**: Generated (Verification Focus)

## Phase 1: Environment Verification

**Goal**: Confirm the established project structure and configuration logic.

- [x] T001 Verify the Pygame-CE and Pymunk grid initialization in `main.py`.
- [x] T002 Check the `EnvironmentManager` configuration loading and YAML parsing in `utils/environment_manager.py`.

## Phase 2: Core Architecture Validation (WOLF)

**Goal**: Document and validate the fundamental WOLF and FlowEntity systems.

- [x] T003 Confirm `FlowEntity` base class implementation in `entities/flow_entity.py`.
- [x] T004 Validate `resolve_exit_path` against the "Zero Rule" (No custom trig in routing) in `utils/routing.py`.
- [x] T005 Verify the `Kill Z` floor threshold logic in `main.py`.
- [x] T006 Confirm the PyMunk garbage collection pipeline (to_delete flag) is functional in `main.py`.

## Phase 3: Routing & Programming Logic (US1)

**Goal**: Verify the visual programming interface and backpressure handling.

- [x] T007 [P] [US1] Validate standard factory and pipe node behaviors in the simulation.
- [x] T008 [P] [US1] Confirm Pygame-GUI event blocking during node placement in `main.py`.
- [x] T009 [US1] Verify `broadcast_status` handshakes across connected nodes.
- [x] T010 [US1] Validate `WarehousePart` and `GuardPart` active pull interaction logic.

## Phase 4: Synthetic Data Pipeline (US2)

**Goal**: Confirm the Faker ETL and FileSink export mechanics.

- [x] T011 [P] [US2] Verify JSON payload record mutation in `PayloadPart`.
- [x] T012 [P] [US2] Confirm `FakerSource` and `FakerEngine` API integration.
- [x] T013 [US2] Validate `FileSink` exports to `saves/[flow_name]/`.

## Phase 5: Gamepad & Avatar Integration (US3)

**Goal**: Verify controller mapping and physical avatar response.

- [x] T014 [P] [US3] Confirm `ControllerManager` Left Stick virtual mouse mapping in `utils/controller.py`.
- [x] T015 [US3] Validate `PlayerAvatarPart` physics velocity response to Right Stick.
- [x] T016 [US3] Verify collision haptics (rumble) on avatar impact impulses in `utils/physics_events.py`.

## Phase 6: Polish & Assets

**Goal**: Finalize documentation and asset fallbacks.

- [x] T017 Verify visual particle kinetics (M41) correctly bypass PyMunk.
- [x] T018 Confirm `AssetManager` cascading fallbacks for missing assets.
- [x] T019 Document the Headless QA architecture in `main.py`.

## Dependencies & Execution Order

- **Linear Validation**: Confirming engine stability before testing complex WOLF interactions.
- **Parallel Opportunities**: US1, US2, and US3 verification tasks are independent and can be audited concurrently.
