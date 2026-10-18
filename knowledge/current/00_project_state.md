# 00 - Project State

*Stand: 2026-10-18*

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
    provider_config.py         env-based feature flags for live providers
    route_cache.py
    routing.py                  DemoRoutingProvider + route_live()
    geocoding.py                Nominatim geocoding (rate-limited, cached)
    osrm_routing.py             OSRM routing provider (cached, parsing)
    elevation.py                Open-Meteo elevation (rate-limited, cached, resampling)
  ui/
    charts.py
    state.py
    tables.py                HTML detail cards, SPEED_OPTIONS, IMAGES_DIR
    layout.py                Shared page layout (top nav, title, dark-mode)
    theme.py                 Central CSS tokens, light/dark palette
    nicegui_tables.py        Native NiceGUI table/ranking renderers
    components/
      __init__.py
      vehicle_selector.py    Reusable vehicle selection + filter helpers
      map_widget.py             NiceGUI Leaflet wrapper (Python layer API)
      route_controls.py
      route_summary.py
      route_results.py       Map-route energy results (tabs, responsive)
    pages/
      __init__.py
      route_planner.py          manual/expert route planner (/route/manual)
      map_route_planner.py      map route planner (/route) with demo + live mode
  main.py
  tests/
    test_physics.py
    test_repository.py
    test_route_energy.py
    test_ui_smoke.py
    test_provider_models.py
    test_provider_config.py     env flag tests
    test_route_cache.py
    test_route_geometry.py
    test_route_segmentizer.py
    test_map_route_smoke.py
    test_live_providers.py      OSRM parsing, geocoding cache, elevation, disabled providers
    fixtures/
      routes/
        demo_city_commute.json
        demo_hilly_commute.json
        demo_highway_route.json
      geocode/
        nominatim_landstrasse.json
        nominatim_eidenberg.json
      osrm/
        osrm_landstrasse_eidenberg.json
        osrm_no_route.json
      elevation/
        open_meteo_landstrasse_eidenberg.json
  assets/
    sample_vehicles.yaml
    fuel_constants.yaml
    vehicles/                     per-brand vehicle YAMLs (24 files, 131 vehicles)
    images/                       vehicle images (~94 jpg)
  .cache/
    routes/                     cached provider route responses (gitignored)
    geocode/                    cached geocoding responses (gitignored)
    elevation/                  cached elevation responses (gitignored)
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
- Provider config (env-based feature flags) in `app/services/provider_config.py`
- Route cache (file-based, `.cache/routes/`) in `app/services/route_cache.py`
- Demo routing provider (offline, deterministic) in `app/services/routing.py`
- Nominatim geocoding (rate-limited to 1 req/s, cached) in `app/services/geocoding.py`
- OSRM routing provider (cached, parsing) in `app/services/osrm_routing.py`
- Open-Meteo elevation (rate-limited, cached, resampling) in `app/services/elevation.py`
- Live route chain: geocode → OSRM route → elevation enrichment in `app/services/routing.py`
- NiceGUI dashboard with tabs: Compare, Table (rotated: vehicles as columns, mobile-friendly), Ranking, Settings
- Fleet ranking with collapsible filters (weight, length, ground clearance, drivetrain, price, trunk volume; AND logic)
- Ranking entries link to `/vehicle/{vid}`; detail page has "Back to Ranking" link
- Shared page layout + central theme (light/dark) used by all pages
- 131 vehicles in 24 brand YAMLs (`app/assets/vehicles/`) plus `sample_vehicles.yaml`; 94 vehicle images
- Manual route planner page at `/route/manual` with segment editor
- Map route planner page at `/route` with demo + live provider selector
- NiceGUI Leaflet map with polyline, markers, fit-bounds (Python layer API)
- Chart export to PNG
- Dark mode
- ICE comparison (chemical vs wheel energy)

## Live provider pipeline (when enabled)

```text
start address + destination address
  -> geocoding (Nominatim, rate-limited, cached)
  -> routing polyline (OSRM, cached)
  -> elevation profile (Open-Meteo, resampled to ~1km, cached, capped at 50 pts)
  -> segmentization (implemented)
  -> physics calculation (implemented)
  -> map + elevation/speed/energy charts (implemented)
```

## Two route modes

1. **Map Route Planner** - default at `/route` (demo + live providers)
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
geopy >= 2.4     (Nominatim geocoding)
httpx >= 0.27    (HTTP client for OSRM + Open-Meteo)
pytest           (testing)
ruff             (lint/format)
pyright          (type checking)
```

## Quality gates

```bash
pytest
ruff check app/
ruff format app/
pyright app/
```