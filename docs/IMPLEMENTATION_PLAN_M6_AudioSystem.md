# Milestone 6: Implementation Plan (Universal Audio System)

This document provides a sequential, step-by-step roadmap for integrating a robust, in-memory audio management system into "The Incredible Machine Clone", in compliance with Sections 8 and 9 of the Project Constitution.

## Phase 1: Audio Management Infrastructure

### Task 1: Initialize Pygame Mixer and Create SoundManager
**Objective:** Establish a centralized `SoundManager` utility to preload audio files into memory, ensuring zero-latency playback during physics simulation.
**Actions:**
1. Open `main.py` and ensure `pygame.mixer.init()` is called before the main game loop.
2. Create a new utility file: `utils/sound_manager.py`.
3. Implement a `SoundManager` class (following a Singleton pattern or as a global initialized object).
4. Implement a `load_sound(sound_id, filepath)` method that loads a standard `.wav` file into a `pygame.mixer.Sound` object and caches it in a dictionary.
5. Implement a `play_sound(sound_id)` method to trigger the cached sound.

**Validation (QA Rule):** 
1. In `main.py`, create a temporary call to `SoundManager.load_sound()` with a non-existent file path. Run the game.
2. The system MUST "Fail Loudly" locally during load, confirming the file loading works before we try playing it. (Remove the temporary call after testing).

### Task 2: Implement "Fallback Logic" Integration
**Objective:** Tie the `SoundManager` to the YAML configuration and enforce the global fallback rule (Section 8).
**Actions:**
1. Open `config/entities.yaml` and add `collision_sound: "default_collision.wav"` to the `default_properties` block.
2. Add `collision_sound: "bounce.wav"` specifically to the `bouncy_ball` block.
3. Update `SoundManager` to automatically load the global `"default_collision.wav"` on initialization. 
4. Modify the `play_sound(sound_id)` method: If the requested `sound_id` is missing or invalid in the in-memory cache, it MUST automatically play the default sound instead of failing during gameplay.

**Validation (QA Rule):** 
1. Write a temporary test snippet in `main.py` calling `SoundManager.play_sound("missing_sound_key")`. 
2. Run the game and verify the default collision sound plays instead of raising an error.

## Phase 2: Physics and Event Integration

### Task 3: Pymunk Collision Handler (PostSolve)
**Objective:** Trigger physics-based audio based on collision strength, avoiding spammy sounds when objects settle.
**Actions:**
1. Open `main.py` and define a Pymunk collision handler: `handler = space.add_default_collision_handler()`.
2. Define a `post_solve` callback function for the handler.
3. Inside the callback, calculate the total collision impulse magnitude: `impulse = arbiter.total_impulse`.
4. If `impulse.length > 500` (or an appropriate threshold), identify the two shapes involved.
5. Retrieve the corresponding entity's `collision_sound` property (which was automatically loaded into `self.properties` in M5).
6. Call `SoundManager.play_sound(entity_sound)`.

**Validation (QA Rule):** 
1. Run the game, spawn a Ball above a Ramp, and enter Play mode.
2. Verify a sound plays *only* upon significant impacts, and not continuously while the ball is resting on the ramp.

### Task 4: Base Class One-Shot Event Audio
**Objective:** Enable entities to play sounds for non-physics interactions automatically (e.g., UI interactions, spawning, or highlighting).
**Actions:**
1. Open `entities/base.py`.
2. Add a helper method `play_event_sound(event_type)` to the `GamePart` class.
3. This method checks `self.properties` for the specified `event_type` sound (e.g., `spawn_sound`, `hover_sound`).
4. If it exists, call `SoundManager.play_sound(...)`.
5. Update `main.py` to trigger `entity.play_event_sound("spawn_sound")` whenever a new entity is appended to the `entities` list.

**Validation (QA Rule):** 
1. Add a dummy `spawn_sound: "spawn.wav"` to `config/entities.yaml`.
2. Run the game in EDIT mode. Press `B` to spawn a Ball.
3. Verify the spawn sound plays immediately upon creation.

## Phase 3: Final QA Testing
### Task 5: Manual Test Script Validation
**Objective:** Formally execute the testing steps outlined in the M6 Specification to prove dynamic YAML audio updates and Fallback logic work concurrently.
**Actions:**
1. Launch the game, drop a ball onto a ramp, and verify the specific `bounce.wav` sound plays.
2. Edit `entities.yaml` to change the `collision_sound` path. 
3. Spawn a new ball in-game and verify the new sound plays without needing a restart.
4. Delete the sound path from YAML entirely, spawn a new ball, and verify the universal "Fallback" sound (`default_collision.wav`) plays.
