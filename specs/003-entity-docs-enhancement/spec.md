# Feature Specification: Entity Docs Enhancement

**Feature Branch**: `003-entity-docs-enhancement`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "enhancement to current specification , update all the entity documents with missing attribtes which can be found in files with the name single_entity_<entity_name>.yaml. A a description of entity , then a summary , and then detail section , followed by all the parameters and functionality"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standardized Entity Documentation Reading (Priority: P1)

As a user or physical layout editor, I want to read comprehensive documentation for each entity that follows a specific structure (Description, Summary, Detail, Parameters) and matches the actual in-game data so that I know exactly how an entity will behave when placed.

**Why this priority**: Documentation is critical for users to interact with complex entities appropriately without trial and error.

**Independent Test**: Can be fully tested by verifying an entity document and ensuring it matches the data found in its corresponding `single_entity_<entity_name>.yaml` file.

**Acceptance Scenarios**:

1. **Given** a user reads an entity document in `docs/entity/`, **When** they look for the structural headers, **Then** they see "Description", "Summary", "Detail", and section(s) for parameters and functionality.
2. **Given** a user examines the parameters inside the documentation, **When** they compare it against `single_entity_<entity_name>.yaml`, **Then** all parameters from the YAML file are accurately represented.

---

### Edge Cases

- What happens when a `single_entity_<entity_name>.yaml` does not exist for an entity? 
- How does the documentation handle dynamic or optional parameters that only appear under certain conditions in the YAML?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST have documentation for every entity that exists as a `single_entity_<entity_name>.yaml` test file.
- **FR-002**: System MUST structure all entity documents with a "Description" section.
- **FR-003**: System MUST structure all entity documents with a "Summary" section.
- **FR-004**: System MUST structure all entity documents with a "Detail" section.
- **FR-005**: System MUST list all parameters and functionality found in the corresponding `single_entity_*.yaml` configuration.

### Key Entities *(include if feature involves data)*

- **Entity Document**: Markdown `.md` document in the `docs/entity/` directory representing an entity.
- **Entity YAML**: Configuration file at `tests/single_entity_<entity_name>/single_entity_<entity_name>.yaml` containing actual instance data.

### Core Architecture Compliance *(mandatory)*

- **FlowEntity Pattern**: Feature nodes MUST inherit from FlowEntity and use `ingest_payload`.
- **WOLF Routing**: All payload ejections MUST use `resolve_exit_path` without custom trigonometry.
- **Backpressure**: Sources/Sinks MUST implement handshake signals (`broadcast_status`).
- **ETL & Visuals**: Use faker for data generation (M40) and 2D kinematics for visual FX (M41).
- **Configuration**: All new parameters MUST be defined in `config/entities.yaml` and not hardcoded.
- **Entity Documentation**: All entities MUST be documented in `docs/entity/` with a dedicated file explaining required and optional properties, and indexed in `docs/entity/README.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the attributes found in the `single_entity_*.yaml` files exist in their corresponding markdown documentation.
- **SC-002**: 100% of entity markdown files follow the exact required structure (Description, Summary, Detail, Parameters/Functionality).

## Assumptions

- Users have access to the `docs/entity/` directory to read documentation.
- The `single_entity_*.yaml` files contain the correct and complete set of runtime parameters that need documenting.
