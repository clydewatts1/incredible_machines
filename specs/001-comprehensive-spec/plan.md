# Implementation Plan: Incredible Machines Baseline

**Branch**: `001-comprehensive-spec` | **Date**: 2026-03-26 | **Spec**: [specs/001-comprehensive-spec/spec.md](spec.md)
**Input**: Feature specification from `specs/001-comprehensive-spec/spec.md`

## Summary

This plan formalizes the verification and documentation of the established Incredible Machines engine. It confirms that the existing implementation of WOLF routing, M40 ETL data pipelines, and M42 gamepad support aligns with the principles defined in the Project Constitution.

## Technical Context

**Language/Version**: Python 3.11+ (Current)
**Primary Dependencies**: Pygame-CE, Pymunk, Pygame-GUI, Faker (All Integrated)
**Storage**: Local YAML configs and JSONL data exports.
**Testing**: Verification via existing test harness in `main.py` and `/tests/`.
**Target Platform**: Desktop (Windows/Linux/macOS)
**Project Type**: Established Physics Sandbox / Visual ETL Engine.
**Performance Goals**: Maintaining 60 FPS baseline.
**Constraints**: Single-threaded main loop (Maintained).

## Constitution Check

*GATE: Verified against existing implementation.*

- [x] **FlowEntity Pattern**: Verified in `entities/flow_entity.py`.
- [x] **Zero Rule / Routing**: Implementation confirmed in `utils/routing.py`.
- [x] **Handshake / Backpressure**: Operational in Source/Sink logic.
- [x] **Data Mutation (M40)**: Faker integration verified in `entities/`.
- [x] **Visual FX (M41)**: Particle logic correctly bypasses Pymunk.
- [x] **Deletion Pipeline/Kill Z**: Flag-based GC verified in `main.py`.
- [x] **Configuration Isolation**: Centralized in `config/*.yaml`.

## Project Structure

### Documentation (Verification Artifacts)

```text
specs/001-comprehensive-spec/
├── plan.md              # This file
├── research.md          # Tech validation of existing systems
├── data-model.md        # Documented object hierarchy
└── quickstart.md        # Usage guidelines
```

### Source Code (Existing Root Structure)

```text
root/
├── main.py              # Main Engine Loop & GC
├── utils/               # Physics, Routing, & Config Utilities
├── entities/            # Part hierarchy (FlowEntity)
├── config/              # YAML Configuration Truths
├── assets/              # Global Sound & Sprite assets
└── tests/               # Headless QA scenarios
```

**Structure Decision**: Validating the current single-project root-based layout to ensure zero-friction integration with existing development tools.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| No direct object deletion | To maintain stable PyMunk Space integration | Direct array removal causes index errors and dangling C-pointers in Pymunk. |
