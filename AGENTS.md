# AGENTS.md - car_consumption

Stand: 2026-05-23

## Project overview

Physics-based vehicle consumption analyzer with two route modes:

- **Manual Route (v2)** — expert mode with direct parameter input (already implemented)
- **Map Route (v3)** — Google-Maps-like UX (to be built)

## Route transition state

**Current state:**

- `/route` points to the existing manual/expert route planner
- `/route/manual` does not yet exist as a stable alias
- The map route planner has not been built yet

**Transition plan:**

1. Add `/route/manual` as a stable path for the manual/expert route planner (Phase A)
2. Build the map route MVP with `/route/map` or a temporary path (Phase B)
3. Switch `/route` to the map route planner only after the map MVP works and all tests pass
4. Keep `/route/manual` permanently for expert/debug use

**Rule:** Do not break `/route` until the replacement is tested and working.

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
- real provider integration is optional and guarded by env config
- route results are cached
- tests cover provider parsing, caching, segmentization and energy calculation
- `pytest`, `ruff check`, and `ruff format --check` have been run
- no API key or personal location is committed
- README and knowledge files are updated