"""Geometry helpers for route processing.

Pure functions operating on GeoPoint/GeoPoint3D coordinates.
No UI imports, no provider imports except DTO typing.
"""

from __future__ import annotations

import math

from app.services.provider_models import GeoPoint, GeoPoint3D

EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(a: GeoPoint, b: GeoPoint) -> float:
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    val = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(val), math.sqrt(1 - val))


def cumulative_distances_km(points: list[GeoPoint3D]) -> list[float]:
    if not points:
        return []
    dists = [0.0]
    for i in range(1, len(points)):
        d = haversine_distance_km(
            GeoPoint(lat=points[i - 1].lat, lon=points[i - 1].lon),
            GeoPoint(lat=points[i].lat, lon=points[i].lon),
        )
        dists.append(dists[-1] + d)
    return dists


def compute_elevation_gain_loss(points: list[GeoPoint3D], noise_threshold_m: float = 3.0) -> tuple[float, float]:
    gain = 0.0
    loss = 0.0
    for i in range(1, len(points)):
        prev_e = points[i - 1].elevation_m
        curr_e = points[i].elevation_m
        if prev_e is None or curr_e is None:
            continue
        delta = curr_e - prev_e
        if delta > noise_threshold_m:
            gain += delta
        elif delta < -noise_threshold_m:
            loss += abs(delta)
    return round(gain, 1), round(loss, 1)


def resample_route_points(points: list[GeoPoint3D], target_spacing_km: float = 0.2) -> list[GeoPoint3D]:
    if len(points) <= 2:
        return list(points)
    if target_spacing_km <= 0:
        return list(points)

    dists = cumulative_distances_km(points)
    total = dists[-1]
    if total <= 0:
        return list(points)

    n_samples = max(2, int(total / target_spacing_km) + 1)
    target_dists = [total * i / (n_samples - 1) for i in range(n_samples)]
    resampled = [_interpolate_at_distance(points, dists, target_dists[0])]

    for td in target_dists[1:]:
        pt = _interpolate_at_distance(points, dists, td)
        if pt is not None:
            resampled.append(pt)

    if resampled[-1] != points[-1]:
        resampled.append(
            GeoPoint3D(
                lat=points[-1].lat,
                lon=points[-1].lon,
                elevation_m=points[-1].elevation_m,
                distance_from_start_km=total,
            )
        )

    for i, pt in enumerate(resampled):
        if pt.distance_from_start_km is None:
            pt.distance_from_start_km = dists[i] if i < len(dists) else total

    return resampled


def _interpolate_at_distance(points: list[GeoPoint3D], dists: list[float], target_km: float) -> GeoPoint3D | None:
    if target_km <= 0:
        return GeoPoint3D(
            lat=points[0].lat,
            lon=points[0].lon,
            elevation_m=points[0].elevation_m,
            distance_from_start_km=0.0,
        )
    if target_km >= dists[-1]:
        return GeoPoint3D(
            lat=points[-1].lat,
            lon=points[-1].lon,
            elevation_m=points[-1].elevation_m,
            distance_from_start_km=dists[-1],
        )

    for i in range(1, len(dists)):
        if dists[i] >= target_km:
            seg_len = dists[i] - dists[i - 1]
            if seg_len <= 0:
                continue
            t = (target_km - dists[i - 1]) / seg_len
            lat = points[i - 1].lat + t * (points[i].lat - points[i - 1].lat)
            lon = points[i - 1].lon + t * (points[i].lon - points[i - 1].lon)
            e_prev = points[i - 1].elevation_m if points[i - 1].elevation_m is not None else 0.0
            e_curr = points[i].elevation_m if points[i].elevation_m is not None else 0.0
            elev = e_prev + t * (e_curr - e_prev)
            return GeoPoint3D(
                lat=round(lat, 6),
                lon=round(lon, 6),
                elevation_m=round(elev, 1),
                distance_from_start_km=round(target_km, 4),
            )
    return None


def estimate_bearing_degrees(a: GeoPoint, b: GeoPoint) -> float:
    lat1, lon1 = math.radians(a.lat), math.radians(a.lon)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lon)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0
