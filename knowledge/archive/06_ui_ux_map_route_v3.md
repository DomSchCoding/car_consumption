# 06 - UI/UX map route v3

## UI goal

The route feature should look and feel like a route planner, not a physics form.

## Recommended layout

```text
+--------------------------------------------------------------+
| Header: Route Planner                                        |
+--------------------------+-----------------------------------+
| Left control panel       | Map                               |
| - start input            | - route polyline                  |
| - destination input      | - start/end markers               |
| - route button           | - optional click-to-set markers    |
| - return trip toggle     |                                   |
| - provider status        |                                   |
+--------------------------+-----------------------------------+
| Route summary cards                                          |
+--------------------------------------------------------------+
| Elevation profile | Speed profile | Energy stacked bars       |
+--------------------------------------------------------------+
| Vehicle comparison table                                     |
+--------------------------------------------------------------+
```

## NiceGUI map implementation

Use `ui.leaflet` for the initial map UI. Keep map-related helper functions in `app/ui/components/map_widget.py`.

MVP map helpers:

```python
def create_route_map(center: tuple[float, float], zoom: int): ...
def draw_route_polyline(map_element, points): ...
def set_start_end_markers(map_element, start, destination): ...
def fit_bounds(map_element, points): ...
```

If `ui.leaflet` does not expose a direct Python method for some operation, use `run_method` or JavaScript bridge carefully and wrap it in one helper module. Do not scatter raw JavaScript across pages.

## Address UX

MVP:

- two text fields
- explicit `Geocode` or `Calculate route` button
- show first candidate automatically if unambiguous
- if multiple candidates, show dropdown selection

Future:

- autocomplete while typing
- recent/favorite routes
- click map to set start/end
- draggable markers
- via points

## Charts

Add route-specific charts:

1. Elevation vs distance.
2. Speed vs distance.
3. Stacked energy breakdown per selected vehicle.
4. Outward vs return comparison if return trip is enabled.

Do not overload the map with all information. Keep the map focused on spatial context.

## Manual route mode

The existing manual route planner remains useful. Rename visually:

```text
Manual / Expert Route Calculator
```

Expose it from the map route page:

```text
Need exact control or no API? Open manual route calculator.
```

## User-facing wording

Use plain wording:

- "Route aus Karte berechnen"
- "Hoehenprofil automatisch ermitteln"
- "Rueckweg mit umgekehrtem Hoehenprofil"
- "Geschwindigkeit aus Routendauer geschaetzt"
- "Rekuperation bergab"
- "Stop-and-go geschaetzt"

Avoid making provider-derived values look exact.

## UI acceptance criteria

- Map renders on route page.
- User can enter start/destination and see a route line.
- The app can show a demo route without external API config.
- Provider/cache/warning status is visible.
- Results update when selected vehicles or environmental parameters change without re-fetching the route.
