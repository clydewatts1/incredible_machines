# Incredible Machines 🧩 - Master Technical Manual

This definitive manual covers every aspect of the Incredible Machines engine, including editor controls, automated testing, and an exhaustive 100% coverage YAML schema reference for all entities.

---

## 🕹️ Editor & Interaction

### Core Controls
- **Left Click**: Place part / Select part for inspection.
- **Right Click**: Delete part.
- **Mouse Wheel**: Rotate selected part (Edit Mode).
- **Delete Key**: Remove selected part.
- **WASD / Arrows**: Pan camera.
- **1-7**: Fast-spawn common parts (Bouncy Ball, Ramps, Boxes).

### Top Panel
- **PLAY / EDIT**: Toggle physics states.
- **SAVE / LOAD**: Project persistence.
- **● REC**: Start/Stop test recording.
- **REIMAGE**: Force asset and icon regeneration.

---

## 🏗️ Universal Property Schema
These properties apply to **every** entity in the game.

| Property | Type | Requirement | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `template` | string | **REQUIRED** | - | `Circle`, `Rectangle`, `Square`, `Diamond`, `UShape`, `Half-Circle`, `Quarter-Circle`. |
| `label` | string | Optional | `variant_key` | Name shown in the UI/Inspector. |
| `mass` | float | Optional | 1.0 | Influence on gravity/momentum. |
| `friction` | float | Optional | 0.5 | Sliding resistance (0.0 - 1.0). |
| `elasticity` | float | Optional | 0.5 | Bounciness (0.0 - 1.0+). |
| `is_static` | bool | Optional | False | If True, object is immovable. |
| `color` | [R,G,B] | Optional | varies | RGB list (0-255). |
| `collision_sound` | string | Optional | "default_collision.wav" | Sound file in `assets/sounds/`. |
| `spawn_sound` | string | Optional | "spawn.wav" | Sound played on creation. |
| `texture_path` | string | Optional | (auto) | Path to sprite. Defaults to `assets/sprites/<variant>.png`. |
| `key_bind` | string | Optional | - | Keyboard key to select this part in the palette. |

---

## 📄 Definitive Entity Schema Reference

### 📡 Data Sources (`data_source`, `data_source_csv`, `test_source`)
*Required: `template`*
- **Optional**:
  - `emit_interval` (float): Seconds between emissions (Default: 2.0).
  - `output_variant` (string): Part to spawn (Default: `payload_ball`).
  - `exit_velocity` (float): Ejection speed (Default: 150.0).
  - `exit_angle` (float): Angle offset from face normal (Default: 0.0).
  - `active_side` (string): Face to emit from (`top`, `bottom`, `left`, `right`).
  - `engine_type` (string): `null`, `csv`, `mcp`.
  - `instructions` (dict):
    - `filepath` (string): For `csv` engine.
    - `url` / `tool_name` (string): For `mcp` engine.
    - `loop` (bool): For `csv` engine (Default: True).

### 📥 Data Sinks (`data_sink`, `data_sink_csv`, `data_sink_json`)
*Required: `template`, `exporter_type`*
- **Optional**:
  - `accepts_types` (list): Ball types allowed (Default: `["all"]`).
  - `consumption_time` (float): Delay while "processing" (Default: 1.0).
  - `export` (dict):
    - `exporter_type` (string): `null`, `csv`, `json`, `yaml`, `mcp`.
    - `directory` (string): Export folder.
    - `file_prefix` (string): Output filename start.
    - `max_objects` (int): Items before internal buffer flush.

### 🧠 Logic Nodes (`ai_brain`, `logic_factory`)
*Required: `template`, `routing`*
- **Optional**:
  - `model` (string): LLM to use (Default: `llama3.2`).
  - `system_prompt` (string): AI instructions.
  - `routing` (list of dicts): `max_state`, `output_side`, `velocity`, `angle`, `desc`.
  - `input_side` (string): Face that accepts payloads (Default: `top`).
  - `cost_modifier` (float): Energy consumed per thought (Default: -10.0).
  - `default_state` (int): Fallback state if no rules match.

### ⚙️ Mechanical & Drive (`motor`, `conveyor_belt`, `gear_driver`)
*Required: `template: Circle` (for gears/motors)*
- **Optional**:
  - `motor_speed` (float): Rotation velocity (radians/sec).
  - `speed` (float): Linear conveyor surface velocity (pixels/sec).
  - `direction` (string): `clockwise`, `counter-clockwise` (Motors) or `left`, `right` (Conveyors).
  - `is_driver` (bool): If True, provides torque to connected gears.

### 📦 Logistics & Storage (`warehouse`, `smart_splitter`, `portal`)
- **Required**: `template`
- **Optional**:
  - `capacity` (int): Max items held (Default: 20 for Warehouse, 5 for Portal).
  - `release_interval` (float): Delay between releasing buffered items (Default: 1.0).
  - `left_weight` / `right_weight` (float): Splitter probabilities (Default: 10.0).
  - `learning_rate` (float): Splitter optimization speed (Default: 2.0).
  - `transit_time` (float): Duration in Portal or Pipe (Default: 0.5 - 2.0).
  - `target_uuid` (string): UUID of linked destination.

### 🧪 Automated Testing (M35 Special)
- **`failure_trace.json`**: Captured state of all parts during failure.
- **`inputs.json`**: Scheduled payload timings.
- **`expected_output.csv`**: Target behavior for regression checks.

---

*Manual Version 1.2 - Milestone 35 Revision*
