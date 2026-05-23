# 00 - Current status v3

Stand: 2026-05-23

## Observed repository state

The repository has progressed from the first MVP to a more modular structure:

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
knowledge/
AGENTS.md
```

The route_v2 prompt has been implemented in a useful but still manual way. The current route planner collects values such as distance, average speed, net elevation gain, detailed gain/loss, stops, dwell time, wind and temperature. That is good for an expert calculator, but not yet the expected end-user experience.

## What already works well

- Core route energy calculations exist in `app/core/route_energy.py`.
- Route segments include distance, speed, elevation gain/loss, stops, dwell time, wind, payload and aux override.
- Commute scenarios support one-way and return-trip modes.
- The return route swaps elevation gain/loss and can invert wind.
- UI refactoring has moved reusable state, charts and tables out of a single monolithic file.
- `pyproject.toml` currently uses a lean dependency set: NiceGUI, Plotly, Pydantic, Pandas, PyYAML and Kaleido, plus dev tools.

## Main gap

The app currently asks users to manually provide route-derived values. The next version should derive these values from a real route:

```text
start address + destination address
  -> geocoding
  -> routing polyline
  -> elevation profile
  -> segmentization
  -> physics calculation
  -> map + elevation/speed/energy charts
```

## Product decision

Keep two route modes:

1. `Map Route Planner` - default end-user feature.
2. `Manual Route / Expert Planner` - existing calculator, retained as fallback and for debugging.

## Non-goals for the next iteration

- Do not implement live traffic prediction.
- Do not require Google Maps APIs.
- Do not require a paid provider for the app to start.
- Do not build complex map matching for arbitrary GPS tracks yet.
- Do not scrape routing or map websites.
