# Feature Specification: Standardized FlowEntity Signaling & Routing

**Feature Branch**: `004-standardized-flow`  
**Created**: 2026-03-28  
**Status**: Completed  
**Input**: User description: "Specification: Standardized FlowEntity Signaling & Routing..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standardized Backpressure (Priority: P1)
As a developer, I want all machine types to share a universal signaling mechanism so that backpressure (JAMMED/FULL states) propagates reliably from downstream pipes to upstream factories.

**Why this priority**: Core stability. Prevents simulation "flooding" and ensures machines pause when their output path is blocked.

**Independent Test**: Connect a Factory to a Data Pipe. Manually fill/block the pipe. Verify the Factory enters a JAMMED state and stops processing.

**Acceptance Scenarios**:
1. **Given** a DataPipe at capacity, **When** a Factory attempts to ingest a new payload, **Then** the Factory MUST set its state to JAMMED and pause the engine.
2. **Given** a JAMMED pipe, **When** the pipe clears space, **Then** it MUST broadcast an IDLE signal and the upstream Factory MUST resume processing.

---

### User Story 2 - Wildcard Pipe Routing (Priority: P2)
As a user, I want to connect a Factory to a Data Pipe using a wildcard "any" state, so I don't have to define complex numeric routing tables for simple direct connections.

**Why this priority**: Usability. Simplifies the common use case of "send everything from this factory into this pipe."

**Independent Test**: Connect a Factory to a Data Pipe with `route_state: "any"`. Verify all processed payloads enter the pipe regardless of their result value.

**Acceptance Scenarios**:
1. **Given** a DataPipe with `route_state: "any"`, **When** the upstream Factory finishes processing a payload with any result (>0), **Then** the payload MUST be handed to that pipe.

---

### User Story 3 - Aware Guards (Priority: P3)
As a system, I want Guard nodes to be aware of the state of their upstream Warehouse, so they don't waste CPU cycles scanning for payloads when the warehouse is empty.

**Why this priority**: Performance. Reduces rule-engine evaluations in large simulations.

**Independent Test**: Attach a Guard to an empty Warehouse. Verify the Guard remains in an IDLE visual state and does not execute rules.

**Acceptance Scenarios**:
1. **Given** an empty WarehousePart, **When** the simulation is running, **Then** the connected GuardPart MUST remain IDLE and skip its `radar` scan logic.

---

### Edge Cases

- **Multi-Guard Competition**: If multiple Guards pull from the same Warehouse, the first one to process a payload effectively "wins" it, but the Warehouse persists in an ACTIVE state as long as any payloads remain.
- **Zero Rule Conflict**: If a Factory result is <= 0 (Error), the "Zero Rule" in `FlowEntity` takes precedence over "any" routing, and the payload is ejected as an error.
- **Bi-directional Signals**: Logic wires are bi-directional; ensure that signal feedback loops do not cause infinite status toggling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `FlowEntity` MUST centralize `receive_signal` and `broadcast_status` logic. It MUST implement a conservative signal policy: any "JAMMED" status from a connected route takes precedence and pauses the machine.
- **FR-002**: `resolve_exit_path` MUST support a wildcard `"any"` for pipe matching. If multiple valid wildcard pipes exist, the system MUST use the first one encountered in the entity list.
- **FR-003**: `DataPipePart` MUST inherit from `FlowEntity` and participate in signaling. It MUST only broadcast status signals when crossing critical state boundaries (e.g., from IDLE to JAMMED).
- **FR-004**: `WarehousePart` MUST expose a `last_state` property reflecting its internal buffer count (IDLE vs ACTIVE).
- **FR-005**: `GuardPart` MUST check the upstream `last_state` before initiating a scan. However, manual triggers and external REFRESH signals MUST prioritize a scan regardless of the reported state.

## Clarifications

### Session 2026-03-29 (Strict I/O Rule)
- **Principle**: To minimize complexity and maximize Separation of Concerns, we adopt the following Strict I/O constraints:
    - **Sources** (0 In, 1 Out): Pure generators. No incoming payloads.
    - **Factories** (1 In, 1 Out): Pure transformers. No routing logic; they just process and hand off to a single output (via `target_uuid` or proximity).
    - **Sinks** (1 In, 0 Out): Pure consumers. 
    - **Warehouses** (N In, N Out): Central "Message Brokers". They hold state and allow merging/splitting of streams.
    - **Guards** (1 In, 1 Out): Dedicated routers. They pull from a Warehouse and push to exactly one destination.

- Q: Can a Factory still have multiple output paths? → A: No. Under the Strict I/O Rule, a Factory should output to exactly one destination (usually a Pipe or a Warehouse). If routing is needed, it should output to a Warehouse, and Guards should handle the splits.
- Q: How does this affect existing YAML configs? → A: It means we can eventually deprecate the `routing: []` property on Factories, moving all decision-making logic to Guard predicates.


### Key Entities *(include if feature involves data)*

- **FlowEntity**: Base class for all logic nodes; handles backpressure and routing.
- **DataPipePart**: Moving from `GamePart` to `FlowEntity`; acts as both a transit vessel and a signal propagator.

### Core Architecture Compliance *(mandatory)*

- **FlowEntity Pattern**: Yes, `DataPipePart` refactored to inherit from `FlowEntity`.
- **WOLF Routing**: Yes, utilizing `resolve_exit_path` for "any" routing.
- **Backpressure**: Standardizing `receive_signal` and `broadcast_status`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Data Pipes correctly propagate JAMMED signals to upstream nodes.
- **SC-002**: Factory configuration size reduced by 50% for simple pipe-out connections (by removing routing tables).
- **SC-003**: CPU usage for Guard nodes reduced by >90% when upstream warehouses are empty.

## Assumptions

- No changes required to `rule_engine` syntax.
- DataPipePart remains `pymunk.Body.KINEMATIC`.
- Existing YAML configurations for entities are compatible with the new "any" route state.
