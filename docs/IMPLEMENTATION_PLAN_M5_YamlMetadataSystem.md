# Milestone 5: Implementation Plan (YAML Metadata & Property System)

This document provides a sequential, step-by-step roadmap for refactoring "The Incredible Machine Clone" to utilize an external YAML configuration for physics properties and metadata, in compliance with Section 9 of the Constitution.

## Phase 1: Configuration Infrastructure

### Task 1: Setup `config/entities.yaml`
**Objective:** Establish the external data structure to hold physics configurations and generic entity metadata, enabling future scalability (e.g., Audio).
**Actions:**
1. Create a `config` directory in the project root.
2. Inside `config`, create `entities.yaml`.
3. The YAML file must contain:
   * A `default_properties` section containing baseline values (e.g., `friction: 0.5`, `elasticity: 0.5`).
   * A `bouncy_ball` section containing its overrides (e.g., `mass: 1.0`, `elasticity: 0.8`).
   * A `static_ramp` section defining its properties (e.g., `friction: 0.7`).

**Validation (QA Rule):** 
1. Open the file in a text editor and visually verify the YAML syntax is valid and hierarchical. 

### Task 2: Implement Config Loader Utility
**Objective:** Create a utility to parse the YAML file robustly, ensuring it "Fails Loudly" upon syntax issues or missing files.
**Actions:**
1. Add `PyYAML` to the `requirements.txt` and environment.
2. Create `utils/config_loader.py` adhering to snake_case naming rules (Sec. 7).
3. Implement a `load_entity_config(property_key)` function that reads `config/entities.yaml`.
4. It must extract the `default_properties` dict, extract the specific `property_key` dict, and perform a dictionary merge right over the defaults so the entity gets a complete, fully populated dictionary.
5. **Fail Loudly:** `assert` or raise an explicit `FileNotFoundError` if `entities.yaml` is missing. Raise a specific `ValueError` if the `property_key` does not exist in the YAML.

**Validation (QA Rule):** 
1. Write a temporary test snippet in `main.py` calling `load_entity_config("non_existent_key")`. Run it and ensure the game crashes with the custom "Fail Loudly" error message. Remove the snippet after.

## Phase 2: Base Class Integration

### Task 3: Refactor `GamePart` Base Entity Class
**Objective:** All entities must derive their operational parameters from the loaded configuration, setting up a scalable foundation for M6 Audio.
**Actions:**
1. Open `entities/base.py`.
2. Modify the `__init__(self, space, property_key)` signature.
3. Call `load_entity_config(property_key)` inside the initializer.
4. Store the resulting merged dictionary as `self.properties`. 
   * *Scalability Note:* Storing the whole dict ensures future features like `self.properties.get("sound_file")` (Milestone 6) will work natively without touching the base class signature again.

**Validation (QA Rule):** 
1. This step represents an intermediate architecture shift. Creating a dummy `GamePart` object without passing a `property_key` (if the old signature is accidentally used) will raise a Python `TypeError`, which satisfies the immediate fail state until subclasses are updated.

## Phase 3: Entity Refactoring & QA Testing

### Task 4: Remove Hardcoded Values in Subclasses
**Objective:** Eliminate all magic numbers for physics from `Ball` and `Ramp`.
**Actions:**
1. Update `entities/ball.py` to pass `"bouncy_ball"` to `super().__init__(space, "bouncy_ball")`.
2. Replace hardcoded `mass`, `friction`, and `elasticity` inside `ball.py` with `self.properties["mass"]`, `self.properties["friction"]`, etc.
   * **Fail Loudly:** Because we are using dictionary indexing (e.g., `["friction"]`) instead of `.get()`, Python will naturally throw a loud `KeyError` if a required physics property failed to populate from the YAML.
3. Update `entities/ramp.py` to pass `"static_ramp"` and similarly retrieve `friction` and `elasticity` from `self.properties`.

**Validation (QA Rule) & Final QA Test:** 
This covers the constitutional mandate from M5 Specification regarding dynamic updates.
1. Run `python main.py` and spawn a Ball (`B`) over a Ramp (`R`). Enter Play mode. Observe normal behavior.
2. While the application is *still running*, open `config/entities.yaml`. Change the `elasticity` of `bouncy_ball` to `1.5` and save the file.
3. Switch the game to EDIT mode, spawn a *new* Ball. Switch to PLAY mode.
4. Verify the newly spawned ball is wildly elastic while the first ball remains normal.
5. **Missing Property Test:** Close the game. Remove `friction` from both defaults and `bouncy_ball` in the YAML. Run the game, spawn a Ball. Verify the whole app crashes with a `KeyError: 'friction'`.
