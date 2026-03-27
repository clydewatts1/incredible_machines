# Data Model: Entity Documentation Enhancement

## Entity: Entity Documentation (.md)

- **Description**: The top-level sentence describing the entity.
- **Summary**: A bullet-list summary or brief paragraph detailing the primary use case.
- **Detail**: In-depth explanations of edge cases and internal workings (without exposing code logic).
- **Parameters and Functionality**: Required vs optional properties, default values, states (animations), and connections.

## Relationship

Each `.md` document maps 1:1 to a `single_entity_*.yaml` configuration file representing a minimal test case of that entity.
