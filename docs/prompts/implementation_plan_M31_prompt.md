Milestone 31: Pygame GUI Migration & Advanced Controls

Objective

Replace the custom UIManager with the pygame-gui library to provide a stable, professional interface. This includes grouped menus, transport controls, and time-scaling (Slow-mo/Fast-forward).

Core UI Components

1. The Top Menu Bar

File Menu (Left): A UIDropDownMenu labeled "FILE" with:

Save, Save As, Load.

Transport Controls (Center): A cluster of five buttons for simulation control:

[ << ]: Slow Motion (0.5x speed).

[ ▶ ]: Play (1.0x speed).

[ ⏸ ]: Pause (0.0x speed).

[ >> ]: Fast Forward (2.0x - 4.0x speed).

[ ■ ]: Stop/Edit Mode.

Global Settings (Right): Access to Flow Metadata (Name/Description).

2. Side Panels

Inspector (Left): A UIWindow or UIPanel for editing object properties.

Palette (Right): A UIScrollingContainer for selecting tools, featuring hover tooltips.

3. Time Scaling Logic

Speed Multiplier: A new game_state["speed_multiplier"] variable.

Physics Integration: The space.step(dt * multiplier) will allow for smooth slow-motion or fast-forwarding of the simulation without losing precision.

Theming

A custom theme.json will be used to maintain the project's visual identity:

Colors: Dark gray background (#282828), neon pink highlights (#FF00FF), and cyan accents (#00FFFF).

Fonts: Clean sans-serif with distinct sizes for headers and properties.

Benefits

Input Isolation: pygame-gui automatically prevents clicks on buttons from interacting with the physics world behind them.

UX Professionalism: Nested menus and standard file dialogs.

Efficiency: Removes manual collision math for UI elements.