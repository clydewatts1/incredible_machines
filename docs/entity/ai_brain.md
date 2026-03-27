# Ai Brain
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
- `auto_release`: `True`
- `collision_sound`: `default_collision.wav`
- `cost_modifier`: `-10.0`
- `elasticity`: `0.5`
- `friction`: `0.5`
- `height`: `96`
- `input_side`: `top`
- `mass`: `1.0`
- `model`: `llama3.2`
- `output_side`: `right`
- `routing`: `[{'max_state': 10, 'velocity': 200, 'angle': 45, 'desc': 'Success Route', 'output_side': 'right'}, {'max_state': 100, 'velocity': 10, 'angle': 45, 'desc': 'Failure Route', 'output_side': 'left'}]`
- `spawn_sound`: `spawn.wav`
- `system_prompt`: `You are a quality control AI. Look at the 'status' field. If the status is 'SUCCESS', return route_state 10. If 'FAILURE', return route_state 100.`
- `width`: `96`

### Animation States
- `False`: `ai_brain_off`
- `INITIALIZING`: `ai_brain_initializing`
- `IDLE`: `ai_brain_idle`
- `INGESTING`: `ai_brain_ingesting`
- `WRITING`: `ai_brain_writing`
- `FATAL`: `ai_brain_fatal`