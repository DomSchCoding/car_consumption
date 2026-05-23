# 00 - Project State

*Stand: 2026-05-23*

## Repository structure

```text
app/
  core/
    physics.py
    route_energy.py
  data/
    models.py
    repository.py
  ui/
    charts.py
    state.py
    tables.py
    components/vehicle_selector.py
    pages/route_planner.py
  main.py
  tests/
    test_physics.py
    test_repository.py
    test_route_energy.py
    test_ui_smoke.py
  assets/
    sample_vehicles.yaml
    fuel_constants.yaml
knowledge/
AGENTS.md
```

## What works

- Core physics calculations in `app/core/physics.py`
- Route energy calculations with segments, elevation, stops, wind, payload in `app/core/route_energy.py`
- Commute scenarios: one-way and return-trip modes
- Return route swaps elevation gain/loss and can invert wind
- Vehicle data loading from YAML via `app/data/repository.py`
- Pydantic models for Vehicle, Route, RouteSegment, CommuteScenario, PhysicsParams
- NiceGUI dashboard with vehicle comparison, consumption curves, and ranking
- Manual route planner page at `/route` with segment editor
- Chart export to PNG
- Dark mode
- ICE comparison (chemical vs wheel energy)

## Main gap

The app currently requires manual route parameter input. The next product leap is a map-based route planner where the user enters addresses and the app derives distance, speed, elevation, and stops from a real route.

```text
start address + destination address
  -> geocoding
  -> routing polyline
  -> elevation profile
  -> segmentization
  -> physics calculation
  -> map + elevation/speed/energy charts
```

## Two route modes

1. **Map Route Planner** - default end-user feature (v3, to be built)
2. **Manual Route / Expert Planner** - existing calculator, retained as fallback and debug tool

## Non-goals for next iteration

- No live traffic prediction
- No Google Maps API dependency
- No paid provider required to start the app
- No complex map matching for arbitrary GPS tracks yet
- No web scraping of routing/map sites

## Tech stack

```text
Python 3.12+
NiceGUI >= 2.0  (web UI)
Plotly           (charts)
Pydantic >= 2    (models)
Pandas >= 2      (data)
PyYAML >= 6      (vehicle data)
Kaleido          (chart export)
pytest           (testing)
ruff             (lint/format)
pyright          (type checking)
```

Planned additions for map route feature: `httpx` (HTTP client), `polyline` (geometry decoding).

## Quality gates

```bash
pytest
ruff check app/
ruff format app/
pyright app/
```