# Milestone 3 Specification: Interaction Highlighting

## Overview
This specification defines the implementation of the UX and Visual Feedback Standards introduced in Milestone 3. The goal is to provide universal interaction highlighting for all interactive game entities.

## 1. Feature Requirements
### Hover-Detection System
* **Implementation:** The game must detect when the mouse cursor is hovering over an interactive physics object while in `EDIT` mode. 
* **Mechanism:** This should be achieved using `pymunk.Space.point_query` to locate shapes under the mouse cursor.
* **State Management:** A property (e.g., `is_hovered`) must be maintained and updated on the entity or its physics shape/body based on the mouse position.

### Visual Feedback Style
* **Base Class Integration:** Per Section 8 of the Constitution, the visual feedback logic MUST be implemented within the base `GamePart` (in `entities/base.py`) so all subclasses (Ball, Ramp, etc.) inherit it automatically.
* **Styling:** When an object is hovered, it must provide clear architectural visual feedback. 
  * Recommended style: A distinct outline (e.g., a yellow or white border 2-3 pixels thick) drawn around the shape's perimeter, or a noticeable color tint/brightness increase.

## 2. Technical Considerations
* **Performance:** The hover detection spatial query should run efficiently during the `EDIT` mode loop, updating the hovered state of entities before rendering.
* **Separation of Concerns:** `pymunk` handles the spatial queries to determine intersections with the mouse coordinates. `pygame` handles the rendering of the highlight based entirely on that queried state.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating Universal Interaction Highlighting
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Setup the Test Environment**
1. Launch the application (starts in `Mode: EDIT`).
2. Press `R` to spawn a Ramp.
3. Press `B` to spawn a Bouncy Ball.

**Step 2: Verify Highlighting on the Angled Ramp**
1. Move the mouse cursor so it hovers directly over the static Ramp.
2. **Success Check:** The Ramp immediately displays the designated visual feedback (e.g., a white/yellow outline).
3. Move the mouse cursor away from the Ramp so it is over empty space.
4. **Success Check:** The visual feedback immediately disappears, returning the Ramp to its normal appearance.

**Step 3: Verify Highlighting on the Bouncy Ball**
1. Move the mouse cursor so it hovers directly over the Bouncy Ball.
2. **Success Check:** The Ball immediately displays the designated visual feedback.
3. Move the mouse cursor away from the Ball.
4. **Success Check:** The visual feedback immediately disappears.

**Sign-off:** The feature is complete when explicit, universal visual feedback reliably activates and deactivates on both entity types solely based on mouse hover proximity.
