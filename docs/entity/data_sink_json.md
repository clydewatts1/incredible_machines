# Data Sink Json
**Category**: sinks  
**Key Bind**: N/A

## Description
A sinks component.

## Summary
Summary goes here.

## Detail
Detail goes here.

## Parameters and Functionality

### Baseline Properties
- `template`: Unknown
- `is_static`: True

### Additional Parameters
- `accepts_types`: `['bouncy_ball', 'payload_ball']`
- `active_sides`: `['top']`
- `collision_sound`: `default_collision.wav`
- `consumption_time`: `1.0`
- `elasticity`: `0.5`
- `exporter_type`: `json`
- `friction`: `0.5`
- `height`: `96`
- `mass`: `1.0`
- `spawn_sound`: `spawn.wav`
- `width`: `96`

### Animation States
- `False`: `data_sink_off_json`
- `INITIALIZING`: `data_sink_initializing_json`
- `IDLE`: `data_sink_idle_json`
- `INGESTING`: `data_sink_ingesting_json`
- `WRITING`: `data_sink_writing_json`
- `FATAL`: `data_sink_fatal_json`

### Export Configuration
- `directory`: `exports`
- `file_prefix`: `sink_json`
- `max_objects`: `10`
- `rotation_seconds`: `180`