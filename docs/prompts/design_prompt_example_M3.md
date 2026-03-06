Role: Lead System Designer

Context: Please read docs/CONSTITUTION.md. We are moving into Milestone 3.

Task 1: Update Constitution
First, add a new section to docs/CONSTITUTION.md as follows:
## 8. UX & Visual Feedback Standards
* **Universal Interaction Highlighting:** Any object in the game that can be interacted with, dragged, or modified MUST provide clear, immediate visual feedback when the mouse cursor hovers over it or selects it (e.g., color tint, glow, or outline). This logic should be implemented in the base GamePart/Entity class so all future items inherit it automatically.

Task 2: Generate Specification
Create a new specification file following our naming conventions: docs/SPECIFICATION_M3_InteractionHighlighting.md.

Requirements for M3:

Implement a hover-detection system using pymunk's point query or pygame's rect collision.

Define the visual feedback style (e.g., a white border or a 20% brightness increase).

Per Section 8 of the Constitution, this must be integrated into the base class.

Mandatory Quality Assurance:
Per Section 6 of the Constitution, you MUST include a "Manual Test Script & Success Criteria" in the spec. The test must verify:

Highlighting occurs on the Bouncy Ball.

Highlighting occurs on the Angled Ramp.

Highlighting stops when the mouse leaves the object.

Constraint: Do not write code yet. Provide the updated Constitution and the new M3 Specification for my review.