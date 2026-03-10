Role: Senior Systems Programmer

Context: Please perform a comprehensive review of the following documents:

docs/CONSTITUTION.md (Pay close attention to Sections 13, 14, 15, & 16 regarding Thread Safety, Plugin Architecture, Data Degradation, and Payload Scoring)

docs/SPECIFICATION_M22_LogicFactories.md

docs/IMPLEMENTATION_PLAN_M22_LogicFactories.md

Task: Implement Milestone 22: Logic Factories & Async Processors. Execute the 8 phased steps exactly as outlined in the implementation plan.

Critical Instructions:

Explicit Data Structures (Engines & Routing): You must rigidly adhere to the JSON structure defined in the specification.

RegexEngine must loop over "rules" and extract "target_field" if the payload is a dictionary.

RandomEngine must parse "distribution", "params", and map states using "rules".

The Factory output MUST be routed by checking the returned state sequentially against "max_state" in the "routing" array.

Payload Health/Scoring (Gamification): The payload score attribute acts as its health. When determining the exit trajectory from the "routing" array, extract the "score" (health modifier) from that specific rule (defaulting to 0 if missing). Add this value to the ball's payload['score']. Crucial: If the payload does not have a score yet, initialize it to 100 before applying the modifier.

Safe Thread Cleanup (CRITICAL): Ensure the Factory entity has a cleanup() or destroy() method override. It must set self._is_destroyed = True. Inside your background thread execution, you MUST wrap the queue insertion in a check: if not self._is_destroyed: self.queue.put(result). This prevents ghost threads from crashing the game if the Factory is deleted mid-processing.

Sensor Cooldown (Double-Bounce Prevention): Implement a cooldown timer (e.g., self.cooldown_timer). Set it to 0.5 seconds when transitioning to or from the EMITTING state. While this timer is active, the Top collision sensor must ignore incoming payloads (acting as a solid wall) to prevent infinite bouncing loops.

FATAL Feedback UX: If the process() engine throws an exception or returns a fatal error string instead of a numerical state, set the visual state to FATAL. You must then spawn a floating text label (reusing M18's payload label logic) above the Factory displaying the specific error reason so the player can debug it.

Payload Lifecycle (Age/Cost): * Cost: Enforce the cost_modifier. If cost <= 0, bypass the engine and eject out the Bottom edge.

Age: Enforce the drop_dead_age. If expired, bypass the engine and eject out the Top edge. Physics Warning: Do NOT assign negative mass. You must flag the entity and apply an upward anti-gravity force continuously in the main update() loop.

Thread Safety (CRITICAL): Pymunk is not thread-safe. Background threads MUST ONLY process healthy payloads and place the resulting state in a queue.Queue(). The main Pygame update() loop must poll this queue to execute the actual physical ejection and trajectory calculations.

Plugin Architecture: Use the EngineRegistry. Do NOT use monolithic, hardcoded if/elif chains checking strings to select the engine type. Instantiate them dynamically.