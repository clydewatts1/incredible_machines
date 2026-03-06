# Milestone 6 Specification: Universal Audio System

## Overview
This specification details the implementation of a centralized, zero-latency Audio System for "The Incredible Machine Clone" per Section 8 of the Project Constitution. It leverages the YAML metadata system established in Milestone 5 to assign specific sound effects to entities, while ensuring a robust global fallback.

## 1. Feature Requirements
### Sound Manager
* **In-Memory Loading:** A dedicated audio manager (`utils/sound_manager.py`) must be created to preload all `.wav` or `.ogg` files into memory via `pygame.mixer.Sound` during engine startup. This prevents disk I/O lag during physics collisions.
* **Playback Interface:** The manager must provide a simple interface (e.g., `play_sound("bounce")`) for the physics engine to call.

### YAML Integration & The Fallback Rule
* **Entity Config:** The `config/entities.yaml` must be updated to include a `collision_sound` key in the `default_properties` block (e.g., `collision_sound: "default_collision.wav"`). 
* **Overrides:** Specific entities (like `bouncy_ball`) can override this with their own sound file paths (e.g., `collision_sound: "rubber_bounce.wav"`).
* **Fallback Priority:** If an entity's specific YAML entry lacks the `collision_sound` key, the `config_loader` will inherently pull the `default_properties` fallback, satisfying the Constitution's strict "Fallback Sound Logic" requirement.

### Collision Logic (Pymunk)
* **Collision Handler:** A `pymunk.CollisionHandler` must be attached to the physics space. 
* **Trigger Condition:** Upon the `post_solve` phase of a collision, the system will evaluate the collision impulse (strength). If the impact exceeds a minimum threshold (to avoid a cacophony of micro-bounces when an object settles), a sound event will trigger.
* **Data Retrieval:** The collision handler will look at the `shape.body` involved, identify its corresponding `GamePart`, read its `self.properties["collision_sound"]`, and pass that string to the Sound Manager.

## 2. Technical Considerations
* **Asset Location:** Sound files must be stored in a new `assets/sounds/` directory.
* **Pygame Mixer Initialization:** `pygame.mixer.init()` must be called early in `main.py` before any sound assets are loaded.

## 3. Manual Test Script & Success Criteria (Per Constitution Section 6)

### QA Test: Validating Universal Audio and Fallback Logic
To pass quality assurance for this feature, the human tester or developer MUST execute the following steps exactly as written:

**Step 1: Setup & Initial Verification**
1. Ensure placeholder sound files exist in `assets/sounds/` (the AI will generate basic synth waves or provide explicit instructions if needed).
2. Launch the application (starts in `Mode: EDIT`).
3. Press `R` to spawn a Ramp, tilt it, and `B` to spawn a Ball above it.
4. Press `SPACE` to switch to `PLAY` mode.
5. **Success Check:** As the ball strikes the ramp, an audible sound (e.g., a "bounce") MUST immediately play without visual stuttering.

**Step 2: Dynamic YAML Verification (No Restart)**
1. While the game is still running, open `config/entities.yaml` in your text editor.
2. Under the `bouncy_ball` entry, change the `collision_sound` to a different valid filename (e.g., swap `bounce.wav` for `thud.wav`). Save the file.
3. In the game, switch back to `EDIT` mode, spawn a *new* Ball, and drop it.
4. **Success Check:** The new ball must play the newly assigned sound upon impact.

**Step 3: Fallback Logic Verification**
1. Open `config/entities.yaml` and completely delete the `collision_sound` key from the `bouncy_ball` entry. Save.
2. In the game, switch to `EDIT` mode, spawn a *new* ball, and drop it.
3. **Success Check:** The ball must now audibly play the `default_collision.wav` defined in the global defaults block.
