"""Tests for route geometry helpers."""

from __future__ import annotations

import pytest

from app.core.route_geometry import (
    compute_elevation_gain_loss,
    cumulative_distances_km,
    estimate_bearing_degrees,
    haversine_distance_km,
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
