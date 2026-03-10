# Milestone 22: Logic Factories & Async Processors - Implementation Plan

This document breaks down Milestone 22 into granular, sequential phases to safely introduce Factory-based asynchronous processing without destabilizing physics or frame timing.

## Phase 1: Engine Architecture & Registry
**Goal:** Establish a plugin-style engine framework and dynamic lookup system.
**Target Files:**
- `utils/engines.py` (create)

**Steps:**
1. Create `utils/engines.py` and define the shared engine contract (`BaseEngine`) with the required lifecycle:
   - constructor accepts configuration/instructions data
   - processing method accepts payload + instructions and returns a discrete state or fatal context
   - configuration validation hook
2. Define `EngineRegistry` as a centralized mapping from `engine_type` strings to engine classes.
3. Add a null/passthrough fallback engine for unknown `engine_type` values to enforce graceful failure.
4. Define startup registration flow (registry initialized once, no gameplay-time hardcoded engine branching).
5. Add minimal logging contract for registry lookup failures.

**Constraints & Notes:**
- Must satisfy Constitution Section 14 (Registry Mandate, no monolithic if/elif engine chains).
- Keep factory logic agnostic to specific engine internals.

**Manual Verification:**
- Verify a known engine key resolves correctly and an unknown key uses fallback behavior without crashing.

## Phase 2: Regex Engine Implementation
**Goal:** Add deterministic, rule-based regex evaluation for payload-driven states.
**Target Files:**
- `utils/engines.py`

**Steps:**
1. Implement `RegexEngine` using Python `re` with strict instruction parsing.
2. Enforce required `instructions` shape:
   - `rules` list with `{target_field, pattern, state}` entries
   - `default_state`
3. Process rules sequentially.
4. If payload is a dictionary, extract `target_field` before regex match.
5. If payload is a string, evaluate the string directly.
6. Return the first matching rule's `state`; otherwise return `default_state`.
7. Handle invalid regex syntax as fatal engine output (for later FATAL UX handling).

**Constraints & Notes:**
- Must support explicit dictionary extraction exactly as specified.
- Must not mutate payload ownership/state from inside engine logic.

**Manual Verification:**
- Verify multiple regex rules resolve in-order.
- Verify dict payload extraction works and string payload direct-match works.
- Verify invalid pattern surfaces fatal error context.

## Phase 3: Random Engine Implementation
**Goal:** Add probabilistic state generation with deterministic threshold mapping.
**Target Files:**
- `utils/engines.py`

**Steps:**
1. Implement `RandomEngine` with instruction parsing for:
   - `distribution`
   - `params`
   - `rules`
2. Support `uniform` and `normal` distributions.
3. For `uniform`, generate value from configured range.
4. For `normal`, generate value using configured `mu` and `sigma`.
5. Evaluate rules sequentially using threshold logic (`x < rule['random']`) to map sampled value to discrete state.
6. Return deterministic fallback state when no threshold rule matches.
7. Emit fatal error context for invalid distribution/params.

**Constraints & Notes:**
- Must use `random.uniform` / `random.gauss` per requirements.
- Mapping must come from rule data, not hardcoded thresholds.

**Manual Verification:**
- Verify both distributions generate expected ranges.
- Verify threshold rules map sampled values to configured states.

## Phase 4: YAML Configuration & Animation Mapping
**Goal:** Introduce Factory entity configuration and visual-state animation mapping.
**Target Files:**
- `config/entities.yaml`

**Steps:**
1. Add one or more Factory variants to `entities.yaml`.
2. Define body shape/type metadata for Factory use case.
3. Add `animations` dictionary mapping all required visual states to sprite base names.
4. Add engine parameters:
   - `engine_type`
   - `instructions`
5. Add lifecycle/process controls:
   - `cost_modifier`
   - `tired_velocity`
   - optional cooldown tuning values
6. Add routing structure as ordered `routing` array with each rule containing:
   - `max_state`
   - ejection trajectory attributes (`angle`, `velocity`)
   - optional `score` modifier
   - optional human-readable descriptor
7. Ensure config remains compatible with current config loader and inheritance model.

**Constraints & Notes:**
- Must satisfy Constitution Section 3 Data-Driven Design and Section 8 YAML standards.
- Animation states and routing data must be explicitly data-driven.

**Manual Verification:**
- Boot game and verify YAML loads without parse errors.
- Confirm Factory variant appears with expected configuration fields.

## Phase 5: Thread-Safe Background Processing
**Goal:** Process engine logic asynchronously while preserving main-thread-only physics mutation.
**Target Files:**
- `entities/active.py` (create or extend)
- `main.py`

**Steps:**
1. Implement Factory runtime class in `entities/active.py`.
2. Add background task execution using `threading.Thread` for engine processing only.
3. Add thread-safe result handoff using `queue.Queue`.
4. Ensure worker thread receives immutable/copy-safe payload data for processing.
5. In main loop (`main.py`), poll Factory queue each frame and apply physical outcomes (ejection, velocity, state updates) on main thread only.
6. Implement Factory `destroy()` or `cleanup()` override that sets `_is_destroyed = True`.
7. In worker completion path, guard queue insertion with destruction check (`if not _is_destroyed`) to prevent ghost-thread callbacks.
8. Ensure teardown path does not block game loop and avoids orphan thread interactions.

**Constraints & Notes:**
- Must satisfy Constitution Section 13: Pymunk is not thread-safe.
- Worker threads must never mutate `space`, entity lists, or instance dictionaries.

**Manual Verification:**
- Start Factory processing and delete the Factory mid-processing.
- Verify no crash, no late invalid queue write, and no physics mutation from worker thread.

## Phase 6: Payload Lifecycle Pre-Processing (Age & Cost)
**Goal:** Enforce lifecycle firewall checks before engine execution.
**Target Files:**
- `entities/active.py`
- `main.py`

**Steps:**
1. On payload ingest, apply Factory `cost_modifier` to payload cost.
2. If resulting cost is `<= 0`, bypass engine and eject through Bottom edge immediately.
3. Evaluate payload expiration using `start_time` and `drop_dead_age`.
4. If expired, bypass engine and eject through Top edge.
5. Mark expired payload as floating.
6. In main update loop, apply continuous upward anti-gravity force to floating payloads.
7. Define cleanup/retirement criteria for floating payloads to avoid endless retention.

**Constraints & Notes:**
- Must satisfy Constitution Section 15.
- Do not use negative mass under any condition.

**Manual Verification:**
- Confirm exhausted-cost payloads always exit Bottom.
- Confirm expired payloads always exit Top and visibly float via anti-gravity behavior.

## Phase 7: Routing Table & Health Modifiers
**Goal:** Route output via ordered state thresholds and apply payload health/score effects.
**Target Files:**
- `entities/active.py`
- `config/entities.yaml`

**Steps:**
1. After processing returns state, evaluate `routing` rules in order using `state <= max_state`.
2. Select first matching route and derive left-edge ejection trajectory from that rule.
3. Read route `score` modifier (default `0` when missing).
4. Initialize payload `score` to `100` if absent.
5. Apply route modifier to payload score and clamp lower bound as needed.
6. Record score change in payload processing history for diagnostics/scoring.
7. Ensure selected route descriptor can be surfaced for debugging output.

**Constraints & Notes:**
- Must satisfy Constitution Section 16 (score/health semantics).
- Route selection order is authoritative and must be deterministic.

**Manual Verification:**
- Verify different returned states pick the expected route by `max_state` order.
- Verify score initialization to `100` when missing and correct modifier application per route.

## Phase 8: UX Polish & Collision Safety
**Goal:** Improve player-facing diagnostics and prevent collision-loop instability.
**Target Files:**
- `entities/active.py`
- `main.py`
- (if needed for existing visualizer integration) `utils/` modules hosting M18 payload label behavior

**Steps:**
1. Add Factory cooldown timer (`0.5s`) on transition to/from `EMITTING`.
2. While cooldown is active, top sensor ignores new ingest collisions (or enforces solid-wall behavior).
3. Add FATAL transition logic when engine throws exception or returns fatal/non-numeric state.
4. On FATAL, spawn temporary red floating text above Factory with specific error reason.
5. Reuse M18 payload label visualizer path/style to ensure visual consistency.
6. Ensure fatal labels auto-expire and do not leak entities/resources.
7. Add small debug hooks/logging for cooldown gate and fatal reason visibility.

**Constraints & Notes:**
- Cooldown is mandatory to prevent double-bounce infinite loops.
- FATAL reason text must be actionable and specific.

**Manual Verification:**
- Trigger rapid re-collision scenario and confirm cooldown suppresses loop behavior.
- Trigger known engine error and confirm Factory enters FATAL with visible red diagnostic label.

## Final Integration Validation
**Goal:** Confirm end-to-end milestone stability and compliance.
**Target Files:**
- `main.py`
- `entities/active.py`
- `utils/engines.py`
- `config/entities.yaml`

**Steps:**
1. Run integrated scenarios for regex-based routing, random-based routing, expired payload, and exhausted-cost payload.
2. Validate queue handoff correctness under repeated processing load.
3. Validate no thread-related crashes during entity deletion and mode transitions.
4. Confirm animation state transitions remain coherent under normal, cooldown, and fatal flows.
5. Confirm score updates track route rules and remain stable under repeated passes.

**Manual Verification:**
- Execute a full play session with multiple Factories and payloads; verify stable FPS, deterministic routing, visible diagnostics, and clean shutdown without orphan processing behavior.
