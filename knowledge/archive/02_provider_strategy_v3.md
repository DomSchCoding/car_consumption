# 02 - Provider strategy v3

## Why provider abstraction matters

A Google-Maps-like route planner needs three logically separate services:

1. Geocoding: text address -> latitude/longitude.
2. Routing: coordinates -> road route geometry, distance, duration, route legs/steps.
3. Elevation: route geometry -> elevation at sampled points.

Different APIs provide different subsets. Therefore the project needs protocols/interfaces before implementing concrete providers.

## Provider priority

### Provider 0: Demo/offline provider - mandatory

Purpose:

- app works without API key
- tests are deterministic
- UI can be developed without quota usage

Implementation:

- hard-coded or YAML fixture routes such as:
  - short city commute
  - hilly commute
  - highway route
  - mountain route
- returns realistic geometry, elevation, distance, duration and maybe synthetic speed samples

### Provider 1: OpenRouteService - recommended first real provider

Why:

- Python wrapper exists
- API covers directions, geocoding and elevation
- OSM-based and open-source ecosystem
- good fit for Europe/Austria use cases

Caveats:

- requires API key for public API
- quotas/rate limits must be respected
- details like speed limits may be limited; if detailed speed is unavailable, derive average speed from distance/duration per route step

Environment:

```text
ORS_API_KEY=...
ROUTING_PROVIDER=ors
```

### Provider 2: OSRM + elevation provider - useful fallback/self-host path

Why:

- OSRM is fast and open source
- can be self-hosted
- gives route geometry, duration, distance and steps

Caveats:

- no native elevation profile in standard route response
- needs separate elevation provider such as Open-Meteo Elevation, Open-Elevation or self-hosted OpenTopoData

Environment:

```text
OSRM_BASE_URL=https://router.project-osrm.org
ELEVATION_PROVIDER=open_meteo
```

### Provider 3: Valhalla - strong future option

Why:

- open-source routing engine
- supports advanced route information
- documentation includes route shape and elevation options
- good long-term option if self-hosting or hosted Valhalla becomes desired

Caveats:

- integration complexity higher than ORS MVP
- hosted endpoints depend on chosen provider

## Protocols

```python
class Geocoder(Protocol):
    async def geocode(self, query: str) -> list[GeoCandidate]: ...

class RoutingProvider(Protocol):
    async def route(self, request: RouteRequest) -> ProviderRoute: ...

class ElevationProvider(Protocol):
    async def enrich(self, points: list[GeoPoint]) -> list[GeoPoint3D]: ...
```

## ProviderRoute minimum fields

```text
provider
profile
start
destination
waypoints
geometry_points
legs
steps
summary_distance_km
summary_duration_s
source_quality
warnings
raw_response_hash
```

## Caching

External results must be cached by a stable key:

```text
provider + profile + start_coord + dest_coord + waypoints + options + schema_version
```

Recommended cache path:

```text
.cache/routes/{hash}.json
```

Never cache API keys. Consider a `clear cache` button in developer settings later.

## References for implementation choices

- NiceGUI includes `ui.leaflet` for Leaflet maps.
- openrouteservice-py provides directions, elevation and Pelias geocoding/autocomplete support.
- OSRM route API provides route geometry, duration and steps but should be paired with elevation when elevation is needed.
- Open-Elevation and OpenTopoData are useful self-hostable elevation options.
- Open-Meteo Elevation API can provide elevation samples and is attractive for low-friction use cases, with attribution requirements.
