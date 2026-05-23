"""Physics-based vehicle consumption calculations.

All functions are pure and operate on basic numeric types.
Units are explicit in parameter and return names.
"""

from __future__ import annotations

from dataclasses import dataclass

G = 9.81  # gravitational acceleration m/s^2
JOULES_PER_KWH = 3_600_000
METERS_PER_100KM = 100_000


@dataclass(frozen=True)
class ConsumptionBreakdown:
    """Energy consumption breakdown at a single speed."""

    aero_kwh_per_100km: float
    roll_kwh_per_100km: float
    aux_kwh_per_100km: float
    total_wheel_kwh_per_100km: float
    total_battery_kwh_per_100km: float


def kmh_to_ms(speed_kmh: float) -> float:
    """Convert km/h to m/s."""
    return speed_kmh / 3.6


def ms_to_kmh(speed_ms: float) -> float:
    """Convert m/s to km/h."""
    return speed_ms * 3.6


def wh_per_km_to_kwh_per_100km(wh_per_km: float) -> float:
    """Convert Wh/km to kWh/100 km."""
    return wh_per_km / 10.0


def kwh_per_100km_to_wh_per_km(kwh_per_100km: float) -> float:
    """Convert kWh/100 km to Wh/km."""
    return kwh_per_100km * 10.0


def kwh_per_100mi_to_kwh_per_100km(kwh_per_100mi: float) -> float:
    """Convert kWh/100 mi to kWh/100 km."""
    return kwh_per_100mi / 1.609344


def kwh_per_100km_to_kwh_per_100mi(kwh_per_100km: float) -> float:
    """Convert kWh/100 km to kWh/100 mi."""
    return kwh_per_100km * 1.609344


def force_to_kwh_per_100km(force_newton: float) -> float:
    """Convert a constant force in Newton to kWh/100 km.

    E = F * d  =>  kWh/100km = F * 100000 / 3_600_000
    """
    return force_newton * METERS_PER_100KM / JOULES_PER_KWH


def aero_force(rho_air: float, cd: float, frontal_area_m2: float, speed_ms: float) -> float:
    """Calculate aerodynamic drag force in Newton.

    F_aero = 0.5 * rho_air * Cd * A * v^2
    """
    return 0.5 * rho_air * cd * frontal_area_m2 * speed_ms**2


def aero_consumption(rho_air: float, cd: float, frontal_area_m2: float, speed_kmh: float) -> float:
    """Calculate aerodynamic energy consumption in kWh/100 km."""
    speed_ms = kmh_to_ms(speed_kmh)
    force = aero_force(rho_air, cd, frontal_area_m2, speed_ms)
    return force_to_kwh_per_100km(force)


def roll_force(mass_kg: float, c_rr: float) -> float:
    """Calculate rolling resistance force in Newton.

    F_roll = c_rr * mass * g
    """
    return c_rr * mass_kg * G


def roll_consumption(mass_kg: float, c_rr: float) -> float:
    """Calculate rolling resistance energy consumption in kWh/100 km.

    Independent of speed for constant c_rr.
    """
    force = roll_force(mass_kg, c_rr)
    return force_to_kwh_per_100km(force)


def aux_consumption(p_aux_kw: float, speed_kmh: float) -> float:
    """Calculate auxiliary consumer energy consumption in kWh/100 km.

    kWh/100km = P_aux_kW / speed_kmh * 100
    """
    if speed_kmh <= 0:
        return float("inf")
    return p_aux_kw / speed_kmh * 100.0


def drivetrain_loss(wheel_kwh_per_100km: float, eta_drivetrain: float) -> float:
    """Calculate battery energy from wheel energy accounting for drivetrain efficiency.

    battery_energy = wheel_energy / eta_drivetrain
    """
    if eta_drivetrain <= 0:
        return float("inf")
    return wheel_kwh_per_100km / eta_drivetrain


def hvac_power_kw(
    temperature_c: float,
    cabin_target_c: float = 21.0,
    base_aux_kw: float = 0.3,
    has_heat_pump: bool = False,
    hvac_cop_heat: float | None = None,
) -> float:
    """Calculate HVAC power demand in kW based on temperature difference.

    Heating mode (cold):
    - Heat pump: P_demand = heating_need / COP (typically COP 2-4)
    - Resistive: P_demand = heating_need / 1.0 (=1)
    COP degrades at very low temperatures.

    Cooling mode (hot): COP applies to cooling as well (typically 2-3).

    base_aux_kw covers electronics (infotainment, controls, lights) ≈ 0.3 kW.
    """
    delta_t = cabin_target_c - temperature_c
    electronics = base_aux_kw

    if delta_t > 0:
        if has_heat_pump:
            cop = hvac_cop_heat if hvac_cop_heat and hvac_cop_heat > 0 else 2.5
            if temperature_c < -10:
                cop = max(1.3, cop * 0.55)
            elif temperature_c < 0:
                cop = max(1.5, cop * 0.75)
            elif temperature_c < 10:
                cop = max(1.8, cop * 0.9)
            heating_need = 0.08 * delta_t + 1.2
            hvac_power = heating_need / cop
        else:
            hvac_power = 0.08 * delta_t + 1.5

        return electronics + hvac_power
    elif delta_t < -5:
        if has_heat_pump:
            cop_cool = 2.5
            cooling_need = 0.06 * abs(delta_t) + 0.8
            hvac_power = cooling_need / cop_cool
        else:
            hvac_power = 0.06 * abs(delta_t) + 1.0
        return electronics + hvac_power
    elif delta_t < 0:
        return electronics + 0.3 * abs(delta_t) / 5.0
    else:
        return electronics


def battery_capacity_factor(temperature_c: float) -> float:
    """Estimate battery capacity retention factor based on ambient temperature.

    Based on typical lithium-ion behavior:
    - 25°C: 100%
    - 0°C: ~85%
    - -10°C: ~75%
    - -20°C: ~65%
    - 45°C: ~97%

    Uses a piecewise-linear approximation for simplicity.
    """
    if temperature_c >= 25:
        return 1.0 - 0.0012 * (temperature_c - 25)
    elif temperature_c >= 15:
        return 0.97 + 0.003 * (temperature_c - 15)
    elif temperature_c >= 0:
        return 0.85 + 0.008 * (temperature_c - 0)
    elif temperature_c >= -10:
        return 0.75 + 0.010 * (temperature_c - (-10))
    elif temperature_c >= -20:
        return 0.65 + 0.010 * (temperature_c - (-20))
    else:
        return max(0.50, 0.65 + 0.015 * (temperature_c - (-20)))


def total_consumption(
    rho_air: float,
    cd: float,
    frontal_area_m2: float,
    mass_kg: float,
    c_rr: float,
    p_aux_kw: float,
    speed_kmh: float,
    eta_drivetrain: float = 1.0,
) -> ConsumptionBreakdown:
    """Calculate full consumption breakdown at a given speed.

    Returns a ConsumptionBreakdown with all components and totals.
    """
    aero = aero_consumption(rho_air, cd, frontal_area_m2, speed_kmh)
    roll = roll_consumption(mass_kg, c_rr)
    aux = aux_consumption(p_aux_kw, speed_kmh)
    total_wheel = aero + roll + aux
    total_battery = drivetrain_loss(total_wheel, eta_drivetrain)

    return ConsumptionBreakdown(
        aero_kwh_per_100km=aero,
        roll_kwh_per_100km=roll,
        aux_kwh_per_100km=aux,
        total_wheel_kwh_per_100km=total_wheel,
        total_battery_kwh_per_100km=total_battery,
    )


def consumption_curve(
    rho_air: float,
    cd: float,
    frontal_area_m2: float,
    mass_kg: float,
    c_rr: float,
    p_aux_kw: float,
    speed_min_kmh: float,
    speed_max_kmh: float,
    steps: int = 50,
    eta_drivetrain: float = 1.0,
) -> list[ConsumptionBreakdown]:
    """Calculate consumption over a speed range.

    Returns list of ConsumptionBreakdown from speed_min to speed_max inclusive.
    """
    if steps < 2:
        steps = 2
    speeds = [speed_min_kmh + (speed_max_kmh - speed_min_kmh) * i / (steps - 1) for i in range(steps)]
    return [
        total_consumption(
            rho_air=rho_air,
            cd=cd,
            frontal_area_m2=frontal_area_m2,
            mass_kg=mass_kg,
            c_rr=c_rr,
            p_aux_kw=p_aux_kw,
            speed_kmh=s,
            eta_drivetrain=eta_drivetrain,
        )
        for s in speeds
    ]


def charge_time_minutes(
    battery_kwh: float,
    charging_curve: list[tuple[float, float]] | None,
    peak_dc_kw: float | None,
    soc_from: float = 20.0,
    soc_to: float = 80.0,
) -> float | None:
    """Calculate charging time in minutes from soc_from% to soc_to%.

    If a charging curve is provided (list of (soc%, power_kW) tuples),
    integrates the piecewise-linear power curve.
    Otherwise, uses peak_dc_kw as a constant power estimate with a linear
    derating above 80% SoC.

    Returns None if insufficient data is available.
    """
    if peak_dc_kw is None or peak_dc_kw <= 0 or battery_kwh <= 0:
        return None
    if soc_from >= soc_to:
        return None

    if charging_curve and len(charging_curve) >= 2:
        curve = sorted(charging_curve, key=lambda p: p[0])
        curve_soc = [p[0] for p in curve]
        curve_kw = [p[1] for p in curve]

        if soc_to <= curve_soc[0] or soc_from >= curve_soc[-1]:
            return None

        total_time_hours = 0.0
        steps = 200
        dt_soc = (soc_to - soc_from) / steps
        for i in range(steps):
            soc = soc_from + dt_soc * (i + 0.5)
            power = _interpolate_charging_curve(curve_soc, curve_kw, soc)
            if power <= 0:
                continue
            energy_kwh = battery_kwh * dt_soc / 100.0
            total_time_hours += energy_kwh / power

        return total_time_hours * 60.0
    else:
        avg_power = peak_dc_kw * 0.75
        energy_kwh = battery_kwh * (soc_to - soc_from) / 100.0
        time_hours = energy_kwh / avg_power
        return time_hours * 60.0


def _interpolate_charging_curve(
    soc_points: list[float],
    kw_points: list[float],
    soc: float,
) -> float:
    """Linearly interpolate charging power at a given SoC."""
    if soc <= soc_points[0]:
        return kw_points[0]
    if soc >= soc_points[-1]:
        return kw_points[-1]
    for i in range(len(soc_points) - 1):
        if soc_points[i] <= soc <= soc_points[i + 1]:
            t = (soc - soc_points[i]) / (soc_points[i + 1] - soc_points[i])
            return kw_points[i] + t * (kw_points[i + 1] - kw_points[i])
    return kw_points[-1]


def charging_curve_points(
    charging_curve: list[tuple[float, float]] | None,
    peak_dc_kw: float | None,
    battery_kwh: float | None,
    num_points: int = 50,
    soc_min: float = 0.0,
    soc_max: float = 100.0,
) -> list[tuple[float, float]]:
    """Generate (soc%, power_kW) points for a charging curve plot.

    If a full curve is provided, uses it directly.
    If only peak_dc_kw is available, generates an estimated curve:
    - Full power from 0% to ~20% SoC
    - Flat until ~50% SoC
    - Linearly declining to ~30% of peak at 100% SoC
    """
    if not peak_dc_kw or not battery_kwh:
        return []

    if charging_curve and len(charging_curve) >= 2:
        curve = sorted(charging_curve, key=lambda p: p[0])
        points = []
        for i in range(num_points):
            soc = soc_min + (soc_max - soc_min) * i / (num_points - 1)
            power = _interpolate_charging_curve([p[0] for p in curve], [p[1] for p in curve], soc)
            points.append((soc, power))
        return points

    estimated_curve = [
        (0, peak_dc_kw * 0.5),
        (5, peak_dc_kw * 0.9),
        (10, peak_dc_kw),
        (30, peak_dc_kw),
        (50, peak_dc_kw * 0.95),
        (70, peak_dc_kw * 0.80),
        (80, peak_dc_kw * 0.60),
        (90, peak_dc_kw * 0.40),
        (100, peak_dc_kw * 0.25),
    ]
    points = []
    for i in range(num_points):
        soc = soc_min + (soc_max - soc_min) * i / (num_points - 1)
        power = _interpolate_charging_curve(
            [p[0] for p in estimated_curve],
            [p[1] for p in estimated_curve],
            soc,
        )
        points.append((soc, power))
    return points


def fuel_liters_to_kwh(liters: float, kwh_per_liter: float) -> float:
    """Convert fuel volume to chemical energy in kWh."""
    return liters * kwh_per_liter


def fuel_consumption_to_kwh_per_100km(liters_per_100km: float, kwh_per_liter: float) -> float:
    """Convert l/100 km to chemical kWh/100 km."""
    return fuel_liters_to_kwh(liters_per_100km, kwh_per_liter)


def fuel_wheel_energy(liters_per_100km: float, kwh_per_liter: float, thermal_efficiency: float) -> float:
    """Estimate wheel energy from fuel consumption and thermal efficiency."""
    chemical_kwh = fuel_consumption_to_kwh_per_100km(liters_per_100km, kwh_per_liter)
    return chemical_kwh * thermal_efficiency
