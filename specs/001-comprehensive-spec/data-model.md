# Data Model: Incredible Machines Core Baseline

The Incredible Machines core sandbox utilizes a Pymunk physics world overlaid with a Pygame-GUI event loop. The following established hierarchy defines the engine's primary entities.

## 1. Physical Payload (`PayloadPart`)
- **Existence**: Established.
- **Attributes**:
    - `id`: Unique UUID per instance.
    - `data`: Mutable JSON record for ETL (M40).
    - `trace_history`: Trail behavior metadata.
- **Rules**: Bypasses direct deletion in favor of `to_delete = True` flags handled by the `main.py` garbage collector.

## 2. Machine Nodes (`FlowEntity`)
- **Existence**: Established.
- **Hierarchy**: Base for Sources, Sinks, and Factories.
- **Rules**: All nodes MUST use `ingest_payload()` and `resolve_exit_path()`. Logic updates occur in `update_logic(dt)` while rendering is isolated to `draw()`.

## 3. Pull-Based Components (WOLF)
- **Existence**: Established (`WarehousePart`, `GuardPart`).
- **Rules**: Supports active pull mechanics where Guards evaluate Warehouse payloads against rule engines, independent of the push-based physics stream.

## 4. Visual Payoff Nodes (M41)
- **Existence**: Established (`EffectBoxPart`, `PressurePlatePart`).
- **Rules**: Particles are drawn as 2D primitives within the `draw()` loop. They are kinematic and do not participate in PyMunk collision resolution.

## 5. Input & Avatar (M42)
- **Existence**: Established (`PlayerAvatarPart`, `ControllerManager`).
- **Rules**: `ControllerManager` provides a hardware-agnostic interface in `utils/controller.py`. Right Stick velocity is applied directly to the `PlayerAvatarPart` physics body in PLAY mode.
