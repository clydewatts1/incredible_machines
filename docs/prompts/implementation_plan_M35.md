Milestone 35: Automated Testability & Headless Execution

Objective

To build a robust, automated testing framework that prevents regression bugs. This allows the factory to run in a headless, deterministic mode for a set duration, injecting predefined payloads and automatically comparing the Sink's output against an expected baseline. It supports batch execution via wildcard matching and AI-assisted evaluations.

1. CLI Test Runner (main.py)

Enhance the command-line interface to support a dedicated testing mode.

Arguments: * -t <test_pattern> or --test <test_pattern>: Triggers the test suite. Supports wildcards (e.g., sort_* or all).

-v or --visible: Optional flag. If passed, the tests render the Pygame window so the user can watch the execution.

Execution Modes: * Headless (Default for tests): Skips the Pygame visual window (pygame.display.set_mode with hidden flags or bypassing draw calls entirely) to run the simulation at maximum CPU speed.

Visible (Visual Debugging): Renders the factory normally while still enforcing the test boundaries and payload injections.

Deterministic Physics: Instead of using real-time delta (dt), the test loop forces a fixed timestep (e.g., space.step(1/60.0)) for a predetermined number of "ticks". This guarantees that the physics engine produces the exact same result 100% of the time.

2. Test Directory & Metadata Structure

Tests are self-contained environments ensuring clean inputs and outputs. The inputs.json file now acts as the root configuration for the test.

tests/
└── <testname>/
    ├── <testname>.yaml        # The factory layout to load
    ├── inputs.json            # Contains Test Metadata, Evaluator Type, and Payloads
    ├── expected_output.csv    # The baseline assertion file
    └── output/                # Where Sinks write their data during the test


Example inputs.json Structure:

{
  "test_name": "Basic AI Sorting",
  "test_description": "Verifies that the BrainPart correctly identifies fruit vs vegetables.",
  "evaluator": "llm_semantic", 
  "payload_events": [
    {"tick": 60, "payload": {"item": "Apple"}},
    {"tick": 120, "payload": {"item": "Carrot"}}
  ]
}


3. Test Suite Execution & Teardown

To support running multiple tests in sequence:

Batch Processing: The runner resolves the wildcard pattern against the tests/ directory to build a queue of tests.

State Teardown: Between every test, the entities list is cleared, active_instances is wiped, and a brand new pymunk.Space is initialized to prevent cross-test contamination.

Aggregate Reporting: A summary is printed at the end of the batch (e.g., "5 Tests: 4 PASS, 1 FAIL").

4. Sink Redirection & Auto-Assertion

Redirection: When game_state["test_mode"] is active, any DataSink that writes to a file must redirect its output path from the standard exports/ folder to tests/<testname>/output/.

Assertion Engine: Once the simulation reaches its maximum tick count, the test runner reads the evaluator flag from inputs.json to determine how to score the test:

strict_csv (Default): Performs a standard 1:1 string comparison between actual and expected CSVs.

llm_semantic (AI Judge): Bypasses strict string matching. It passes both outputs to an LLM with a prompt: "Evaluate if the actual output fulfills the requirements of the expected output. Ignore slight phrasing differences. Reply strictly with PASS or FAIL."

5. The Test Recorder (Snapshot Generator)

To easily create test cases without writing JSON/CSV by hand, the Editor UI includes a "RECORD TEST" feature.

Trigger: Clicking "RECORD TEST" prompts for a test name, description, and evaluator type.

Snapshot: It immediately saves the current layout to tests/<testname>/<testname>.yaml and initializes the inputs.json metadata.

Input/Output Logging: Standard DataSource entities append their emitted payloads to the inputs.json events, while Sinks write to expected_output.csv.

6. Advanced Testing Recommendations (Future-Proofing)

To make the testing suite fully production-ready, consider implementing these advanced concepts:

Performance Benchmarking: Alongside correctness assertions, the test runner should track how long it took the CPU to compute the required ticks. If a code change drops the simulation speed by a significant margin, the test should flag a "Performance Regression."

Chaos / Fuzz Testing: Introduce a --fuzz CLI flag. When active, the TestSource deliberately mutates the inputs.json data (e.g., turning strings into integers, or stripping expected dictionary keys). This verifies that the Zero Rule error routing works flawlessly and prevents the factory from crashing on bad data.

CI/CD Integration (JUnit Output): Update the Aggregate Reporting step to optionally write a test_results.xml file in standard JUnit format. This allows platforms like GitHub Actions to automatically parse the results and display beautiful test dashboards on your repository.