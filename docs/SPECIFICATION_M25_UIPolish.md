# Specification: Milestone 25 - UI Polish & Scrollable Grid Palettes

## 1. Overview

Milestone 25 redesigns the editing interface to improve usability, visual clarity, and scalability as the entity catalog grows. The current dual-sidebar spawning model is replaced by a consolidated, scrollable, multi-column palette on the right side, while the left side becomes a dedicated Inspector/Property Editor workspace.

This milestone focuses on UI architecture and interaction behavior, not gameplay logic changes. The goal is to maximize central canvas space, reduce palette clutter, and ensure precise, predictable panel behavior under scrolling and dynamic content growth.

## 2. Goals

- Consolidate all entity spawning controls into a single Right Panel palette.
- Increase Right Panel width to comfortably support a 3-column button grid.
- Convert Left Panel into a dedicated Inspector/Properties panel only.
- Recalculate the central playable canvas to fit tightly between both side panels.
- Rebuild physics boundaries to align with the resized playable area.
- Introduce a reusable `UIScrollPanel` component with clipping-safe rendering and wheel scrolling.
- Arrange dynamic palette entries using deterministic 3-column grid math.
- Regroup top-bar controls into clear visual clusters (left/center/right).

## 3. Technical Implementation Details

### 3.1 Panel Role Consolidation

#### Right Panel (Palette)
- The Right Panel is the sole location for object/entity spawning controls.
- All dynamically generated entity buttons must render inside the Right Panel.
- Right Panel width must be expanded from prior values to a new target range of 300-320 px.
- The Right Panel must host a scrollable container to support overflow.

#### Left Panel (Inspector)
- The Left Panel must no longer contain object spawning buttons.
- The Left Panel is permanently designated as the Inspector/Property Editor region established in M14.
- Inspector content appears only when an instance is selected on the canvas.
- When no object is selected, the panel may show placeholder text/state but must remain spawn-free.

### 3.2 Playable Area Recalculation and Boundary Alignment

The playable area must be recalculated strictly from panel geometry each frame (or each layout rebuild):

- `playable_left = left_panel_rect.right`
- `playable_right = right_panel_rect.left`
- `playable_top = top_panel_rect.bottom`
- `playable_bottom = bottom_panel_rect.top`
- `playable_width = playable_right - playable_left`
- `playable_height = playable_bottom - playable_top`

`playable_rect` must be defined from those exact edges.

#### Boundary Rule
- Pymunk static walls (left, right, floor, ceiling) must be rebuilt/repositioned to tightly frame the recalculated `playable_rect`.
- There must be no gap where bodies can enter behind UI panels.
- There must be no overlap where walls clip into UI surfaces.

### 3.3 UIScrollPanel Component (`utils/ui_manager.py`)

A new `UIScrollPanel` UI component must be introduced as a reusable container for vertically overflowing content.

#### Inheritance
- `UIScrollPanel` must inherit from `UIPanel` or `UIElement`.

#### Required State
- `content_height`: total scrollable content extent in panel-local coordinates.
- `scroll_y`: current vertical scroll offset.

#### Input Handling
- Wheel input is active only when the cursor is hovering over the scroll panel rect.
- On `pygame.MOUSEWHEEL`, update `scroll_y` based on wheel delta and scroll speed.
- Clamp `scroll_y` to valid bounds:
  - Upper bound: `0`
  - Lower bound: `min_scroll = min(0, panel_height - content_height)`
- Child hit testing/click dispatch must be transformed by scroll offset so visual and clickable positions remain aligned.

#### Rendering and Clipping
- Use clipping to constrain child rendering to panel bounds:
  - Apply `pygame.Surface.set_clip(self.rect)` before drawing children.
  - Restore previous clip after draw pass.
- Any child visually outside panel bounds must be masked out and must not overlap Top/Bottom bars or adjacent UI.

### 3.4 Dynamic 3-Column Grid Layout Algorithm

Entity spawn buttons inside the Right Panel scroll content must use deterministic 3-column layout math:

- `col = index % 3`
- `row = index // 3`

Button local position uses:
- Horizontal: `x = inner_left + col * (button_width + gap_x)`
- Vertical: `y = inner_top + row * (button_height + gap_y)`

#### Layout Constraints
- Grid must respect panel inner padding on all sides.
- Button size and horizontal gap must be chosen so exactly 3 columns fit within the expanded panel width.
- `content_height` must be derived from final row count and vertical spacing.
- Dynamic rebuilds must preserve deterministic ordering of entities.

### 3.5 Top Bar Regrouping

Top bar buttons must be intentionally clustered by function, not uniformly distributed.

#### Left-Aligned Cluster (Modes)
- `Play`, `Edit`, `Clear`

#### Center-Aligned Cluster (File Operations)
- `Q.Save`, `Q.Load`, `Save`, `Load`

#### Right-Aligned Cluster (Meta)
- `Challenges`, `Help`, `Level Settings`

#### Positioning Rule
- Each cluster must use explicit X-offset anchoring and intra-cluster spacing.
- Center cluster is anchored around screen midpoint.
- Right cluster is anchored to right margin with inward placement.
- Cluster spacing must remain stable across window size changes.

### 3.6 Interaction and Event Routing Expectations

- UI hit testing must occur before world interaction logic.
- Scroll wheel events over the Right Panel scroll region must scroll the palette, not rotate/place world entities.
- Inspector interactions must remain isolated from palette interactions.
- Selection state drives Inspector content only; it does not alter palette container behavior.

### 3.7 Visual and UX Consistency

- The UI layout must communicate clear role separation:
  - Left: inspect/edit selected instance
  - Center: world canvas
  - Right: spawn palette
- Scrolling behavior must feel bounded and predictable (no elastic overscroll).
- Clipping must guarantee clean, professional panel boundaries under heavy content.

## 4. Acceptance Criteria

- All spawnable entity buttons appear only in the Right Panel.
- Right Panel width is increased and can visually host a 3-column grid without overlap.
- Left Panel contains no spawning controls and functions strictly as Inspector/Properties.
- `playable_rect` is recalculated from panel edges and remains centered between sidebars.
- Pymunk static boundaries match the new playable area and prevent bodies from entering behind UI.
- `UIScrollPanel` tracks `content_height` and `scroll_y`, supports hover-wheel scrolling, and clamps correctly.
- Child clicks inside the scroll panel map correctly with scroll offset applied.
- Clipping masks out-of-bounds palette buttons so they never draw across top/bottom bars.
- Grid placement uses `col = index % 3` and `row = index // 3` with consistent padding/gaps.
- Top bar controls are visibly grouped into three functional clusters: left, center, right.
- Wheel scrolling over palette region scrolls UI content rather than triggering world-side actions.

## 5. Out of Scope

- No changes to simulation physics behavior beyond boundary repositioning to match layout.
- No new entity types or gameplay mechanics.
- No persistence format changes required for this milestone.
