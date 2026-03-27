<!--
Sync Impact Report:
- Version change: v1.1.0 → v1.2.0
- List of modified principles: N/A
- Added sections:
  - 10. Entity Documentation Standards
- Removed sections: N/A
- Templates requiring updates:
  - ✅ updated: .specify/memory/constitution.md
  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: README.md
- Follow-up TODOs: Implement missing entity documents in docs/entity/
-->

# Incredible Machines (Fuath an Mhadra) Constitution

## 1. Project Philosophy
This project is a visual programming environment disguised as a physics sandbox game. At its core, it is a workflow engine based loosely on WOLF (Workflow Object Logic Framework) and a visual ETL (Extract, Transform, Load) synthetic data pipeline. It blends strict, deterministic logic (regex, rules engines, faker data) with chaotic, rigid-body physics. Features MUST prioritize visual feedback, emergent gameplay, and modularity over rigid hardcoding.

## 2. Core Architecture
All physical and logical objects in the simulation MUST adhere to the established class hierarchy.

### 2.1 The FlowEntity Pattern
- **Rule**: Any machine that processes, routes, or generates data (Sources, Sinks, Factories, Brains, Guards) MUST inherit from `FlowEntity` (which inherits from `GamePart`).
- **Ingestion**: Do not write custom collision handlers for standard ingestion. Use `FlowEntity.ingest_payload(payload_entity)`.
- **State Management**: Always use `self.visual_state` (e.g., IDLE, INGESTING, WRITING, JAMMED, FATAL). The base class automatically handles animation frame loading and procedural placeholder generation based on this state.

### 2.2 Standardized Routing & The "Zero Rule"
- **Rule**: Custom trigonometry for payload ejection is forbidden in sub-classes.
- **Mechanism**: All outputs MUST be routed using `self.resolve_exit_path(payload_entity, state_result, entities)`.
- **The Zero Rule**: Any processing error, exception, or failure to match a logic rule MUST result in a state of 0 or less. The `FlowEntity` base class will automatically catch this and route it to an Error Pipe or drop it out of the bottom of the machine.

### 2.3 Handshake & Backpressure
- **Rule**: Machines MUST never blindly emit payloads.
- **Mechanism**: Always verify downstream availability. Sources and Sinks MUST use `broadcast_status` and `receive_signal` to communicate FULL or JAMMED states, pausing upstream emission timers to prevent physics flooding.

### 2.4 Active vs. Passive Routing (WOLF)
- **Passive Push**: Standard nodes (Factories, Sources) process and forcefully push payloads downstream via Pipes or Physics.
- **Active Pull (Interactions & Guards)**: The engine supports a pull-based workflow. `WarehousePart` (with `auto_release: false`) acts as a passive "Interaction" storage node. `GuardPart` nodes actively pull payloads out of Interactions by evaluating them against rule-engine queries, holding backpressure if their target is full.

### 2.5 Synthetic Data & ETL (M40)
- **Data Mutation**: Payloads are not just empty physics objects; they are carriers of mutable JSON records. Entities like `FakerSource` and `FakerEngine` use the `faker` library to generate and overwrite data mid-flight. Sinks like `FileSink` act as the load layer, exporting this data to local directories.

### 2.6 Visual FX & Triggers (M41)
- **Separation of Physics and Visuals**: Entities like `EffectBoxPart` and `PressurePlatePart` exist solely for visual payoff. They MUST utilize lightweight, 2D kinematic particle lists (internal drawing routines) rather than bogging down the main Pymunk physics engine with hundreds of tiny rigid bodies.

## 3. Physics & Memory Standards (Pymunk)
- **Separation of Concerns**: Physics and logic state mutations MUST happen ONLY in `update_logic(dt)`. Rendering MUST happen ONLY in `draw(surface, camera)`.
- **Framerate Independence**: Every movement, timer, and lerp MUST be multiplied by `dt` (Delta Time) and scaled by `game_state["speed_multiplier"]`.
- **Memory Management & The Deletion Pipeline**: NEVER delete objects directly using Python's `del` or by modifying arrays mid-loop. Always flag objects with `entity.to_delete = True`. The central garbage collection pipeline in `main.py` is responsible for safely removing Pymunk constraints and shapes after the physics step.
- **The "Kill Z" Volume**: To prevent infinite falls, any dynamic payload falling below the Kill Z threshold (e.g., y > 3000) MUST be flagged for the deletion pipeline.
- **Trace Cleanup**: Payloads accumulate glowing stigmergic `trace_history`. When Sinks consume payloads, they MUST explicitly clear these lists and dictionaries to free Python RAM immediately.

## 4. UI & Input Standards
- **Framework**: All new UI overlays, buttons, dropdowns, and text entries MUST be built using `pygame-gui`. Legacy custom UI rendering is deprecated.
- **Event Blocking**: Before triggering any physical world interactions (like spawning or deleting machines), input handlers MUST verify that `ui_manager.get_focus_set()` is None to prevent clicks from bleeding through the interface.
- **Controller & Avatar Support (M42)**: The engine supports gamepads via `pygame.joystick` routed through `utils.controller`. Controllers function as a Virtual Mouse in UI/Edit modes, and control a physical, high-friction `PlayerAvatarPart` in Play mode. Do not hardcode raw keyboard logic without considering the controller mapping in `config/environment.yaml`.

## 5. Data-Driven Configuration (YAML)
- **Rule**: Hardcoding object dimensions, speeds, logic patterns, colors, or hardware input mappings in Python files is strictly forbidden.
- **Entity Configuration**: All machine parameters and default states MUST be defined in `config/entities.yaml`. Entities are spawned dynamically using the `create_part` factory function based on their `variant_key`.
- **Environment Configuration**: Global engine settings, UI fallback colors, directory paths (`icon_dir`, `sprite_dir`), and hardware controls (e.g., gamepad mapping, cursor speeds, stick deadzones) MUST be defined in `config/environment.yaml` and accessed via `utils.environment_manager`.
- **Project Directory Structure**: Saves are not single YAML files. A flow is an isolated project residing at `saves/[flow_name]/`. This folder contains the root `[flow_name].yaml`, plus local overrides in `icons/` and `sprites/`.

## 6. Asset Generation & Fallbacks
- **Graceful Degradation**: If an asset (`.png`, `.wav`) is missing, the game MUST NOT crash.
- **Asset Cascading**: When loading images, the `AssetManager` MUST search the local project directory first (`saves/[flow_name]/sprites/`), fall back to global `assets/`, and finally trigger procedural/AI generation if missing.
- **Procedural Fallback**: Use `AssetManager` to dynamically generate textured placeholders or missing icons using standard Pygame drawing primitives.
- **AI Generation**: For missing assets, attempt to ping the local Ollama instance (`x/flux2-klein`) using the project's metadata (`flow_name`, `flow_description`) to generate a thematic asset dynamically, caching it in the local project directory.

## 7. Testing & Quality Assurance
- **Test Mode**: The engine supports headless execution via `python main.py --test <pattern>`.
- **Determinism**: Tests run at a forced fixed timestep (`space.step(1/60.0)`).
- **State Isolation**: AI Agents writing tests MUST ensure that `entities`, `active_instances`, and `pymunk.Space` are completely purged and re-initialized between wildcard test batches to prevent cross-contamination.
- **Test Architecture**: Tests reside in `tests/<testname>/`. They MUST contain an `inputs.json` (defining metadata, evaluators, and payload events) and an `expected_output.csv` baseline.
- **Redirection**: When test_mode is active, Sinks automatically redirect their output to `tests/<testname>/output/` for automated assertion (either strict CSV matching or LLM semantic evaluation).

## 8. External Agent Control (MCP)
- **Thread Safety**: The Pygame rendering and Pymunk physics step MUST run on the main thread. The MCP Server runs in a background daemon thread (uvicorn/starlette).
- **The Bridge**: External API/MCP endpoints MUST NEVER modify entities, `active_instances`, or space directly. All commands MUST be pushed to `mcp_command_queue`, which the main Pygame loop safely pops and executes synchronously once per frame.

## 9. AI Agent Coding Directives (For Claude/Cursor/Antigravity)
- **Spec-Driven Development**: Prior to executing any large feature or milestone, rely on spec-kit to generate formal specifications (`spec.md`, `plan.md`, `tasks.md`). Agents SHOULD follow the exact architecture defined in the plans.
- **Review the Rules**: Always refer to this constitution before modifying routing or physics logic. Ensure you do not violate the "Zero Rule" or introduce memory leaks by failing to use `entity.to_delete`.
- **Configuration Truth**: Check `config/entities.yaml` and `config/environment.yaml` to verify properties and variables before hardcoding assumptions in Python.
- **Utility Reusability**: Prioritize utilizing existing utility modules (`utils/routing.py`, `utils/physics_events.py`) before writing new helper functions.

## 10. Entity Documentation Standards
- **Requirement**: All entities MUST be documented in the `docs/entity/` directory with a dedicated Markdown document for each entity.
- **Content**: Each entity document MUST explain all of the entity's properties, explicitly distinguishing between required and optional properties.
- **Indexing**: There MUST be a `README.md` in the `docs/entity/` directory referencing each of the individual entity documents.
- **Global Reference**: The main project `README.md` MUST reference the `docs/entity/README.md`.

**Version**: 1.2.0 | **Ratified**: 2026-03-26 | **Last Amended**: 2026-03-26
