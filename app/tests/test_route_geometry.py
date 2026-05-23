"""Tests for route geometry helpers."""

from __future__ import annotations

import pytest

from app.core.route_geometry import (
    compute_elevation_gain_loss,
    cumulative_distances_km,
    elevation_stats,
    estimate_bearing_degrees,
    expected_climb_battery_kwh,
    expected_descent_recovered_kwh,
    haversine_distance_km,
    potential_energy_kwh,
    resample_route_points,
)
from app.services.provider_models import GeoPoint, GeoPoint3D


class TestHaversineDistance:
    def test_haversine_distance_zero(self):
        a = GeoPoint(lat=48.2, lon=16.37)
        result = haversine_distance_km(a, a)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_haversine_distance_known_values(self):
        vienna = GeoPoint(lat=48.2082, lon=16.3738)
        graz = GeoPoint(lat=47.0707, lon=15.4395)
        dist = haversine_distance_km(vienna, graz)
        assert 140 < dist < 160

    def test_haversine_distance_short(self):
        a = GeoPoint(lat=48.2082, lon=16.3738)
        b = GeoPoint(lat=48.2154, lon=16.3988)
        dist = haversine_distance_km(a, b)
        assert 1.5 < dist < 3.0

    def test_haversine_symmetry(self):
        a = GeoPoint(lat=48.2, lon=16.37)
        b = GeoPoint(lat=48.3, lon=16.4)
        assert haversine_distance_km(a, b) == pytest.approx(haversine_distance_km(b, a), rel=1e-10)


class TestCumulativeDistance:
    def test_cumulative_distance_monotonic(self):
        points = [
            GeoPoint3D(lat=48.2082, lon=16.3738, elevation_m=200),
            GeoPoint3D(lat=48.2100, lon=16.3800, elevation_m=210),
            GeoPoint3D(lat=48.2154, lon=16.3988, elevation_m=195),
        ]
        dists = cumulative_distances_km(points)
        assert dists[0] == 0.0
        assert dists[1] > 0
        assert dists[2] > dists[1]
        assert all(d1 <= d2 for d1, d2 in zip(dists, dists[1:], strict=False))

    def test_cumulative_distance_single_point(self):
        points = [GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200)]
        dists = cumulative_distances_km(points)
        assert dists == [0.0]

    def test_cumulative_distance_empty(self):
        assert cumulative_distances_km([]) == []


class TestElevationGainLoss:
    def test_flat_route_no_gain_loss(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200),
            GeoPoint3D(lat=48.21, lon=16.38, elevation_m=200),
            GeoPoint3D(lat=48.22, lon=16.39, elevation_m=200),
        ]
        gain, loss = compute_elevation_gain_loss(points, noise_threshold_m=3.0)
        assert gain == pytest.approx(0.0, abs=1e-6)
        assert loss == pytest.approx(0.0, abs=1e-6)

    def test_uphill_route_has_gain(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200),
            GeoPoint3D(lat=48.21, lon=16.38, elevation_m=220),
            GeoPoint3D(lat=48.22, lon=16.39, elevation_m=250),
        ]
        gain, loss = compute_elevation_gain_loss(points, noise_threshold_m=3.0)
        assert gain > 0
        assert loss == pytest.approx(0.0, abs=1e-6)

    def test_downhill_route_has_loss(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=300),
            GeoPoint3D(lat=48.21, lon=16.38, elevation_m=280),
            GeoPoint3D(lat=48.22, lon=16.39, elevation_m=250),
        ]
        gain, loss = compute_elevation_gain_loss(points, noise_threshold_m=3.0)
        assert gain == pytest.approx(0.0, abs=1e-6)
        assert loss > 0

    def test_elevation_gain_loss_with_noise_threshold(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200),
            GeoPoint3D(lat=48.21, lon=16.38, elevation_m=202),
            GeoPoint3D(lat=48.22, lon=16.39, elevation_m=200),
        ]
        gain_1, loss_1 = compute_elevation_gain_loss(points, noise_threshold_m=5.0)
        assert gain_1 == 0.0
        assert loss_1 == 0.0

        gain_2, loss_2 = compute_elevation_gain_loss(points, noise_threshold_m=0.5)
        assert gain_2 > 0
        assert loss_2 > 0

    def test_none_elevation_ignored(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200),
            GeoPoint3D(lat=48.21, lon=16.38, elevation_m=None),
            GeoPoint3D(lat=48.22, lon=16.39, elevation_m=250),
        ]
        gain, loss = compute_elevation_gain_loss(points, noise_threshold_m=3.0)
        assert gain == 0.0
        assert loss == 0.0


class TestResample:
    def test_resample_preserves_start_end(self):
        points = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=100),
            GeoPoint3D(lat=48.2, lon=16.1, elevation_m=200),
            GeoPoint3D(lat=48.4, lon=16.2, elevation_m=300),
        ]
        resampled = resample_route_points(points, target_spacing_km=0.5)
        assert resampled[0].lat == pytest.approx(48.0, abs=0.01)
        assert resampled[0].lon == pytest.approx(16.0, abs=0.01)
        assert resampled[-1].lat == pytest.approx(48.4, abs=0.01)
        assert resampled[-1].lon == pytest.approx(16.2, abs=0.01)

    def test_resample_single_point(self):
        points = [GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200)]
        result = resample_route_points(points, target_spacing_km=1.0)
        assert len(result) == 1

    def test_resample_two_points(self):
        points = [
            GeoPoint3D(lat=48.2, lon=16.37, elevation_m=200),
            GeoPoint3D(lat=48.3, lon=16.40, elevation_m=220),
        ]
        result = resample_route_points(points, target_spacing_km=1.0)
        assert len(result) >= 2


class TestBearing:
    def test_bearing_east(self):
        a = GeoPoint(lat=48.0, lon=16.0)
        b = GeoPoint(lat=48.0, lon=17.0)
        bearing = estimate_bearing_degrees(a, b)
        assert 80 < bearing < 100

    def test_bearing_north(self):
        a = GeoPoint(lat=48.0, lon=16.0)
        b = GeoPoint(lat=49.0, lon=16.0)
        bearing = estimate_bearing_degrees(a, b)
        assert bearing > 350 or bearing < 10


class TestElevationStats:
    def test_flat_route(self):
        points = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
            GeoPoint3D(lat=48.01, lon=16.01, elevation_m=200, distance_from_start_km=1.0),
            GeoPoint3D(lat=48.02, lon=16.02, elevation_m=200, distance_from_start_km=2.0),
        ]
        stats = elevation_stats(points)
        assert stats["start_elevation"] == 200.0
        assert stats["end_elevation"] == 200.0
        assert stats["net_elevation_diff"] == 0.0
        assert stats["min_elevation"] == 200.0
        assert stats["max_elevation"] == 200.0
        assert stats["accumulated_gain"] == 0.0
        assert stats["accumulated_loss"] == 0.0
        assert stats["sample_count"] == 3
        assert stats["noise_threshold"] == 3.0

    def test_uphill_route(self):
        points = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=260, distance_from_start_km=0.0),
            GeoPoint3D(lat=48.01, lon=16.01, elevation_m=400, distance_from_start_km=1.0),
            GeoPoint3D(lat=48.02, lon=16.02, elevation_m=600, distance_from_start_km=2.0),
        ]
        stats = elevation_stats(points, noise_threshold_m=1.0)
        assert stats["start_elevation"] == 260.0
        assert stats["end_elevation"] == 600.0
        assert stats["net_elevation_diff"] == 340.0
        assert stats["accumulated_gain"] > 0
        assert stats["accumulated_loss"] >= 0

    def test_none_elevation_returns_nones(self):
        points = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=None),
            GeoPoint3D(lat=48.01, lon=16.01, elevation_m=None),
        ]
        stats = elevation_stats(points)
        assert stats["start_elevation"] is None
        assert stats["end_elevation"] is None
        assert stats["net_elevation_diff"] is None
        assert stats["min_elevation"] is None
        assert stats["max_elevation"] is None
        assert stats["accumulated_gain"] == 0.0
        assert stats["accumulated_loss"] == 0.0

    def test_sample_count_includes_all_points(self):
        points = [GeoPoint3D(lat=48.0 + i * 0.01, lon=16.0, elevation_m=200 + i * 10) for i in range(10)]
        stats = elevation_stats(points)
        assert stats["sample_count"] == 10


class TestPotentialEnergy:
    def test_known_value(self):
        result = potential_energy_kwh(1700, 400)
        assert result == pytest.approx(1.85, abs=0.01)

    def test_1000kg_100m(self):
        result = potential_energy_kwh(1000, 100)
        assert result == pytest.approx(0.2725, abs=0.005)

    def test_zero_height(self):
        assert potential_energy_kwh(1700, 0) == pytest.approx(0.0, abs=1e-10)


class TestClimbBatteryKwh:
    def test_divides_by_eta(self):
        e_pot = potential_energy_kwh(1700, 400)
        e_bat = expected_climb_battery_kwh(1700, 400, 0.92)
        assert e_bat == pytest.approx(e_pot / 0.92, rel=0.001)

    def test_known_value(self):
        result = expected_climb_battery_kwh(1700, 400, 0.92)
        assert result == pytest.approx(2.011, abs=0.01)


class TestDescentRecovered:
    def test_multiplies_by_eta(self):
        e_pot = potential_energy_kwh(1700, 400)
        e_rec = expected_descent_recovered_kwh(1700, 400, 0.65)
        assert e_rec == pytest.approx(e_pot * 0.65, rel=0.001)

    def test_known_value(self):
        result = expected_descent_recovered_kwh(1700, 400, 0.65)
        assert result == pytest.approx(1.2025, abs=0.01)


class TestElevationResampleEndpoint:
    def test_last_point_always_retained_when_over_max(self):
        n = 100
        points = [
            GeoPoint3D(
                lat=48.0 + i * 0.001,
                lon=16.0 + i * 0.001,
                elevation_m=200 + i * 5,
                distance_from_start_km=i * 0.1,
            )
            for i in range(n)
        ]
        from app.services.elevation import resample_route_points

        result = resample_route_points(points, spacing_km=1.0, max_points=50)
        first_point = (points[0].lat, points[0].lon)
        last_point = (points[-1].lat, points[-1].lon)
        assert result[0] == pytest.approx(first_point, abs=1e-6)
        assert result[-1] == pytest.approx(last_point, abs=1e-6)

    def test_small_route_preserved_under_max(self):
        points = [
            GeoPoint3D(lat=48.0, lon=16.0, elevation_m=200, distance_from_start_km=0.0),
            GeoPoint3D(lat=48.01, lon=16.01, elevation_m=250, distance_from_start_km=1.3),
            GeoPoint3D(lat=48.02, lon=16.02, elevation_m=300, distance_from_start_km=2.6),
        ]
        from app.services.elevation import resample_route_points

        result = resample_route_points(points, spacing_km=1.0, max_points=50)
        assert len(result) == 3
        assert result[0] == (points[0].lat, points[0].lon)
        assert result[-1] == (points[-1].lat, points[-1].lon)

    def test_max_points_applies_to_intermediates_not_endpoints(self):
        n = 200
        points = [
            GeoPoint3D(
                lat=48.0 + i * 0.0005,
                lon=16.0 + i * 0.0005,
                elevation_m=200 + i * 2,
                distance_from_start_km=i * 0.05,
            )
            for i in range(n)
        ]
        from app.services.elevation import resample_route_points

        max_pts = 20
        result = resample_route_points(points, spacing_km=0.5, max_points=max_pts)
        first_point = (points[0].lat, points[0].lon)
        last_point = (points[-1].lat, points[-1].lon)
        assert result[0] == pytest.approx(first_point, abs=1e-6)
        assert result[-1] == pytest.approx(last_point, abs=1e-6)
        assert len(result) <= max_pts + 1
