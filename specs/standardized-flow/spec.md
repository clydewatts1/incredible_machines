Specification: Standardized FlowEntity Signaling & Routing

1. Problem Statement

Currently, signal processing (backpressure) and routing are fragmented across different entity types. Data Pipes fail to reliably propagate JAMMED states back to upstream factories. Factory entities require complex YAML routing tables even when a simple direct pipe connection exists. Furthermore, Guard nodes waste CPU cycles evaluating payloads in upstream Warehouses even when the Warehouse is completely empty or paused.

2. Solution Definition

We must fully commit to the Unified Flow Architecture defined in the Constitution by centralizing signaling and routing logic in the FlowEntity base class.

Specifically, we will:

Standardize Signals: Move receive_signal and broadcast_status into FlowEntity so every machine naturally shares backpressure.

Elevate Data Pipes: Refactor DataPipePart to inherit from FlowEntity so it participates in the universal signal handshake and propagates downstream blockages.

Simplify Factory Routing: Modify resolve_exit_path to support a wildcard route_state: "any". This allows a Factory to seamlessly dump all processed payloads into a connected pipe without requiring explicit YAML routing states.

Aware Guards: Expose a last_state tracking property on WarehousePart. GuardPart will check this state and abort its expensive rules-engine scan if the upstream Warehouse is empty (IDLE).

3. Scope

In Scope

Updating FlowEntity in entities/base.py to handle universal signal handshakes and the "any" route state.

Refactoring DataPipePart in entities/data_pipe.py to inherit from FlowEntity.

Simplifying FactoryPart in agent_engine.py to rely on the base class resolve_exit_path.

Updating WarehousePart in entities/warehouse.py to reliably track and expose last_state.

Updating GuardPart in entities/guard.py to check the upstream last_state.

Out of Scope

Changes to the rule_engine parsing syntax.

Changes to Pymunk rigid-body physics interactions (e.g., collision handlers in physics_events.py do not need modification for this specific routing update).

UI or Palette modifications.

4. Acceptance Criteria

[ ] A DataPipePart properly halts an upstream FactoryPart (sets it to JAMMED) when the pipe's internal transit queue reaches its capacity.

[ ] A FactoryPart connected to a WarehousePart via a DataPipe automatically routes its processed payloads into the pipe without needing a specific route_state integer defined in config/entities.yaml.

[ ] A GuardPart attached to an empty WarehousePart remains in an IDLE visual state and skips payload scanning.

[ ] The project runs without throwing inheritance or method-resolution errors for receive_signal.

5. Technical Constraints

The changes must adhere to the "Zero Rule" as defined in the docs/CONSTITUTION.md (errors resolve to state <= 0).

DataPipePart must remain pymunk.Body.KINEMATIC.