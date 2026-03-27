# Data Sink
**Category**: sinks  
**Key Bind**: N/A

A sinks component.

## Required Properties
- `template`: Rectangle
- `is_static`: True
- `width`: 96
- `height`: 96
- `active_sides`: `['top']`
- `accepts_types`: `['bouncy_ball', 'payload_ball']`
- `exporter_type`: `null`

## Optional Properties & Defaults
- `export`:
  - `directory`: `"exports"`
  - `file_prefix`: `"sink_output"`
  - `max_objects`: `10`
  - `rotation_seconds`: `180`
- `animations`: `OFF`, `INITIALIZING`, `IDLE`, `INGESTING`, `WRITING`, `FATAL`

