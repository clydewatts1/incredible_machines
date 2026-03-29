# Task Checklist: DataPipe & Factory Standardization (Phase 2)

- [ ] Phase 1: Planning and Research
    - [x] Analyze current DataPipe and Factory implementation
    - [x] Create implementation plan for Phase 2
- [ ] Phase 2: Implementation (DataPipe)
    - [ ] Update [entities/data_pipe.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/data_pipe.py) to inherit from [FlowEntity](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#544-897)
    - [ ] Update [update_logic](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/agent_engine.py#215-239) for backpressure signaling
- [ ] Phase 3: Implementation (Factory)
    - [ ] Update [agent_engine.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/agent_engine.py) to respect `downstream_status`
    - [ ] Delegate ejection to [resolve_exit_path](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#777-861)
- [ ] Phase 4: Verification
    - [ ] Update [tests/test_flow_standardization.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py)
    - [ ] Manual smoke test with [saves/defect_data_tube.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/defect_data_tube.yaml)
