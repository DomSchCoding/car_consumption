# 02 - Architecture

## Layering

```text
UI layer           NiceGUI pages and components, user interaction, map rendering
Service/provider   geocoding, routing, elevation, caching, external API adapters
Domain transform   route geometry, resampling, segmentization, speed/elevation derivation
Physics layer       energy breakdown using route_energy and physics functions
```

Rule: UI calls services, never httpx directly. Physics has no UI dependency.

```text
allowed:
  ui -> services -> core
  ui -> data
  services -> core
  services -> data
  data -> models

forbidden:
  core -> ui
  data -> ui
  physics.py -> repository.py
```

## Current modules

```text
app/core/physics.py          aero, roll, aux, drivetrain, fuel conversions
app/core/route_energy.py     segment energy, route energy, commute scenarios
app/data/models.py           Vehicle, Route, RouteSegment, CommuteScenario, PhysicsParams
app/data/repository.py       YAML loading, vehicle queries
app/ui/charts.py             Plotly chart construction
app/ui/tables.py             HTML table construction
app/ui/state.py              session state
app/ui/components/            reusable UI components
app/ui/pages/route_planner.py manual/expert route planner
app/main.py                  NiceGUI entry point, dashboard page, route page wrapper
```

## Target modules (additive, not replacing)

```text
app/services/
  __init__.py
  provider_models.py           shared provider DTOs (GeoPoint, ProviderRoute, etc.)
  geocoding.py                Geocoder protocol + implementations
  routing.py                  RoutingProvider protocol + implementations
  elevation.py                ElevationProvider protocol + implementations
  route_cache.py              file cache for provider responses

app/core/
  route_geometry.py           geometry helpers: haversine, cumulative distance, resampling
  route_segmentizer.py        converts route geometry into RouteSegment list
  route_energy.py             existing energy calculation (extend, don't rewrite)

app/ui/
  pages/route_planner.py      keep as manual/expert page
  pages/map_route_planner.py  new map-based route page
  components/map_widget.py   NiceGUI Leaflet wrapper helpers
  components/route_controls.py address inputs, provider selection, route options
  components/route_summary.py summary cards, provider status, warnings
```

## Page routing

```text
/                 dashboard (vehicle comparison)
/route            map route planner (new default)
/route/manual     manual/expert route planner (existing)
/vehicle/{vid}    vehicle detail page
```

During transition, `/route` continues pointing to the old page until the new page works; then switch.

## Provider status UI

```text
Provider: Demo / OpenRouteService / OSRM / Valhalla
Status: configured / missing key / cached / offline fallback
Cache: hit / miss
Warnings: elevation unavailable, speed estimated, route asymmetry not supported, etc.
```

## Dependency strategy

Current:

```toml
dependencies = [
  "nicegui>=2.0.0",
  "plotly>=5.0.0",
  "pydantic>=2.0.0",
  "pandas>=2.0.0",
  "pyyaml>=6.0",
  "kaleido>=0.1.0",
]
```

Planned additions:

```toml
"httpx>=0.27.0",       # HTTP client for provider APIs
"polyline>=2.0.0",    # decode OSRM/Valhalla route geometry
```

Optional later:

```toml
"python-dotenv>=1.0.0"       # convenient local env loading
"openrouteservice>=2.3.3"    # optional wrapper if simpler than direct httpx
```

Rationale: httpx keeps providers explicit and testable. polyline helps decode encoded geometry. Avoid SDK lock-in until provider model is stable.

## Async/network rule

All external calls isolated in services. UI may call async methods. No API calls from chart/table functions. Tests never hit the network.