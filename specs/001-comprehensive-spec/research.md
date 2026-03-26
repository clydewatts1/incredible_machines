# Validation Research: Project Baseline

## Established Technical Choices

1. **Deterministic Physics Verification**
   - **Current System**: PyMunk (Chipmunk2D port) + Fixed 60FPS update loop in `main.py`.
   - **Validation**: confirmed that physics steps use `dt` scaling and a fixed timestep of `1/60.0` in test modes, ensuring deterministic results across different hardware.

2. **Visual Processing Isolation (M41)**
   - **Current System**: Pure 2D Pygame rendering for `EffectBoxPart` and particles.
   - **Validation**: Confirmed that these effects do not generate PyMunk bodies, preventing engine bloat during high-volume data events.

3. **Data Mutation Engine (M40)**
   - **Current System**: `faker` library integration for JSON record synthesis.
   - **Validation**: Confirmed that `FakerSource` and `FakerEngine` correctly mutate payload data dictionaries without modifying physical collision properties.

4. **Gamepad & Virtual Mouse (M42)**
   - **Current System**: `pygame.joystick` routed through `utils/controller.py`.
   - **Validation**: Verified that the Left Stick correctly maps to `pygame.mouse.set_pos()` for UI interaction, and the Right Stick directly influences the `PlayerAvatarPart` velocity.
