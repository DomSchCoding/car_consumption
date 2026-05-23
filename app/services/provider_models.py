"""Provider data models for routing, geocoding, and elevation services.

These models describe external provider results. They are separate from
the internal physics Route/RouteSegment models. Conversion between the two
is explicit and testable.
"""

from __future__ import annotations

from enum import Enum

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


class RouteRequest(BaseModel):
    start_text: str | None = None
    destination_text: str | None = None
    start_coord: GeoPoint | None = None
    destination_coord: GeoPoint | None = None
    profile: str = "car_fastest"
    provider: str = "demo"


class ProviderRoute(BaseModel):
    provider: str
    profile: str
    start: GeoPoint
    destination: GeoPoint
    start_label: str | None = None
    destination_label: str | None = None
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


class ProviderStatus(BaseModel):
    name: str
    configured: bool = False
    available: bool = False
    message: str = ""


class RouteSourceKind(str, Enum):
    manual = "manual"
    provider = "provider"
    gpx = "gpx"
    demo = "demo"
