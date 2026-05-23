# AGENTS.md - car_consumption

Stand: 2026-05-23

## Project overview

Physics-based vehicle consumption analyzer with two route modes:

- **Manual Route (v2)** — expert mode with direct parameter input (`/route/manual`)
- **Map Route (v3)** — Google-Maps-like UX with demo + live providers (`/route`)

## Route transition state

**Current state:**

- `/route` points to the map route planner (demo + live)
- `/route/manual` is the stable path for the manual/expert route planner
- The map route planner supports both demo and live (Nominatim+OSRM+Open-Meteo) modes
- Live providers are disabled by default; enable via env variables

**Live provider env variables:**

```text
CAR_CONSUMPTION_ENABLE_LIVE_ROUTING=false
CAR_CONSUMPTION_ENABLE_NOMINATIM=false
CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM=false
CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION=false
CAR_CONSUMPTION_USER_AGENT=car_consumption_private_dev/0.1
CAR_CONSUMPTION_OSRM_BASE_URL=https://router.project-osrm.org
CAR_CONSUMPTION_OPEN_METEO_ELEVATION_URL=https://api.open-meteo.com/v1/elevation
```

## Knowledge base

Only `knowledge/current/` is authoritative. `knowledge/archive/` is historical context only.

```text
knowledge/current/00_project_state.md    repository structure, what works, gaps, tech stack
knowledge/current/01_product_vision.md   users, principles, two route concepts, energy output
knowledge/current/02_architecture.md      layering, modules, dependencies, page routing
knowledge/current/03_physics_model.md     formulas, elevation, stops, regen, return trip
knowledge/current/04_route_map_feature.md user flow, providers, data model, caching, map, security
knowledge/current/05_ui_ux.md            pages, layouts, charts, wording, progressive disclosure
knowledge/current/06_testing_strategy.md  test layers, fixtures, regression, DoD
knowledge/current/07_roadmap.md          phases A-G and prioritized implementation order
```

## Mandatory agent principles

1. Core first: route/geocoding/elevation/provider logic must be implemented outside
   UI modules.
2. No network calls in unit tests. Use fixtures and mock providers.
3. Keep the existing manual route planner working while adding the map route planner.
4. API keys must never be hard-coded. Use environment variables and visible provider
   status.
5. Implement provider abstraction before deeply integrating any single API.
6. Cache external route/elevation responses to reduce quota usage and to make debugging
   reproducible.
7. Distinguish route geometry, route metadata, speed profile, elevation profile and
   physical energy calculation.
8. Do not pretend precision: provider-derived speed and elevation are estimates unless
   sourced from detailed route annotations.
9. Preserve one-way vs return-trip handling. Return route is not simply 2x outward if
   elevation, wind or route asymmetry are involved.
10. Every new route model or formula needs tests.

## Definition of Done

A task is complete only if:

- app still starts with `python -m app.main`
- existing manual route planner still works
- new map route page has a working offline/demo provider
- live provider integration is optional and guarded by env config
- route results are cached
- tests cover provider parsing, caching, segmentization and energy calculation
- `pytest`, `ruff check`, and `ruff format --check` have been run
- no API key or personal location is committed
- README and knowledge files are updated