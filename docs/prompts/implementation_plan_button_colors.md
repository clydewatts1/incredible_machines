# Implementation Plan - Dynamic UI Button Colors

The goal is to provide visual feedback for the active simulation state (Play, Pause, Stop, Fast, Slow) by changing the background color of the corresponding control buttons.

## User Review Required

> [!NOTE]
> I will be adding new `object_id`s to [theme.json](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/theme.json) to support these color changes.
> The logic will trigger a rebuild of the top panel whenever the transport state changes (which is already handled in [main.py](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/main.py)).

## Proposed Changes

### [UI Theme]

#### [MODIFY] [theme.json](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/theme.json)
- Add `#play_btn_active`, `#fast_btn_active`, `#slow_btn_active` with Green background (`#00FF00`).
- Add `#stop_btn_active` with Red background (`#FF0000`).
- Add `#pause_btn_active` with Orange background (`#FFA500`).
- Ensure `normal_text` is black for these statuses.

### [UI Logic]

#### [MODIFY] [utils/editor_ui.py](file:///c:/Users/cw171001/OneDrive - Teradata/Documents/GitHub/incredible_machines/utils/editor_ui.py)
- Update [rebuild_top_panel](file:///c:/Users/cw171001/OneDrive%20-%20Teradata/Documents/GitHub/incredible_machines/utils/editor_ui.py#212-303) to determine the correct `object_id` for each transport button based on `self.game_state["mode"]` and `self.game_state["speed_multiplier"]`.
- Ensure the speed buttons reset to `#transport_btn` when speed is 1.0.

## Verification Plan

### Automated Tests
- N/A (Visual UI change)

### Manual Verification
1. Launch the application: `python main.py`.
2. Observe the **Stop** button (■): It should be **RED** by default in EDIT mode.
3. Click **Play** (▶): The Play button should turn **GREEN**, and the Stop button should return to grey.
4. Click **Pause** (⏸): The Pause button should turn **ORANGE**.
5. Click **Fast** (>>): The Fast button should turn **GREEN**.
6. Click **Slow** (<<): The Slow button should turn **GREEN**.
7. Click **Stop** (■): The Stop button should turn **RED**, and others should reset.
