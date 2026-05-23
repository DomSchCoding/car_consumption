# 04 - Route data model v3

## Design intent

Separate provider data from physics input. Provider data can be messy and detailed; physics should receive clean `RouteSegment` objects.

## New provider models

Recommended file: `app/services/provider_models.py`

```python
from pydantic import BaseModel, Field

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

## Existing domain models

Keep current Pydantic models:

```text
RouteSegment
Route
CommuteScenario
RouteEnergyBreakdown
```

But consider adding:

```python
class RouteSourceKind(str, Enum):
    manual = "manual"
    provider = "provider"
    gpx = "gpx"
    demo = "demo"
```

And optional fields on `Route`:

```python
source_kind: RouteSourceKind = RouteSourceKind.manual
geometry: list[GeoPoint3D] | None = None
provider: str | None = None
provider_profile: str | None = None
warnings: list[str] = Field(default_factory=list)
```

## Segmentization settings

Recommended file: `app/core/route_segmentizer.py`

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

## Conversion pipeline

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

## Important distinction

A `ProviderRoute` is not the same as a `Route`.

- `ProviderRoute` describes the external routing result.
- `Route` describes the internal physics route.
- Conversion must be explicit and testable.
