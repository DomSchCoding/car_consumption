# 00 - Project State

*Stand: 2026-05-23*

## Repository structure

```text
app/
  core/
    physics.py
    route_energy.py
    route_geometry.py
    route_segmentizer.py
  data/
    models.py
    repository.py
  services/
    __init__.py
    provider_models.py
    route_cache.py
    routing.py
  ui/
    charts.py
    state.py
    tables.py
    components/
      __init__.py
      vehicle_selector.py
      map_widget.py
      route_controls.py
      route_summary.py
    pages/
      __init__.py
      route_planner.py
      map_route_planner.py
  main.py
  tests/
    test_physics.py
    test_repository.py
    test_route_energy.py
    test_ui_smoke.py
    test_provider_models.py
    test_route_cache.py
    test_route_geometry.py
    test_route_segmentizer.py
    test_map_route_smoke.py
    fixtures/routes/
      demo_city_commute.json
      demo_hilly_commute.json
      demo_highway_route.json
  assets/
    sample_vehicles.yaml
    fuel_constants.yaml
knowledge/
  current/
    00_project_state.md
    01_product_vision.md
    02_architecture.md
    03_physics_model.md
    04_route_map_feature.md
    05_ui_ux.md
    06_testing_strategy.md
    07_roadmap.md
  archive/
AGENTS.md
```

## What works

- Core physics calculations in `app/core/physics.py`
- Route energy calculations with segments, elevation, stops, wind, payload in `app/core/route_energy.py`
- Route geometry helpers (haversine, elevation gain/loss, resampling) in `app/core/route_geometry.py`
- Route segmentizer (provider route to RouteSegments) in `app/core/route_segmentizer.py`
- Commute scenarios: one-way and return-trip modes
- Return route swaps elevation gain/loss and can invert wind
- Vehicle data loading from YAML via `app/data/repository.py`
- Pydantic models for Vehicle, Route, RouteSegment, CommuteScenario, PhysicsParams
- Provider models (GeoPoint, ProviderRoute, RouteRequest) in `app/services/provider_models.py`
- Route cache (file-based, `.cache/routes/`) in `app/services/route_cache.py`
- Demo routing provider (offline, deterministic) in `app/services/routing.py`
- NiceGUI dashboard with vehicle comparison, consumption curves, and ranking
- Manual route planner page at `/route/manual` with segment editor
- Map route planner page at `/route` with demo provider, map, and energy comparison
- Chart export to PNG
- Dark mode
- ICE comparison (chemical vs wheel energy)

## Main gap

The map route planner MVP (Phase B) is complete with a demo/offline provider. The next step is integrating a real routing provider (ORS) for live routes with geocoding.

```text
start address + destination address
  -> geocoding (demo only, no real geocoder yet)
  -> routing polyline (demo provider)
  -> elevation profile (demo geometry)
  -> segmentization (implemented)
  -> physics calculation (implemented)
  -> map + elevation/speed/energy charts (implemented)
```

## Two route modes

1. **Map Route Planner** - default at `/route` (demo provider, fully functional offline)
2. **Manual Route / Expert Planner** - at `/route/manual` (existing calculator, fallback and debug tool)

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