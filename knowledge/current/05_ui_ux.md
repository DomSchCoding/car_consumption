# 05 - UI/UX

## Design principles

1. Result first, then details
2. Every number has a unit
3. Every assumption is visible
4. Every component can be expanded
5. Demo/uncertain data clearly marked
6. Charts show comparison and cause
7. UI never calculates physics directly

## Page structure

### Dashboard `/`

- vehicle comparison curves
- consumption at multiple speeds
- ranking by consumption or range
- vehicle selection with EV/ICE filter
- expandable physics settings
- expandable physics formulas reference

### Map Route Planner `/route` (new, default)

```text
+--------------------------------------------------------------+
| Header: Route Planner                                        |
+--------------------------+-----------------------------------+
| Left control panel       | Map (Leaflet)                     |
| - start input            | - route polyline                  |
| - destination input      | - start/end markers               |
| - route button           |                                   |
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

### Manual Route Planner `/route/manual` (existing, expert mode)

- segment editor
- direct parameter entry
- manual elevation, speed, stops
- link: "Need exact control or no API? Open manual route calculator."

### Vehicle Detail `/vehicle/{vid}`

- single vehicle specs
- source references
- confidence badges

## Route result cards

```text
Distance: 23.4 km
Duration: 31 min
Average speed: 45 km/h
Elevation gain/loss: +280 m / -120 m
Return mode: one-way / there-and-back
Provider: ORS, cache hit/miss
Data quality: speed estimated, elevation sampled every X m
```

## Charts for route results

1. Elevation vs distance
2. Speed vs distance
3. Stacked energy breakdown per selected vehicle
4. Outward vs return comparison if return trip

Keep the map focused on spatial context. Do not overload the map with all data.

## Address UX

MVP:

- two text fields for start and destination
- explicit "Calculate route" button
- auto-select first candidate if unambiguous
- dropdown if multiple candidates

Future:

- autocomplete while typing
- recent/favorite routes
- click map to set start/end
- draggable markers

## User-facing wording

Use plain, honest wording:

- "Route aus Karte berechnen"
- "Hoehenprofil automatisch ermitteln"
- "Rueckweg mit umgekehrtem Hoehenprofil"
- "Geschwindigkeit aus Routendauer geschaetzt"
- "Rekuperation bergab"
- "Stop-and-go geschaetzt"

Never make provider-derived values look exact.

## Progressive disclosure

Defaults are simple. Advanced parameters are expandable:

- air density, tire class, drivetrain/regen efficiency
- segmentization resolution
- provider selection
- force refresh / cache

## Dark mode

Already supported via CSS class toggle on `body.dark`.