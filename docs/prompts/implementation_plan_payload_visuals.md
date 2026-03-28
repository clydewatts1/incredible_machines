# Implementation Plan: Payload Visual Debugging

This plan enhances the visual representation of payload balls to provide immediate debugging information about their state, type, and routing history using three distinct color zones.

## Proposed Changes

### Physics & Base Entity

#### [MODIFY] [base.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/base.py)
- **`GamePart.__init__`**:
    - When `template == "Circle"`, initialize the following default colors in `self.payload`:
        - `ball_inner_colour`: [(0, 100, 0)](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py#219-239) (Dark Green - State)
        - `ball_colour`: [(0, 200, 0)](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py#219-239) (Green - Ball Type)
        - `ball_rim_colour`: [(100, 255, 100)](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py#219-239) (Light Green - Routing)
- **`FlowEntity.resolve_exit_path`**:
    - After a routing rule is successfully matched (either via Pipe or Explicit Rule), update the `payload_entity.payload["ball_rim_colour"]`.
    - I will generate a new color (e.g., based on the `search_state` or a cycle of distinct colors) to indicate that a routing decision was made.

### Specialized Entities

#### [MODIFY] [payloadball.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/payloadball.py)
- **[draw](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py#219-239)**:
    - Replace the single `pygame.draw.circle` call with three concentric circle calls:
        1. **Outer Rim**: `ball_rim_colour` at full radius.
        2. **Main Body**: `ball_colour` at ~75% radius.
        3. **Inner State**: `ball_inner_colour` at ~40% radius.
    - **Spin Line**: Draw a black line ([(0, 0, 0)](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/warehouse.py#219-239)) from the center to the outer edge based on `self.body.angle`.
    - Maintain the glossy highlight overlay.
+
+### Documentation
+
+#### [MODIFY] [payload_ball.md](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/docs/entity/payload_ball.md)
+- Update the documentation to explain the 3-color coding system for visual debugging.
+- Define the conventions:
+    - Inner Circle: State.
+    - Ball Body: Type.
+    - Ball Rim: Routing Information.
+    - Document default green shades for each zone.

---

## Verification Plan

### Manual Verification
1. Run `python main.py`.
2. Load the newly created demo: [saves/demo_source_ai/demo_source_ai.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/demo_source_ai/demo_source_ai.yaml).
3. Start the simulation (**▶**).
4. Observe the balls emitted by the CSV Source.
5. **Verify Initial State**: The balls should have three shades of green (dark inner, medium body, light rim).
6. Observe the balls exiting the AI Brain.
7. **Verify Routing Color**: When a ball is routed to the "Success" or "Failure" path, its **Rim Color** should change to a different color (e.g., Yellow or Blue) to indicate the routing logic has fired.
8. Use the **PAUSE** mode and the **Detail** dialog to verify that the [payload](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#211-234) dictionary correctly contains these color values.
