# [Improved Wire & Connection Deletion]

The user reported being unable to delete a "wire logic" (the connection tool). This is likely due to the disconnect between the visual [connections](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/utils/visual_fx_manager.py#223-269) list (managed by the wire tool) and the underlying `target_uuid` properties (used for actual routing in components like AI Brain and Pipes).

## Proposed Changes

### main.py

#### [MODIFY] [main.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/main.py)
Update [handle_tool_click](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/main.py#1262-1385) for the `wire_tool`:
- When a connection is established between a source and target, explicitly set `source.overrides["target_uuid"] = target.uuid`.
- When a connection is toggled OFF (removed), check if `source.overrides["target_uuid"]` matches the target and clear it if so.
- Add a "Clear All Wires" shortcut: If the user clicks on an entity with the `wire_tool` while holding **SHIFT** (or a similar modifier), clear all outgoing connections from that entity.

## Verification Plan

### Automated Tests
- No automated tests for UI interactions currently exist that support multi-click tools.

### Manual Verification
1. Open [demo_source_ai.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/demo_source_ai/demo_source_ai.yaml).
2. Select the **Wire Logic** tool.
3. Establish a connection from the AI Brain to a Sink.
4. Verify in the Inspector that `target_uuid` is now set to the Sink's ID.
5. Click the AI Brain then the Sink again to toggle the wire OFF.
6. Verify the wire line disappears AND the `target_uuid` in the inspector is cleared.
7. Verify that the ball no longer routes to the Sink.
