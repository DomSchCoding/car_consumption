"""Routing provider protocol and demo provider implementation.

The demo provider returns deterministic fixture routes for offline use
and testing. It does not require network access or API keys.
"""

from __future__ import annotations

import math
from pathlib import Path

from app.services.provider_models import (
    GeoCandidate,
    GeoPoint,
    GeoPoint3D,
    ProviderRoute,
    ProviderStatus,
    RouteRequest,
    RouteStep,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "routes"

DEMO_ROUTES: dict[str, dict] = {
    "city_commute": {
        "start_label": "Vienna City Center",
        "destination_label": "Vienna Donauinsel",
        "start": GeoPoint(lat=48.2082, lon=16.3738),
        "destination": GeoPoint(lat=48.2154, lon=16.3988),
        "distance_km": 3.8,
        "duration_s": 480,
        "elevation_gain_m": 12.0,
        "elevation_loss_m": 8.0,
        "avg_speed_kmh": 28.5,
        "road_type": "city",
        "stops_per_km": 2.0,
    },
    "hilly_commute": {
        "start_label": "Klosterneuburg",
        "destination_label": "Vienna Kahlenbergerdorf",
        "start": GeoPoint(lat=48.3050, lon=16.3090),
        "destination": GeoPoint(lat=48.2670, lon=16.3500),
        "distance_km": 8.2,
        "duration_s": 720,
        "elevation_gain_m": 150.0,
        "elevation_loss_m": 120.0,
        "avg_speed_kmh": 41.0,
        "road_type": "rural",
        "stops_per_km": 0.5,
    },
    "highway_route": {
        "start_label": "Vienna Sued",
        "destination_label": "Wiener Neustadt",
        "start": GeoPoint(lat=48.1740, lon=16.3800),
        "destination": GeoPoint(lat=47.8100, lon=16.2420),
        "distance_km": 42.5,
        "duration_s": 1800,
        "elevation_gain_m": 45.0,
        "elevation_loss_m": 50.0,
        "avg_speed_kmh": 85.0,
        "road_type": "highway",
        "stops_per_km": 0.0,
    },
}

DEMO_GEOCODE: dict[str, list[GeoCandidate]] = {
    "demo city start": [
        GeoCandidate(
            label="Vienna City Center (Demo)", point=GeoPoint(lat=48.2082, lon=16.3738), confidence=0.9, provider="demo"
        )
    ],
    "demo city destination": [
        GeoCandidate(
            label="Vienna Donauinsel (Demo)", point=GeoPoint(lat=48.2154, lon=16.3988), confidence=0.9, provider="demo"
        )
    ],
    "demo hilly start": [
        GeoCandidate(
            label="Klosterneuburg (Demo)", point=GeoPoint(lat=48.3050, lon=16.3090), confidence=0.9, provider="demo"
        )
    ],
    "demo hilly destination": [
        GeoCandidate(
            label="Vienna Kahlenbergerdorf (Demo)",
            point=GeoPoint(lat=48.2670, lon=16.3500),
            confidence=0.9,
            provider="demo",
        )
    ],
    "demo highway start": [
        GeoCandidate(
            label="Vienna Sued (Demo)", point=GeoPoint(lat=48.1740, lon=16.3800), confidence=0.9, provider="demo"
        )
    ],
    "demo highway destination": [
        GeoCandidate(
            label="Wiener Neustadt (Demo)", point=GeoPoint(lat=47.8100, lon=16.2420), confidence=0.9, provider="demo"
        )
    ],
}


def _generate_demo_geometry(
    start: GeoPoint, end: GeoPoint, n_points: int, elevation_gain_m: float = 0.0, elevation_loss_m: float = 0.0
) -> list[GeoPoint3D]:
    base_elev = 200.0
    points: list[GeoPoint3D] = []
    hill_amp = max(elevation_gain_m, elevation_loss_m) * 0.6
    for i in range(n_points + 1):
        t = i / n_points
        lat = start.lat + t * (end.lat - start.lat)
        lon = start.lon + t * (end.lon - start.lon)
        net_change = (elevation_gain_m - elevation_loss_m) * t
        peak = hill_amp * math.sin(t * math.pi)
        elev = base_elev + net_change + peak
        points.append(GeoPoint3D(lat=round(lat, 6), lon=round(lon, 6), elevation_m=round(elev, 1)))
    return points


class DemoRoutingProvider:
    """Deterministic offline routing provider for testing and demo."""

    def __init__(self, routes: dict[str, dict] | None = None, geocode_db: dict[str, list[GeoCandidate]] | None = None):
        self._routes = routes or DEMO_ROUTES
        self._geocode = geocode_db or DEMO_GEOCODE

    def status(self) -> ProviderStatus:
        return ProviderStatus(name="demo", configured=True, available=True, message="Demo provider always available")

    def geocode(self, query: str) -> list[GeoCandidate]:
        key = query.strip().lower()
        return self._geocode.get(key, [])

    def route(self, request: RouteRequest) -> ProviderRoute | None:
        start_text = (request.start_text or "").strip().lower()
        dest_text = (request.destination_text or "").strip().lower()

        query = f"{start_text} {dest_text}".lower().replace("demo ", "").strip()

        match_key = None
        for route_key, route_def in self._routes.items():
            s_key = route_def["start_label"].lower()
            d_key = route_def["destination_label"].lower()
            combined = f"{s_key} {d_key}"
            if any(kw in combined for kw in query.split() if len(kw) >= 3):
                match_key = route_key
                break

        if match_key is None:
            if "hilly" in query or "hill" in query or "klosterneuburg" in query:
                match_key = "hilly_commute"
            elif "highway" in query or "neustadt" in query:
                match_key = "highway_route"
            else:
                match_key = "city_commute"

        route_def = self._routes[match_key]
        start = route_def["start"]
        destination = route_def["destination"]

        n_points = max(10, int(route_def["distance_km"] * 5))
        geometry = _generate_demo_geometry(
            start,
            destination,
            n_points,
            elevation_gain_m=route_def.get("elevation_gain_m", 0) or 0,
            elevation_loss_m=route_def.get("elevation_loss_m", 0) or 0,
        )

        total_dist = 0.0
        for i in range(len(geometry)):
            if i == 0:
                geometry[i].distance_from_start_km = 0.0
            else:
                d = _haversine_km(geometry[i - 1].lat, geometry[i - 1].lon, geometry[i].lat, geometry[i].lon)
                total_dist += d
                geometry[i].distance_from_start_km = round(total_dist, 4)

        avg_speed = route_def["avg_speed_kmh"]
        dist = route_def["distance_km"]
        duration = route_def.get("duration_s", dist / avg_speed * 3600)

        step = RouteStep(
            name=f"Demo {match_key.replace('_', ' ')}",
            distance_km=dist,
            duration_s=duration,
            road_type=route_def.get("road_type", "mixed"),
            speed_kmh=avg_speed,
            geometry=geometry,
        )

        warnings: list[str] = ["Demo route: speed and elevation are estimated"]

        from app.services.route_cache import compute_cache_key

        cache_key = compute_cache_key(
            provider="demo",
            profile=request.profile,
            start_lat=start.lat,
            start_lon=start.lon,
            dest_lat=destination.lat,
            dest_lon=destination.lon,
        )

        return ProviderRoute(
            provider="demo",
            profile=request.profile,
            start=start,
            destination=destination,
            start_label=route_def.get("start_label"),
            destination_label=route_def.get("destination_label"),
            geometry=geometry,
            steps=[step],
            summary_distance_km=dist,
            summary_duration_s=duration,
            elevation_gain_m=route_def.get("elevation_gain_m"),
            elevation_loss_m=route_def.get("elevation_loss_m"),
            warnings=warnings,
            cache_key=cache_key,
        )

    def list_routes(self) -> list[str]:
        return list(self._routes.keys())


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
