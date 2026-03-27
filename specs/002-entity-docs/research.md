# Research: Entity Configuration Targets

## Problem
The `docs/entity/` directory must be fully populated based on existing entities. Which entities are active?

## Decision
We extracted the definitions directly from `config/entities.yaml`. 

The following logical variants must be documented:
- **Payloads**: `bouncy_ball`, `payload_ball`
- **Blocks**: `long_ramp`, `diamond`, `half_circle`, `quarter_circle`, `textured_rectangle`, `box`, `spring`, `bouncy`
- **Active/Visuals**: `cannon`, `basket`, `motor`, `effect_box`, `pressure_plate`
- **Logic**: `guard`, `logic_factory`, `warehouse`, `portal`, `data_pipe`, `smart_splitter`, `ai_brain`
- **Sources**: `data_source`, `data_source_csv`, `data_source_mcp`, `test_source`, `faker_source`
- **Sinks**: `data_sink`, `data_sink_csv`, `data_sink_json`, `data_sink_yaml`, `data_sink_mcp`, `file_sink`
- **Mechanical**: `gear_driver`, `gear_follower`, `axle`, `belt_tool`, `conveyor_belt`
- **Other**: `text_box`, `avatar`

## Execution Strategy (Gemini Flash)
Given the user intends to use Gemini Flash for implementation, the implementer agent should loop through these names and generate the documentation strictly following the schema laid out in `data-model.md`.
