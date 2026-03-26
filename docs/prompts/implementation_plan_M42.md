Milestone 42: Gamepad Control & Physics Avatar

Objective

To add native controller support (pygame.joystick) optimized for dual-analog controllers (like the Nintendo Switch Pro Controller). The controller must act as a virtual mouse for UI interaction, provide direct camera control, and optionally drive a physical Avatar in the game world. All mappings must be configurable via environment.yaml.

Control Scheme

Left Stick: Virtual Mouse Cursor (Moves the cursor across the screen in both EDIT and PLAY modes).

A Button (Cross/B): Primary Action (Simulates Left Mouse Click).

B Button (Circle/A): Secondary Action (Simulates Right Mouse Click / Delete / Context Menu).

D-Pad (Cross Control): Camera Panning (Scrolls the factory window in both modes).

Right Stick: Avatar Movement (Controls the physical PlayerAvatarPart during PLAY mode).

Core Features

1. The Controller Manager (utils/controller.py)

A new utility class that reads mappings from config/environment.yaml.

Virtual Mouse: Reads the configured Left Stick axes. Updates pygame.mouse.set_pos() to physically move the computer's mouse cursor.

Camera Scrolling: Reads the D-Pad (Hat) state. Exposes a get_camera_pan() method that returns an X/Y velocity vector to shift the camera.

Avatar Control: Reads the configured Right Stick axes. Exposes a get_avatar_movement() method for the Avatar entity to consume.

2. Integration (main.py)

Initialize pygame.joystick at startup and instantiate the ControllerManager.

In the while running: loop:

Call controller_manager.update(dt) to process the virtual mouse.

Fetch the camera pan vector from the D-Pad and apply it to camera.x and camera.y.

In the event loop:

Catch pygame.JOYBUTTONDOWN and pygame.JOYBUTTONUP.

Map the configured "A" button to post a pygame.MOUSEBUTTONDOWN (button 1).

Map the configured "B" button to post a pygame.MOUSEBUTTONDOWN (button 3).

3. The Player Avatar (entities/avatar.py)

A dynamic physics entity. In its update_logic loop, it reads the Right Stick output from the ControllerManager. It directly modifies self.body.velocity to give the player snappy, responsive movement, allowing them to push payloads and trigger pressure plates.

4. Advanced Enhancements & Suggestions

Configurable Deadzones: Analog sticks rarely rest exactly at 0.0. Implementing a deadzone config (e.g., 0.15) prevents the mouse cursor or avatar from drifting when you let go of the sticks.

Palette Cycling (Bumpers/Shoulders): Map L1 and R1 to cycle through the component palette (Left/Right). This saves the player from having to drag the virtual mouse to the UI panel every time they want to select a new machine.

Camera Zoom (Triggers): Map L2 and R2 to simulate the mouse scroll wheel, zooming the factory camera in and out.

Haptic Feedback (Rumble): Use self.joystick.rumble() to make the controller vibrate when the Avatar takes a hard physical impact or when placing a machine.