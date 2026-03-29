# Data Model: Standardized Flow

This document defines the properties and state transitions for entities participating in the standardized flow signaling and routing.

## Entities

### `FlowEntity` (Base Class)
Base class handling signaling and routing.
- **Properties**:
  - `uuid` (str): Unique identifier.
  - `connected_uuids` (list): Registered downstream listeners.
- **Runtime State**:
  - `downstream_status` (str): Status received from neighbors (IDLE, JAMMED, etc.).
  - `visual_state` (str): Current machine animation state.

### `DataPipePart` (inherits FlowEntity)
- **Properties**:
  - `capacity` (int): Max payloads in transit.
  - `transit_time` (float): Time to traverse pipe.
  - `route_state` (str/float): Numeric route ID or "any" for wildcard fallback.
- **Runtime State**:
  - `transit_queue` (list): Active payloads in pipe.

### `WarehousePart` (inherits FlowEntity)
- **Runtime State**:
  - `stored_payload_uuids` (list): Buffering payloads.
  - `last_state` (str, dynamic): `ACTIVE` if buffer > 0, else `IDLE`.

### `GuardPart` (inherits FlowEntity)
- **Properties**:
  - `source_uuid` (str): Upstream warehouse or factory.
- **Runtime State**:
  - `needs_scan` (bool): Flag to initiate rules testing.

## State Transitions (Backpressure)

| From (State) | To (State) | Trigger | Action |
|--------------|------------|---------|--------|
| IDLE | JAMMED | Target FULL / Pipe at Capacity | `broadcast_status("JAMMED")` |
| JAMMED | IDLE | Target space becomes available | `broadcast_status("IDLE")` |
| ACTIVE | IDLE | Warehouse buffer empty | `broadcast_status("IDLE")` (Notifications) |
| IDLE | ACTIVE | Payload enters Warehouse | `broadcast_status("ACTIVE")` (Wake-up) |

## Guard Interaction Rules

- **Destructive Pull**: When a Guard "wins" a competition for a payload (it matches a rule and is successfully processed), the payload MUST be immediately removed from the `WarehousePart` buffer.
- **State Persistence**: The Warehouse remains in an `ACTIVE` state as long as at least one payload remains in the buffer after a successful Guard pull.
