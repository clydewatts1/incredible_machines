# IMPLEMENTATION PLAN: Milestone 23 – Data Generators & External Ingestion

**Document Version:** 1.0  
**Status:** Active  
**Date:** March 9, 2026  
**Related Specification:** [docs/SPECIFICATION_M23_DataGenerators.md](SPECIFICATION_M23_DataGenerators.md)  
**Constitution Sections:** §13–16 (Thread Safety, Plugins, Async Handoff, Degradation)

---

## Overview

This implementation plan breaks down M23 into five sequential phases, each protecting the Pygame 60 FPS render loop while building a data-driven ingestion system. The design mirrors M22's factory pattern (background worker threads, queue handoff, main-thread-only state mutations) extended to support external data sources.

**Key Principle:** No I/O (file reads, network requests) shall block the main loop. All fetch operations occur in background threads with results passed via `queue.Queue()`.

---

## Phase 1: Generator Architecture & Engines

### Objective
Establish the extensible engine registry for data generators (CSVEngine, MCPEngine) and create the base interface that all generators inherit.

### Files to Create
1. **`utils/generators.py`** (new file)
   - Contains the base `BaseGenerator` interface.
   - Implements `CSVEngine` and `MCPEngine` as concrete subclasses.
   - Implements `NullGenerator` (no-op fallback).
   - Defines a `GeneratorRegistry` dict mapping engine type → engine class.
   - Provides a factory function `get_generator(engine_type, instructions)` to instantiate engines.

### Files to Modify
1. **`utils/engines.py`** (if expanding existing registry)
   - Option A: Keep generators separate; import both registries in `main.py`.
   - Option B: Merge `GeneratorRegistry` into the existing `EngineRegistry` under a `generators` sub-key.
   - **Recommendation:** Keep separate for clarity (engines process payloads, generators create them).

### Detailed Tasks

#### Task 1.1: Define BaseGenerator Interface
- **File:** `utils/generators.py`
- **Scope:**
  ```
  class BaseGenerator:
    """Base interface for all data generators."""
    
    def fetch_next(self, instructions: dict) -> dict | None:
      """
      Fetch one item from the source.
      
      Returns:
        dict: Raw data dict (e.g., CSV row as {"name": ..., "age": ...}).
        None: Source is empty or in "empty" state (not an error).
      
      Raises:
        Exception: On unrecoverable error (file not found, connection drop, timeout, JSON parse).
      """
      raise NotImplementedError()
    
    def cleanup(self):
      """Gracefully release resources (close file handles, MCP sessions, etc.)."""
      pass
  ```
- **Implementation Notes:**
  - No arguments passed to `fetch_next()` except instructions (which may contain metadata like file pointer state).
  - If source is truly exhausted (vs. temporarily empty), implementer returns None.
  - Errors are raised as exceptions; DataSource decides whether to escalate to FATAL.

---

#### Task 1.2: Implement NullGenerator
- **File:** `utils/generators.py`
- **Scope:**
  ```
  class NullGenerator(BaseGenerator):
    """No-op generator; used as fallback for unknown engine types."""
    
    def fetch_next(self, instructions: dict) -> dict | None:
      return None  # Always empty
    
    def cleanup(self):
      pass  # Nothing to clean up
  ```

---

#### Task 1.3: Implement CSVEngine
- **File:** `utils/generators.py`
- **Scope:**
  - Read CSV file line-by-line into memory (small files) or via streaming.
  - Parse each line into a dictionary using Python's `csv.DictReader`.
  - Maintain internal file handle and reader state.
  - **Instructions Schema:**
    ```
    {
      "filepath": "data/users.csv",
      "loop": false,
      "delimiter": ",",           # optional, default ","
      "skip_header": true         # optional, default true
    }
    ```
  - **Behavior:**
    - On first call to `fetch_next()`, open file and initialize `csv.DictReader`.
    - Each call yields one row as a dict.
    - On EOF:
      - If `loop=true`, close and reopen to restart; continue.
      - If `loop=false`, return None (signals exhaustion).
    - On errors (file not found, malformed CSV, IO exception), raise IOError or ValueError with descriptive message.
  - **Thread Safety:** Each CSVEngine instance has its own file handle (no shared state across instances).
  - **Cleanup:** Close file handle in `cleanup()`.

**Key Implementation Details:**
  - Use Python's built-in `csv` module (no extra dependencies).
  - Store file pointer and reader state as instance variables.
  - Return rows as dictionaries (keys from header row or auto-generated if `skip_header=false`).
  - Error handling: file not found → IOError; parse error → ValueError.

---

#### Task 1.4: Implement MCPEngine
- **File:** `utils/generators.py`
- **Scope:**
  - Establish MCP client session (via official `mcp` library: `pip install mcp`).
  - Invoke the `get_incredible_machine_data` tool on each `fetch_next()` call.
  - Parse JSON response and check `status` field.
  - **Instructions Schema:**
    ```
    {
      "transport": "sse" | "stdio",      # Connection type
      "url": "http://localhost:8000/sse",  # For SSE
      "command": "mcp-server-binary",     # For stdio
      "args": ["--config", "..."],        # For stdio
      "tool_name": "get_incredible_machine_data",
      "timeout": 5                        # seconds
    }
    ```
  - **Response Schema (from MCP tool):**
    ```json
    {
      "status": "success" | "empty" | "error",
      "data": { ... },
      "message": "..."  # optional, for error context
    }
    ```
  - **Behavior:**
    - On first call to `fetch_next()`, create `mcp.client.session.ClientSession` with appropriate transport.
    - Each call invokes the tool (no arguments) and parses the JSON response.
    - If `status="success"`, extract and return `data` dict.
    - If `status="empty"`, return None (not an error; AI has no data right now).
    - If `status="error"` or any other status, raise Exception with message.
    - On connection errors, timeouts (exceeds `timeout` seconds), malformed JSON, or McpError, raise Exception.
  - **Thread Safety:** Each MCPEngine instance has its own session; no shared connections.
  - **Cleanup:** Close MCP session gracefully (cancel in-flight requests, close transport) in `cleanup()`.

**Key Implementation Details:**
  - Import `mcp.client.session.ClientSession` and relevant transport classes.
  - For SSE: `from mcp.client.sse import SSEClientTransport`.
  - For stdio: `from mcp.client.stdio import StdioClientTransport`.
  - Use `asyncio.run()` or run the async session in a background thread (strategy to be decided in Phase 3).
  - Wrap JSON parsing in try/except; raise on malformed JSON.
  - Timeout enforcement: use Python's `timeout` parameter (socket-level or request-level).
  - Error messages must include context (e.g., "MCP timeout after 5s" or "Tool not found: get_incredible_machine_data").

---

#### Task 1.5: Create GeneratorRegistry
- **File:** `utils/generators.py`
- **Scope:**
  ```
  GENERATOR_REGISTRY = {
    "csv": CSVEngine,
    "mcp": MCPEngine,
    "null": NullGenerator,
  }
  
  def get_generator(engine_type: str, instructions: dict) -> BaseGenerator:
    """
    Factory function to instantiate a generator.
    
    Args:
      engine_type (str): "csv", "mcp", or custom type.
      instructions (dict): Engine-specific configuration.
    
    Returns:
      BaseGenerator: Instantiated generator; NullGenerator if type unknown.
    """
    engine_class = GENERATOR_REGISTRY.get(engine_type, NullGenerator)
    return engine_class()
  ```
- **Notes:**
  - Registry can be extended at runtime by adding new classes: `GENERATOR_REGISTRY["custom"] = CustomEngine`.
  - Unknown types silently fall back to NullGenerator (no exception).

---

#### Task 1.6: Update `requirements.txt`
- **File:** `requirements.txt`
- **Addition:**
  ```
  mcp>=0.1.0  # Model Context Protocol client library
  ```
- **Notes:**
  - Pin version to stable release.
  - Document in setup instructions that MCP is only needed if using MCPEngine.

---

### Manual Verification (Phase 1)
- [ ] Import `utils.generators` in a test script without errors.
- [ ] Instantiate `CSVEngine` with a test CSV file (e.g., `data/test.csv`); verify `fetch_next()` returns dicts.
- [ ] Verify CSV engine respects `loop=true` and `loop=false` (EOF behavior).
- [ ] Verify CSV engine raises IOError on file not found.
- [ ] Instantiate `MCPEngine` (without connecting to real server) and verify initialization.
- [ ] Verify `get_generator("unknown_type")` returns a `NullGenerator` (not an error).
- [ ] Compile check: `python -m py_compile utils/generators.py` should pass.

---

## Phase 2: YAML Configuration & Audio Mapping

### Objective
Define the DataSource entity in YAML with all visual states, animations, sounds, and directional emission parameters. Ensure the entity can be spawned and loaded from level files.

### Files to Modify
1. **`config/entities.yaml`**
   - Add `data_source` base variant.
   - Add `data_source_csv` and `data_source_mcp` specific variants.
   - Define animations (INITIALIZING, IDLE, POLLING, EMITTING, EXHAUSTED, FATAL).
   - Define sounds (optional per state).
   - Define emission parameters (active_side, exit_velocity, exit_angle).

### Files to Create
None (YAML only).

### Detailed Tasks

#### Task 2.1: Define DataSource Base Variant
- **File:** `config/entities.yaml`
- **Scope:**
  ```yaml
  data_source:
    type: "data_source"
    width: 96
    height: 96
    floating: false
    physics: "kinematic"        # No gravity response
    sensor: true                # Collision sensor, no bounces
    
    # Default emission parameters
    active_side: "Bottom"       # Top, Bottom, Left, Right
    exit_velocity: 150.0        # pixels/sec
    exit_angle: 0.0             # degrees relative to active_side
    emit_interval: 2.0          # seconds between emissions
    
    # Engine configuration (inherited by variants)
    engine_type: "null"         # Overridden by variants
    instructions: {}            # Overridden by variants
    
    # State-to-texture mapping
    animations:
      INITIALIZING: "data_source_init"
      IDLE: "data_source_idle"
      POLLING: "data_source_polling"
      EMITTING: "data_source_emit"
      EXHAUSTED: "data_source_empty"
      FATAL: "data_source_error"
    
    # State-to-sound mapping (optional)
    sounds:
      INITIALIZING: null        # No sound
      IDLE: null
      POLLING: null
      EMITTING: null
      EXHAUSTED: null
      FATAL: null
  ```

---

#### Task 2.2: Define DataSource CSV Variant
- **File:** `config/entities.yaml`
- **Scope:**
  ```yaml
  data_source_csv:
    <<: *data_source           # Inherit base variant
    engine_type: "csv"
    active_side: "Bottom"
    exit_velocity: 150.0
    exit_angle: 0.0
    emit_interval: 2.0
    instructions:
      filepath: "data/sample.csv"
      loop: false
      skip_header: true
      delimiter: ","
    # animations & sounds inherited from base
  ```
- **Notes:**
  - Use YAML anchor (`&data_source`) to allow inheritance.
  - Variants can override any base parameter.

---

#### Task 2.3: Define DataSource MCP Variant
- **File:** `config/entities.yaml`
- **Scope:**
  ```yaml
  data_source_mcp:
    <<: *data_source
    engine_type: "mcp"
    active_side: "Top"
    exit_velocity: 120.0
    exit_angle: 45.0
    emit_interval: 3.0
    instructions:
      transport: "sse"
      url: "http://localhost:8000/sse"
      tool_name: "get_incredible_machine_data"
      timeout: 5
    # For stdio variant:
    # transport: "stdio"
    # command: "mcp-server"
    # args: ["--config", "config.json"]
  ```

---

#### Task 2.4: Validate YAML Configuration
- **File:** (existing validation in `main.py`)
- **Scope:**
  - Existing YAML loader must validate that all required fields are present.
  - Add error messages for missing `active_side`, `exit_velocity`, `exit_angle`, `emit_interval`, `engine_type`.
  - No code changes needed if YAML loader is flexible; just document required fields.

---

### Manual Verification (Phase 2)
- [ ] Load `config/entities.yaml` and verify `data_source_csv` variant is parseable.
- [ ] Log the loaded variant dict to confirm all fields are present (active_side, exit_velocity, exit_angle, emit_interval, engine_type, instructions).
- [ ] Verify `animations` dict maps all six states to sprite names.
- [ ] Verify `sounds` dict is present (even if all values are null).
- [ ] Spawn a DataSource entity in game world from YAML; verify it appears with correct sprite orientation.

---

## Phase 3: Thread-Safe Polling & Safe Cleanup

### Objective
Implement the background threading logic (or asyncio in background thread) for fetch operations. Use `queue.Queue()` for thread-safe result handoff. Crucially, implement `_is_destroyed` guards to ensure MCP sessions are cleanly closed and ghost threads are prevented.

### Files to Create
1. **`entities/source.py`** (new file)
   - Contains the `DataSource` class with full lifecycle, state machine, and threading semantics.

### Files to Modify
1. **`main.py`**
   - Import `DataSource` from `entities.source`.
   - Add DataSource creation path in entity spawning (similar to M22's FactoryPart).
   - Add queue polling in main loop (after physics update, before draw).
   - Add cleanup hook in entity deletion and level clear.

2. **`constants.py`**
   - Add M23 constants:
     ```
     DATASOURCE_STATE_TIMEOUT = 10.0  # seconds before transitioning out of INITIALIZING/POLLING
     MAX_BATCH_QUEUE_POLLS = 10       # max results to process per frame
     ```

### Files to Reference
- `utils/generators.py` (import GeneratorRegistry, get_generator)
- `entities/active.py` (M22 reference for threading pattern)
- `entities/base.py` (GamePart base class)

### Detailed Tasks

#### Task 3.1: Create DataSource Class Scaffold
- **File:** `entities/source.py`
- **Scope:**
  ```
  from entities.base import GamePart
  from utils.generators import get_generator
  import threading
  import queue
  import time
  
  class DataSource(GamePart):
    """
    Ingestion node that pulls data from external sources and spawns payloads.
    """
    
    def __init__(self, space, x, y, variant_name="data_source"):
      super().__init__(space, x, y, variant_name)
      
      # Thread-safe queue for generator results
      self.queue = queue.Queue()
      
      # Lifecycle state
      self.visual_state = "OFF"
      self._is_destroyed = False
      
      # Timing
      self.next_emit_time = time.time()
      self.emit_interval = float(self.get_property("emit_interval", 2.0))
      
      # Generator engine
      self.engine = None
      self.engine_type = self.get_property("engine_type", "null")
      self.instructions = self.get_property("instructions", {})
      
      # Current data being fetched
      self.current_fetch_uuid = None
      
      # Animation & sound
      self._animation_textures = {}
      self._load_animation_textures()
  ```
- **Key Structure:**
  - Inherits from `GamePart` (physics body, YAML config, asset loading).
  - Maintains a `queue.Queue()` for background results.
  - Stores engine instance and instructions.
  - Uses `_is_destroyed` flag for safe cleanup.

---

#### Task 3.2: Implement State Machine (`_set_state`)
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _set_state(self, new_state: str):
    """
    Transition to a new state and trigger audio/animation updates.
    
    Args:
      new_state: "OFF", "INITIALIZING", "IDLE", "POLLING", "EMITTING", "EXHAUSTED", "FATAL"
    """
    old_state = self.visual_state
    self.visual_state = new_state
    
    # Play state transition sound (if configured)
    sounds = self.get_property("sounds", {})
    if new_state in sounds and sounds[new_state]:
      # Play sound file (via asset manager or audio system)
      pass  # Implementation in Phase 5
    
    # Log state transitions for debugging
    # e.g., print(f"DataSource: {old_state} -> {new_state}")
  ```

---

#### Task 3.3: Implement Animation Texture Loading
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _load_animation_textures(self):
    """
    Load state-specific texture images from assets/sprites.
    """
    animations = self.get_property("animations", {})
    if not isinstance(animations, dict):
      return
    
    width = int(float(self.get_property("width", 96)))
    height = int(float(self.get_property("height", 96)))
    
    for state_name, sprite_name in animations.items():
      sprite_rel = f"assets/sprites/{sprite_name}.png"
      # Load image; use asset manager (from previous milestones)
      self._animation_textures[state_name] = asset_manager.get_image(
        sprite_rel,
        fallback_size=(width, height),
        text_label=f"DataSource:{state_name}",
      )
  ```
- **Notes:**
  - Mirrors M22 FactoryPart's texture loading.
  - Fallback to default sprite if image not found.

---

#### Task 3.4: Implement Generator Initialization & Worker Thread
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _initialize_engine(self):
    """
    Create the generator engine instance and optionally start a background thread.
    """
    self._set_state("INITIALIZING")
    self.engine = get_generator(self.engine_type, self.instructions)
  
  def _start_worker(self):
    """
    Start a background thread to fetch the next data item.
    """
    def _worker():
      try:
        data = self.engine.fetch_next(self.instructions)
      except Exception as exc:
        data = {"error": str(exc)}  # Wrapped error
      
      # Guard: if destroyed, discard result
      if not self._is_destroyed:
        self.queue.put({"data": data, "error": None if "error" not in data else data["error"]})
    
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
  ```
- **Key Details:**
  - Generator creation is synchronous (Phase 3); async logic deferred to Phase 4-5 if needed.
  - Background thread checks `_is_destroyed` before queuing (prevents ghost queues).
  - Errors are wrapped and queued, not re-raised (main thread decides how to handle).

---

#### Task 3.5: Implement Safe Cleanup
- **File:** `entities/source.py`
- **Scope:**
  ```
  def cleanup(self):
    """
    Gracefully shutdown the DataSource and clean up generator resources.
    Called when user deletes the entity or game unloads.
    """
    self._is_destroyed = True
    
    # Stop accepting new queue results
    # Drain any pending results to prevent dangling references
    while not self.queue.empty():
      try:
        self.queue.get_nowait()
      except queue.Empty:
        break
    
    # Shutdown generator (close files, MCP sessions, etc.)
    if self.engine:
      self.engine.cleanup()
  
  def destroy(self):
    """Alias for cleanup; called by physics deletion."""
    self.cleanup()
  ```
- **Key Details:**
  - Set `_is_destroyed` immediately to prevent late queue operations.
  - Drain queue to avoid stale data loops.
  - Call engine's `cleanup()` to release resources (file handles, network sessions).

---

#### Task 3.6: Implement Main-Loop Polling
- **File:** `entities/source.py`
- **Scope:**
  ```
  def poll_results(self, entities: list, active_instances: dict):
    """
    Poll the background fetch queue and handle results.
    Called once per frame from main loop.
    
    Args:
      entities (list): World entity list (may append spawned balls or labels).
      active_instances (dict): UUID -> entity map for lookups.
    """
    if self._is_destroyed:
      # Drain queue to prevent stale data
      while not self.queue.empty():
        try:
          self.queue.get_nowait()
        except queue.Empty:
          break
      return
    
    # Poll up to MAX_BATCH_QUEUE_POLLS results per frame
    polls = 0
    while not self.queue.empty() and polls < constants.MAX_BATCH_QUEUE_POLLS:
      result_data = self.queue.get()
      polls += 1
      
      error = result_data.get("error")
      data = result_data.get("data")
      
      self.current_fetch_uuid = None
      
      if error:
        # Error path: transition to FATAL (Phase 5)
        pass
      elif data is None:
        # Empty signal: return to IDLE
        self._set_state("IDLE")
      else:
        # Success: spawn ball with payload (Phase 4)
        pass
  ```

---

### Manual Verification (Phase 3)
- [ ] Instantiate DataSource with `engine_type="csv"` and test CSV file in a harness.
- [ ] Verify `_initialize_engine()` creates the engine without errors.
- [ ] Verify `_start_worker()` successfully starts a background thread.
- [ ] Verify queue receives results without blocking the main thread.
- [ ] Call `cleanup()` while a worker thread is pending; verify thread discards result (check `_is_destroyed`).
- [ ] Verify MCP engine's `cleanup()` closes session gracefully (no hung connections).
- [ ] Compile check: `python -m py_compile entities/source.py` should pass.

---

## Phase 4: Payload Initialization & Physical Emission

### Objective
Implement the payload construction and ball spawning logic. When data arrives from the queue, build the exact payload dictionary (data, score: 100, cost: 100, start_time, routing_depth: 0, ttl: 50, drop_dead_age: 10.0, processing_history: []) and spawn a physics projectile with calculated velocity.

### Files to Modify
1. **`entities/source.py`**
   - Implement `_construct_payload()` method.
   - Implement `_emit_ball()` method with angle/velocity calculations.
   - Extend `poll_results()` to spawn balls on success.
   - Extend `update_logic()` to drive the IDLE → POLLING transition.

2. **`main.py`**
   - Add DataSource spawning path (similar to FactoryPart).
   - Add DataSource update/poll hooks in main loop.

3. **`constants.py`**
   - Add payload defaults:
     ```
     DEFAULT_PAYLOAD_SCORE = 100
     DEFAULT_PAYLOAD_COST = 100
     DEFAULT_PAYLOAD_TTL = 50
     DEFAULT_PAYLOAD_DROP_DEAD_AGE = 10.0
     ```

### Detailed Tasks

#### Task 4.1: Implement Payload Construction
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _construct_payload(self, raw_data: dict) -> dict:
    """
    Build the full payload dict from raw generator data.
    
    Args:
      raw_data (dict): Data from the generator (CSV row, MCP response, etc.)
    
    Returns:
      dict: Complete payload with all required fields.
    """
    now_secs = time.time()
    
    payload = {
      "data": raw_data,
      "score": constants.DEFAULT_PAYLOAD_SCORE,      # 100
      "cost": constants.DEFAULT_PAYLOAD_COST,        # 100
      "start_time": now_secs,
      "routing_depth": 0,
      "ttl": constants.DEFAULT_PAYLOAD_TTL,          # 50
      "drop_dead_age": constants.DEFAULT_PAYLOAD_DROP_DEAD_AGE,  # 10.0
      "processing_history": [],
    }
    
    return payload
  ```

---

#### Task 4.2: Implement Velocity & Angle Calculation
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _compute_emission_velocity(self) -> tuple[float, float]:
    """
    Compute world-space velocity (vx, vy) from exit_velocity, exit_angle, and active_side.
    
    Returns:
      (vx, vy): Velocity vector in pixels/sec.
    """
    exit_velocity = float(self.get_property("exit_velocity", 150.0))
    exit_angle_deg = float(self.get_property("exit_angle", 0.0))
    active_side = self.get_property("active_side", "Bottom")
    
    # Global angle reference: 0° = East, 90° = North, 180° = West, 270° = South
    # Adjust per side:
    if active_side == "Top":
      angle_offset = 90.0
    elif active_side == "Bottom":
      angle_offset = 270.0
    elif active_side == "Left":
      angle_offset = 180.0
    else:  # Right
      angle_offset = 0.0
    
    final_angle_deg = exit_angle_deg + angle_offset
    final_angle_rad = math.radians(final_angle_deg)
    
    vx = exit_velocity * math.cos(final_angle_rad)
    vy = -exit_velocity * math.sin(final_angle_rad)  # Negate Y because Pygame Y increases downward
    
    return (vx, vy)
  ```
- **Notes:**
  - Angle reference frame: 0° points right (east), 90° points up (north).
  - Negate Y for Pymunk coordinate system (Y increases upward in physics, downward in screen).

---

#### Task 4.3: Implement Ball Emission
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _emit_ball(self, payload: dict, entities: list, active_instances: dict):
    """
    Spawn a new ball with the given payload at the output port position.
    
    Args:
      payload (dict): Initialized payload dict.
      entities (list): World entity list (append new ball).
      active_instances (dict): UUID -> entity map (add new ball).
    """
    # 1. Compute port position (center of active edge)
    width = float(self.get_property("width", 96))
    height = float(self.get_property("height", 96))
    half_w = width / 2.0
    half_h = height / 2.0
    
    fx = self.body.position.x
    fy = self.body.position.y
    active_side = self.get_property("active_side", "Bottom")
    
    if active_side == "Top":
      port_x, port_y = fx, fy - half_h
    elif active_side == "Bottom":
      port_x, port_y = fx, fy + half_h
    elif active_side == "Left":
      port_x, port_y = fx - half_w, fy
    else:  # Right
      port_x, port_y = fx + half_w, fy
    
    # 2. Create physics ball (bouncy_ball variant)
    ball = GamePart(self.body.space, port_x, port_y, "bouncy_ball")
    ball.payload = payload
    
    # 3. Apply velocity
    vx, vy = self._compute_emission_velocity()
    ball.body.velocity = (vx, vy)
    
    # 4. Add to world
    entities.append(ball)
    active_instances[ball.uuid] = ball
    
    # 5. State transition
    self._set_state("EMITTING")
  ```

---

#### Task 4.4: Extend `poll_results()` to Emit Balls
- **File:** `entities/source.py`
- **Scope:**
  ```
  def poll_results(self, entities: list, active_instances: dict):
    """Poll and handle results; spawn balls on success."""
    
    # ... (existing guard and loop structure from Phase 3) ...
    
    while not self.queue.empty() and polls < constants.MAX_BATCH_QUEUE_POLLS:
      result_data = self.queue.get()
      polls += 1
      
      error = result_data.get("error")
      data = result_data.get("data")
      
      self.current_fetch_uuid = None
      
      if error:
        # Will be handled in Phase 5 (FATAL state)
        self._set_state("FATAL")
        continue
      
      if data is None:
        # Empty signal: return to IDLE
        self._set_state("IDLE")
        continue
      
      # Success: construct payload and emit ball
      payload = self._construct_payload(data)
      self._emit_ball(payload, entities, active_instances)
  ```

---

#### Task 4.5: Implement Tick Timing (`update_logic`)
- **File:** `entities/source.py`
- **Scope:**
  ```
  def update_logic(self, dt: float, game_state: dict, entities: list, active_instances: dict):
    """
    Update DataSource state and drive the emit interval.
    
    Args:
      dt (float): Delta time (seconds).
      game_state (dict): Current game mode and state.
      entities (list): World entity list.
      active_instances (dict): UUID -> entity map.
    """
    if game_state.get("mode") != "PLAY":
      return
    
    # Initialize engine on first update (in IDLE state)
    if self.visual_state == "OFF":
      self._initialize_engine()
      self._set_state("IDLE")
      self.next_emit_time = time.time() + self.emit_interval
    
    current_time = time.time()
    
    # Check if it's time to emit and not currently fetching
    if current_time >= self.next_emit_time and self.visual_state == "IDLE":
      self._set_state("POLLING")
      self._start_worker()
      self.next_emit_time = current_time + self.emit_interval
    
    # Return to IDLE from EMITTING after brief time
    if self.visual_state == "EMITTING":
      self._set_state("IDLE")
  ```

---

#### Task 4.6: Integrate DataSource into Main Loop
- **File:** `main.py`
- **Scope:**
  - In entity creation section: recognize `type: "data_source"` and instantiate `DataSource`.
  - In main loop (after physics `update`, before draw):
    ```
    # Poll DataSource results (after physics update, before collision processing)
    for entity in entities:
      if hasattr(entity, 'poll_results') and isinstance(entity, DataSource):
        entity.poll_results(entities, active_instances)
  
    # Update DataSource logic (tick-driven emission)
    for entity in entities:
      if hasattr(entity, 'update_logic') and isinstance(entity, DataSource):
        entity.update_logic(dt, game_state, entities, active_instances)
    ```
  - In deletion hook: call `entity.cleanup()` if DataSource.
  - In level clear: iterate DataSources and call `cleanup()`.

---

### Manual Verification (Phase 4)
- [ ] Spawn a DataSource with test CSV and verify ball spawns every N seconds.
- [ ] Verify spawned ball has payload dict with all required keys (data, score, cost, start_time, routing_depth, ttl, drop_dead_age, processing_history).
- [ ] Verify ball physics work (gravity, collisions).
- [ ] Verify exit_angle and exit_velocity are applied correctly (use trajectory inspection).
- [ ] Test all four active_side values (Top, Bottom, Left, Right); verify port positions and velocities.
- [ ] Verify payload is passed to downstream M22 factories without error.

---

## Phase 5: UX Feedback & State Polish

### Objective
Complete state transitions, integrate audio cues for state changes, handle empty MCP responses gracefully, and spawn floating error labels for FATAL conditions (reusing M18 label infrastructure).

### Files to Modify
1. **`entities/source.py`**
   - Implement `_spawn_fatal_label()` method.
   - Complete `_set_state()` audio playback.
   - Handle EXHAUSTED state transition.
   - Fine-tune state machine edge cases.

2. **`main.py`**
   - Ensure audio manager is initialized and accessible.

### Detailed Tasks

#### Task 5.1: Implement State Audio Playback
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _set_state(self, new_state: str):
    """Transition to a new state, play audio, update animation."""
    old_state = self.visual_state
    self.visual_state = new_state
    
    # Play state transition sound (if configured)
    sounds = self.get_property("sounds", {})
    sound_file = sounds.get(new_state)
    
    if sound_file:
      try:
        # Use game's audio manager (same as M6 audio system)
        audio_manager.play_sound(sound_file)
      except Exception as e:
        # Silent fail: missing sound file is non-fatal
        pass
  ```
- **Notes:**
  - Assumes `audio_manager` is a global or imported module (from M6).
  - Sound files referenced relative to `assets/sounds/`.

---

#### Task 5.2: Implement Floating Error Labels
- **File:** `entities/source.py`
- **Scope:**
  ```
  def _spawn_fatal_label(self, entities: list, reason: str):
    """
    Spawn a floating red diagnostic label for FATAL errors.
    Reuses FloatingTextLabel from M18/M22.
    
    Args:
      entities (list): World entity list (append label).
      reason (str): Error message (e.g., "MCP connection failed").
    """
    from entities.active import FloatingTextLabel
    
    label = FloatingTextLabel(
      self.body.position.x,
      self.body.position.y - 40,  # Above the DataSource
      reason
    )
    entities.append(label)
  ```

---

#### Task 5.3: Complete Error Handling in `poll_results()`
- **File:** `entities/source.py`
- **Scope:**
  ```
  def poll_results(self, entities: list, active_instances: dict):
    """Poll results and handle all outcomes."""
    
    if self._is_destroyed:
      # Drain queue
      while not self.queue.empty():
        try:
          self.queue.get_nowait()
        except queue.Empty:
          break
      return
    
    polls = 0
    while not self.queue.empty() and polls < constants.MAX_BATCH_QUEUE_POLLS:
      result_data = self.queue.get()
      polls += 1
      
      error = result_data.get("error")
      data = result_data.get("data")
      
      self.current_fetch_uuid = None
      
      # Error path: network, timeout, JSON parse, etc.
      if error:
        self._set_state("FATAL")
        self._spawn_fatal_label(entities, f"fatal: {error}")
        continue
      
      # Empty signal: MCP returned {"status": "empty"}
      if data is None:
        self._set_state("IDLE")
        continue
      
      # Success: construct and emit ball
      payload = self._construct_payload(data)
      self._emit_ball(payload, entities, active_instances)
  ```

---

#### Task 5.4: Handle EXHAUSTED State Transition
- **File:** `entities/source.py`
- **Scope:**
  - EXHAUSTED is reached when CSVEngine returns None (EOF with loop=false) and the user should see a distinct visual/audio state.
  - Decision: Should emit_interval continue ticking?
    - **Recommendation:** On EXHAUSTED, stop ticking; user must reload or delete and recreate DataSource.
  ```
  def update_logic(self, dt: float, game_state: dict, entities: list, active_instances: dict):
    """Update state machine."""
    
    if game_state.get("mode") != "PLAY":
      return
    
    if self.visual_state == "OFF":
      self._initialize_engine()
      self._set_state("IDLE")
      self.next_emit_time = time.time() + self.emit_interval
    
    if self.visual_state in {"EXHAUSTED", "FATAL"}:
      # Stop polling; entity is dormant
      return
    
    current_time = time.time()
    
    if current_time >= self.next_emit_time and self.visual_state == "IDLE":
      self._set_state("POLLING")
      self._start_worker()
      self.next_emit_time = current_time + self.emit_interval
    
    if self.visual_state == "EMITTING":
      self._set_state("IDLE")
  ```

---

#### Task 5.5: Implement Animation State Drawing
- **File:** `entities/source.py`
- **Scope:**
  ```
  def draw(self, surface):
    """Draw the DataSource with state-specific texture."""
    state_texture = self._animation_textures.get(self.visual_state)
    if state_texture is not None:
      # Temporarily replace base_texture and draw
      old_texture = self.base_texture
      self.base_texture = state_texture
      self.draw_texture(surface)
      self.base_texture = old_texture
      return
    
    # Fallback to default sprite if no state texture
    super().draw(surface)
  ```
- **Notes:**
  - Mirrors M22 FactoryPart's draw override.
  - Ensures correct visual feedback for all states.

---

#### Task 5.6: Prevent Rapid Retries on Error
- **File:** `entities/source.py`
- **Scope:**
  - Once DataSource enters FATAL, it should not automatically retry.
  - User must manually delete and recreate to reset.
  - OR: Implement optional exponential backoff (future enhancement).
  - **For M23:** Keep simple—FATAL is terminal until user resets.

---

#### Task 5.7: Level Save/Load Filtering
- **File:** `utils/level_manager.py` (if exists)
- **Scope:**
  - DataSources are regular entities and should save/load normally.
  - **Exception:** Floating labels (errors) are transient and should NOT be saved.
  - Existing M22 save filtering already excludes non-physics entities; no new changes needed if DataSource has a physics body.
  - Confirm: DataSource has `physics: "kinematic"` in YAML (has a body, can be saved).

---

### Manual Verification (Phase 5)
- [ ] Spawn DataSource; verify it enters IDLE state and play IDLE sound (if configured).
- [ ] Trigger FATAL via bad MCP config; verify red floating error label appears immediately.
- [ ] Verify error label floats upward and disappears after timeout.
- [ ] Test empty MCP response ({"status": "empty"}); verify DataSource returns to IDLE (does NOT transition to EXHAUSTED).
- [ ] Test CSV with loop=false; verify EXHAUSTED state is reached after final row.
- [ ] Verify DataSource stops ticking after EXHAUSTED (no more fetch attempts).
- [ ] Verify all state animations render correctly (IDLE, POLLING, EMITTING, EXHAUSTED, FATAL).
- [ ] Save a level with a DataSource; reload; verify DataSource is restored with same config.

---

## Integration Checkpoints

### After Phase 1
- **Blocked By:** Nothing.
- **Unblocks:** Phase 2, 3.
- **Risk:** MCP library installation, async/sync strategy for MCPEngine.

### After Phase 2
- **Blocked By:** Phase 1.
- **Unblocks:** Phase 4.
- **Risk:** YAML syntax errors, animation/sound file not found (handled gracefully later).

### After Phase 3
- **Blocked By:** Phases 1, 2.
- **Unblocks:** Phase 4, 5.
- **Risk:** Threading race conditions, MCP session lifecycle (critical for safe cleanup).

### After Phase 4
- **Blocked By:** Phases 1, 2, 3.
- **Unblocks:** Phase 5, full integration.
- **Risk:** Velocity/angle math, ball physics interaction with existing entities.

### After Phase 5
- **Blocked By:** All prior phases.
- **Unblocks:** QA, documentation, live testing.
- **Risk:** Audio system integration, animation texture availability.

---

## Final Integration & System Testing

### Objective
Verify M23 works end-to-end with m22 factories, existing physics, and level save/load.

### Manual Test Scenarios

#### Scenario A: CSV-to-Factory Pipeline
1. Spawn a `data_source_csv` DataSource (pointing to test file).
2. Spawn an M22 Factory (logic_factory variant) adjacent to DataSource.
3. Route DataSource's emitted balls into Factory's top sensor.
4. Verify balls are processed by Factory and routed to output ports.
5. Verify payload stays intact (score, cost, history).

#### Scenario B: MCP-to-Factory Pipeline (with mock MCP)
1. Start a mock MCP server returning `{"status": "success", "data": {...}}`.
2. Spawn a `data_source_mcp` DataSource pointing to mock server.
3. Verify balls spawn every N seconds.
4. Verify balls are consumed by Factory (same as Scenario A).

#### Scenario C: Error Handling & Recovery
1. Spawn a `data_source_csv` pointing to non-existent file.
2. Verify DataSource transitions to FATAL immediately.
3. Verify red floating error label appears.
4. Delete the DataSource (verify cleanup works).
5. Spawn a new DataSource with valid file; verify it works normally.

#### Scenario D: Level Save/Load
1. Build a level with 2+ DataSources, Factories, and balls in transit.
2. Save the level.
3. Reload the level in a fresh game session.
4. Verify all DataSources are restored with same config.
5. Verify emission resumes; balls spawn and route to factories.

#### Scenario E: MCP Session Closure
1. Start mock MCP server.
2. Spawn a DataSource in MCP mode.
3. While DataSource is POLLING (awaiting fetch), delete it immediately.
4. Verify MCP session closes without hanging.
5. Verify game continues to run ( no freeze or crash).

---

## Dependencies & External Libraries

| Library | Version | Usage | Reason |
|---------|---------|-------|--------|
| `mcp` | ≥0.1.0 | MCPEngine client session, tool invocation | Official MCP protocol library |
| `threading` | stdlib | Background fetch operations | Python standard library |
| `queue` | stdlib | Thread-safe result handoff | Python standard library |
| `asyncio` | stdlib | Optional: async support for MCPEngine | Python standard library |
| `csv` | stdlib | CSVEngine file reading | Python standard library |
| `time` | stdlib | Tick timing, emission intervals | Python standard library |
| `pygame` | existing | Audio playback (M6) | Already in project |
| `pymunk` | existing | Physics bodies, spaces | Already in project |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| MCP library not available | Low | Integration fails | Document `pip install mcp` in setup; graceful fallback to NullGenerator. |
| MCPEngine blocking main loop | High | 60 FPS drops | **Critical:** Enforce background threading; test with high timeouts. |
| MCP session hung on cleanup | Medium | Game freeze on delete | Implement session timeout; use try/except in cleanup(). |
| CSV file not found | Medium | DataSource FATAL'd | Handled gracefully; user sees error label and can delete/recreate. |
| Stale queue results after deletion | High | Physics corruption | **Critical:** Implement `_is_destroyed` check before queue.put(); test in Phase 3. |
| Payload structure mismatch | Medium | Downstream factory errors | **Testing:** Ensure payload dict has all required keys; add unit test. |
| Angle/velocity computation errors | Medium | Balls emit in wrong direction | **Testing:** Verify all 4 active_side values; use trajectory visualization. |
| Missing animation/sound files | Low | Silent fallback | Handled gracefully; use placeholder; doesn't crash. |

---

## Estimation & Timeline

| Phase | Tasks | Estimated Duration |
|-------|-------|-------------------|
| 1 | Generator engines, registry | 2–3 hours |
| 2 | YAML config | 1 hour |
| 3 | Threading, cleanup guards | 3–4 hours |
| 4 | Payload, emission, main loop | 2–3 hours |
| 5 | Audio, error labels, polish | 1–2 hours |
| Integration & System Testing | All scenarios, edge cases | 2–3 hours |
| **Total** | | **12–16 hours** |

---

## Acceptance & Sign-Off

All phases are complete when:
- [ ] All Phase 1–5 manual verifications pass.
- [ ] Compile checks pass (`py_compile`).
- [ ] All 5 integration scenarios (A–E) execute successfully.
- [ ] No unhandled exceptions; clean error messages for all failure modes.
- [ ] M23 entities are saveable and loadable.
- [ ] Thread safety validated (no race conditions, no ghost threads).
- [ ] Documentation (this plan) is accurate and complete.

---

**End of Implementation Plan**
