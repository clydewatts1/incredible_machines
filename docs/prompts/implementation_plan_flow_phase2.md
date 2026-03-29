# Implementation Plan: DataPipe & Factory Standardization (Phase 2)

This plan upgrades [DataPipePart](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py#18-146) and [FactoryPart](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/agent_engine.py#17-239) to leverage the standardized [FlowEntity](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#544-897) architecture (Phase 1). We will unify backpressure propagation and simplify routing delegation.

## Proposed Changes

### [DataPipe]
#### [MODIFY] [data_pipe.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py)
- Change inheritance from [GamePart](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#11-538) to [FlowEntity](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#544-897).
- Update [update_logic](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py#66-111) to call `super().update_logic(dt, game_state, entities, active_instances)`.
- Set `self.visual_state = "JAMMED"` when `len(self.payload_stack) >= self.get_property("capacity", 5)`.
- Ensure `self.logic_signal` follows the conservative policy.

### [Factory]
#### [MODIFY] [agent_engine.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/agent_engine.py)
- Update [ingest_payload](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/agent_engine.py#109-135) to check `self.downstream_status` and return `False` if `JAMMED`.
- Simplify [poll_results](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/agent_engine.py#162-214) to delegate ejection entirely to `self.resolve_exit_path`.
- Remove legacy "target lookup" logic from the factory engine.

## Verification Plan

### Automated Tests
- Extend [tests/test_flow_standardization.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py) to cover:
    - DataPipe backpressure propagation to upstream Factory.
    - Factory "any" routing to adjacent DataPipe.

### Manual Verification
- Load [saves/defect_data_tube.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/defect_data_tube.yaml).
- Observe factory behavior when the downstream pipe is full.
- Verify "any" routing works without explicit YAML rules.
