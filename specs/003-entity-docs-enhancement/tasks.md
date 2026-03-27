# Tasks: Entity Docs Enhancement

**Input**: Design documents from `/specs/003-entity-docs-enhancement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current state before modifying docs.

- [ ] T001 [P] Run all test suites or check `tests/` to identify all `single_entity_*.yaml` files.
- [ ] T002 [P] Cross-reference `single_entity_*.yaml` files against `docs/entity/*.md` to find missing files.

---

## Phase 2: User Story 1 - Standardized Entity Documentation Reading (Priority: P1)

**Goal**: Update all entity documents to match their corresponding YAML configurations, ensuring Description, Summary, Detail, and Parameters structure is present.

### Tests for User Story 1 (OPTIONAL)

- [ ] T003 [P] [US1] Run `speckit-checklist` or equivalent tool to validate documentation matches schemas after updates (if applicable).

### Implementation for User Story 1

- [ ] T004 [P] [US1] Update `docs/entity/` markdown files for basic shapes (Box, Bouncy Ball, Diamond, etc.)
- [ ] T005 [P] [US1] Update `docs/entity/` markdown files for mechanical parts (Gear Driver, Gear Follower, Axle, Motor, Belt Tool, Conveyor Belt)
- [ ] T006 [P] [US1] Update `docs/entity/` markdown files for logic and ETL (AI Brain, Data Source, Data Sink, Faker Factory, etc.)
- [ ] T007 [P] [US1] Update `docs/entity/` markdown files for portals and interactive elements (Portal, Pressure Plate, Smart Splitter, etc.)

**Checkpoint**: At this point, User Story 1 should be fully functional and all documents should be populated.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T008 [P] Update `docs/entity/README.md` to ensure all newly documented entities are indexed.
- [ ] T009 Code cleanup: Fix any formatting issues across the markdown files.
