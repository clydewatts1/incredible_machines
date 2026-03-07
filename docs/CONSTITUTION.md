# **Incredible Machines: Project Constitution**

This document defines the core principles, architectural constraints, and coding standards for the "Incredible Machines" project. All AI agents and developers must adhere to these rules to maintain project integrity.

## **1\. Project Identity**

* **Name:** Incredible Machines  
* **Genre:** 2D Physics-based puzzle game (inspired by The Incredible Machine)  
* **Core Loop:** Place parts \-\> Run simulation \-\> Achieve goal \-\> Next level  
* **Vibe:** Tinkering, experimentation, playful physics, mechanical logic.

## **2\. Core Technologies**

* **Language:** Python 3.x  
* **Rendering & Input:** Pygame Community Edition (CE) is highly recommended over standard Pygame for better performance and modern features.  
* **Physics Engine:** Pymunk (2D physics library)  
* **Configuration:** YAML (for levels, parts, environment settings)

## **3\. Architectural Principles**

* **Separation of Concerns:**  
  * *Physics (Pymunk):* Handles all collision, gravity, mass, and movement. Visuals must *follow* physics, not dictate them.  
  * *Rendering (Pygame):* Only reads physics state to draw the screen.  
  * *Game Logic:* State machine managing transitions (Edit Mode vs. Play Mode).  
* **Data-Driven Design:** Hardcoding values (mass, friction, sprite paths) in Python is strictly prohibited. All entity definitions must live in config/entities.yaml.  
* **Modularity:** New parts/entities should be easily added by creating a new class inheriting from a base Entity class and adding a YAML entry.

## **4\. Physics Engine (Pymunk) Mandates**

* **The Single Source of Truth:** Pymunk's Space is the absolute authority on object position and rotation.  
* **Coordinate Systems:** Pygame's origin (0,0) is top-left. Pymunk's origin can be bottom-left (standard) or top-left depending on setup. *Mandate:* Explicitly define and document the coordinate conversion functions and use them universally.  
* **Units:** 1 Pymunk unit \= 1 pixel (unless a specific scale factor is explicitly decided and documented). Keep mass and forces within reasonable, stable ranges.  
* **Time Step:** The physics simulation must use a fixed time step (e.g., 60Hz) to ensure deterministic behavior across different machines. Do *not* use variable delta-time for physics step().

## **5\. Coding Standards (Python)**

* **Style:** PEP 8 compliant. Use type hinting (e.g., def calculate\_force(mass: float) \-\> float:) for all function signatures.  
* **Naming Conventions:**  
  * Classes: PascalCase  
  * Variables/Functions: snake\_case  
  * Constants: UPPER\_SNAKE\_CASE  
* **Error Handling:** Fail gracefully. If a sprite is missing, draw a magenta placeholder rectangle and log a warning; do not crash.

## **6\. The State Machine**

The game must clearly distinguish between:

1. **Edit Mode:** Physics simulation is *paused*. Players can place, move, and configure parts.  
2. **Play Mode:** Physics simulation is *running*. Player input is restricted to interactive parts (e.g., flipping a switch). Parts cannot be added or moved freely.

## **7\. Version Control & AI Interaction**

* **Incremental Commits:** Code changes must be small, focused, and tied to a specific milestone.  
* **Agent Roles:** Respect the defined roles of the Speckit AI agents (Plan, Specify, Implement, Checklist, Review). Do not merge steps.

## **8\. YAML Configuration Standards**

* All configurations (entities, levels) must be validated upon loading.  
* Structure must be clean and self-documenting.  
* Example:  
  ball\_bowling:  
    type: dynamic  
    mass: 10  
    radius: 15  
    elasticity: 0.1  
    friction: 0.8  
    visual: "bowling\_ball.png"

## **9\. Performance Constraints**

* Target Framerate: 60 FPS.  
* Object limits: The game should comfortably handle at least 100 physics objects simultaneously without dropping frames.  
* Avoid loading assets (images, sounds) during the main loop. Pre-load everything during initialization.

## **10\. Milestone Progression**

* Work must proceed strictly according to the defined milestones.  
* No "feature creep." Do not implement features from Milestone 4 while working on Milestone 2\.

## **11\. User Interface (UI) Standards**

* **Playable Area Boundary:** The UI acts as a physical picture frame. The Pymunk physics boundaries (static lines for floor/walls/ceiling) must be inset to match the playable\_rect. Objects must never spawn, fall, or bounce *behind* the UI elements.  
* **Separation of Input:** The game must distinguish between "UI Clicks" and "World Clicks." The main event loop must process UI collisions first. If a click falls on a UI element, it MUST NOT accidentally interact with the physics space behind it.  
* **Lightweight UI:** Avoid heavy external UI libraries (like pygame\_gui) unless absolutely necessary. Maintain a simple, custom UI manager (utils/ui\_manager.py) focusing on clear, basic components like buttons and panels.  
* **Data-Driven Toolbars:** Object palettes (side panels) must populate dynamically based on the variants loaded from config/entities.yaml. Avoid hardcoding object buttons. Icons should be auto-generated by drawing the entity onto a temporary surface.  
* **Graceful Stubs:** If a UI element represents a feature that does not yet exist (e.g., "Save", "Load", "Challenges"), it must render visually but safely log a "Not Implemented" message to the console when clicked, preventing game crashes.  
* **Clear State Indication:** The UI must provide immediate, obvious visual feedback of the current game state (e.g., highlighting whether the game is currently in PLAY or EDIT mode, and indicating the active tool via a "ghost" cursor).

## **12. Relational Architecture & Constraints**

* **Two-Pass Instantiation Rule:** The engine must spawn all bodies/shapes first, and then apply constraints/joints in a second pass.  
* **Instance Identity Rule:** Every spawned entity must have a Unique Identifier (UUID) to allow constraints and save/load files to target specific instances on the canvas.  
* **Cascading Deletion Rule:** If an entity is deleted, the system must safely remove any associated Pymunk constraints attached to it before removing the body.