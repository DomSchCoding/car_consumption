# UI Module - `app/main.py`

## NiceGUI 3.x Architectural Decisions

### Why native elements, not HTML+JS bridges

**Problem:** `ui.html().set_content()` renders HTML but cannot trigger Python callbacks directly.
Building JS→Python bridges (hidden inputs, `run_javascript` polling, WebSocket events)
proved unreliable in NiceGUI 3.x because:

1. **`ui.input.on_value_change`** only fires on user-initiated value changes, not programmatic
   `element.value = x; element.dispatchEvent(new Event('input'))` — Vue 3 ignores this.
2. **`ui.run_javascript`** with `await` in async button handlers works but requires a
   hidden button that JS must find and click — fragile DOM queries.
3. **`ui.on('custom_event', handler)`** requires correct WebSocket message format from
   client-side JS which is undocumented internals.

**Solution:** Use native NiceGUI interactive elements exclusively:
- `ui.select(multiple=True)` for model selection (handles multi-select + search natively)
- `ui.button(on_click=...)` for remove actions (pre-created, never deleted)
- `ui.button` for sort toggle (native click handling)

### Anti-pattern: `.clear()` + `with container:` rebuild

**Problem:** `container.clear()` enqueues deletions via `outbox.enqueue_delete()`
but new elements added immediately via `with container:` may render before
old elements are removed from the DOM. Race condition → duplicated elements.

**Solution:** Never use `.clear()` + rebuild. Instead:
- Pre-create all elements once, then show/hide them (selected list: 8 rows)
- Use `ui.select` which manages its own options via `.set_options()` (no clear needed)
- Use `ui.html()` for read-only content that only replaces, never adds interactive elements

## Purpose
NiceGUI web application that orchestrates vehicle selection, physics calculations, and visualization.

## Architecture
Single-page application with reactive updates. Modern card-based layout with gradient background.

## Dependencies
```
main.py
  -> core/physics.py: consumption_curve(), total_consumption()
  -> data/models.py: FuelConstants, FuelType, PhysicsParams, Vehicle, VehicleType
  -> data/repository.py: VehicleRepository, load_fuel_constants
  -> plotly.graph_objects: Figure, Scatter
  -> nicegui.ui: All UI components
```

## Global State
```python
REPO = VehicleRepository()         # Loaded once at startup
FUEL_CONST = load_fuel_constants() # Loaded once at startup
VEHICLE_COLORS = [...]             # 15-color palette for vehicles
```

## Helper Functions

### `make_vehicle_label(v: Vehicle) -> str`
Full display label: "Make Model Variant"

### `short_label(v: Vehicle) -> str`
Short label: "Model Variant" (for chips and buttons)

### `get_vehicles_by_make() -> dict[str, list[Vehicle]]`
Groups all vehicles by make, sorted alphabetically.

### `build_chart(...) -> go.Figure`
Creates a Plotly figure with:
- **EVs**: Single total consumption line per vehicle
  - Hover shows: 💨 Aero, 🛞 Roll, ⚡ Aux, 🔋 Total
- **ICE**: Two lines - wheel energy (solid) + chemical (dashed)
  - Hover shows: ⛽ Chemical, 🔧 Wheel, thermal efficiency
- Clean white theme, custom hover labels (dark background)
- One color per vehicle from VEHICLE_COLORS palette

### `build_table(...) -> str`
Creates HTML table with:
- Columns: Vehicle, Type, CdA, 50/80/100/130 km/h
- Alternating row backgrounds
- ICE shows estimated wheel energy with * footnote

## Page Layout (Sprint 2)

```
[Header: ⚡ Vehicle Consumption Analyzer]

[Row - 2 columns]
  [Col 1: Vehicle Selection Card]     [Col 2: Main Content]
  🚗 Vehicle Selection                [⚙️ Settings (expansion)]
  [EV ☑] [ICE ☐]                      [Parameters] [ICE] [Speed]
  [Make: ▼ BMW      ]
  ──────────────                      [Chart Area]
  + 3 Series
  + i4 ✓                              [📋 Consumption Table]
  + i5
  ──────────────                      [📊 Consumption Ranking]
  Selected                            [Speed: 100 km/h ▼] [EV ☑] [ICE ☐]
  3 Series           🗑️               [1. Hyundai Ioniq    ████ 12.5]
  i4                 🗑️               [2. Tesla Model 3    ████ 14.2]
  i5                 🗑️               [3. VW ID.3          █████ 16.8]
                                      [...                  ...    ... ]
```

## Key UI Components (Sprint 2)

| Component | Purpose |
|-----------|---------|
| `ui.expansion()` | Collapsible Settings menu |
| `ui.checkbox()` | EV/ICE filters (main + ranking) |
| `ui.select()` | Make dropdown, Speed dropdown |
| `ui.column()` (scrollable) | Model list, Selected vehicles |
| `ui.button()` | Add/remove vehicles |
| `🗑️` label + click | Remove vehicle from selection |

## Filter Logic
- Main EV/ICE checkboxes filter the make dropdown
- Makes without matching vehicle types are removed
- Model list shows only vehicles matching the filter
- Ranking list has its own EV/ICE checkboxes (synced from main)

## UI Components (NiceGUI 3.x API)

| Component | Usage | Notes |
|-----------|-------|-------|
| `ui.label()` | Text labels | No positional args |
| `ui.number(label, ...)` | Numeric inputs | label is first positional |
| `ui.button(text, on_click=)` | Action buttons | Use .style() for custom look |
| `ui.slider(min, max, ...)` | Range sliders | NO label param, use separate label |
| `ui.card()` | Container cards | .style() for CSS |
| `ui.row()` / `ui.column()` | Layout containers | Combine with .style() |
| `ui.plotly(fig)` | Plotly chart | .style() for sizing |
| `ui.html(html)` | Raw HTML | For table rendering |
| `ui.element("span")` | Inline elements | For vehicle chips |
| `ui.add_css()` | Global CSS | Call in page function |
| `ui.timer()` | Initial render | once=True |

## Important NiceGUI 3.x API Notes
- `ui.slider()` has NO label parameter - use separate `ui.label()` before it
- All slider params are keyword-only: `ui.slider(min=..., max=..., value=..., step=...)`
- `ui.number()` accepts label as first positional: `ui.number("Label", value=...)`
- `ui.select()` accepts options as first positional
- `ui.button()` with custom styling needs .style() after creation

## Reactive Update Pattern
```python
selected_ids: list[str] = []

def update() -> None:
    # 1. Read current values from all controls
    # 2. Build chart with build_chart()
    # 3. Clear chart_container, add new ui.plotly()
    # 4. Build table with build_table()
    # 5. Clear table_container, add new ui.html()

def update_chips() -> None:
    # Rebuild vehicle chip display
    # Colored chips with × remove button

def add_vehicle(vid) / remove_vehicle(vid):
    # Modify selected_ids, call update_chips() + update()

# Wire all controls to update()
control.on_value_change(lambda _: update())

# Initial render
ui.timer(0.1, update, once=True)
```

## CSS Styling
Global CSS via `ui.add_css()`:
- Gradient background
- Card border-radius and shadows
- Vehicle chip styling (colored, hover effect)
- Make header styling (uppercase, small)
- Add button hover states

## Port Configuration
```python
ui.run(title="Vehicle Consumption Analyzer", port=8080, reload=False)
```

## Entry Points
- Start: `python -m app.main`
- URL: http://localhost:8080
