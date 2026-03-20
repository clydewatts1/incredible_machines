Command Line Interface (CLI) Enhancement

Objective

To enable automated control, testing, and batch processing by adding robust command-line argument parsing to main.py. This allows the game to be launched in specific states, for limited durations, and with automated loading/saving.

Core Features

1. Argument Parsing (argparse)

Integrate Python's argparse library to handle the following flags:

-l / --load <path>: Immediately calls the level_manager to load the specified YAML model file on startup.

-s / --state <PLAY|EDIT>: Sets the initial game_state["mode"]. Defaults to EDIT.

-t / --timeout <minutes>: Sets a countdown timer. When reached, the game automatically triggers the quit sequence.

-d / --dump <path>: Specifies a filename to which the current world configuration will be saved automatically upon exit (either by timeout or manual quit).

2. Logic Integration

Initialization: Arguments are parsed before pygame initializes. Loading logic runs immediately after the space and entities list are created.

The Exit Timer: A start_time is recorded. Inside the while running loop, a check compares (current_time - start_time) against the timeout threshold.

The Auto-Dump: The handle_quit function is modified to check for the --dump argument. If present, it calls level_manager.save_level() before shutting down the process.

Benefits

Automated Testing: Run a simulation for 5 minutes and save the result to see how the factory performed.

Quick Boot: Jump straight into "PLAY" mode with a specific level loaded.

Headless-Ready: Sets the stage for running the logic without a window for data processing.