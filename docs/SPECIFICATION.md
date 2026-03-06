# Milestone 1 Specification: Basic Sandbox Foundation

## Overview
This specification details the first milestone for "The Incredible Machine Clone". 
The goal is to establish the foundational architecture, integrating Pygame for rendering and Pymunk for physics simulation according strictly to our Project Constitution.
It will include a basic Pygame window with static boundaries, an Edit/Play mode state machine, and the ability to spawn two rudimentary entities: a bouncy ball and a static ramp.

## 1. Technical Requirements
* **Language:** Python 3.11+
* **Libraries:** `pygame` (rendering, input), `pymunk` (physics)
* **Architecture:** Strict separation of concerns. The Pymunk body dictates the Pygame sprite position and rotation.

## 2. Window and Environment
* **Resolution:** A standard window size (e.g., 800x600 or 1024x768), defined clearly in a constants file.
* **Static Boundaries:** The screen will have invisible or visible static Pymunk segments around the window edges to prevent objects from falling out of bounds.
* **Constants Setup:** A dedicated configuration/constants file (e.g., `constants.py`) must be created to hold screen dimensions, physics constants (gravity, fixed time steps like `1/60.0`), colors, etc. Avoid hardcoding magic numbers.

## 3. Game State Management
The application will implement a clear state machine for the two primary game modes:

### Edit Mode (Build Phase)
* Physics simulation (`space.step()`) is paused.
* Gravity effect is effectively zero (objects remain static).
* User Interface: Mouse input allows the user to click, grab, move, and potentially rotate spawned objects around the screen.
* Spawning: A mechanism (e.g., keyboard shortcuts like 'B' for Ball, 'R' for Ramp) allows spawning new objects at the mouse cursor.

### Play Mode (Simulation Phase)
* Physics simulation is active, stepping forward at a fixed timestep (`space.step(1/60.0)`).
* Gravity is applied to the Pymunk space.
* User Interface: Mouse drag-and-drop on game entities is disabled.
* A toggle mechanism (e.g., hitting the SPACEBAR or an explicitly drawn UI button) transitions smoothly between Edit Mode and Play Mode.

## 4. Entity Architecture
* **Base Class:** A base `GamePart` or `Entity` class will be designed using OOP principles. It must manage:
  * A Pymunk `Body` and `Shape` for physics.
  * A Pygame `Surface` or drawing method for visuals.
  * An `update()` method that synchronizes the Pygame visual position and rotation exactly with the Pymunk physics state.
* **Fail Loudly Pattern:** The synchronization logic must include assertions or explicit checks ensuring physical and visual components exist and match properly. If they mismatch, the game should raise an error rather than fail silently.

## 5. Milestone 1 Game Parts

### Bouncy Ball (Dynamic Entity)
* Has a dynamic Pymunk body with defined mass, moment of inertia, and high elasticity.
* Represented visually by a drawn circle graphic in Pygame. 
* Responds to gravity during Play Mode.

### Static Ramp (Static/Kinematic Entity)
* Has a static Pymunk body (mass and moment = infinity) with a segment or flat polygon shape.
* Does not fall or respond to gravity, providing a solid surface for the Bouncy Ball to interact with.
* Represented visually by a drawn line or filled polygon in Pygame.

## 6. Implementation Constraints (From Constitution)
* **No internal variable framerates:** Physics must strictly use a fixed `space.step(1/60.0)`.
* **The Pymunk Rule:** No visual coordinates can be manually updated during Play Mode; they must rely entirely on querying Pymunk's physical reporting.
* **Coordinate Awareness:** The implementation handles the Pygame/Pymunk coordinate mapping carefully. Pygame's Y-axis goes down, so appropriate translations and rotation mappings (radians) must be addressed if Pymunk's standard behavior requires it.
* **Code Quality:** The code must be heavily commented, explaining *why* specific Pymunk joints or constraints are used. Build incrementally.

## Success Criteria for Milestone 1
1. The game launches an initialized Pygame window.
2. The user can seamlessly toggle between Edit and Play modes.
3. In Edit mode, the user can spawn a Bouncy Ball and a Static Ramp, and reposition them using the mouse.
4. In Play mode, the ball drops under the influence of gravity, bounces off the static ramp accurately, and is fully contained by the screen edges.
5. All codebase elements strictly adhere to the Project Constitution. No Python code will be written until this specification is approved.
