# Implementation Tasks: Entity Documentation Standards

**Feature**: [002-entity-docs]
**Plan**: [plan.md](plan.md)
**Status**: Generated

## Phase 1: Setup

**Goal**: Initialize the documentation structure and gather reference schemas.

- [x] T001 Initialize `docs/entity` directory structure if not fully present.
- [x] T002 Parse `config/entities.yaml` to extract required and optional properties for all targets.

## Phase 2: Foundational (Index)

**Goal**: Create the root documentation index as mandated by the Constitution.

- [x] T003 Create `docs/entity/README.md` containing the master entity index framework.
- [x] T004 Update the main project `README.md` to point to `docs/entity/README.md`.

## Phase 3: Centralized Entity Reference [US1]

**Goal**: Systematically create markdown files for every entity variant.

- [x] T005 [P] [US1] Document Payload entities (`bouncy_ball.md`, `payload_ball.md`) in `docs/entity/`.
- [x] T006 [P] [US1] Document Block entities (`long_ramp.md`, `diamond.md`, `half_circle.md`, `quarter_circle.md`, `textured_rectangle.md`, `box.md`, `spring.md`, `bouncy.md`) in `docs/entity/`.
- [x] T007 [P] [US1] Document Active/Visual entities (`cannon.md`, `basket.md`, `motor.md`, `effect_box.md`, `pressure_plate.md`) in `docs/entity/`.
- [x] T008 [P] [US1] Document Logic entities (`guard.md`, `logic_factory.md`, `warehouse.md`, `portal.md`, `data_pipe.md`, `smart_splitter.md`, `ai_brain.md`) in `docs/entity/`.
- [x] T009 [P] [US1] Document Source entities (`data_source.md`, `data_source_csv.md`, `data_source_mcp.md`, `test_source.md`, `faker_source.md`) in `docs/entity/`.
- [x] T010 [P] [US1] Document Sink entities (`data_sink.md`, `data_sink_csv.md`, `data_sink_json.md`, `data_sink_yaml.md`, `data_sink_mcp.md`, `file_sink.md`) in `docs/entity/`.
- [x] T011 [P] [US1] Document Mechanical entities (`gear_driver.md`, `gear_follower.md`, `axle.md`, `belt_tool.md`, `conveyor_belt.md`) in `docs/entity/`.
- [x] T012 [P] [US1] Document Other entities (`text_box.md`, `avatar.md`) in `docs/entity/`.

## Phase 4: Standardized Documentation Format [US2]

**Goal**: Validate all documents against the strict schema.

- [x] T013 [P] [US2] Verify every document in `docs/entity/` has "Required Properties" and "Optional Properties" sections conforming exactly to `data-model.md`.
- [x] T014 [US2] Update `docs/entity/README.md` to ensure all 35 entity links are populated, valid, and unbroken.

## Phase 5: Polish & Final Review

**Goal**: Final proofreading.

- [x] T015 Perform final Markdown linting and verification across `docs/entity/`.

## Execution Strategy

Given that the Gemini Flash agent will execute this, tasks **T005 through T012** represent parallel track opportunities. They can be executed iteratively or batched by the implementing agent. Task **T013** acts as a structural validation gate before closing out [US2].
