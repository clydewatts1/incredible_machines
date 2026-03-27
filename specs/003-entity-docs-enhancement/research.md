# Research: Entity Docs Enhancement

## Investigation Areas

There are no major architectural unknowns for this documentation task. The main strategy is defined:
- Compare `tests/single_entity_<entity_name>/single_entity_<entity_name>.yaml` against `docs/entity/<entity_name>.md`.

### Missing YAML Files

**Decision**: If an entity is documented but lacks a `single_entity_*.yaml` test file, the test file must be generated (either manually via the UI test recorder or dynamically). The priority is ensuring that the documentation matches what the system currently emits, so missing files might necessitate a small detour to generate the missing state.

**Rationale**: The specification explicitly states the attributes can be found in `single_entity_<entity_name>.yaml`. It serves as the absolute ground truth.

### Dynamic or Optional Parameters

**Decision**: Group non-required properties under an "Optional Properties & Defaults" or "Parameters" section. Clearly state conditions under which they appear (e.g., animation strings, specific physics overrides).

**Rationale**: Since some YAML overrides will only appear if users modify them from defaults, it is best to provide the user with the exhaustive list of possible settings alongside standard baseline values if they don't explicitly set them.
