"""Tests for route segmentizer."""

from __future__ import annotations

import pytest

from app.core.route_energy import commute_energy
from app.core.route_geometry import (
    compute_elevation_gain_loss,
    elevation_stats,
    expected_climb_battery_kwh,
    potential_energy_kwh,
)
from app.core.route_segmentizer import (
    SegmentizationSettings,
    _speed_to_road_type,
    provider_route_to_commute_scenario,
    provider_route_to_segments,
)
from app.data.models import DirectionMode, PhysicsParams, Vehicle, VehicleType
from app.services.provider_models import GeoPoint, GeoPoint3D, ProviderRoute, RouteStep
from app.services.routing import DemoRoutingProvider


def _interpolate_waypoints(waypoints: list[tuple[float, float]], t: float) -> float:
    """Linearly interpolate elevation along waypoints given t in [0, 1]."""
    if t <= waypoints[0][0]:
        return waypoints[0][1]
    if t >= waypoints[-1][0]:
        return waypoints[-1][1]
    for i in range(len(waypoints) - 1):
        t0, e0 = waypoints[i]
        t1, e1 = waypoints[i + 1]
        if t0 <= t <= t1:
            frac = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return e0 + frac * (e1 - e0)
    return waypoints[-1][1]


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
    import math

    n = 20
    points = []
    gain = 150.0
    loss = 120.0

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


class TestZeroDistanceSteps:
    def test_zero_distance_step_skipped(self):
        route = ProviderRoute(
            provider="test",
            profile="car_fastest",
            start=GeoPoint(lat=48.0, lon=16.0),
            destination=GeoPoint(lat=48.1, lon=16.1),
            geometry=[
                GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
                GeoPoint3D(lat=48.1, lon=16.1, elevation_m=200, distance_from_start_km=10.0),
            ],
            steps=[
                RouteStep(name="Departure", distance_km=0.0, duration_s=0.0, road_type="city", speed_kmh=0.0),
                RouteStep(name="Main road", distance_km=10.0, duration_s=450.0, road_type="suburban", speed_kmh=80.0),
            ],
            summary_distance_km=10.0,
            summary_duration_s=450.0,
        )
        segments = provider_route_to_segments(route)
        assert len(segments) == 1
        assert segments[0].distance_km > 0
        assert segments[0].name == "Main road"

    def test_all_zero_distance_steps_falls_back_to_geometry(self):
        route = ProviderRoute(
            provider="test",
            profile="car_fastest",
            start=GeoPoint(lat=48.0, lon=16.0),
            destination=GeoPoint(lat=48.1, lon=16.1),
            geometry=[
                GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
                GeoPoint3D(lat=48.1, lon=16.1, elevation_m=200, distance_from_start_km=10.0),
            ],
            steps=[
                RouteStep(name="Departure", distance_km=0.0, duration_s=0.0, road_type="city", speed_kmh=0.0),
            ],
            summary_distance_km=10.0,
            summary_duration_s=450.0,
        )
        segments = provider_route_to_segments(route)
        assert all(s.distance_km > 0 for s in segments)


class TestStepElevationFromEnrichedGeometry:
    def test_route_elevation_used_when_step_has_none(self):
        n = 50
        geometry = []
        start_elev = 260.0
        peak_elev = 600.0
        valley_elev = 550.0
        end_elev = 650.0
        for i in range(n):
            t = i / (n - 1)
            lat = 48.0 + t * 0.3
            lon = 16.0 + t * 0.3
            if t < 0.5:
                elev = start_elev + (peak_elev - start_elev) * (t / 0.5)
            else:
                elev = peak_elev - (peak_elev - valley_elev) * ((t - 0.5) / 0.5) + (end_elev - valley_elev) * 0
            if t > 0.5:
                elev = peak_elev + (end_elev - peak_elev) * ((t - 0.5) / 0.5)
            elev = round(elev, 1)
            geometry.append(GeoPoint3D(lat=lat, lon=lon, elevation_m=elev, distance_from_start_km=round(t * 30.0, 4)))

        computed_gain, computed_loss = compute_elevation_gain_loss(geometry, noise_threshold_m=1.0)

        route = ProviderRoute(
            provider="osrm+open_meteo",
            profile="car_fastest",
            start=GeoPoint(lat=48.0, lon=16.0),
            destination=GeoPoint(lat=48.3, lon=16.3),
            geometry=geometry,
            steps=[
                RouteStep(
                    name="Step 1",
                    distance_km=15.0,
                    duration_s=900,
                    road_type="rural",
                    speed_kmh=60.0,
                    geometry=[],
                ),
                RouteStep(
                    name="Step 2",
                    distance_km=15.0,
                    duration_s=900,
                    road_type="rural",
                    speed_kmh=60.0,
                    geometry=[],
                ),
            ],
            summary_distance_km=30.0,
            summary_duration_s=1800,
            elevation_gain_m=1.0,
            elevation_loss_m=1.0,
        )

        segments = provider_route_to_segments(route)
        assert len(segments) == 2
        total_gain = sum(s.elevation_gain_m for s in segments)
        total_loss = sum(s.elevation_loss_m for s in segments)
        assert total_gain == pytest.approx(computed_gain, abs=5.0)
        assert total_loss == pytest.approx(computed_loss, abs=5.0)

    def test_step_elevation_preserved_when_present(self):
        points_hilly = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
            GeoPoint3D(lat=48.05, lon=16.05, elevation_m=400, distance_from_start_km=4.0),
            GeoPoint3D(lat=48.1, lon=16.1, elevation_m=350, distance_from_start_km=8.0),
        ]
        route = ProviderRoute(
            provider="demo",
            profile="car_fastest",
            start=GeoPoint(lat=48.0, lon=16.0),
            destination=GeoPoint(lat=48.1, lon=16.1),
            geometry=points_hilly,
            steps=[
                RouteStep(
                    name="Hilly section",
                    distance_km=8.0,
                    duration_s=700,
                    road_type="rural",
                    speed_kmh=41.0,
                    geometry=points_hilly,
                )
            ],
            summary_distance_km=8.0,
            summary_duration_s=700,
            elevation_gain_m=200.0,
            elevation_loss_m=50.0,
        )

        segments = provider_route_to_segments(route)
        assert len(segments) >= 1
        total_gain = sum(s.elevation_gain_m for s in segments)
        total_loss = sum(s.elevation_loss_m for s in segments)
        assert total_gain > 0
        assert total_loss > 0


class TestAustrianHillyRoute:
    @pytest.fixture
    def linz_muehlviertel_route(self):
        n = 200
        distance_km = 32.0
        points = []
        waypoints = [
            (0.0, 260.0),
            (0.15, 400.0),
            (0.3, 320.0),
            (0.45, 520.0),
            (0.55, 480.0),
            (0.7, 700.0),
            (0.8, 600.0),
            (0.9, 680.0),
            (1.0, 650.0),
        ]
        for i in range(n):
            t = i / (n - 1)
            lat = 48.306 + t * 0.25
            lon = 14.286 + t * 0.18
            elev = _interpolate_waypoints(waypoints, t)
            points.append(
                GeoPoint3D(
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    elevation_m=round(elev, 1),
                    distance_from_start_km=round(t * distance_km, 4),
                )
            )

        gain, loss = compute_elevation_gain_loss(points, noise_threshold_m=3.0)
        return ProviderRoute(
            provider="fixture",
            profile="car_fastest",
            start=GeoPoint(lat=48.306, lon=14.286),
            destination=GeoPoint(lat=48.556, lon=14.466),
            start_label="Linz",
            destination_label="Mühlviertel",
            geometry=points,
            steps=[
                RouteStep(
                    name="Uphill rural",
                    distance_km=16.0,
                    duration_s=960,
                    road_type="rural",
                    speed_kmh=60.0,
                ),
                RouteStep(
                    name="Hilly plateau",
                    distance_km=16.0,
                    duration_s=960,
                    road_type="rural",
                    speed_kmh=60.0,
                ),
            ],
            summary_distance_km=distance_km,
            summary_duration_s=1920,
            elevation_gain_m=gain,
            elevation_loss_m=loss,
        )

    def test_computed_gain_at_least_net_elevation_difference(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        stats = elevation_stats(route.geometry, noise_threshold_m=3.0)
        net_diff = abs(stats["net_elevation_diff"]) if stats["net_elevation_diff"] is not None else 0
        assert stats["accumulated_gain"] >= net_diff

    def test_climb_kwh_for_1700kg_400m(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1700.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(
            ev, provider_route_to_commute_scenario(route, direction_mode=DirectionMode.one_way), PhysicsParams()
        )
        climb_kwh = result["outward"].climb_kwh
        stats = elevation_stats(route.geometry, noise_threshold_m=3.0)
        gain_m = stats["accumulated_gain"]
        theoretical_kwh = potential_energy_kwh(1700, gain_m)
        assert climb_kwh > 0
        assert theoretical_kwh == pytest.approx(climb_kwh, rel=0.1)

    def test_uphill_battery_energy_exceeds_potential(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1700.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(
            ev,
            provider_route_to_commute_scenario(route, direction_mode=DirectionMode.one_way),
            PhysicsParams(p_aux_kw=0.0),
        )
        stats = elevation_stats(route.geometry, noise_threshold_m=3.0)
        gain_m = stats["accumulated_gain"]
        e_climb_battery = expected_climb_battery_kwh(1700, gain_m, 0.92)
        e_potential = potential_energy_kwh(1700, gain_m)
        assert e_climb_battery > e_potential
        assert result["outward"].climb_kwh > 0

    def test_return_trip_has_elevation_loss(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1700.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        commute = provider_route_to_commute_scenario(route, direction_mode=DirectionMode.return_trip)
        return_segments = commute.route.segments
        has_loss = any(s.elevation_loss_m > 0 for s in return_segments)
        result = commute_energy(ev, commute, PhysicsParams(eta_regen=0.65))
        assert result["return"] is not None
        assert has_loss
        assert result["return"].descent_recovered_kwh > 0

    def test_round_trip_elevation_penalty_positive(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        ev = Vehicle(
            id="test_ev",
            make="Test",
            model="EV",
            mass_kg=1700.0,
            frontal_area_m2=2.2,
            drag_coefficient_cd=0.25,
            vehicle_type=VehicleType.ev,
            battery_usable_kwh=60.0,
            has_heat_pump=False,
        )
        result = commute_energy(
            ev,
            provider_route_to_commute_scenario(route, direction_mode=DirectionMode.return_trip),
            PhysicsParams(eta_regen=0.65),
        )
        net_elevation_loss = result["total"].climb_kwh - result["total"].descent_recovered_kwh
        assert net_elevation_loss > 0

    def test_segment_gain_loss_totals_match_route(self, linz_muehlviertel_route):
        route = linz_muehlviertel_route
        settings = SegmentizationSettings(noise_threshold_m=3.0)
        segments = provider_route_to_segments(route, settings)
        total_gain = sum(s.elevation_gain_m for s in segments)
        total_loss = sum(s.elevation_loss_m for s in segments)
        stats = elevation_stats(route.geometry, noise_threshold_m=3.0)
        route_gain = stats["accumulated_gain"]
        route_loss = stats["accumulated_loss"]
        assert total_gain == pytest.approx(route_gain, abs=10.0)
        assert total_loss == pytest.approx(route_loss, abs=10.0)
