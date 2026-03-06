# Milestone 5 Specification: YAML Metadata & Property System

## Overview
This specification details the transition from hardcoded physics properties to an external YAML-based configuration system. In accordance with Section 9 of the Constitution, this architecture ensures consistency, allows for real-time dynamic updates without code modification, and provides a structured metadata foundation for future features (like the Audio System).

## 1. Feature Requirements
### External Configuration (`config/entities.yaml`)
* A new directory and file (`config/entities.yaml`) must be created to store all configurable properties.
* The YAML structure must define a `default_properties` block as a fallback, followed by specific entity definitions (e.g., `BouncyBall`, `StaticRamp`).
* Required properties to migrate to YAML for Milestone 5:
  * `entity_id` and `label` (Metadata mapping)
  * `mass` (for dynamic bodies)
  * `friction`
  * `elasticity` 

### Base Class Refactoring (`entities/base.py`)
* The `GamePart` (or `Entity`) base class must be refactored to accept or load a dictionary-based `properties` attribute during initialization.
* **Component Defaulting:** If an entity's specific YAML definition is missing a property (e.g., a ball definition lacks "friction"), the system must automatically populate that missing value from the `default_properties` block defined in the YAML file before assigning it to the physics body.

### Dynamic Updates (No Hardcoding)
* All hardcoded physics values (e.g., `self.shape.elasticity = 0.5`) in subclass files like `ball.py` and `ramp.py` MUST be removed.
* During gameplay (Edit Mode), when a new entity is spawned (e.g., pressing `B` for Ball), the system must read the *latest* values from `config/entities.yaml`. This allows a developer/level designer to change the YAML file, save it, and immediately spawn a differently behaved object in-game without restarting the Python process.

## 2. Technical Considerations
* **YAML Parsing Library:** The `PyYAML` library will be required as a new dependency.
* **File I/O Performance:** While reading a small YAML file on every spawn is acceptable for a sandbox (and explicitly requested for dynamic updates), in a production environment this might be cached and reloaded via a hot-reloader. For M5, reading on spawn is the simplest way to achieve the dynamic update requirement.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating YAML Dynamic Updates and Fallbacks
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Verify Initial YAML Load**
1. Launch the application (starts in `Mode: EDIT`).
2. Press `R` to spawn a Ramp, tilt it slightly, and `B` to spawn a Ball above it.
3. Switch to `PLAY` mode and observe the baseline bounce and roll behavior.

**Step 2: Test Dynamic Updates (No Restart Required)**
1. While the game is still running, open `config/entities.yaml` in your text editor.
2. Locate the `BouncyBall` definition and drastically change its `elasticity` (e.g., from `0.5` to `1.5` for extreme bounciness) and save the file.
3. In the game, switch back to `EDIT` mode.
4. Press `B` to spawn a *new* Bouncy Ball next to the old one.
5. Switch to `PLAY` mode.
6. **Success Check:** The newly spawned ball should exhibit the extreme, updated bouncing behavior, while the old ball maintains the original behavior it was spawned with.

**Step 3: Test "Fail Loudly" Rule**
1. Close the game.
2. Open `config/entities.yaml` and completely delete or rename the `friction` key from both the `BouncyBall` definition AND the `default_properties` block. Save the file.
3. Launch the game and attempt to spawn a Bouncy Ball.
4. **Success Check:** The game MUST immediately crash and print an explicit error to the console (failing loudly) stating that a required property (`friction`) is missing from the configuration.

**Sign-off:** The feature is complete when the user can dynamically alter physics via YAML without restarting, and the engine explicitly rejects missing foundational data.
