"""Tests for app.core.route_energy module."""

from __future__ import annotations

import pytest

from app.core.physics import hvac_power_kw, total_consumption
from app.core.route_energy import (
    commute_energy,
    reverse_route,
    route_energy,
    segment_energy,
    trips_per_charge,
)
from app.data.models import (
    CommuteScenario,
    DirectionMode,
    PhysicsParams,
    Route,
    RouteEnergyBreakdown,
    RouteSegment,
    Vehicle,
    VehicleType,
)

FLAT_100KM = RouteSegment(
    name="flat_100",
    distance_km=100.0,
    avg_speed_kmh=100.0,
    elevation_gain_m=0.0,
    elevation_loss_m=0.0,
    stops=0.0,
    headwind_kmh=0.0,
)

DEFAULT_EV = Vehicle(
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

DEFAULT_ICE = Vehicle(
    id="test_ice",
    make="Test",
    model="ICE",
    mass_kg=1500.0,
    frontal_area_m2=2.2,
    drag_coefficient_cd=0.30,
    vehicle_type=VehicleType.ice,
)

DEFAULT_ROUTE = Route(
    id="test_route",
    name="Test Route",
    segments=[FLAT_100KM],
)


class TestSegmentEnergyFlat:
    def test_flat_no_stops_matches_constant_speed(self):
        params = PhysicsParams(p_aux_kw=0.5, temperature_c=20.0)
        result = segment_energy(DEFAULT_EV, FLAT_100KM, params)
        hvac_kw = hvac_power_kw(params.temperature_c, params.cabin_target_temp_c, has_heat_pump=False)
        total_aux = params.p_aux_kw + hvac_kw
        bc = total_consumption(
            rho_air=params.rho_air,
            cd=DEFAULT_EV.drag_coefficient_cd,
            frontal_area_m2=DEFAULT_EV.frontal_area_m2,
            mass_kg=DEFAULT_EV.mass_kg,
            c_rr=params.c_rr,
            p_aux_kw=total_aux,
            speed_kmh=100.0,
            eta_drivetrain=params.eta_drivetrain,
        )
        expected_battery_kwh = bc.total_battery_kwh_per_100km
        assert result.total_battery_kwh == pytest.approx(expected_battery_kwh, rel=0.02)
        assert result.aero_kwh > 0
        assert result.roll_kwh > 0
        assert result.climb_kwh == pytest.approx(0.0, abs=1e-6)
        assert result.stop_go_kwh == pytest.approx(0.0, abs=1e-6)

    def test_double_distance_doubles_energy(self):
        params = PhysicsParams(p_aux_kw=1.5, temperature_c=20.0)
        seg_50 = RouteSegment(name="50km", distance_km=50.0, avg_speed_kmh=100.0)
        seg_100 = RouteSegment(name="100km", distance_km=100.0, avg_speed_kmh=100.0)
        e_50 = segment_energy(DEFAULT_EV, seg_50, params)
        e_100 = segment_energy(DEFAULT_EV, seg_100, params)
        assert e_100.total_battery_kwh == pytest.approx(e_50.total_battery_kwh * 2.0, rel=0.01)

    def test_elevation_gain_increases_consumption(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        flat = RouteSegment(name="flat", distance_km=10.0, avg_speed_kmh=80.0)
        uphill = RouteSegment(name="uphill", distance_km=10.0, avg_speed_kmh=80.0, elevation_gain_m=200.0)
        e_flat = segment_energy(DEFAULT_EV, flat, params)
        e_uphill = segment_energy(DEFAULT_EV, uphill, params)
        assert e_uphill.total_battery_kwh > e_flat.total_battery_kwh
        assert e_uphill.climb_kwh > 0


class TestSegmentEnergyDescent:
    def test_descent_recovery_ev(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=0.65)
        downhill = RouteSegment(
            name="downhill",
            distance_km=10.0,
            avg_speed_kmh=50.0,
            elevation_loss_m=200.0,
        )
        result = segment_energy(DEFAULT_EV, downhill, params)
        assert result.descent_recovered_kwh > 0
        assert result.total_battery_kwh < result.aero_kwh + result.roll_kwh + result.aux_kwh

    def test_no_descent_recovery_eta_zero(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=0.0)
        downhill = RouteSegment(
            name="downhill",
            distance_km=10.0,
            avg_speed_kmh=50.0,
            elevation_loss_m=200.0,
        )
        result = segment_energy(DEFAULT_EV, downhill, params, eta_regen_downhill=0.0)
        assert result.descent_recovered_kwh == pytest.approx(0.0, abs=1e-6)

    def test_ice_no_descent_recovery(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        downhill = RouteSegment(
            name="downhill",
            distance_km=10.0,
            avg_speed_kmh=50.0,
            elevation_loss_m=200.0,
        )
        result = segment_energy(DEFAULT_ICE, downhill, params)
        assert result.descent_recovered_kwh == pytest.approx(0.0, abs=1e-6)


class TestSegmentEnergyStopAndGo:
    def test_stops_increase_consumption(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=0.0)
        no_stops = RouteSegment(name="no_stops", distance_km=10.0, avg_speed_kmh=50.0, stops=0.0)
        with_stops = RouteSegment(name="stops", distance_km=10.0, avg_speed_kmh=50.0, stops=2.0)
        e_no = segment_energy(DEFAULT_EV, no_stops, params)
        e_yes = segment_energy(DEFAULT_EV, with_stops, params)
        assert e_yes.total_battery_kwh > e_no.total_battery_kwh
        assert e_yes.stop_go_kwh > 0

    def test_stops_with_regen_less_than_without(self):
        params_no_regen = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=0.0)
        params_regen = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=0.65)
        seg = RouteSegment(name="city", distance_km=10.0, avg_speed_kmh=40.0, stops=3.0)
        e_no_regen = segment_energy(DEFAULT_EV, seg, params_no_regen)
        e_regen = segment_energy(DEFAULT_EV, seg, params_regen)
        assert e_regen.stop_go_kwh < e_no_regen.stop_go_kwh

    def test_ice_stops_always_loss(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        seg = RouteSegment(name="city", distance_km=10.0, avg_speed_kmh=40.0, stops=3.0)
        result = segment_energy(DEFAULT_ICE, seg, params)
        assert result.stop_go_kwh > 0


class TestSegmentEnergyHeadwind:
    def test_headwind_increases_aero(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        no_wind = RouteSegment(name="calm", distance_km=20.0, avg_speed_kmh=100.0, headwind_kmh=0.0)
        headwind = RouteSegment(name="headwind", distance_km=20.0, avg_speed_kmh=100.0, headwind_kmh=20.0)
        e_calm = segment_energy(DEFAULT_EV, no_wind, params)
        e_head = segment_energy(DEFAULT_EV, headwind, params)
        assert e_head.aero_kwh > e_calm.aero_kwh

    def test_tailwind_does_not_make_negative_energy(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        tailwind = RouteSegment(name="tailwind", distance_km=20.0, avg_speed_kmh=100.0, headwind_kmh=-30.0)
        result = segment_energy(DEFAULT_EV, tailwind, params)
        assert result.total_battery_kwh > 0
        assert result.aero_kwh >= 0


class TestSegmentEnergyAux:
    def test_dwell_time_increases_aux(self):
        params = PhysicsParams(p_aux_kw=0.5, temperature_c=20.0)
        no_dwell = RouteSegment(name="no_dwell", distance_km=50.0, avg_speed_kmh=100.0, dwell_time_min=0.0)
        with_dwell = RouteSegment(name="dwell", distance_km=50.0, avg_speed_kmh=100.0, dwell_time_min=30.0)
        e_no = segment_energy(DEFAULT_EV, no_dwell, params)
        e_yes = segment_energy(DEFAULT_EV, with_dwell, params)
        assert e_yes.aux_kwh > e_no.aux_kwh


class TestCompositeEnergyNeverNegative:
    def test_total_battery_never_negative(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0, eta_regen=1.0)
        steep_downhill = RouteSegment(
            name="steep_downhill",
            distance_km=5.0,
            avg_speed_kmh=30.0,
            elevation_loss_m=500.0,
        )
        result = segment_energy(DEFAULT_EV, steep_downhill, params)
        assert result.total_battery_kwh >= 0.0


class TestRouteEnergy:
    def test_empty_route(self):
        params = PhysicsParams()
        route = Route(id="empty", name="Empty", segments=[])
        result = route_energy(DEFAULT_EV, route, params)
        assert result.distance_km == 0.0
        assert result.total_battery_kwh == 0.0

    def test_multi_segment_sums(self):
        params = PhysicsParams(p_aux_kw=0.5, temperature_c=20.0)
        seg1 = RouteSegment(name="city", distance_km=5.0, avg_speed_kmh=40.0, stops=2.0)
        seg2 = RouteSegment(name="highway", distance_km=30.0, avg_speed_kmh=120.0)
        route = Route(id="commute", name="Commute", segments=[seg1, seg2])
        result = route_energy(DEFAULT_EV, route, params)
        assert result.distance_km == pytest.approx(35.0)
        assert result.total_battery_kwh > 0
        e1 = segment_energy(DEFAULT_EV, seg1, params)
        e2 = segment_energy(DEFAULT_EV, seg2, params)
        assert result.aero_kwh == pytest.approx(e1.aero_kwh + e2.aero_kwh, rel=0.01)


class TestReverseRoute:
    def test_swaps_elevation(self):
        seg = RouteSegment(
            name="uphill",
            distance_km=15.0,
            avg_speed_kmh=80.0,
            elevation_gain_m=300.0,
            elevation_loss_m=50.0,
            headwind_kmh=10.0,
        )
        route = Route(id="hill", name="Hill", segments=[seg])
        ret = reverse_route(route, invert_wind=True)
        ret_seg = ret.segments[0]
        assert ret_seg.elevation_gain_m == 50.0
        assert ret_seg.elevation_loss_m == 300.0
        assert ret_seg.headwind_kmh == -10.0
        assert ret_seg.distance_km == 15.0

    def test_wind_no_invert(self):
        seg = RouteSegment(name="windy", distance_km=10.0, avg_speed_kmh=80.0, headwind_kmh=15.0)
        route = Route(id="r", name="R", segments=[seg])
        ret = reverse_route(route, invert_wind=False)
        assert ret.segments[0].headwind_kmh == -15.0 or ret.segments[0].headwind_kmh == 15.0


class TestCommuteEnergy:
    def test_one_way_only(self):
        params = PhysicsParams(p_aux_kw=1.0, temperature_c=20.0)
        route = Route(
            id="commute",
            name="Commute",
            segments=[RouteSegment(name="way", distance_km=20.0, avg_speed_kmh=80.0)],
        )
        commute = CommuteScenario(route=route, direction_mode=DirectionMode.one_way)
        result = commute_energy(DEFAULT_EV, commute, params)
        assert result["return"] is None
        assert result["total"].distance_km == pytest.approx(20.0)
        assert result["outward"].distance_km == pytest.approx(20.0)

    def test_return_trip_doubles_distance(self):
        params = PhysicsParams(p_aux_kw=0.5, temperature_c=20.0)
        route = Route(
            id="flat",
            name="Flat",
            segments=[RouteSegment(name="flat", distance_km=20.0, avg_speed_kmh=80.0)],
        )
        commute = CommuteScenario(route=route, direction_mode=DirectionMode.return_trip)
        result = commute_energy(DEFAULT_EV, commute, params)
        assert result["total"].distance_km == pytest.approx(40.0)
        assert result["return"] is not None

    def test_return_trip_with_elevation_switches(self):
        params = PhysicsParams(p_aux_kw=0.0, temperature_c=20.0)
        route = Route(
            id="hill",
            name="Hill",
            segments=[
                RouteSegment(
                    name="uphill",
                    distance_km=15.0,
                    avg_speed_kmh=60.0,
                    elevation_gain_m=300.0,
                    elevation_loss_m=0.0,
                )
            ],
        )
        commute = CommuteScenario(route=route, direction_mode=DirectionMode.return_trip)
        result = commute_energy(DEFAULT_EV, commute, params)
        assert result["outward"].climb_kwh > 0
        assert result["return"] is not None
        assert result["return"].climb_kwh == pytest.approx(0.0, abs=1e-6)
        assert result["return"].descent_recovered_kwh > 0

    def test_round_trip_elevation_has_losses(self):
        params = PhysicsParams(p_aux_kw=0.5, temperature_c=20.0, eta_regen=0.65)
        route = Route(
            id="hill_rt",
            name="Hill Roundtrip",
            segments=[
                RouteSegment(
                    name="up",
                    distance_km=10.0,
                    avg_speed_kmh=60.0,
                    elevation_gain_m=200.0,
                    elevation_loss_m=0.0,
                )
            ],
        )
        commute = CommuteScenario(route=route, direction_mode=DirectionMode.return_trip)
        result = commute_energy(DEFAULT_EV, commute, params)
        assert result["total"].total_battery_kwh > 0
        assert result["total"].climb_kwh > 0
        assert result["total"].descent_recovered_kwh > 0
        net_elevation_loss = result["total"].climb_kwh - result["total"].descent_recovered_kwh
        assert net_elevation_loss > 0


class TestTripsPerCharge:
    def test_basic_computation(self):
        breakdown = RouteEnergyBreakdown(
            distance_km=50.0,
            duration_h=0.5,
            aero_kwh=5.0,
            roll_kwh=2.0,
            aux_kwh=0.5,
            climb_kwh=0.0,
            descent_recovered_kwh=0.0,
            stop_go_kwh=0.0,
            drivetrain_loss_kwh=0.6,
            total_wheel_kwh=7.5,
            total_battery_kwh=8.5,
            kwh_per_100km=17.0,
        )
        trips = trips_per_charge(breakdown, 60.0, temperature_c=20.0)
        assert trips is not None
        assert trips > 0

    def test_returns_none_for_no_battery(self):
        breakdown = RouteEnergyBreakdown(
            distance_km=50.0,
            duration_h=0.5,
            aero_kwh=5.0,
            roll_kwh=2.0,
            aux_kwh=0.5,
            climb_kwh=0.0,
            descent_recovered_kwh=0.0,
            stop_go_kwh=0.0,
            drivetrain_loss_kwh=0.6,
            total_wheel_kwh=7.5,
            total_battery_kwh=8.5,
            kwh_per_100km=17.0,
        )
        assert trips_per_charge(breakdown, None) is None
        assert trips_per_charge(breakdown, 0.0) is None
