"""Routing provider protocol and demo provider implementation.

The demo provider returns deterministic fixture routes for offline use
and testing. It does not require network access or API keys.

The live provider chains Nominatim geocoding + OSRM routing + Open-Meteo
elevation when enabled via environment variables.
"""

from __future__ import annotations

import logging
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

_logger = logging.getLogger(__name__)

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
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lon1)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def route_live(request: RouteRequest) -> tuple[ProviderRoute | None, list[str]]:
    """Chain Nominatim geocoding + OSRM routing + Open-Meteo elevation.

    Returns (provider_route, info_messages). Returns (None, messages) on failure.
    All providers must be enabled via environment variables.
    """
    messages: list[str] = []

    start_coord = request.start_coord
    dest_coord = request.destination_coord

    if start_coord is None or dest_coord is None:
        from app.services.geocoding import geocode as nominatim_geocode

        if start_coord is None and request.start_text:
            candidates, geo_err = nominatim_geocode(request.start_text)
            if candidates:
                start_coord = candidates[0].point
                messages.append(f"Geocoded start: {candidates[0].label}")
            else:
                detail = geo_err if geo_err else "No results found"
                messages.append(f"Could not geocode start address '{request.start_text}': {detail}")
                return None, messages

        if dest_coord is None and request.destination_text:
            candidates, geo_err = nominatim_geocode(request.destination_text)
            if candidates:
                dest_coord = candidates[0].point
                messages.append(f"Geocoded destination: {candidates[0].label}")
            else:
                detail = geo_err if geo_err else "No results found"
                messages.append(f"Could not geocode destination address '{request.destination_text}': {detail}")
                return None, messages

    if start_coord is None or dest_coord is None:
        messages.append("Missing start or destination coordinates")
        return None, messages

    enriched_request = request.model_copy(update={"start_coord": start_coord, "destination_coord": dest_coord})

    from app.services.osrm_routing import fetch_osrm_route

    provider_route = fetch_osrm_route(enriched_request)
    if provider_route is None:
        messages.append("OSRM routing failed — no route found")
        return None, messages

    messages.append(f"OSRM route: {provider_route.summary_distance_km:.1f} km")

    from app.services.elevation import enrich_route_with_elevation

    enriched_geometry = enrich_route_with_elevation(provider_route.geometry)
    if enriched_geometry and enriched_geometry[0].elevation_m is not None:
        from app.core.route_geometry import compute_elevation_gain_loss

        gain, loss = compute_elevation_gain_loss(enriched_geometry)
        provider_route.geometry = enriched_geometry
        provider_route.elevation_gain_m = gain
        provider_route.elevation_loss_m = loss
        messages.append(f"Elevation: +{gain:.0f}m / -{loss:.0f}m (approximate)")

        from app.core.route_geometry import cumulative_distances_km

        dists = cumulative_distances_km(enriched_geometry)
        for i, pt in enumerate(enriched_geometry):
            pt.distance_from_start_km = round(dists[i], 4) if i < len(dists) else None
    else:
        messages.append("Elevation data unavailable — using flat terrain")

    from app.services.route_cache import compute_cache_key, write_route

    if not provider_route.cache_key:
        provider_route.cache_key = compute_cache_key(
            provider="osrm+open_meteo",
            profile=enriched_request.profile,
            start_lat=start_coord.lat,
            start_lon=start_coord.lon,
            dest_lat=dest_coord.lat,
            dest_lon=dest_coord.lon,
        )
    write_route(provider_route)

    return provider_route, messages
