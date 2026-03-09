# Implementation Plan: Milestone 17 - Logic Wiring & Signals

## Phase 1: Wire Tool & State Management
**Goal:** Introduce the `WIRE` tool to the UI and handle the two-click selection state (Sender to Target).
**Target Files:** `main.py`, `utils/ui_manager.py` (if applicable)
**Actions:**
1. In `main.py`, add a `"WIRE"` button to the left UI panel alongside other tools (like `PLAY`, `EDIT`, `DELETE`).
2. Add a global tracking state for the active wiring operation, e.g., `game_state["wiring_source"] = None`.
3. In the main event loop under `pygame.MOUSEBUTTONDOWN`, when the active tool is `WIRE` and the user clicks on the canvas:
    - Determine which entity was clicked by intersecting the mouse position with the shapes in `entities`.
    - If no `wiring_source` is set, set it to the clicked entity (this becomes the Sender).
    - If a `wiring_source` *is* set and the user clicks a valid entity (the Receiver), append the Receiver's UUID to an array stored on the Sender (e.g., `wiring_source.connected_uuids.append(receiver.uuid)`). Then reset `wiring_source = None`.
4. Ensure `GamePart` in `entities/base.py` is updated to initialize `self.connected_uuids = []`.
**Verification:** Launch the game, select the WIRE tool, click two entities. Add a `print(sender.connected_uuids)` to verify that the selection click successfully recorded the target's UUID.

## Phase 2: Connection Rendering
**Goal:** Visually draw the logical links between connected entities when in EDIT mode.
**Target Files:** `main.py`
**Actions:**
1. In `main.py`'s Pygame rendering loop, check if `game_state["mode"] == "EDIT"` (or if the active tool is `WIRE`).
2. If so, iterate over all `entities`. For each entity, iterate over its `connected_uuids` list.
3. For each UUID, safely look up the target entity in the `active_instances` dictionary using `active_instances.get(target_uuid)`.
4. If found, extract the Pygame screen coordinates for both the Sender (`entity.body.position`) and the Receiver (`target_entity.body.position`).
5. Use `pygame.draw.aaline(surface, color, start_pos, end_pos)` to draw a clean line connecting them.
6. (Optional visual feedback) Draw the line starting from the sender and add a small circle acting as an arrowhead at the receiver to denote signal direction.
**Verification:** Launch the game, use the WIRE tool to link several objects together. You should see instant visual confirmation of the connected nodes dynamically following the objects if they are moved.

## Phase 3: Signal Execution Logic
**Goal:** Empower the logic web to actually transmit and execute events decoupled from the physics step.
**Target Files:** `main.py`, `entities/base.py`
**Actions:**
1. Define a standardized input interface. In `entities/base.py`, add a `receive_signal(self, payload=None)` method. For the "Cannon" variant, this should trigger an immediate shot (bypassing the timer, e.g., setting `self.force_shoot = True`).
2. Implement safety decoupling. Do NOT trigger logic directly inside Pymunk collision handlers. Instead, create a global `signal_queue = []` in `main.py`.
3. Update the `basket_sensor_begin` collision handler in `main.py`. When an object matches `accepts_types` and is successfully ingested, append the Basket entity to `signal_queue`.
4. In the core `while running:` loop of `main.py`, *after* the `space.step()` call has completed:
    - Iterate through the `signal_queue`.
    - For each Sender entity in the queue, iterate over its `connected_uuids`.
    - Retrieve the target entity safely using `target = active_instances.get(uuid)`.
    - If it exists, call `target.receive_signal()`.
    - Finally, clear the `signal_queue`.
**Verification:** Transition to PLAY mode with a Basket wired to a Cannon. Drop an accepted bouncy_ball into the Basket. Validate that the Cannon immediately fires, and no physics lockups or crashes occur.

## Phase 4: Serialization
**Goal:** Ensure the logic web persists when levels are saved and loaded.
**Target Files:** `utils/level_manager.py`, `main.py`
**Actions:**
1. In `utils/level_manager.py`'s `save_level` function, add logic to traverse `active_instances`.
2. Extract all pairs of connections into a structure like `connections: [{"sender": uuid1, "receiver": uuid2}, ...]`. Embed this alongside the `entities` array in the saved YAML output.
3. In `load_level`, ensure it processes the new `connections` array.
4. After all entities are instantiated and spawned into `active_instances`, iterate over the loaded `connections`.
5. For each connection pair, securely retrieve the `sender` and `receiver` entities from `active_instances`, and append the receiver's UUID to the sender's `connected_uuids` attribute, thereby restoring the logic web.
**Verification:** Create a complex Level with multiple entities. Wire them together. Save the level using the UI. Clear the screen. Load the level using the UI. The wiring lines should seamlessly reappear and function perfectly in PLAY mode.
