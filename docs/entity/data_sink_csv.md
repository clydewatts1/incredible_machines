# Data Sink Csv
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
- `exporter_type`: `csv`
- `friction`: `0.5`
- `height`: `96`
- `mass`: `1.0`
- `spawn_sound`: `spawn.wav`
- `width`: `96`

### Animation States
- `False`: `data_sink_off_csv`
- `INITIALIZING`: `data_sink_initializing_csv`
- `IDLE`: `data_sink_idle_csv`
- `INGESTING`: `data_sink_ingesting_csv`
- `WRITING`: `data_sink_writing_csv`
- `FATAL`: `data_sink_fatal_csv`

### Export Configuration
- `directory`: `exports`
- `file_prefix`: `sink_csv`
- `max_objects`: `10`
- `rotation_seconds`: `180`