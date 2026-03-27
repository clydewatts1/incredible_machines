# CSV Data Source
**Category**: sources  
**Key Bind**: N/A

A sources component.

## Required Properties
- `template`: Rectangle
- `is_static`: True
- `width`: 96
- `height`: 96
- `engine_type`: `csv`
- `active_side`: `Left`
- `exit_velocity`: `150.0`
- `exit_angle`: `180.0`
- `output_variant`: `payload_ball`
- `instructions`:
  - `filepath`: (CSV file path)
  - `loop`: `true`
  - `skip_header`: `true`
  - `delimiter`: `','`

## Optional Properties & Defaults
- `emit_interval`: `2.0`
- `mass`: `1.0`
- `friction`: `0.5`
- `elasticity`: `0.5`
- `collision_sound`: `default_collision.wav`
- `spawn_sound`: `spawn.wav`
- `animations`: `OFF`, `INITIALIZING`, `IDLE`, `POLLING`, `EMITTING`, `EXHAUSTED`, `FATAL`

