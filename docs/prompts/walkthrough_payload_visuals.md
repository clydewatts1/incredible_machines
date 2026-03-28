# Walkthrough: Payload Visual Debugging

I have implemented the **Three-Color Payload Ball** system to provide immediate visual feedback on the state, type, and routing history of data packets (balls) as they move through your machines.

## Changes Made

### 1. Three-Color Visual Coding
- **File**: [entities/payloadball.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/payloadball.py)
- Payload balls now render as three distinct areas instead of a solid color:
    1.  **Inner Circle (40% radius)**: Represents the **State** of the payload. Sourced from `payload["ball_inner_colour"]`. Default is Dark Green.
    2.  **Main Body (75% radius)**: Represents the **Ball Type**. Sourced from `payload["ball_colour"]`. Default is Green.
    3.  **Outer Rim (100% radius)**: Represents **Routing Information**. Sourced from `payload["ball_rim_colour"]`. Default is Light Green.

### 2. Rotational Spin Line
- **File**: [entities/payloadball.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/payloadball.py)
- A black line is now drawn from the center of the ball to its outer edge.
- This line rotates accurately with the Pymunk physics body (`body.angle`), allowing you to easily see the physical spin of the ball as it rolls or flies through the air.

### 3. Dynamic Routing Feedback
- **File**: [entities/base.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py)
- Updated the [resolve_exit_path](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#766-893) function to automatically modify the `ball_rim_colour` when a payload passes through routing logic:
    -   **Pipes**: If successfully ingested by a pipe, the rim turns **Blue**.
    -   **Explicit Rules**: If routed by an explicit rule (like in a Brain), the rim turns **Yellowish** (tinted slightly based on the target state).
    -   **Hard Exits (Errors)**: If the payload faces a hard exit (e.g., no matching rule or pipe), the rim turns **Red**.

### 4. Documentation
- **File**: [docs/entity/payload_ball.md](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/docs/entity/payload_ball.md)
- Updated the manual entry to officially document this new 3-color coding system, the routing feedback conventions, and the physical spin line.

## Verification
1. Load [saves/demo_source_ai/demo_source_ai.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/demo_source_ai/demo_source_ai.yaml).
2. Start the simulation.
3. Watch the balls spawn from the CSV source. They will appear in three shades of green.
4. Watch as the balls roll down the ramps (you will see the black line spinning).
5. Watch the balls enter the AI Brain.
6. When the balls exit the Brain, you will notice their **Outer Rim** has changed color (likely to a yellowish tint) because they were successfully routed by the Brain's logic rules.
7. Pause the simulation and click "Detail" on a ball to see these precise RGB color values stored in its payload dictionary.
