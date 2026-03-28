# Data Pipe

Data Pipes are specialized physical conduits that transport **Payloads** (data balls) visually between entities. They differ from Logic Wires in that they carry physical objects rather than signals.

## Configuration

Data Pipes connect a **Source** to a **Target**. They pull payloads from the source and deliver them to the target.

### Standard Properties
- `source_uuid`: The UUID of the upstream entity.
- `target_uuid`: The UUID of the downstream entity.
- `route_state`: (Optional) Numeric state/result that this pipe handles.
- `route_type`: (Optional) Generic string tag (e.g., 'JSON', 'Image') for specialized paths.

## Entity Combinations

### 1. Warehouse -> Data Pipe
When a Warehouse has an attached Data Pipe, it will preferentially release its payloads into the pipe rather than spitting them out the bottom.
- **Route State**: 10.0 (default success state for Warehouse).
- **Route Type**: Matches the `type` property in the payload ball's data.

### 2. Smart Splitter -> Data Pipe
A Smart Splitter can be connected to two different Data Pipes to separate results.
- **Left Path**: Configure the pipe with `route_state: 10.0`.
- **Right Path**: Configure the pipe with `route_state: 20.0`.

### 3. AI Brain (Factory) -> Data Pipe
Configure the AI Brain's `routing` rules to output specific numeric results, then match those results to your Data Pipes.
- **Example**: If an AI Brain system prompt results in `route_state 100` for "High Value" items, create a Data Pipe with `route_state: 100.0` to route them to a specific destination.

### 4. Generic Type Routing
If your payloads have a `type` defined in their payload dictionary (e.g., `{"type": "audit"}`), you can configure a Data Pipe with `route_type: audit`. The engine will find this pipe automatically without needing a specific numeric state!
