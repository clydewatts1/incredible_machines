Role: Lead System Architect

Context: Please read docs/CONSTITUTION.md and the most recent Specification for Milestone 3 (Interaction Highlighting). We are ready to move from Specification to Planning.

Task: Generate a comprehensive technical implementation plan for Milestone 3.

Operational Constraints:

Naming Convention: Per Section 7 of the Constitution, name the file docs/IMPLEMENTATION_PLAN_M3_InteractionHighlighting.md.

Base Class Integration: The plan must explicitly detail how the hover detection and highlighting logic will be implemented within the base GamePart or Entity class to ensure universal inheritance for all current and future objects.

Validation Steps: Per Section 6, every task in the plan MUST include a "Validation" step. This step must describe how to verify the code works before moving to the next task.

Strict Separation: Ensure the plan maintains the separation between Pymunk (the query for the object under the mouse) and Pygame (the rendering of the highlight effect).

Required Tasks to include in the plan:

Update the base class to handle a hovered state.

Implement the Pymunk point_query logic in the main loop to detect the topmost object under the mouse.

Update the rendering logic in the base class to apply visual feedback based on the hovered state.

Verify that existing objects (Bouncy Ball, Angled Ramp) automatically display this behavior.

Final Action: Output the Markdown file for my review. Do not write any Python code yet.