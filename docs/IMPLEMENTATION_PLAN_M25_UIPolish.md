# Implementation Plan: Milestone 25 - UI Polish & Scrollable Grid Palettes

## Overview

This implementation plan breaks Milestone 25 into sequential, low-risk phases to overhaul the UI layout while preserving existing gameplay behavior. The implementation is constrained by `docs/CONSTITUTION.md` Section 11, especially:

- Playable physics area must be tightly framed by UI boundaries.
- UI input must be processed before world input.
- Palette content must remain data-driven from `config/entities.yaml`.
- Input focus behavior for text inputs must not regress.

## Implementation Strategy

- Implement foundational UI container behavior first (`UIScrollPanel`), then migrate layout responsibilities in `main.py`.
- Recompute canvas geometry and physics boundaries only after panel roles are stable.
- Move dynamic entity population to a deterministic 3-column scrollable grid.
- Refactor top bar grouping last to reduce merge risk with panel changes.
- Validate each phase manually before moving to the next.

---

## Phase 1: UIScrollPanel Component

### Objective
Create a reusable scrollable UI container in `utils/ui_manager.py` that supports wheel scrolling, click-coordinate translation for children, and clipped rendering.

### Files
- Modify: `utils/ui_manager.py`

### Tasks

1. Add a new `UIScrollPanel` class inheriting from `UIPanel` or `UIElement`.
2. Add required state fields:
- `content_height`
- `scroll_y`
- optional scroll tuning fields such as `scroll_speed`
3. Add child-management support if not already available in the parent abstraction:
- add/remove child element hooks
- local-to-screen transform expectations
4. Implement wheel input behavior:
- Handle `pygame.MOUSEWHEEL` only when cursor is over the panel rect.
- Update `scroll_y` by wheel delta scaled by scroll speed.
- Clamp `scroll_y` to valid range:
- max `0`
- min `min(0, panel_height - content_height)`
5. Implement event forwarding for children with scroll compensation:
- For mouse click/hit testing, offset child interaction coordinates by `scroll_y` so visual position and clickable region match.
6. Implement clipped rendering:
- Before drawing children, capture current clip state.
- Apply `pygame.Surface.set_clip(self.rect)` to mask draw output.
- Draw children using scroll-transformed Y positions.
- Restore prior clip state after drawing.
7. Ensure panel does not break existing `UIManager` event routing or draw order.

### Pygame / Technical Constraints

- Must use `pygame.MOUSEWHEEL` for scroll updates.
- Must use `pygame.Surface.set_clip(...)` to guarantee children do not draw outside panel bounds.
- Event coordinates passed to children must account for current `scroll_y`.

### Manual Verification

- Hover over scroll panel and use mouse wheel: content moves up/down.
- Content cannot scroll past top or beyond final item (clamping works).
- Buttons near edges disappear cleanly when out of bounds.
- Clicking visible buttons still triggers correct callback while scrolled.

---

## Phase 2: Panel Reallocation & Inspector Setup

### Objective
Reassign panel responsibilities so the right panel owns all palette spawning UI and the left panel is Inspector-only.

### Files
- Modify: `main.py`
- (Read-only reference): `config/entities.yaml`

### Tasks

1. Expand right panel width constant/value to target 300-320 px.
2. Remove any logic that creates object spawn buttons in the left panel.
3. Keep left panel permanently reserved for Inspector/Properties content from M14.
4. Ensure Inspector rendering rules:
- Show property editor when an entity is selected.
- Show neutral placeholder/empty state when nothing is selected.
- Never show palette spawn controls in the left panel.
5. Ensure all dynamic palette button creation references right-panel container only.
6. Verify UIManager registration order still renders panel chrome and children correctly.

### Pygame / Technical Constraints

- Preserve existing UI-first input processing to avoid world interactions through UI.
- Do not regress focus handling for `UITextInput` / `UITextArea` (Section 11 input focus rule).

### Manual Verification

- Launch editor mode and confirm left panel has no spawn buttons.
- Select an entity and confirm Inspector data appears in left panel.
- Deselect and confirm Inspector empty/placeholder state returns.
- Confirm right panel is visibly wider and ready for multi-column content.

---

## Phase 3: Playable Area & Physics Boundaries

### Objective
Recompute central playable area from panel geometry and align static Pymunk boundaries to that recalculated rectangle.

### Files
- Modify: `main.py`

### Tasks

1. Recalculate `playable_rect` from UI panel geometry:
- left edge = `left_panel.right`
- right edge = `right_panel.left`
- top edge = `top_panel.bottom`
- bottom edge = `bottom_panel.top`
2. Replace any hardcoded playable bounds with geometry-derived values.
3. Update static boundary creation logic (floor, ceiling, left wall, right wall) to match the new playable rectangle exactly.
4. Ensure boundary rebuild/reposition occurs during initialization and any layout rebuild paths.
5. Verify no physics body can move behind side/top/bottom UI frames.
6. Keep world simulation behavior unchanged except boundary placement.

### Pygame / Technical Constraints

- Boundary lines/shapes must tightly frame `playable_rect` with no visual or collision gap.
- Maintain existing physics update loop; only wall geometry should move.

### Manual Verification

- Spawn objects near each edge of playable area and run simulation.
- Confirm collisions occur at inner frame edges, not behind UI panels.
- Confirm no object can be dragged or launched into hidden UI-covered regions.

---

## Phase 4: 3-Column Grid Population in UIScrollPanel

### Objective
Populate right-panel entity palette into a scrollable 3-column grid using deterministic index math.

### Files
- Modify: `main.py`
- Modify (if required for child API): `utils/ui_manager.py`

### Tasks

1. Instantiate `UIScrollPanel` inside the right panel content region.
2. Define right-panel inner layout metrics:
- panel padding
- button width/height
- horizontal gap (`gap_x`)
- vertical gap (`gap_y`)
3. Generate entity buttons dynamically from variants list (data-driven).
4. Apply required 3-column index math for each button:
- `col = index % 3`
- `row = index // 3`
5. Compute per-button position from row/col and spacing metrics.
6. Add generated buttons as children of `UIScrollPanel`, not as free-floating UI elements.
7. Compute final `content_height` from row count and vertical spacing.
8. Ensure scroll panel receives wheel events before world-side wheel behaviors when hovered.
9. Ensure icon generation remains auto-derived (no hardcoded static sprite sheet assumptions).
10. Validate deterministic ordering so rebuilds do not reshuffle button locations unexpectedly.

### Pygame / Technical Constraints

- Maintain wheel-event routing priority for hovered scroll panel.
- Child click hit testing must remain accurate at non-zero `scroll_y`.
- Clipping must prevent draw overlap into top/bottom bars.

### Manual Verification

- Confirm all palette buttons are in right panel only.
- Confirm exactly 3 columns are visible with stable spacing.
- Scroll with wheel while hovering right panel: content scrolls and masks cleanly.
- Click multiple buttons at different scroll positions: correct entity selection/spawn tool activates.
- Use wheel outside right panel: world-side wheel behavior remains unchanged.

---

## Phase 5: Top Bar Regrouping

### Objective
Refactor top bar button layout into functional clusters with explicit anchor zones: left, center, right.

### Files
- Modify: `main.py`

### Tasks

1. Replace uniform/sequential top-bar placement with cluster-based placement strategy.
2. Define left cluster (`Play`, `Edit`, `Clear`) anchored from left margin.
3. Define center cluster (`Q.Save`, `Q.Load`, `Save`, `Load`) centered around screen midpoint.
4. Define right cluster (`Challenges`, `Help`, `Level Settings`) anchored from right margin inward.
5. Apply explicit intra-cluster spacing and inter-cluster separation.
6. Ensure button widths and labels do not overlap at supported window size.
7. Keep existing callbacks and stub behaviors intact.
8. Verify visual state indicators (mode/edit highlights) still render and align.

### Pygame / Technical Constraints

- Placement must remain stable on resize or layout recalculation.
- No button should drift into side panel regions.

### Manual Verification

- Confirm top controls appear in three visual groups (left/center/right).
- Verify all buttons remain clickable and trigger correct behavior.
- Verify placeholder buttons still fail gracefully via log messages.

---

## Integration Validation Checklist

After all phases are complete, verify end-to-end behavior:

1. Left panel is Inspector-only; right panel is palette-only.
2. Right panel palette scrolls with proper clipping and click accuracy.
3. 3-column grid math is correct and deterministic.
4. `playable_rect` and Pymunk boundaries match new panel geometry.
5. UI input is processed before world input, including wheel-over-panel behavior.
6. Text input focus still suppresses global hotkeys per Constitution Section 11.
7. No regressions in spawning, selecting, property editing, or simulation transitions.

---

## Rollback / Debug Notes

- If buttons draw over bars, inspect clip lifecycle (`set_clip` restore path).
- If clicks miss while scrolled, inspect child hit-test coordinate transform with `scroll_y`.
- If wheel scroll also rotates world objects while hovering panel, adjust event routing priority in UI manager/main loop.
- If bodies appear behind UI, verify boundary coordinates are derived from current `playable_rect` edges.

---

## Definition of Done

Milestone 25 UI Polish is complete when:

- The dual-sidebar spawning pattern is fully removed.
- The right panel hosts a scrollable, clipped, dynamic 3-column palette.
- The left panel is dedicated to Inspector/Properties behavior.
- Playable area and physics boundaries are tightly aligned to the new central canvas.
- Top bar controls are clustered by function with clear visual grouping.
- All manual verification checks pass without regressions.
