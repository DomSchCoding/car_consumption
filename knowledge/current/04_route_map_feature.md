# 04 - Route Map Feature

## User flow

```text
1. Select vehicles on dashboard
2. Open Route
3. Enter start and destination addresses
4. Click "Find route"
5. App geocodes, shows candidates if ambiguous
6. App calculates route
7. Display:
   - map with start/end markers and route polyline
   - route summary: distance, duration, avg speed, elevation gain/loss
   - one-way / return-trip toggle
   - energy comparison table
   - energy breakdown stacked chart
   - elevation profile and speed profile
8. Changing vehicles or physics params updates results without re-fetching route
```

## Basic controls

```text
Start address / place
Destination address / place
Route profile: car fastest, car shorter, highway avoid (later)
Button: Calculate route
Checkbox: Return trip
Checkbox: Use same route reversed for return (MVP)
```

## Advanced controls

```text
Provider: Demo / ORS / OSRM / Valhalla
Temperature [C]
Headwind along route [km/h] or simple outward headwind
Payload [kg]
Aux override [kW]
Regen efficiency downhill
Regen efficiency stop-go
Segmentization resolution [m]
Force refresh / use cache
```

## Provider abstraction

### Why abstraction matters

Geocoding, routing, and elevation are logically separate services. Different APIs provide different subsets. Define protocols before implementing concrete providers.

### Protocols

```python
class Geocoder(Protocol):
    async def geocode(self, query: str) -> list[GeoCandidate]: ...

class RoutingProvider(Protocol):
    async def route(self, request: RouteRequest) -> ProviderRoute: ...

class ElevationProvider(Protocol):
    async def enrich(self, points: list[GeoPoint]) -> list[GeoPoint3D]: ...
```

### Provider priority

**Provider 0: Demo/offline (mandatory)**

- app works without API key
- tests are deterministic
- hard-coded or YAML fixture routes: city commute, hilly commute, highway, mountain
- returns realistic geometry, elevation, distance, duration

**Provider 1: OpenRouteService (recommended first real)**

- Python wrapper available
- API covers directions, geocoding, elevation
- OSM-based, good for Europe/Austria
- Requires API key, quotas apply
- Environment: `ORS_API_KEY`, `ROUTING_PROVIDER=ors`

**Provider 2: OSRM + elevation provider**

- Fast, open-source, self-hostable
- No native elevation in route response
- Pair with Open-Meteo, Open-Elevation, or self-hosted OpenTopoData
- Environment: `OSRM_BASE_URL`, `ELEVATION_PROVIDER=open_meteo`

**Provider 3: Valhalla (future option)**

- Open-source, advanced route information
- Higher integration complexity
- Phase D/E unless strong reason

### ProviderRoute minimum fields

```text
provider, profile, start, destination, waypoints
geometry_points, legs, steps
summary_distance_km, summary_duration_s
elevation_gain_m, elevation_loss_m (if available)
source_quality, warnings
raw_response_hash
```

## Data model

### Provider models (`app/services/provider_models.py`)

```python
class GeoPoint(BaseModel):
    lat: float
    lon: float

class GeoPoint3D(GeoPoint):
    elevation_m: float | None = None
    distance_from_start_km: float | None = None

class GeoCandidate(BaseModel):
    label: str
    point: GeoPoint
    confidence: float | None = None
    provider: str
    raw: dict | None = None

class RouteStep(BaseModel):
    name: str | None = None
    distance_km: float
    duration_s: float | None = None
    road_type: str | None = None
    speed_kmh: float | None = None
    geometry: list[GeoPoint3D] = Field(default_factory=list)

class ProviderRoute(BaseModel):
    provider: str
    profile: str
    start: GeoPoint
    destination: GeoPoint
    waypoints: list[GeoPoint] = Field(default_factory=list)
    geometry: list[GeoPoint3D]
    steps: list[RouteStep] = Field(default_factory=list)
    summary_distance_km: float
    summary_duration_s: float | None = None
    elevation_gain_m: float | None = None
    elevation_loss_m: float | None = None
    warnings: list[str] = Field(default_factory=list)
    cache_key: str | None = None
    raw_response: dict | None = None
```

### Route source kind (add to existing models)

```python
class RouteSourceKind(str, Enum):
    manual = "manual"
    provider = "provider"
    gpx = "gpx"
    demo = "demo"
```

### Segmentization settings (`app/core/route_segmentizer.py`)

```python
class SegmentizationSettings(BaseModel):
    target_segment_length_km: float = 1.0
    max_segment_length_km: float = 3.0
    min_segment_length_km: float = 0.2
    slope_change_threshold: float = 0.03
    speed_change_threshold_kmh: float = 15.0
    default_city_stop_per_km: float = 2.0
    default_rural_stop_per_km: float = 0.2
    default_highway_stop_per_km: float = 0.0
```

### Conversion pipeline

```text
ProviderRoute
  -> resampled GeoPoint3D list
  -> derive cumulative distance
  -> derive local slopes and elevation gain/loss
  -> derive speed per step or sample
  -> classify approximate road type
  -> merge/split into RouteSegment list
  -> existing commute_energy
```

Important: `ProviderRoute` describes external routing result. `Route` describes internal physics route. Conversion must be explicit and testable.

## Route result display

Top cards:

```text
Distance: 23.4 km
Duration: 31 min
Average speed: 45 km/h
Elevation gain/loss: +280 m / -120 m
Return mode: one-way / there-and-back
Provider: ORS, cache hit/miss
Data quality: speed estimated, elevation sampled every X m
```

## Map interactions

MVP:

- show map centered on route
- show start and end markers
- show route polyline
- allow address text input

Phase 2:

- click map to set start/destination
- draggable markers
- optional via points
- route alternatives
- save favorite commute routes

## NiceGUI Leaflet

Use `ui.leaflet` for map rendering. Keep map helpers in `app/ui/components/map_widget.py`:

```python
def create_route_map(center: tuple[float, float], zoom: int): ...
def draw_route_polyline(map_element, points): ...
def set_start_end_markers(map_element, start, destination): ...
def fit_bounds(map_element, points): ...
```

Do not scatter raw JavaScript across pages. Wrap in one helper module.

## Caching

Cache provider results by stable key:

```text
provider + profile + start_coord + dest_coord + waypoints + options + schema_version
```

Cache path: `.cache/routes/{hash}.json`

Never cache API keys. Cache normalized ProviderRoute JSON with schema version.

## Security and privacy

- Never commit API keys. Use environment variables.
- Show provider status in UI (configured / missing key / offline).
- Routes can contain personal locations. Do not commit cache files. Add `.cache/` to `.gitignore`.
- Attribution required for map tiles and data providers.
- Demo mode must work without API key.
- If provider fails: use cache if available, otherwise show error and offer demo/manual route.