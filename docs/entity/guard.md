# Guard
**Category**: logic  
**Key Bind**: N/A

## Description
A logic component.

## Summary
Summary goes here.

## Detail
Detail goes here.

## Parameters and Functionality

### Baseline Properties
- `template`: Unknown
- `is_static`: True

### Additional Parameters
- `guard_query`: `True` (Standard rule-engine expression)
- `source_uuid`: UUID of the Warehouse to pull from.
- `target_uuid`: UUID of the destination entity or Data Pipe.
- `sort_by`: Property key to sort payloads by before pulling.
- `sort_order`: `desc` or `asc`.

## Hibernation & Signaling
Guards use an event-driven "active pull" model to conserve CPU:
- **Hibernation (Slumber)**: The Guard skips CPU-intensive rule scans while the upstream Source is in an **IDLE** state.
- **Wake-up**: The Guard automatically begins scanning when the upstream Source broadcasts an **ACTIVE** signal (payload available).
- **Manual Override**: External REFRESH signals and manual UI triggers force a scan regardless of the upstream state.
- **Backpressure**: The Guard will pause pulling if the downstream target broadcasts a **JAMMED** signal.

### Visual States
- **Blue Beam**: Idle/Slumbering.
- **Yellow Beam**: Active scanning (searching for matching payloads).
- **Green Flash**: Successful match and payload extraction.

- `collision_sound`: `default_collision.wav`
- `color`: `[0, 150, 255]`
- `elasticity`: `0.5`
- `friction`: `0.5`
- `height`: `64`
- `mass`: `1.0`
- `scan_interval`: `0.5`
- `spawn_sound`: `spawn.wav`
- `width`: `64`