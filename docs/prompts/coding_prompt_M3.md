Role: Senior Gameplay Programmer

Context: > Please perform a comprehensive review of the following documents:

docs/CONSTITUTION.md (specifically Sections 2, 5, 6, 7, and the new Section 8).

docs/SPECIFICATION_M3_InteractionHighlighting.md.

docs/IMPLEMENTATION_PLAN_M3_InteractionHighlighting.md.

Task:
It is time to implement Milestone 3: Universal Interaction Highlighting.

Execution Requirements:

Base Class Refactoring: You MUST refactor the base GamePart (or Entity) class to include a hovered state and a method for rendering highlights. Do not implement this per-object; use inheritance as mandated by Section 8 of the Constitution.

Pymunk Querying: Implement the point_query_nearest logic in the main loop to detect which object the mouse is over. Ensure you handle the conversion between Pygame and Pymunk coordinates correctly.

Fail Loudly: Maintain strict assertions. If an object is detected but lacks the necessary base class attributes for highlighting, the system should raise an explicit error.

Naming Conventions: Any helper files created must follow the snake_case rule from Section 7.

Final Action & Quality Assurance:

After writing the code, run main.py to ensure there are no crashes.

Human-in-the-Loop Validation: Once the code is running, provide a response confirming that the "Manual Test Script" from the Milestone 3 Specification is ready for me to execute. State clearly that you have verified the highlighting works on both the Bouncy Ball and the Angled Ramp.