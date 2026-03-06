# **Project Constitution: The Incredible Machine Clone**

## **1\. Core Identity & Tech Stack**

* **Project Type:** 2D Physics Puzzle Sandbox Game.  
* **Language:** Python 3.11+  
* **Rendering & Window Management:** pygame (Strictly for drawing graphics, handling UI, and capturing user input).  
* **Physics Engine:** pymunk (Strictly for mathematical simulation of gravity, collisions, and constraints).  
* **Prohibited Tech:** Do not introduce other game engines (like Godot, Unity, Arcade) or physics wrappers. Stick strictly to Pygame and Pymunk.

## **2\. Architectural Rules (The Golden Rule)**

* **Strict Separation of Concerns:** The physics simulation (pymunk.Space) and the graphical rendering (pygame.Surface) must be strictly decoupled.  
* **The Pymunk Rule:** Visuals must *always* follow the physics. The Pymunk body's position and rotation dictate where the Pygame sprite is drawn. Never update a Pygame visual coordinate directly during gameplay; update the Pymunk body and let the renderer follow it.  
* **Object-Oriented Design (OOP):** All game pieces (balls, ramps, gears, ropes) must inherit from a base GamePart or Entity class that manages both its Pymunk body/shape and its Pygame rendering logic.

## **3\. Game State Management**

The game exists in two mutually exclusive primary states:

1. **Edit Mode (Build Phase):** \* The physics space DOES NOT step (space.step() is not called).  
   * Gravity is effectively zero/paused.  
   * User input (mouse) can grab, move, and rotate objects.  
2. **Play Mode (Simulation Phase):**  
   * The physics space steps forward at a fixed time step (e.g., 1/60.0).  
   * Gravity is active.  
   * User cannot move objects directly with the mouse (unless interacting with specific "trigger" UI items).

## **4\. Physics & Simulation Standards**

* **Fixed Time Steps:** Always use a fixed delta time for space.step(1/60.0) to ensure deterministic physics behavior. Do not use variable frame rates for physics calculations.  
* **Constants File:** All physics variables (gravity, elasticity, friction, density) must be stored in easily adjustable variables or a constants configuration. Do not hardcode magic numbers deep inside functions.  
* **Coordinate Conversion:** Remember that Pygame's Y-axis goes *down* (top-left is 0,0) and Pymunk's standard Y-axis often goes *up*. **Crucial:** Pymunk 5.0+ handles Pygame coordinates natively if configured correctly, but you must ensure visual rotation matches physics rotation (which is in radians).

## **5\. Agent Coding Guidelines**

* **Readability over Cleverness:** Write clear, heavily commented code. Explain *why* a specific Pymunk joint or constraint is being used.  
* **Incremental Implementation:** Build components one by one. Do not attempt to build gears, ropes, and pulleys simultaneously.  
* **Fail Loudly:** If there is a mismatch between a Pygame visual and a Pymunk body, throw an error or log it. Do not swallow exceptions.