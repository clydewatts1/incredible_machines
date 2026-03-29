# Walkthrough: FlowEntity Standardization (Phase 1)

This walkthrough documents the standardization of the [FlowEntity](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#544-897) base class, unifying signaling and routing logic across all machine entities.

## 1. Key Accomplishments
*   **Centralized Signaling**: Implemented [receive_signal](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/guard.py#71-79) and [broadcast_status](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#733-744) in the base class with a **Conservative Signal Policy** (JAMMED status takes priority).
*   **Routing Precedence**: Refactored [resolve_exit_path](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py#777-861) to enforce a strict order of operations:
    1.  **Data Pipes**: Direct connection check.
    2.  **YAML Rules**: Explicit routing table search.
    3.  **Physics**: Physical ejection fallback.
*   **The Zero Rule**: Standardized handling of logic factory results `<= 0`, automatically triggering FATAL states and zeroing out search parameters.
*   **Stability Restoration**: Cleared corrupted code blocks and `IndentationError` in [entities/base.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/entities/base.py) caused by previous merge conflicts.

## 2. Verification Results

### Automated Tests
Ran the targeted test suite [tests/test_flow_standardization.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py):
*   [test_fr001_conservative_signaling](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py#17-27): **PASS** (JAMMED precedence verified)
*   [test_fr002_wildcard_routing](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py#28-45): **PASS** (Direct pipe vs physical fallback verified)
*   [test_fr003_datapipe_inheritance](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py#46-60): **PASS** (Inheritance structure verified)
*   [test_fr004_warehouse_state](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py#61-69): **PASS** (IDLE/ACTIVE logic verified)
*   [test_fr005_guard_hibernation](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py#70-92): **PASS** (Upstream-driven scanning verified)

### Runtime Smoke Test
Verified that [main.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/main.py) loads and runs [saves/defect_data_tube.yaml](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/saves/defect_data_tube.yaml) without crashing, confirming that the standardized routing logic handles complex flow definitions correctly.

## 3. Files Modified
*   [base.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/entities/base.py) - Central routing and signaling logic.
*   [test_flow_standardization.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/tests/test_flow_standardization.py) - Functional verification suite.
