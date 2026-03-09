# Specification: Milestone 17 - Logic Wiring & Signals

## Overview
Milestone 17 introduces a visual logic wiring system to "Incredible Machines." Rather than entities operating entirely independently based on local physics events, players will be able to interconnect them to form complex Rube Goldberg-style reactive systems. For example, a Basket successfully ingesting an item can transmit a signal to a distant Cannon, commanding it to fire instantly. This fundamentally shifts the game from a sandbox physics simulator to a logic puzzle creator.

## Goals
1. Introduce a new UI tool state enabling users to draw logic connections between entities.
2. Render anti-aliased, reactive logic wires in both EDIT and PLAY modes.
3. Establish a standard, decoupled signal-passing interface to prevent physics-step lockups.
4. Adapt the Level Manager to successfully serialize and deserialize this web of connections.

## Technical Implementation Details

### 1. The Wire Tool (UI & Interaction)
*   **Tool State:** Introduce a new `WIRE` state to the main application's tool palette.
*   **Interaction Flow:**
    *   While the `WIRE` tool is active, the left-click behavior changes.
    *   The first click on an entity sets it as the "Sender." Visual feedback (e.g., a colored highlight or rubber-band line attached to the cursor) should indicate an active wiring operation.
    *   The second click on a different entity sets it as the "Receiver."
*   **Data Structure:** The connection explicitly maps the Sender's raw `UUID` to the Receiver's `UUID`. An entity can have multiple outbound and inbound connections.

### 2. Visualizing Connections
*   **EDIT Mode:** Connections map visually as lines drawn via `pygame.draw.aaline` connecting the calculated center coordinates of the Sender and Receiver. These lines provide immediate visual documentation of the level's logic flow.
*   **PLAY Mode Flow Indication:** To provide runtime feedback, the connection line should not remain static. When a signal is successfully transmitted from Sender to Receiver, the specific line connecting them should flash prominently (e.g., spike in thickness or briefly change to a bright, emissive color like bright yellow/cyan) before fading back to its default state.

### 3. Signal Logic (Sender to Receiver)
*   **Interface Upgrade:** Active entities must implement a standardized interface method to receive external commands, such as `receive_signal(payload)`. For a Cannon, executing this method might force an immediate projectile spawn sequence.
*   **Trigger Event:** When a Sender entity hits its trigger condition (e.g., the Basket's physics handler successfully filtering and destroying an incoming object), it must broadcast a signal to its connected UUIDs.
*   **Decoupled Processing:** *CRITICAL SAFETY REQUIREMENT*. Emitting signals directly inside a Pymunk collision handler (like the Basket's `pre_solve` or `begin` events) risks modifying the simulation state while the engine step is locked, causing hard crashes.
    *   The Sender must instead enqueue the signal (pushing the Receiver UUIDs into a buffer).
    *   The main `update()` loop of the game (or a centralized `LogicManager`) must empty this queue *after* `space.step(dt)` completes, safely invoking `receive_signal()` on the targeted active instances.

### 4. Save/Load System Updates
*   **Serialization:** The `LevelManager` (`utils/level_manager.py`) must be upgraded. The generated YAML (or relevant file structure) must now include a top-level `connections: []` list alongside the existing `entities: []` array.
*   **Data Format:** Each entry in `connections` simply stores the pairs of linked UUIDs (e.g., `{ "sender": "uuid-A", "receiver": "uuid-B" }`).
*   **Deserialization:** Upon loading a level, the connections list is rehydrated into the active game state memory, immediately linking the freshly spawned entities and restoring the visual logic web.

## Acceptance Criteria
- [ ] A dedicated `WIRE` tool exists in the UI and allows drawing sequential links between two entities.
- [ ] Connected entities are visually joined by lines in EDIT mode.
- [ ] In PLAY mode, successfully triggering a Basket causes a connected Cannon to fire, accompanied by an animated visual flash along the connection line.
- [ ] Signal transmission is safely deferred to outside the Pymunk physics step, preventing engine crashes.
- [ ] Logic connections persist through saving and loading the level file.
