# Data Sink Mcp
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
- `exporter_type`: `mcp`
- `friction`: `0.5`
- `height`: `96`
- `mass`: `1.0`
- `spawn_sound`: `spawn.wav`
- `width`: `96`

### Animation States
- `False`: `data_sink_off_mcp`
- `INITIALIZING`: `data_sink_initializing_mcp`
- `IDLE`: `data_sink_idle_mcp`
- `INGESTING`: `data_sink_ingesting_mcp`
- `WRITING`: `data_sink_writing_mcp`
- `FATAL`: `data_sink_fatal_mcp`

### Export Configuration
- `transport`: `sse`
- `url`: `http://localhost:8000/sse`
- `tool_name`: `post_incredible_machine_data`
- `timeout`: `5`