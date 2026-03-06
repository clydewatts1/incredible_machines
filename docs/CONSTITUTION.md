# **Project Constitution: The Incredible Machine Clone**

## **1\. Core Identity & Tech Stack**

* **Project Type:** 2D Physics Puzzle Sandbox Game.  
* **Language:** Python 3.11+  
* **Rendering & Window Management:** pygame.  
* **Physics Engine:** pymunk.

## **2\. Architectural Rules (The Golden Rule)**

* **Strict Separation of Concerns:** Physics simulation and graphical rendering must be strictly decoupled.  
* **The Pymunk Rule:** Visuals must *always* follow the physics.  
* **Object-Oriented Design (OOP):** All game pieces inherit from a base GamePart or Entity class.

## **3\. Game State Management**

1. **Edit Mode (Build Phase):** Physics paused, dragging enabled.  
2. **Play Mode (Simulation Phase):** Physics active, dragging disabled.

## **4\. Physics & Simulation Standards**

* **Fixed Time Steps:** 1/60.0.  
* **Constants File:** No magic numbers in functions.  
* **Coordinate Conversion:** Pymunk (radians) to Pygame (degrees) conversion must be consistent.

## **5\. Agent Coding Guidelines**

* **Readability over Cleverness.**  
* **Incremental Implementation.**  
* **Fail Loudly:** Throw errors for mismatched physics/visuals.

## **6\. Quality Assurance & Validation**

* **Human-in-the-Loop Testing:** Every spec must include "Manual Test Instructions".

## **7\. Documentation & Naming Conventions**

* **Specifications:** docs/SPECIFICATION\_M\[Number\]\_\[Name\].md  
* **Implementation Plans:** docs/IMPLEMENTATION\_PLAN\_M\[Number\]\_\[Name\].md  
* **Code Files:** snake\_case.py.

## **8\. Audio & Sound Standards**

* **Universal Audio Feedback.**  
* **In-Memory Management.**  
* **Fallback Sound Logic.**

## **9\. Data Management & Property Standards**

* **YAML-Based Configuration:** All configurable properties live in external YAML files.  
* **Template-Variant Inheritance:** The YAML structure must support templates (base properties) and variants (specific instances).  
* **Property Merging:** When loading a variant, the system must deep-merge the template's properties with the variant's overrides.  
* **Entity Metadata Structure:** Entities support a dictionary-based properties attribute.

## **10\. Visual Asset & Aesthetic Standards**

* **YAML-Driven Assets:** Backgrounds and entity textures must be defined in YAML.  
* **Sprite-based Entities:** If an entity specifies a texture\_path, the draw() method must render a rotated pygame.Surface.  
* **Rotation Sync:** Sprites must be rotated using \-math.degrees(self.body.angle).