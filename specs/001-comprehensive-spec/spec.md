# Feature Specification: Incredible Machines Baseline

**Feature Branch**: `001-comprehensive-spec`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "generate a specification based on the current code base and /docs/prompts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Programming & Routing (Priority: P1)

As a player/user, I want to place various mechanical nodes (Sources, Sinks, Factories, Brains) onto a 2D canvas and connect them with cables, belts, and pipes so that I can visually program data flows and physics interactions.

**Why this priority**: Building and connecting machines is the core interactive loop of the Sandbox.

**Independent Test**: Can be fully tested by placing a Source, connecting it via a pipe to a Factory, and observing payloads successfully route from one to the other.

**Acceptance Scenarios**:

1. **Given** an empty canvas in EDIT mode, **When** I select a node from the palette and click, **Then** the node is spawned at that location.
2. **Given** two nodes on the canvas, **When** I use the wiring tool to connect an output port to an input port, **Then** a visual connection is established and data/payloads can flow between them.

---

### User Story 2 - Synthetic Data Generation & ETL (Priority: P2)

As a data engineer, I want to use `FakerSource` and `FakerEngine` nodes to generate and mutate JSON records mid-flight, and route them to a `FileSink` to export the synthetic data.

**Why this priority**: Defines the M40 ETL requirement that upgrades the physics sandbox into an actual data generation tool.

**Independent Test**: Can be tested by setting up a FakerSource -> FileSink pipeline and verifying that a .jsonl file is produced on the local disk.

**Acceptance Scenarios**:

1. **Given** a connected Faker pipeline, **When** I switch to PLAY mode, **Then** payloads containing mutated JSON data are visually emitted and processed.
2. **Given** payloads reaching a FileSink, **When** they are consumed, **Then** their internal JSON records are written to a project-specific export directory.

---

### User Story 3 - Native Gamepad & Avatar Control (Priority: P3)

As a console-style player, I want to use a dual-analog gamepad to navigate the UI via a virtual mouse and directly control a physical Avatar character during gameplay.

**Why this priority**: Delivers the M42 objective for native gamepad inputs and physical interaction.

**Independent Test**: Can be tested by plugging in an XInput controller, verifying the left stick moves the cursor, and the right stick drives the `PlayerAvatarPart` in PLAY mode.

**Acceptance Scenarios**:

1. **Given** a connected controller, **When** I move the Left Stick in EDIT mode, **Then** the UI virtual mouse moves correspondingly.
2. **Given** the engine is in PLAY mode, **When** I move the Right Stick, **Then** the Player Avatar applies physical force to move around the environment.

### Edge Cases

- What happens when a machine tries to output to a full pipe/node? (Backpressure mechanisms pause emission)
- What happens if a payload falls off the screen? (Kill Z volume at y > 3000 catches and flags for deletion)
- What happens if an image or sound asset is missing? (AssetCascading falls back to procedural generation or AI generation)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support spawning, moving, and connecting discrete nodes derived from `FlowEntity`.
- **FR-002**: System MUST process physics step and logic updates consistently independently of framerate (dt scaling).
- **FR-003**: System MUST enforce backpressure using `broadcast_status` and `receive_signal` handshakes.
- **FR-004**: System MUST safely destroy entities using a `to_delete` flag integrated with a garbage collection pipeline.
- **FR-005**: System MUST support gamepad input mapping via configuration, avoiding hardcoded keyboard keys.
- **FR-006**: System MUST persist and load flow graphs, including metadata and custom assets, to `saves/[flow_name]/`.

### Key Entities 

- **FlowEntity**: The base class for all logical machines. Handles visual states and standard ingestion.
- **GuardPart / WarehousePart**: Implement the active pull "WOLF" logic, evaluating rule engines against stored payloads.
- **PlayerAvatarPart**: A physical body driven directly by gamepad input (Right Stick).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can construct a working cyclical data pipeline in under 5 minutes without engine crashes.
- **SC-002**: The physics simulation maintains 60 FPS under a load of 100 simultaneous moving payloads.
- **SC-003**: Connecting a standard gamepad instantly provides virtual mouse access and avatar control without restarting the application.
- **SC-004**: Missing assets do not crash the application, and procedural placeholders are successfully rendered in 100% of failure cases.

## Assumptions

- Target players use standard dual-analog gamepads or mouse and keyboard.
- Synthesized data volume per tick is small enough to be appended to disk without blocking the main Pygame thread.

### Core Architecture Compliance *(mandatory)*

- **FlowEntity Pattern**: Feature nodes MUST inherit from FlowEntity and use `ingest_payload`.
- **WOLF Routing**: All payload ejections MUST use `resolve_exit_path` without custom trigonometry.
- **Backpressure**: Sources/Sinks MUST implement handshake signals (`broadcast_status`).
- **ETL & Visuals**: Use faker for data generation (M40) and 2D kinematics for visual FX (M41).
- **Configuration**: All new parameters MUST be defined in `config/entities.yaml` and not hardcoded.
