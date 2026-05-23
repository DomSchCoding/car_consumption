# 01 - Architecture v3: map-based routing

## Architectural target

The route feature must be decomposed into four layers:

```text
UI layer
  NiceGUI pages and components, user interaction, map rendering

Service/provider layer
  geocoding, routing, elevation, caching, external API adapters

Domain transformation layer
  route geometry, resampling, segmentization, speed/elevation derivation

Physics layer
  energy breakdown using existing route_energy and physics functions
```

## Proposed structure

```text
app/
  services/
    provider_models.py       # shared provider DTOs
    geocoding.py             # geocoder protocol + implementations
    routing.py               # routing provider protocol + implementations
    elevation.py             # elevation provider protocol + implementations
    route_cache.py           # file cache for provider responses

  core/
    route_geometry.py        # geometry helpers: haversine, cumulative distance, resampling
    route_segmentizer.py     # converts route geometry into RouteSegment list
    route_energy.py          # existing energy calculation; extend only where needed

  ui/
    components/
      map_widget.py          # NiceGUI Leaflet wrapper helpers
      route_controls.py      # address inputs, provider selection, route options
      route_summary.py       # summary cards, provider status, warnings
    pages/
      route_planner.py       # existing manual/expert page
      map_route_planner.py   # new Google-Maps-like route page
```

## Dependency strategy

Minimal dependencies first:

```toml
dependencies = [
  "nicegui>=2.0.0",
  "plotly>=5.0.0",
  "pydantic>=2.0.0",
  "pandas>=2.0.0",
  "pyyaml>=6.0",
  "kaleido>=0.1.0",
  "httpx>=0.27.0",
  "polyline>=2.0.0",
]
```

Optional later:

```toml
"python-dotenv>=1.0.0"       # convenient local env loading
"openrouteservice>=2.3.3"    # optional wrapper, only if simpler than direct httpx
```

Rationale:

- `httpx` keeps provider integrations explicit and testable.
- `polyline` helps decode OSRM/Valhalla/Google-style encoded geometry where needed.
- Avoid provider-specific SDK lock-in until the provider model is stable.

## Page routing

Recommended UI routes:

```text
/                 dashboard
/route            new map route planner, default user path
/route/manual     old manual/expert route planner
/vehicle/{vid}    detail page
```

During transition, keep `/route` pointing to the old page until the new page works; then switch and expose the old page as `/route/manual`.

## Provider status

The UI must show route provider status:

```text
Provider: Demo / OpenRouteService / OSRM / Valhalla
Status: configured / missing key / cached / offline fallback
Cache: hit / miss
Warnings: elevation unavailable, speed estimated, route asymmetry not supported, etc.
```

## Async/network rule

All external calls should be isolated in services. The UI page may call async methods, but external APIs must not be called from inside chart/table building functions. Tests must mock providers and never hit the network.
