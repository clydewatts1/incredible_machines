# Payload Ball
**Category**: payloads  
**Key Bind**: N/A

A payloads component.

## Required Properties
- `template`: Circle
- `is_static`: False
- `radius`: 15

## Optional Properties & Defaults
- `color`: `[0, 255, 255]`
- `mass`: `1.0`

## Visual Debugging (3-Color Coding)
When a Payload Ball is created, its visual representation defaults to three concentric circles indicating its status:
1. **Inner Circle (State)**: Dark Green `(0, 100, 0)` by default. Sourced from `payload["ball_inner_colour"]`.
2. **Main Body (Type)**: Green `(0, 200, 0)` by default. Sourced from `payload["ball_colour"]`.
3. **Outer Rim (Routing)**: Light Green `(100, 255, 100)` by default. Sourced from `payload["ball_rim_colour"]`.

**Routing Feedback**: 
If the payload passes through routing logic (e.g., via a Pipe or Explicit Rule in a Brain), the **Outer Rim** color is updated to denote successful routing (e.g., Blue for pipes, Yellowish for Brain rules, Red for hard errors).

**Spin Line**:
A black line from the center to the edge is drawn to display the physical rotation angle (`body.angle`) of the ball as it moves.
