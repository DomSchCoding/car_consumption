"""OSRM routing provider.

Uses the public OSRM demo server for road geometry, distance, and duration.
Does not provide elevation data. Rate-limited and cached.
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

from app.services.provider_config import get_osrm_base_url, is_osrm_enabled
from app.services.provider_models import (
    GeoPoint,
    GeoPoint3D,
    ProviderRoute,
    ProviderStatus,
    RouteRequest,
    RouteStep,
)
from app.services.route_cache import compute_cache_key, write_route

ROUTE_CACHE_DIR = Path(".cache/routes")

_last_request_time: float = 0.0
_MIN_REQUEST_INTERVAL = 1.0


def _rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def osrm_status() -> ProviderStatus:
    enabled = is_osrm_enabled()
    return ProviderStatus(
        name="osrm",
        configured=enabled,
        available=enabled,
        message="OSRM routing enabled" if enabled else "Disabled (set CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM=true)",
    )


def fetch_osrm_route(request: RouteRequest) -> ProviderRoute | None:
    if not is_osrm_enabled():
        return None

    if request.start_coord is None or request.destination_coord is None:
        return None

    start = request.start_coord
    dest = request.destination_coord

    cache_key = compute_cache_key(
        provider="osrm",
        profile=request.profile,
        start_lat=start.lat,
        start_lon=start.lon,
        dest_lat=dest.lat,
        dest_lon=dest.lon,
    )

    from app.services.route_cache import read_route

    cached = read_route(cache_key)
    if cached is not None:
        return cached

    _rate_limit()

    base_url = get_osrm_base_url().rstrip("/")
    url = (
        f"{base_url}/route/v1/driving/{start.lon},{start.lat};{dest.lon},{dest.lat}"
        "?overview=full&geometries=geojson&steps=true&annotations=true"
    )

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        import logging

        logging.getLogger(__name__).warning("OSRM request failed: %s", exc)
        return None

    parsed = parse_osrm_response(data, request)
    if parsed is None:
        return None

    parsed.cache_key = cache_key
    write_route(parsed)
    return parsed


def parse_osrm_route_geometry(geojson_coords: list[list[float]]) -> list[GeoPoint3D]:
    points: list[GeoPoint3D] = []
    for coord in geojson_coords:
        lon, lat = coord[0], coord[1]
        points.append(GeoPoint3D(lat=round(lat, 6), lon=round(lon, 6), elevation_m=None))
    return points


def parse_osrm_steps(legs: list[dict]) -> list[RouteStep]:
    steps: list[RouteStep] = []
    for leg in legs:
        for step in leg.get("steps", []):
            name = step.get("name", "") or ""
            distance_km = step.get("distance", 0) / 1000.0
            duration_s = step.get("duration", 0)
            mode = step.get("mode", "").lower()
            road_type = _osrm_mode_to_road_type(mode)
            speed_kmh = (distance_km / (duration_s / 3600)) if duration_s > 0 else None
            geometry_coords = step.get("geometry", {}).get("coordinates", [])
            geometry = parse_osrm_route_geometry(geometry_coords)
            steps.append(
                RouteStep(
                    name=name or None,
                    distance_km=round(distance_km, 3),
                    duration_s=round(duration_s, 1),
                    road_type=road_type,
                    speed_kmh=round(speed_kmh, 1) if speed_kmh is not None else None,
                    geometry=geometry,
                )
            )
    return steps


def _osrm_mode_to_road_type(mode: str) -> str:
    mapping = {
        "motorway": "highway",
        "trunk": "highway",
        "primary": "suburban",
        "secondary": "rural",
        "tertiary": "rural",
        "residential": "city",
        "living_street": "city",
        "service": "city",
        "unclassified": "mixed",
    }
    return mapping.get(mode, "mixed")


def parse_osrm_response(data: dict, request: RouteRequest) -> ProviderRoute | None:
    routes = data.get("routes", [])
    if not routes:
        return None

    route = routes[0]
    distance_m = route.get("distance", 0)
    duration_s = route.get("duration", 0)

    geometry_coords = route.get("geometry", {}).get("coordinates", [])
    geometry = parse_osrm_route_geometry(geometry_coords)

    legs = route.get("legs", [])
    steps = parse_osrm_steps(legs)

    start = request.start_coord or GeoPoint(lat=0, lon=0)
    destination = request.destination_coord or GeoPoint(lat=0, lon=0)

    warnings = ["OSRM route: no elevation data", "Speed estimated from OSRM durations"]

    return ProviderRoute(
        provider="osrm",
        profile=request.profile,
        start=start,
        destination=destination,
        start_label=request.start_text,
        destination_label=request.destination_text,
        geometry=geometry,
        steps=steps,
        summary_distance_km=round(distance_m / 1000.0, 2),
        summary_duration_s=round(duration_s, 1),
        elevation_gain_m=None,
        elevation_loss_m=None,
        warnings=warnings,
    )
