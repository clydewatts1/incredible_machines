# AI Brain Node
**Category**: logic  
**Key Bind**: N/A

A logic component.

## Required Properties
- `template`: Rectangle
- `is_static`: True
- `width`: 96
- `height`: 96
- `input_side`: `top`
- `output_side`: `right`
- `model`: `llama3.2`
- `system_prompt`: "You are a quality control AI. Look at the 'status' field. If the status is 'SUCCESS', return route_state 10. If 'FAILURE', return route_state 100."

## Optional Properties & Defaults
- `cost_modifier`: `-10.0`
- `routing`: 
  - `Success Route`: `max_state: 10`, `velocity: 200`, `angle: 45`, `output_side: right`
  - `Failure Route`: `max_state: 100`, `velocity: 10`, `angle: 45`, `output_side: left`
- `mass`: `1.0`
- `friction`: `0.5`
- `elasticity`: `0.5`
- `collision_sound`: `default_collision.wav`
- `spawn_sound`: `spawn.wav`
- `animations`: `OFF`, `INITIALIZING`, `IDLE`, `INGESTING`, `WRITING`, `FATAL`

