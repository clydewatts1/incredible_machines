# Milestone 19: Advanced Physics Mechanics (Motors & Conveyors) - Specification

## 1. Overview
Milestone 19 introduces driven, continuous motion mechanics to the "Incredible Machines" sandbox environment. By adding active mechanical components like Conveyor Belts and Motors (Spinning Gears/Wheels), players will be able to construct more elaborate, dynamic Rube Goldberg-style contraptions. This extends the sandbox beyond rudimentary gravity-driven physics, allowing for automated transport and rotational drive systems. 

## 2. Goals
- **Introduce Conveyor Belts**: Implement horizontal transport surfaces that actively push resting dynamic entities.
- **Introduce Motors**: Implement continuously rotating bodies that can physically interact with and propel other entities.
- **Ensure Customizability**: Both mechanics must be tunable in real-time via the existing Milestone 14 Property Editor.
- **Integrate with Signals**: Connect these mechanical components to the Logic Wiring system (Milestone 17) to allow circuit-based toggling (On/Off behavior).

## 3. Technical Implementation Details

### 3.1 Conveyor Belts

- **Shape & Type**: Conveyor Belts will be constructed as static or kinematic rectangular bodies to prevent them from falling or being knocked out of alignment, providing a stable foundation for moving other entities.
- **Physics Property**: The core mechanic relies on Pymunk's `surface_velocity` attribute applied to the shape. This natively imparts a driving velocity to any dynamic objects resting against the surface, perfectly simulating a moving belt.
- **Configuration (`entities.yaml`)**:
  - Introduce a `speed` parameter (float) representing the horizontal surface velocity of the belt. 
  - Introduce a `direction` parameter (string) which can be `"right"` or `"left"`.
- **Instance Overrides**: 
  - Both `speed` and `direction` must be exposed to the M14 Property Editor, enabling players to adjust the delivery speed and heading of items dynamically.

### 3.2 Motors (Spinning Gears/Wheels)

- **Shape & Type**: Motors will be implemented as dynamic bodies (typically circles or polygons representing gears).
- **Physics Constraint**: Because the motor is a dynamic body meant to be placed arbitrarily on the canvas, it requires bracing to avoid falling under gravity.
  - The motor body will be pinned to a static background body using a `pymunk.PivotJoint`. 
  - To drive the rotation, a `pymunk.SimpleMotor` constraint will be attached between the motor body and the static background body.
- **Configuration (`entities.yaml`)**:
  - Introduce a `motor_speed` parameter (float), defined in radians per second.
  - Introduce a `direction` parameter (string) which can be `"clockwise"` or `"counter-clockwise"`.
- **Instance Overrides**: 
  - The `motor_speed` and `direction` properties must be editable via the M14 Property Editor, allowing players to control the rotational momentum and spin direction.

### 3.3 Logic Signal Integration (Milestone 17)

Both Conveyor Belts and Motors will be capable of receiving logic signals (e.g., from a Basket).
- **State Toggling**: These active elements will implement the `receive_signal` interface.
- **Behavior**: When a signal is received, the entity should toggle its current speed between `0` (Off) and its configured `speed` / `motor_speed` (On). This allows for complex dependency chains where machines only activate when specific triggers are met.

## 4. Acceptance Criteria
- [ ] A Conveyor Belt entity can be placed on the canvas and successfully moves resting dynamic bodies horizontally.
- [ ] A Motor entity can be placed, remains suspended in mid-air (pinned), and continuously rotates at a driven speed.
- [ ] Both `speed` (Conveyor) and `motor_speed` (Motor) can be modified on individual instances using the Property Editor.
- [ ] Logic signals (e.g., from a Basket ingest) can successfully start or stop the motion of a wired Conveyor or Motor.
- [ ] The save/load system (Milestone 10/17) correctly persists the customized speeds and logic connections.
