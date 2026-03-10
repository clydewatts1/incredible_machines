# Milestone 22: Logic Factories & Async Processors - Specification

## 1. Overview
Milestone 22 introduces a new `Factory` execution node that ingests payload-carrying balls, evaluates payload content through a configurable engine, produces a normalized state value (`0-100`), and physically ejects the ball through deterministic output paths. This milestone formalizes safe asynchronous processing, extensible engine plugins, payload lifecycle degradation, and score/health-driven routing behavior.

This specification is governed by `docs/CONSTITUTION.md` Sections 13, 14, 15, and 16.

## 2. Goals
- Add a configurable `Factory` entity with clear physical I/O behavior and visible machine states.
- Enable asynchronous engine processing without violating Pymunk thread-safety constraints.
- Implement extensible engine dispatch using a registry pattern.
- Enforce payload lifecycle constraints (cost, age, degradation) before expensive processing.
- Add routing logic that maps engine output state to ejection trajectory using explicit ordered rules.
- Integrate payload score/health modifiers into routing outcomes for gamified feedback.
- Provide clear in-world diagnostics for fatal processing errors.

## 3. Technical Implementation Details

### 3.1 Factory Entity: Physical Form and I/O Contract
- Body type: rectangular `static` or `kinematic` machine body.
- Top edge semantics: input ingestion port for incoming payload balls.
- Top edge semantics: expired payload output path (age-expired payloads eject upward).
- Left edge semantics: standard routed output path for normal processing outcomes.
- Bottom edge semantics: exhausted/tired output path for depleted-cost payloads.

### 3.2 Visual State Machine
The Factory must support the following visual states:
- `OFF`
- `INITIALIZING`
- `IDLE`
- `PROCESSING`
- `EMITTING`
- `FATAL`
- `JAMMED`

State transitions must be deterministic and tied to processing lifecycle events.

### 3.3 Animation Mapping Requirement
`config/entities.yaml` must define an `animations` mapping for Factory states to base sprite names.

Example structure:
```yaml
factory_processor:
  type: kinematic
  width: 96
  height: 96
  animations:
    OFF: "sprite_factory_off"
    INITIALIZING: "sprite_factory_initializing"
    IDLE: "sprite_factory_idle"
    PROCESSING: "sprite_factory_processing"
    EMITTING: "sprite_factory_emitting"
    FATAL: "sprite_factory_fatal"
    JAMMED: "sprite_factory_jammed"
```

### 3.4 Top Sensor Cooldown (Double-Bounce Prevention)
- After `EMITTING`, Factory enters cooldown (`0.5s` nominal).
- During cooldown, top sensor must ignore new ingest collisions or act as a blocking surface.
- Purpose: prevent immediate re-ingestion loops and infinite bounce behavior near the top port.

### 3.5 FATAL Feedback UX
- If processing fails with fatal error context (for example regex syntax failure, missing required target field), Factory enters `FATAL`.
- Factory must spawn temporary red floating text above itself with the exact error reason.
- Label behavior must reuse Milestone 18 payload visualization style conventions.
- FATAL diagnostics must be non-blocking and auto-expire.

### 3.6 Payload Lifecycle Firewall (Cost and Age)
Lifecycle checks must happen before normal engine processing.

Cost rule:
- Apply Factory `cost_modifier` to payload cost.
- If resulting `cost <= 0`, bypass engine and eject via Bottom output.
- Bottom ejection behaves as normal falling/exhaust output.

Age rule:
- Evaluate `start_time` + `drop_dead_age` against current runtime age.
- If expired, bypass engine and eject via Top output.
- Expired payload must be flagged as floating.

Safe floating rule:
- Negative mass is prohibited.
- Floating behavior must be simulated with continuous upward anti-gravity force during physics updates.

### 3.7 Extensible Engine Architecture (Registry Pattern)

#### Base Engine Contract
All engines must conform to:
- `BaseEngine.process(payload, instructions)` input contract.
- Deterministic return of a discrete routing state (`0-100`) or fatal error context.
- Engine-level validation of required instruction fields.

#### Engine Registry Contract
- A central `EngineRegistry` maps `engine_type` identifiers to engine classes.
- Factory must resolve engine dynamically using registry lookup.
- Hardcoded monolithic engine switch chains are prohibited.
- Unknown engine type must fail gracefully through safe fallback behavior.

### 3.8 Engine Parameterization and Payload Extraction
Factory instance overrides must include an `instructions` object that is passed directly to engine processing.

Required override shape:
```json
{
  "engine_type": "regex",
  "instructions": { "...": "..." },
  "routing": [ "...ordered rules..." ]
}
```

### 3.9 RegexEngine Specification
Regex engine instructions must support:
- Multiple rules.
- Explicit `target_field` extraction for dictionary payloads.
- Direct evaluation when payload is a string.
- `default_state` fallback.

Expected instructions schema:
```json
{
  "rules": [
    { "target_field": "status", "pattern": "^SUCCESS$", "state": 100 },
    { "target_field": "user", "pattern": "^ADMIN.*", "state": 50 }
  ],
  "default_state": 0
}
```

Behavior:
- If payload is a dictionary, engine extracts `target_field` value and applies regex pattern.
- If payload is a string, engine applies pattern to the string directly.
- First matched rule determines returned `state`.
- If no rules match, return `default_state`.

### 3.10 RandomEngine Specification
Random engine instructions must support:
- `uniform` and `normal` distributions.
- Distribution `params`.
- Rule-based mapping from sampled random value to discrete state.

Expected instructions schema:
```json
{
  "distribution": "normal",
  "params": { "mu": 50, "sigma": 15 },
  "rules": [
    { "random": 50, "state": 20 },
    { "random": 100, "state": 80 }
  ]
}
```

Behavior:
- Generate float `x` from configured distribution.
- Evaluate rules in order using threshold logic `x < rule.random`.
- First matching threshold returns that rule’s discrete `state`.
- If no threshold matches, engine must use deterministic fallback behavior.

### 3.11 Asynchronous Processing and Thread Safety
- Engine processing must run in background execution context.
- Worker-to-main handoff must use thread-safe `queue.Queue`.
- Background workers must never mutate Pymunk space, entity collections, or shared gameplay state directly.
- Main loop is exclusively responsible for applying physical ejection and state mutation after dequeuing results.

### 3.12 Safe Deletion (Ghost Thread Prevention)
Factory lifecycle must include destruction-safe behavior:
- `destroy()` or `cleanup()` sets `_is_destroyed = True`.
- Worker completion path checks `_is_destroyed` before queue insertion.
- If Factory is destroyed, worker must abort handoff silently.
- Goal: no late-thread callbacks mutating deleted entities.

### 3.13 Routing Table Data Structure and Evaluation
Factory routing must use explicit ordered list of rule objects.

Expected structure:
```json
"routing": [
  { "max_state": 0, "angle": 45, "velocity": 200, "score": -20, "desc": "Error (Heavy Damage)" },
  { "max_state": 50, "angle": 90, "velocity": 100, "score": -5, "desc": "Partial Match (Light Damage)" },
  { "max_state": 100, "angle": 45, "velocity": 100, "score": 10, "desc": "Success (Healing)" }
]
```

Evaluation contract:
- Compare returned engine state against routing entries in list order.
- Select first rule where `state <= max_state`.
- Use selected rule to determine left-edge trajectory (`angle`, `velocity`) and score modification.

### 3.14 Payload Health/Score Modifier Contract
- Payload `score` acts as health.
- On routed output, apply selected route rule `score` modifier.
- If payload has no `score`, initialize to `100` first.
- Then apply route modifier (`payload.score += rule.score`, default rule score is `0` when absent).
- Score updates are part of route resolution and must occur before post-route scoring/victory aggregation.

## 4. Acceptance Criteria
- [ ] Factory entity can be placed and behaves as static/kinematic rectangular execution node.
- [ ] Top, Left, and Bottom edges enforce the exact I/O semantics defined in this specification.
- [ ] Factory supports all required visual states: OFF, INITIALIZING, IDLE, PROCESSING, EMITTING, FATAL, JAMMED.
- [ ] `config/entities.yaml` includes Factory `animations` mapping for every visual state.
- [ ] Cooldown activates for `0.5s` after emission and prevents top-port double-bounce loops.
- [ ] Fatal processing conditions trigger Factory `FATAL` state and temporary red floating error label with specific reason text.
- [ ] Cost lifecycle rule correctly bypasses engine and ejects bottom when cost is depleted.
- [ ] Age lifecycle rule correctly bypasses engine and ejects top with floating behavior.
- [ ] Floating behavior uses anti-gravity force and never uses negative mass.
- [ ] Factory uses asynchronous engine processing and worker-to-main `queue.Queue` handoff.
- [ ] No worker thread directly mutates Pymunk space or shared main-thread game state.
- [ ] Destroying a Factory during active processing does not crash and does not enqueue stale results.
- [ ] Engine selection is registry-based and dynamic; no hardcoded engine selection chain.
- [ ] RegexEngine supports dict `target_field` extraction and direct string evaluation as specified.
- [ ] RandomEngine supports configured distribution sampling and ordered threshold-to-state mapping.
- [ ] Routing uses ordered `<= max_state` selection and applies trajectory from selected rule.
- [ ] Route-level score modifier is applied to payload score, initializing missing score to `100`.
- [ ] End-to-end processing (ingest -> evaluate -> route -> eject) is deterministic and stable under repeated collisions.
