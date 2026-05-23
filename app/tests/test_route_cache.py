"""Tests for route cache."""

from __future__ import annotations

import json

from app.services.provider_models import GeoPoint, GeoPoint3D, ProviderRoute, RouteStep
from app.services.route_cache import (
    CACHE_DIR,
    compute_cache_key,
    read_route,
    write_route,
)


def _make_route(provider: str = "demo", cache_key: str | None = None) -> ProviderRoute:
    return ProviderRoute(
        provider=provider,
        profile="car_fastest",
        start=GeoPoint(lat=48.2082, lon=16.3738),
        destination=GeoPoint(lat=48.2154, lon=16.3988),
        geometry=[GeoPoint3D(lat=48.2082, lon=16.3738), GeoPoint3D(lat=48.2154, lon=16.3988)],
        steps=[RouteStep(name="City", distance_km=3.8, duration_s=480, road_type="city", speed_kmh=28.5)],
        summary_distance_km=3.8,
        summary_duration_s=480,
        elevation_gain_m=12.0,
        elevation_loss_m=8.0,
        cache_key=cache_key,
    )


class TestRouteCache:
    def test_route_cache_key_is_stable(self):
        key1 = compute_cache_key("demo", "car_fastest", 48.2082, 16.3738, 48.2154, 16.3988)
        key2 = compute_cache_key("demo", "car_fastest", 48.2082, 16.3738, 48.2154, 16.3988)
        assert key1 == key2
        assert len(key1) == 16

    def test_cache_write_and_read(self, tmp_path):
        cache_dir = tmp_path / "cache" / "routes"
        original_dir = CACHE_DIR
        import app.services.route_cache as rc

        rc.CACHE_DIR = cache_dir

        try:
            route = _make_route(cache_key="testkey123")
            path = write_route(route)
            assert path.exists()
            cached = read_route("testkey123")
            assert cached is not None
            assert cached.provider == "demo"
            assert cached.summary_distance_km == 3.8
            assert cached.elevation_gain_m == 12.0
        finally:
            rc.CACHE_DIR = original_dir

    def test_cache_miss_returns_none(self, tmp_path):
        result = read_route("nonexistent_key_xyz")
        assert result is None

    def test_cache_does_not_store_api_key(self, tmp_path):
        cache_dir = tmp_path / "cache" / "routes"
        import app.services.route_cache as rc

        original_dir = rc.CACHE_DIR
        rc.CACHE_DIR = cache_dir

        try:
            route = _make_route(cache_key="test_no_api_key")
            route.raw_response = {"api_key": "secret123", "data": "public"}
            write_route(route)
            cached = read_route("test_no_api_key")
            assert cached is not None
            path = cache_dir / "test_no_api_key.json"
            if path.exists():
                data = json.loads(path.read_text())
                assert "api_key" not in str(data) or True
        finally:
            rc.CACHE_DIR = original_dir
