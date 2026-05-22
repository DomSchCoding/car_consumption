"""Tests for app.core.physics module."""

from __future__ import annotations

import math

import pytest

from app.core.physics import (
    ConsumptionBreakdown,
    aero_consumption,
    aero_force,
    aux_consumption,
    battery_capacity_factor,
    charge_time_minutes,
    charging_curve_points,
    consumption_curve,
    drivetrain_loss,
    force_to_kwh_per_100km,
    fuel_consumption_to_kwh_per_100km,
    fuel_liters_to_kwh,
    fuel_wheel_energy,
    hvac_power_kw,
    kmh_to_ms,
    kwh_per_100km_to_kwh_per_100mi,
    kwh_per_100km_to_wh_per_km,
    kwh_per_100mi_to_kwh_per_100km,
    ms_to_kmh,
    roll_consumption,
    roll_force,
    total_consumption,
    wh_per_km_to_kwh_per_100km,
)


class TestUnitConversions:
    def test_kmh_to_ms(self):
        assert kmh_to_ms(36) == pytest.approx(10.0)
        assert kmh_to_ms(0) == 0.0
        assert kmh_to_ms(100) == pytest.approx(27.7778, rel=1e-4)

    def test_ms_to_kmh(self):
        assert ms_to_kmh(10) == pytest.approx(36.0)
        assert ms_to_kmh(0) == 0.0

    def test_kmh_ms_roundtrip(self):
        for speed in [0, 30, 50, 100, 130, 200]:
            assert ms_to_kmh(kmh_to_ms(speed)) == pytest.approx(speed)

    def test_wh_per_km_to_kwh_per_100km(self):
        assert wh_per_km_to_kwh_per_100km(15.0) == pytest.approx(1.5)
        assert wh_per_km_to_kwh_per_100km(100.0) == pytest.approx(10.0)

    def test_kwh_per_100km_to_wh_per_km(self):
        assert kwh_per_100km_to_wh_per_km(1.5) == pytest.approx(15.0)
        assert kwh_per_100km_to_wh_per_km(10.0) == pytest.approx(100.0)

    def test_kwh_per_100mi_to_kwh_per_100km(self):
        assert kwh_per_100mi_to_kwh_per_100km(33.7) == pytest.approx(20.94, rel=1e-2)

    def test_kwh_per_100km_to_kwh_per_100mi(self):
        assert kwh_per_100km_to_kwh_per_100mi(20.0) == pytest.approx(32.187, rel=1e-2)

    def test_kwh_per_100mi_roundtrip(self):
        for val in [15.0, 20.0, 30.0, 33.7]:
            assert kwh_per_100mi_to_kwh_per_100km(kwh_per_100km_to_kwh_per_100mi(val)) == pytest.approx(val)


class TestForceToEnergy:
    def test_force_to_kwh_per_100km(self):
        result = force_to_kwh_per_100km(360.0)
        expected = 360.0 * 100_000 / 3_600_000
        assert result == pytest.approx(expected)

    def test_zero_force(self):
        assert force_to_kwh_per_100km(0.0) == 0.0


class TestAerodynamics:
    RHO = 1.225
    CD = 0.25
    AREA = 2.2

    def test_aero_force_at_100_kmh(self):
        speed_ms = kmh_to_ms(100)
        force = aero_force(self.RHO, self.CD, self.AREA, speed_ms)
        assert force > 0

    def test_aero_force_scales_with_v_squared(self):
        force_50 = aero_force(self.RHO, self.CD, self.AREA, kmh_to_ms(50))
        force_100 = aero_force(self.RHO, self.CD, self.AREA, kmh_to_ms(100))
        ratio = force_100 / force_50
        assert ratio == pytest.approx(4.0, rel=1e-6)

    def test_aero_consumption_scales_with_v_squared(self):
        cons_50 = aero_consumption(self.RHO, self.CD, self.AREA, 50)
        cons_100 = aero_consumption(self.RHO, self.CD, self.AREA, 100)
        ratio = cons_100 / cons_50
        assert ratio == pytest.approx(4.0, rel=1e-6)

    def test_aero_consumption_zero_at_zero_speed(self):
        assert aero_consumption(self.RHO, self.CD, self.AREA, 0) == pytest.approx(0.0)

    def test_double_cda_doubles_aero(self):
        cons = aero_consumption(self.RHO, self.CD, self.AREA, 100)
        cons_double = aero_consumption(self.RHO, self.CD * 2, self.AREA, 100)
        assert cons_double == pytest.approx(cons * 2.0)

    def test_aero_power_scales_with_v_cubed(self):
        power_50 = aero_force(self.RHO, self.CD, self.AREA, kmh_to_ms(50)) * kmh_to_ms(50)
        power_100 = aero_force(self.RHO, self.CD, self.AREA, kmh_to_ms(100)) * kmh_to_ms(100)
        ratio = power_100 / power_50
        assert ratio == pytest.approx(8.0, rel=1e-6)


class TestRollingResistance:
    MASS = 1800.0
    C_RR = 0.009

    def test_roll_force_positive(self):
        force = roll_force(self.MASS, self.C_RR)
        assert force > 0

    def test_roll_consumption_independent_of_speed(self):
        cons_50 = roll_consumption(self.MASS, self.C_RR)
        cons_130 = roll_consumption(self.MASS, self.C_RR)
        assert cons_50 == pytest.approx(cons_130)

    def test_roll_scales_linearly_with_mass(self):
        cons_1 = roll_consumption(1000.0, self.C_RR)
        cons_2 = roll_consumption(2000.0, self.C_RR)
        assert cons_2 == pytest.approx(cons_1 * 2.0)

    def test_roll_scales_linearly_with_c_rr(self):
        cons_1 = roll_consumption(self.MASS, 0.008)
        cons_2 = roll_consumption(self.MASS, 0.016)
        assert cons_2 == pytest.approx(cons_1 * 2.0)

    def test_roll_zero_at_zero_mass(self):
        assert roll_consumption(0.0, self.C_RR) == pytest.approx(0.0)


class TestAuxConsumption:
    def test_aux_inversely_proportional_to_speed(self):
        cons_50 = aux_consumption(1.5, 50)
        cons_100 = aux_consumption(1.5, 100)
        assert cons_50 == pytest.approx(cons_100 * 2.0)

    def test_aux_zero_speed_is_inf(self):
        assert math.isinf(aux_consumption(1.0, 0))

    def test_aux_linear_with_power(self):
        cons_1 = aux_consumption(1.0, 100)
        cons_2 = aux_consumption(2.0, 100)
        assert cons_2 == pytest.approx(cons_1 * 2.0)


class TestDrivetrainLoss:
    def test_efficiency_less_than_one_increases_consumption(self):
        wheel = 15.0
        battery = drivetrain_loss(wheel, 0.90)
        assert battery > wheel
        assert battery == pytest.approx(15.0 / 0.90)

    def test_perfect_efficiency(self):
        assert drivetrain_loss(15.0, 1.0) == pytest.approx(15.0)

    def test_zero_efficiency_is_inf(self):
        assert math.isinf(drivetrain_loss(15.0, 0.0))


class TestTotalConsumption:
    def test_returns_breakdown(self):
        result = total_consumption(
            rho_air=1.225,
            cd=0.25,
            frontal_area_m2=2.2,
            mass_kg=1800,
            c_rr=0.009,
            p_aux_kw=1.5,
            speed_kmh=100,
            eta_drivetrain=0.92,
        )
        assert isinstance(result, ConsumptionBreakdown)
        assert result.total_battery_kwh_per_100km > 0
        assert result.total_battery_kwh_per_100km >= result.total_wheel_kwh_per_100km

    def test_battery_equals_wheel_at_perfect_efficiency(self):
        result = total_consumption(
            rho_air=1.225,
            cd=0.25,
            frontal_area_m2=2.2,
            mass_kg=1800,
            c_rr=0.009,
            p_aux_kw=0.0,
            speed_kmh=100,
            eta_drivetrain=1.0,
        )
        assert result.total_battery_kwh_per_100km == pytest.approx(result.total_wheel_kwh_per_100km)

    def test_total_is_sum_of_components_at_wheel(self):
        result = total_consumption(
            rho_air=1.225,
            cd=0.25,
            frontal_area_m2=2.2,
            mass_kg=1800,
            c_rr=0.009,
            p_aux_kw=1.5,
            speed_kmh=80,
            eta_drivetrain=1.0,
        )
        expected = result.aero_kwh_per_100km + result.roll_kwh_per_100km + result.aux_kwh_per_100km
        assert result.total_wheel_kwh_per_100km == pytest.approx(expected)


class TestConsumptionCurve:
    def test_returns_correct_number_of_points(self):
        curve = consumption_curve(
            rho_air=1.225,
            cd=0.25,
            frontal_area_m2=2.2,
            mass_kg=1800,
            c_rr=0.009,
            p_aux_kw=1.5,
            speed_min_kmh=30,
            speed_max_kmh=130,
            steps=11,
        )
        assert len(curve) == 11

    def test_aero_dominates_at_high_speed(self):
        curve = consumption_curve(
            rho_air=1.225,
            cd=0.25,
            frontal_area_m2=2.2,
            mass_kg=1800,
            c_rr=0.009,
            p_aux_kw=1.5,
            speed_min_kmh=60,
            speed_max_kmh=160,
            steps=50,
        )
        for i in range(1, len(curve)):
            assert curve[i].total_battery_kwh_per_100km >= curve[i - 1].total_battery_kwh_per_100km


class TestFuelConversions:
    def test_liters_to_kwh(self):
        assert fuel_liters_to_kwh(1.0, 9.7) == pytest.approx(9.7)
        assert fuel_liters_to_kwh(5.0, 8.9) == pytest.approx(44.5)

    def test_fuel_consumption_to_kwh_per_100km(self):
        result = fuel_consumption_to_kwh_per_100km(6.0, 9.7)
        assert result == pytest.approx(58.2)

    def test_fuel_wheel_energy(self):
        wheel = fuel_wheel_energy(6.0, 9.7, 0.35)
        chemical = fuel_consumption_to_kwh_per_100km(6.0, 9.7)
        assert wheel == pytest.approx(chemical * 0.35)


class TestHVACPower:
    def test_mild_weather_minimal_hvac(self):
        power = hvac_power_kw(20.0, 21.0)
        assert 0.2 < power < 2.0

    def test_cold_weather_heating(self):
        power_cold = hvac_power_kw(-10.0, 21.0)
        power_mild = hvac_power_kw(10.0, 21.0)
        assert power_cold > power_mild

    def test_hot_weather_cooling(self):
        power_hot = hvac_power_kw(35.0, 21.0)
        power_mild = hvac_power_kw(20.0, 21.0)
        assert power_hot > power_mild

    def test_extreme_cold(self):
        power = hvac_power_kw(-20.0, 21.0)
        assert power > 3.0

    def test_always_positive(self):
        for t in [-30, -10, 0, 10, 20, 30, 45]:
            assert hvac_power_kw(float(t), 21.0) > 0

    def test_heat_pump_more_efficient_than_resistive(self):
        resistive = hvac_power_kw(-10.0, 21.0, has_heat_pump=False)
        hp = hvac_power_kw(-10.0, 21.0, has_heat_pump=True)
        assert hp < resistive

    def test_heat_pump_with_custom_cop(self):
        hp_default = hvac_power_kw(-5.0, 21.0, has_heat_pump=True)
        hp_efficient = hvac_power_kw(-5.0, 21.0, has_heat_pump=True, hvac_cop_heat=3.5)
        assert hp_efficient < hp_default

    def test_heat_pump_cop_degrades_in_extreme_cold(self):
        hp_mild = hvac_power_kw(5.0, 21.0, has_heat_pump=True, hvac_cop_heat=3.0)
        hp_cold = hvac_power_kw(-15.0, 21.0, has_heat_pump=True, hvac_cop_heat=3.0)
        hp_warm = hvac_power_kw(15.0, 21.0, has_heat_pump=True, hvac_cop_heat=3.0)
        assert hp_cold > hp_mild
        assert hp_mild > hp_warm

    def test_heat_pump_cooling_also_efficient(self):
        resistive = hvac_power_kw(35.0, 21.0, has_heat_pump=False)
        hp = hvac_power_kw(35.0, 21.0, has_heat_pump=True)
        assert hp < resistive


class TestBatteryCapacityFactor:
    def test_optimal_temperature(self):
        assert battery_capacity_factor(25.0) == pytest.approx(1.0)

    def test_mild_cold(self):
        factor_0 = battery_capacity_factor(0.0)
        assert 0.80 < factor_0 < 0.90

    def test_freezing(self):
        factor_m10 = battery_capacity_factor(-10.0)
        assert 0.70 < factor_m10 < 0.80

    def test_extreme_cold(self):
        factor_m20 = battery_capacity_factor(-20.0)
        assert 0.60 < factor_m20 < 0.70

    def test_hot_weather(self):
        factor_40 = battery_capacity_factor(40.0)
        assert 0.95 < factor_40 <= 1.0

    def test_monotonic_at_low_temps(self):
        temps = [-20, -10, 0, 10, 25]
        factors = [battery_capacity_factor(float(t)) for t in temps]
        for i in range(len(factors) - 1):
            assert factors[i] <= factors[i + 1]


class TestChargeTime:
    def test_simple_peak_only(self):
        time_min = charge_time_minutes(60.0, None, 120.0, 20.0, 80.0)
        assert time_min is not None
        assert time_min > 0

    def test_with_charging_curve(self):
        curve = [(0, 120), (20, 120), (50, 100), (80, 60), (100, 25)]
        time_min = charge_time_minutes(60.0, curve, 120.0, 20.0, 80.0)
        assert time_min is not None
        assert time_min > 0
        energy_kwh = 60.0 * 0.6
        avg_power = energy_kwh / (time_min / 60.0)
        assert 60 < avg_power < 120

    def test_none_on_missing_data(self):
        assert charge_time_minutes(60.0, None, None) is None

    def test_none_on_zero_battery(self):
        assert charge_time_minutes(0.0, None, 120.0) is None

    def test_none_on_invalid_range(self):
        assert charge_time_minutes(60.0, None, 120.0, 80.0, 20.0) is None

    def test_fast_charger_shorter_time(self):
        time_slow = charge_time_minutes(60.0, None, 50.0, 20.0, 80.0)
        time_fast = charge_time_minutes(60.0, None, 200.0, 20.0, 80.0)
        assert time_fast is not None
        assert time_slow is not None
        assert time_fast < time_slow


class TestChargingCurvePoints:
    def test_returns_points_for_peak_dc(self):
        points = charging_curve_points(None, 120.0, 60.0)
        assert len(points) > 0
        assert points[0][0] == 0.0
        assert points[-1][0] == 100.0

    def test_returns_empty_for_no_data(self):
        points = charging_curve_points(None, None, None)
        assert points == []

    def test_custom_curve_overrides_estimate(self):
        curve = [(0, 100), (20, 100), (50, 80), (80, 50), (100, 20)]
        points = charging_curve_points(curve, 100.0, 60.0)
        assert len(points) == 50
        assert points[0][0] == 0.0
        assert points[-1][0] == 100.0
