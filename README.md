# Incredible Machines 🧩⚙️

Welcome to **Incredible Machines**, a vibe-coded 2D physics-based puzzle sandbox inspired by the classic series *The Incredible Machine*. Build, tinker, and solve mechanical puzzles using a variety of interactive parts, logic wiring, and advanced physics components.

---

## 🚀 Core Gameplay Loop
1. **EDIT MODE**: Drag and drop parts from the palette, rotate them, and configure their properties. The physics simulation is paused, letting you plan your contraption perfectly.
2. **LOGIC WIRING**: Connect "Sender" entities (like Baskets) to "Receiver" entities (like Cannons or Motors) using the **Wire Logic** tool to create cause-and-effect chains.
3. **PLAY MODE**: Hit "Play" to let gravity and momentum take over. Watch your machine come to life as physics objects interact and signals trigger actions!

---

## ✨ Key Features

### 🏗️ Advanced Physics Mechanics
*   **Conveyor Belts**: Kinematic surfaces with adjustable `speed` and `direction` (Left/Right) that actively push resting objects.
*   **Motors**: Continuously spinning gears and wheels pinned in space. Support adjustable `motor_speed` and `direction` (Clockwise/Counter-Clockwise).
*   **Collision Dynamics**: Realistic bouncing, friction, and mass interactions handled by the **Pymunk** engine.

### 🔌 Logic Wiring & Signals
*   **Event-Driven Actions**: Connect a **Basket** to a **Cannon** so that ingesting a ball triggers a projectile launch.
*   **Toggling Systems**: Wire triggers to **Motors** or **Conveyors** to turn them ON/OFF based on in-game events.
*   **Visual Feedback**: Logic wires flash when a signal is successfully transmitted across the circuit.

### 🛠️ Creative Tools
*   **Property Editor**: Select any part in Edit Mode to modify its friction, elasticity, mass, or specific mechanical properties (like motor speed/direction) in real-time.
*   **Asset Management**: Powered by a robust asset pipeline that handles image caching, sprite rotation, and smooth fallback placeholders.
*   **Save/Load Canvas**: Effortlessly save your complex machines to YAML files and reload them later to continue your experimentation.

---

## 🎮 Controls & Interaction

| Key/Action | Description |
| :--- | :--- |
| **Mouse Click** | Place a selected part / Select an existing part. |
| **Right Click** | Delete a part (while in Edit Mode). |
| **Wire Logic Tool** | Click a Sender (source) then a Receiver (target) to create a link. |
| **'Delete' Key** | Remove the currently selected entity. |
| **UI Buttons** | Toggle between **Play** and **Edit** modes, Save/Load, or Clear the canvas. |

---

## 🛠️ Tech Stack
*   **Language**: Python 3.x
*   **Engine**: Pygame Community Edition (CE) 
*   **Physics**: Pymunk 7.2.0 (2D Physics Library)
*   **Config**: YAML for entity definitions and level persistence

---

## 📂 Project Structure
*   `main.py`: The heart of the game loop, UI management, and event handling.
*   `entities/`: Contains `base.py` for part logic and specific entity implementations.
*   `config/`: `entities.yaml` holds the source-of-truth definitions for every part in the game.
*   `utils/`: Core utilities for `AssetManager`, `LevelManager`, and `UIManager`.
*   `saves/`: Your machine inventions live here!

---

*Built with ❤️ and a lot of physics tinkering.*
