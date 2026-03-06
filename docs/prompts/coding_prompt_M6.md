Role: Senior Gameplay Programmer & Audio Engineer

Context: > Please perform a comprehensive review of the following documents:

CONSTITUTION.md (Specifically Section 8: Audio Standards and Section 9: Data Standards).

docs/SPECIFICATION_M6_AudioSystem.md.

docs/IMPLEMENTATION_PLAN_M6_AudioSystem.md.

Task: > Implement the Universal Audio System as defined in the Milestone 6 plan.

Execution Requirements:

Infrastructure: Create utils/sound_manager.py. Implement the SoundManager to load .wav files into memory during initialization.

YAML Integration: Update the base Entity class and config/entities.yaml. Ensure sound file paths are retrieved from the YAML properties dictionary.

Fallback Logic: You MUST implement the global fallback rule. If a specific sound file is missing or the YAML path is invalid, the system must play assets/sounds/default_collision.wav without crashing.

Physics Hooks: Implement the Pymunk PostSolve collision handler in main.py to trigger sounds based on collision impulse.

Placeholders: If .wav files do not exist in the assets/sounds/ directory, please write a small temporary utility script to generate simple placeholder "beep" or "thud" .wav files so we can test the system immediately.

Final Action & Quality Assurance:

Run the game and ensure there are no terminal errors during sound initialization.

Lead Developer Validation: Confirm that the system is ready for me to perform the "Manual Test Script" (verifying collision sounds, spawn sounds, and YAML-driven sound swaps).