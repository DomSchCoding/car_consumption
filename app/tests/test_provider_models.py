"""Tests for provider models."""

from __future__ import annotations

from app.services.provider_models import (
    GeoPoint,
    GeoPoint3D,
    ProviderRoute,
    ProviderStatus,
    RouteSourceKind,
    RouteStep,
)


class TestGeoPoint:
    def test_geopoint_validation_valid(self):
        p = GeoPoint(lat=48.2, lon=16.37)
        assert p.lat == 48.2
        assert p.lon == 16.37

    def test_geopoint_validation_zero(self):
        p = GeoPoint(lat=0.0, lon=0.0)
        assert p.lat == 0.0
        assert p.lon == 0.0

    def test_geopoint3d_with_elevation(self):
        p = GeoPoint3D(lat=48.2, lon=16.37, elevation_m=250.0)
        assert p.elevation_m == 250.0
        assert p.distance_from_start_km is None

    def test_geopoint3d_with_distance(self):
        p = GeoPoint3D(lat=48.2, lon=16.37, elevation_m=250.0, distance_from_start_km=1.5)
        assert p.distance_from_start_km == 1.5


class TestProviderRoute:
    def test_provider_route_minimum_fields(self):
        route = ProviderRoute(
            provider="demo",
            profile="car_fastest",
            start=GeoPoint(lat=48.2, lon=16.37),
            destination=GeoPoint(lat=48.3, lon=16.4),
            geometry=[GeoPoint3D(lat=48.2, lon=16.37), GeoPoint3D(lat=48.3, lon=16.4)],
            summary_distance_km=10.0,
            summary_duration_s=600,
        )
        assert route.provider == "demo"
        assert route.summary_distance_km == 10.0
        assert route.warnings == []
        assert route.elevation_gain_m is None
        assert route.elevation_loss_m is None

    def test_provider_route_with_steps(self):
        route = ProviderRoute(
            provider="demo",
            profile="car_fastest",
            start=GeoPoint(lat=48.2, lon=16.37),
            destination=GeoPoint(lat=48.3, lon=16.4),
            geometry=[GeoPoint3D(lat=48.2, lon=16.37), GeoPoint3D(lat=48.3, lon=16.4)],
            steps=[RouteStep(name="City", distance_km=10.0, duration_s=600, road_type="city", speed_kmh=30.0)],
            summary_distance_km=10.0,
            summary_duration_s=600,
            elevation_gain_m=50.0,
            elevation_loss_m=30.0,
        )
        assert len(route.steps) == 1
        assert route.steps[0].speed_kmh == 30.0
        assert route.elevation_gain_m == 50.0

    def test_route_request_hash_stability(self):
        from app.services.route_cache import compute_cache_key

        key1 = compute_cache_key("demo", "car_fastest", 48.2082, 16.3738, 48.2154, 16.3988)
        key2 = compute_cache_key("demo", "car_fastest", 48.2082, 16.3738, 48.2154, 16.3988)
        assert key1 == key2

        key3 = compute_cache_key("ors", "car_fastest", 48.2082, 16.3738, 48.2154, 16.3988)
        assert key1 != key3

        key4 = compute_cache_key("demo", "car_fastest", 48.2082, 16.3738, 48.22, 16.40)
        assert key1 != key4


class TestRouteSourceKind:
    def test_route_source_kind_values(self):
        assert RouteSourceKind.manual == "manual"
        assert RouteSourceKind.provider == "provider"
        assert RouteSourceKind.demo == "demo"
        assert RouteSourceKind.gpx == "gpx"


class TestProviderStatus:
    def test_provider_status(self):
        status = ProviderStatus(name="demo", configured=True, available=True, message="ok")
        assert status.name == "demo"
        assert status.configured is True
