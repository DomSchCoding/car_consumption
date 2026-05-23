"""Tests for OSRM response parsing and geocoding/elevation modules.

All tests use fixtures or mocked responses — no network calls.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.services.elevation import (
    open_meteo_status,
    resample_route_points,
)
from app.services.geocoding import _cache_key, _read_cache, _write_cache, nominatim_status
from app.services.osrm_routing import (
    _osrm_mode_to_road_type,
    parse_osrm_response,
    parse_osrm_route_geometry,
    parse_osrm_steps,
)
from app.services.provider_models import GeoPoint, GeoPoint3D, RouteRequest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestOSRMParsing:
    def test_parse_route_geometry_empty(self) -> None:
        result = parse_osrm_route_geometry([])
        assert result == []

    def test_parse_route_geometry_basic(self) -> None:
        coords = [[16.3738, 48.2082], [16.3500, 48.2500]]
        result = parse_osrm_route_geometry(coords)
        assert len(result) == 2
        assert result[0].lat == 48.2082
        assert result[0].lon == 16.3738
        assert result[0].elevation_m is None

    def test_parse_osrm_steps(self) -> None:
        legs = [
            {
                "steps": [
                    {
                        "name": "Main Street",
                        "distance": 5000,
                        "duration": 300,
                        "mode": "driving",
                        "geometry": {"type": "LineString", "coordinates": [[16.37, 48.20], [16.35, 48.25]]},
                    }
                ]
            }
        ]
        steps = parse_osrm_steps(legs)
        assert len(steps) == 1
        assert steps[0].name == "Main Street"
        assert steps[0].distance_km == 5.0
        assert steps[0].duration_s == 300.0
        assert steps[0].speed_kmh is not None
        assert abs(steps[0].speed_kmh - 60.0) < 1.0

    def test_parse_osrm_steps_no_name(self) -> None:
        legs = [
            {
                "steps": [
                    {
                        "name": "",
                        "distance": 1000,
                        "duration": 60,
                        "mode": "driving",
                        "geometry": {"type": "LineString", "coordinates": [[16.37, 48.20], [16.38, 48.21]]},
                    }
                ]
            }
        ]
        steps = parse_osrm_steps(legs)
        assert steps[0].name is None

    def test_parse_osrm_response(self) -> None:
        fixture_path = FIXTURES_DIR / "osrm" / "osrm_landstrasse_eidenberg.json"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        request = RouteRequest(
            start_text="Landstraße 1, 4020 Linz",
            destination_text="Eidenberger Alm",
            start_coord=GeoPoint(lat=48.3043, lon=14.2884),
            destination_coord=GeoPoint(lat=48.3982, lon=14.2381),
            profile="car_fastest",
        )
        result = parse_osrm_response(data, request)
        assert result is not None
        assert result.provider == "osrm"
        assert result.summary_distance_km == 25.0
        assert result.summary_duration_s == 1380.0
        assert len(result.geometry) > 0
        assert len(result.steps) == 3
        assert result.elevation_gain_m is None
        assert result.elevation_loss_m is None
        assert "elevation" in " ".join(result.warnings).lower() or "OSRM" in " ".join(result.warnings)

    def test_parse_osrm_response_no_routes(self) -> None:
        fixture_path = FIXTURES_DIR / "osrm" / "osrm_no_route.json"
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        request = RouteRequest(profile="car_fastest")
        result = parse_osrm_response(data, request)
        assert result is None

    def test_road_type_mapping(self) -> None:
        assert _osrm_mode_to_road_type("motorway") == "highway"
        assert _osrm_mode_to_road_type("residential") == "city"
        assert _osrm_mode_to_road_type("unknown_mode") == "mixed"


class TestGeocoding:
    def test_cache_key_deterministic(self) -> None:
        key1 = _cache_key("Vienna, Austria")
        key2 = _cache_key("Vienna, Austria")
        assert key1 == key2

    def test_cache_key_case_insensitive(self) -> None:
        key1 = _cache_key("Vienna")
        key2 = _cache_key("vienna")
        assert key1 == key2

    def test_cache_key_differs_for_different_queries(self) -> None:
        key1 = _cache_key("Vienna")
        key2 = _cache_key("Linz")
        assert key1 != key2

    def test_cache_write_and_read(self, tmp_path: Path) -> None:
        import app.services.geocoding as geocoding_mod

        original_dir = geocoding_mod.GEOCODE_CACHE_DIR
        geocoding_mod.GEOCODE_CACHE_DIR = tmp_path
        try:
            from app.services.provider_models import GeoCandidate, GeoPoint

            data = [
                GeoCandidate(
                    label="Test", point=GeoPoint(lat=48.2, lon=16.37), confidence=0.9, provider="nominatim"
                ).model_dump(mode="json")
            ]
            key = "test_key"
            _write_cache(key, data)
            result = _read_cache(key)
            assert result is not None
            assert result[0]["label"] == "Test"
        finally:
            geocoding_mod.GEOCODE_CACHE_DIR = original_dir

    def test_cache_read_miss(self, tmp_path: Path) -> None:
        import app.services.geocoding as geocoding_mod

        original_dir = geocoding_mod.GEOCODE_CACHE_DIR
        geocoding_mod.GEOCODE_CACHE_DIR = tmp_path
        try:
            result = _read_cache("nonexistent_key")
            assert result is None
        finally:
            geocoding_mod.GEOCODE_CACHE_DIR = original_dir

    def test_nominatim_status_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_NOMINATIM", None)
        status = nominatim_status()
        assert status.name == "nominatim"
        assert status.configured is False
        assert status.available is False

    def test_nominatim_status_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_NOMINATIM"] = "true"
        try:
            status = nominatim_status()
            assert status.configured is True
            assert status.available is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_NOMINATIM"]

    def test_geocode_disabled_returns_empty(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_NOMINATIM", None)
        from app.services.geocoding import geocode

        candidates, error = geocode("Vienna")
        assert candidates == []
        assert "not enabled" in error.lower()

    def test_geocode_no_network_when_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_NOMINATIM", None)
        from app.services.geocoding import geocode

        candidates, error = geocode("any query")
        assert candidates == []
        assert "not enabled" in error.lower()


class TestElevation:
    def test_resample_route_points_empty(self) -> None:
        result = resample_route_points([], spacing_km=1.0, max_points=50)
        assert result == []

    def test_resample_route_points_few_points(self) -> None:
        points = [
            GeoPoint3D(lat=48.0, lon=16.0),
            GeoPoint3D(lat=48.1, lon=16.1),
            GeoPoint3D(lat=48.2, lon=16.2),
        ]
        result = resample_route_points(points, spacing_km=1.0, max_points=50)
        assert len(result) == 3

    def test_resample_route_points_max_points_cap(self) -> None:
        points = [GeoPoint3D(lat=48.0 + i * 0.001, lon=16.0) for i in range(100)]
        result = resample_route_points(points, spacing_km=0.001, max_points=10)
        assert len(result) <= 10

    def test_open_meteo_status_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION", None)
        status = open_meteo_status()
        assert status.name == "open_meteo_elevation"
        assert status.configured is False
        assert status.available is False

    def test_open_meteo_status_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION"] = "true"
        try:
            status = open_meteo_status()
            assert status.configured is True
            assert status.available is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION"]

    def test_fetch_elevation_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION", None)
        from app.services.elevation import fetch_elevation

        result = fetch_elevation([(48.2, 16.37)])
        assert result is None

    def test_enrich_without_elevation_returns_unchanged(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION", None)
        from app.services.elevation import enrich_route_with_elevation

        geometry = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=None),
            GeoPoint3D(lat=48.1, lon=16.1, elevation_m=None),
        ]
        result = enrich_route_with_elevation(geometry)
        assert len(result) == 2
        assert result[0].elevation_m is None


class TestOSRMRoutingDisabled:
    def test_fetch_osrm_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM", None)
        from app.services.osrm_routing import fetch_osrm_route

        request = RouteRequest(
            start_coord=GeoPoint(lat=48.2, lon=16.37),
            destination_coord=GeoPoint(lat=48.3, lon=16.3),
            profile="car_fastest",
        )
        result = fetch_osrm_route(request)
        assert result is None

    def test_osrm_status_disabled(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM", None)
        from app.services.osrm_routing import osrm_status

        status = osrm_status()
        assert status.name == "osrm"
        assert status.configured is False
        assert status.available is False

    def test_osrm_status_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM"] = "true"
        try:
            from app.services.osrm_routing import osrm_status

            status = osrm_status()
            assert status.configured is True
            assert status.available is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM"]


class TestDemoProviderStillWorks:
    def test_demo_provider_unchanged(self) -> None:
        from app.services.routing import DemoRoutingProvider

        provider = DemoRoutingProvider()
        status = provider.status()
        assert status.name == "demo"
        assert status.available is True

        routes = provider.list_routes()
        assert "city_commute" in routes
        assert "hilly_commute" in routes
        assert "highway_route" in routes

    def test_demo_geocode_works(self) -> None:
        from app.services.routing import DemoRoutingProvider

        provider = DemoRoutingProvider()
        result = provider.geocode("demo city start")
        assert len(result) > 0
        assert result[0].provider == "demo"

    def test_demo_route_city(self) -> None:
        from app.services.routing import DemoRoutingProvider

        provider = DemoRoutingProvider()
        request = RouteRequest(
            start_text="demo city start",
            destination_text="demo city destination",
            profile="car_fastest",
            provider="demo",
        )
        route = provider.route(request)
        assert route is not None
        assert route.summary_distance_km > 0
