"""Tests for route segmentizer."""

from __future__ import annotations

import pytest

from app.core.route_energy import commute_energy
from app.core.route_segmentizer import (
    SegmentizationSettings,
    _speed_to_road_type,
    provider_route_to_commute_scenario,
    provider_route_to_segments,
)
from app.data.models import DirectionMode, PhysicsParams, Vehicle, VehicleType
from app.services.provider_models import GeoPoint, GeoPoint3D, ProviderRoute, RouteStep
from app.services.routing import DemoRoutingProvider


def _flat_route(distance_km: float = 10.0, speed_kmh: float = 80.0) -> ProviderRoute:
    return ProviderRoute(
        provider="test",
        profile="car_fastest",
        start=GeoPoint(lat=48.0, lon=16.0),
        destination=GeoPoint(lat=48.1, lon=16.1),
        geometry=[
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
            GeoPoint3D(lat=48.1, lon=16.1, elevation_m=200, distance_from_start_km=distance_km),
        ],
        steps=[
            RouteStep(
                name="Flat",
                distance_km=distance_km,
                duration_s=distance_km / speed_kmh * 3600,
                road_type="rural",
                speed_kmh=speed_kmh,
            )
        ],
        summary_distance_km=distance_km,
        summary_duration_s=distance_km / speed_kmh * 3600,
        elevation_gain_m=0.0,
        elevation_loss_m=0.0,
    )


def _hilly_route() -> ProviderRoute:
    n = 20
    points = []
    gain = 150.0
    loss = 120.0
    import math

    for i in range(n + 1):
        t = i / n
        lat = 48.0 + t * 0.1
        lon = 16.0 + t * 0.1
        hill = gain * math.sin(t * math.pi)
        net = (gain - loss) * t
        elev = 200 + net + hill
        dist = t * 8.0
        points.append(
            GeoPoint3D(
                lat=round(lat, 6), lon=round(lon, 6), elevation_m=round(elev, 1), distance_from_start_km=round(dist, 4)
            )
        )
    return ProviderRoute(
        provider="test",
        profile="car_fastest",
        start=GeoPoint(lat=48.0, lon=16.0),
        destination=GeoPoint(lat=48.1, lon=16.1),
        geometry=points,
        steps=[
            RouteStep(name="Hilly", distance_km=8.0, duration_s=700, road_type="rural", speed_kmh=41.0, geometry=points)
        ],
        summary_distance_km=8.0,
        summary_duration_s=700,
        elevation_gain_m=150.0,
        elevation_loss_m=120.0,
    )


class TestSpeedToRoadType:
    def test_city_speed(self):
        from app.data.models import RoadType

        assert _speed_to_road_type(30) == RoadType.city
        assert _speed_to_road_type(45) == RoadType.city

    def test_rural_speed(self):
        from app.data.models import RoadType

        assert _speed_to_road_type(60) == RoadType.rural
        assert _speed_to_road_type(75) == RoadType.rural

    def test_highway_speed(self):
        from app.data.models import RoadType

        assert _speed_to_road_type(120) == RoadType.highway
        assert _speed_to_road_type(130) == RoadType.highway


class TestStopsPerKm:
    def test_city_stops(self):

        settings = SegmentizationSettings()
        assert settings.default_stops_per_km["city"] == 2.0

    def test_highway_no_stops(self):
        settings = SegmentizationSettings()
        assert settings.default_stops_per_km["highway"] == 0.0


class TestFlatRouteSegmentCount:
    def test_flat_route_becomes_expected_segment_count(self):
        route = _flat_route()
        segments = provider_route_to_segments(route)
        assert len(segments) >= 1
        assert segments[0].distance_km > 0
        assert segments[0].avg_speed_kmh > 0

    def test_speed_from_step_duration(self):
        route = _flat_route(distance_km=10.0, speed_kmh=80.0)
        segments = provider_route_to_segments(route)
        assert segments[0].avg_speed_kmh == pytest.approx(80.0, rel=0.01)

    def test_fallback_average_speed_when_no_steps(self):
        route = ProviderRoute(
            provider="test",
            profile="car_fastest",
            start=GeoPoint(lat=48.0, lon=16.0),
            destination=GeoPoint(lat=48.1, lon=16.1),
            geometry=[
                GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
                GeoPoint3D(lat=48.1, lon=16.1, elevation_m=200, distance_from_start_km=10.0),
            ],
            steps=[],
            summary_distance_km=10.0,
            summary_duration_s=450,
        )
        segments = provider_route_to_segments(route)
        assert len(segments) >= 1
        assert segments[0].avg_speed_kmh == pytest.approx(80.0, rel=0.01)

    def test_route_segments_have_positive_distance_and_speed(self):
        route = _flat_route()
        for seg in provider_route_to_segments(route):
            assert seg.distance_km > 0
            assert seg.avg_speed_kmh > 0

    def test_slope_change_splits_segment(self):
        route = _hilly_route()
        segments = provider_route_to_segments(route, SegmentizationSettings(noise_threshold_m=1.0))
        assert len(segments) >= 1
        assert any(s.elevation_gain_m > 0 for s in segments) or any(s.elevation_loss_m > 0 for s in segments)


class TestProviderRouteToEnergy:
    def test_provider_route_to_energy_flat_route_matches_manual_route(self):
        route = _flat_route(distance_km=25.0, speed_kmh=80.0)
        commute = provider_route_to_commute_scenario(route, direction_mode=DirectionMode.one_way)
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1800.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(ev, commute, PhysicsParams())
        assert result["total"].total_battery_kwh > 0
        assert result["total"].distance_km == pytest.approx(25.0, rel=0.01)
        assert result["total"].kwh_per_100km > 0

    def test_hilly_return_trip_has_energy_loss_despite_net_zero_height(self):
        route = _hilly_route()
        commute = provider_route_to_commute_scenario(route, direction_mode=DirectionMode.return_trip)
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1800.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(ev, commute, PhysicsParams(eta_regen=0.65))
        assert result["total"].total_battery_kwh > 0
        assert result["total"].climb_kwh > 0

    def test_downhill_recovery_is_less_than_climb_energy(self):
        route = _hilly_route()
        commute = provider_route_to_commute_scenario(route, direction_mode=DirectionMode.one_way)
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1800.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(ev, commute, PhysicsParams(eta_regen=0.65))
        outward = result["outward"]
        assert outward.descent_recovered_kwh <= outward.climb_kwh

    def test_headwind_changes_aero_energy(self):
        route_no_wind = _flat_route(distance_km=20.0, speed_kmh=100.0)
        commute_no_wind = provider_route_to_commute_scenario(route_no_wind, direction_mode=DirectionMode.one_way)
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1800.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        for seg in commute_no_wind.route.segments:
            seg.headwind_kmh = 0.0
        result_no_wind = commute_energy(ev, commute_no_wind, PhysicsParams())

        commute_wind = provider_route_to_commute_scenario(route_no_wind, direction_mode=DirectionMode.one_way)
        for seg in commute_wind.route.segments:
            seg.headwind_kmh = 20.0
        result_wind = commute_energy(ev, commute_wind, PhysicsParams())

        assert result_wind["total"].aero_kwh > result_no_wind["total"].aero_kwh


class TestDemoProvider:
    def test_demo_provider_city_route(self):
        provider = DemoRoutingProvider()
        route = provider.route(
            __import__("app.services.provider_models", fromlist=["RouteRequest"]).RouteRequest(
                start_text="demo city start",
                destination_text="demo city destination",
            )
        )
        assert route is not None
        assert route.summary_distance_km > 0
        assert len(route.geometry) > 0

    def test_demo_provider_hilly_route(self):
        provider = DemoRoutingProvider()
        route = provider.route(
            __import__("app.services.provider_models", fromlist=["RouteRequest"]).RouteRequest(
                start_text="demo hilly start",
                destination_text="demo hilly destination",
            )
        )
        assert route is not None
        assert route.elevation_gain_m is not None
        assert route.elevation_gain_m > 0

    def test_demo_provider_status(self):
        provider = DemoRoutingProvider()
        status = provider.status()
        assert status.name == "demo"
        assert status.available is True
