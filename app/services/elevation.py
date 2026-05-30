"""Open-Meteo Elevation API provider.

Resamples route geometry to configurable spacing (default 1 km), caps sample
points (default 50), and enriches points with elevation data. Results are cached.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import httpx

from app.services.provider_config import get_open_meteo_elevation_url, is_open_meteo_elevation_enabled
from app.services.provider_models import GeoPoint3D, ProviderStatus

ELEVATION_CACHE_DIR = Path(".cache/elevation")

_logger = logging.getLogger(__name__)

_last_request_time: float = 0.0
_MIN_REQUEST_INTERVAL = 0.5


def _rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def _cache_key(points: list[tuple[float, float]]) -> str:
    raw = "open_meteo_elev|" + "|".join(f"{lat:.4f},{lon:.4f}" for lat, lon in points)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _ensure_cache_dir() -> None:
    ELEVATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _read_cache(key: str) -> list[float] | None:
    path = ELEVATION_CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(key: str, elevations: list[float]) -> None:
    _ensure_cache_dir()
    path = ELEVATION_CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(elevations), encoding="utf-8")


def open_meteo_status() -> ProviderStatus:
    enabled = is_open_meteo_elevation_enabled()
    return ProviderStatus(
        name="open_meteo_elevation",
        configured=enabled,
        available=enabled,
        message="Open-Meteo elevation enabled"
        if enabled
        else "Disabled (set CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION=true)",
    )


def resample_route_points(
    points: list[GeoPoint3D],
    spacing_km: float = 0.5,
    max_points: int = 200,
) -> list[tuple[float, float]]:
    """Select route points with approximately `spacing_km` between them, capped at `max_points`.

    Always includes the first and last point. The max_points cap applies to
    intermediate points only, so start and destination are never dropped.
    Returns (lat, lon) tuples for the elevation API.
    """
    if not points:
        return []

    if len(points) <= max_points:
        return [(p.lat, p.lon) for p in points]

    from app.core.route_geometry import cumulative_distances_km

    distances = cumulative_distances_km(points)
    total_km = distances[-1] if distances else 0

    if total_km <= 0:
        result = [(p.lat, p.lon) for p in points[: max_points - 1]]
        if result[-1] != (points[-1].lat, points[-1].lon):
            result.append((points[-1].lat, points[-1].lon))
        return result

    intermediate_budget = max_points - 2
    step_km = max(spacing_km, total_km / max(intermediate_budget, 1))

    selected: list[tuple[float, float]] = [(points[0].lat, points[0].lon)]
    next_dist = step_km

    for i in range(1, len(points) - 1):
        d = distances[i]
        if d >= next_dist:
            selected.append((points[i].lat, points[i].lon))
            next_dist = d + step_km
            if len(selected) - 1 >= intermediate_budget:
                break

    if selected[-1] != (points[-1].lat, points[-1].lon):
        selected.append((points[-1].lat, points[-1].lon))

    return selected


def fetch_elevation(points: list[tuple[float, float]]) -> list[float] | None:
    """Fetch elevation for a list of (lat, lon) points from Open-Meteo.

    Returns a list of elevation values in meters, same order as input points.
    Returns None on failure.
    """
    if not is_open_meteo_elevation_enabled():
        return None

    key = _cache_key(points)
    cached = _read_cache(key)
    if cached is not None:
        return cached

    _rate_limit()

    lats = ",".join(str(round(p[0], 4)) for p in points)
    lons = ",".join(str(round(p[1], 4)) for p in points)

    url = get_open_meteo_elevation_url()
    params = {"latitude": lats, "longitude": lons}

    try:
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        _logger.warning("Open-Meteo elevation request failed: %s", exc)
        return None

    elevations = data.get("elevation", [])
    if not isinstance(elevations, list) or len(elevations) != len(points):
        _logger.warning(
            "Open-Meteo elevation returned %d values for %d points",
            len(elevations) if isinstance(elevations, list) else 0,
            len(points),
        )
        return None

    result = [float(e) for e in elevations]
    _write_cache(key, result)
    return result


def enrich_route_with_elevation(
    geometry: list[GeoPoint3D],
    spacing_km: float = 0.5,
    max_points: int = 200,
) -> list[GeoPoint3D]:
    """Resample route, fetch elevation, and map elevations back to the full geometry.

    Uses inverse distance weighting interpolation between sampled points.
    """
    if not geometry:
        return geometry

    if not is_open_meteo_elevation_enabled():
        return geometry

    sample_coords = resample_route_points(geometry, spacing_km=spacing_km, max_points=max_points)
    if len(sample_coords) < 2:
        return geometry

    elevations = fetch_elevation(sample_coords)
    if elevations is None or len(elevations) != len(sample_coords):
        _logger.warning("Elevation enrichment failed, returning geometry without elevation")
        return geometry

    from app.core.route_geometry import cumulative_distances_km

    distances = cumulative_distances_km(geometry)

    sample_dists: list[float] = [0.0]
    sample_map: dict[int, int] = {}

    for i, pt in enumerate(geometry):
        for si, (slat, slon) in enumerate(sample_coords):
            if abs(pt.lat - slat) < 0.0001 and abs(pt.lon - slon) < 0.0001:
                sample_map[i] = si
                break

    sample_indices = sorted(sample_map.keys())
    sample_dists = [distances[i] for i in sample_indices]
    sample_elevs = [elevations[sample_map[i]] for i in sample_indices]

    enriched: list[GeoPoint3D] = []
    for i, pt in enumerate(geometry):
        d = distances[i]

        if i in sample_map:
            elev = elevations[sample_map[i]]
        elif d <= sample_dists[0]:
            elev = sample_elevs[0]
        elif d >= sample_dists[-1]:
            elev = sample_elevs[-1]
        else:
            for j in range(len(sample_dists) - 1):
                if sample_dists[j] <= d <= sample_dists[j + 1]:
                    seg_len = sample_dists[j + 1] - sample_dists[j]
                    if seg_len > 0:
                        t = (d - sample_dists[j]) / seg_len
                        elev = sample_elevs[j] * (1 - t) + sample_elevs[j + 1] * t
                    else:
                        elev = sample_elevs[j]
                    break
            else:
                elev = sample_elevs[-1]

        enriched.append(
            GeoPoint3D(
                lat=pt.lat,
                lon=pt.lon,
                elevation_m=round(elev, 1),
                distance_from_start_km=pt.distance_from_start_km,
            )
        )

    return enriched
