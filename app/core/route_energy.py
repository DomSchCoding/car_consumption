"""Route energy calculation module.

Computes energy consumption for route segments, complete routes,
and commute scenarios (one-way or return trip).

All functions operate on pure data - no side effects, no UI.
"""

from __future__ import annotations

from app.core.physics import (
    JOULES_PER_KWH,
    G,
    battery_capacity_factor,
    hvac_power_kw,
    kmh_to_ms,
)
from app.data.models import (
    DEFAULT_ROAD_STOP_SPEED,
    CommuteScenario,
    DirectionMode,
    PhysicsParams,
    Route,
    RouteEnergyBreakdown,
    RouteSegment,
    Vehicle,
    VehicleType,
)


def segment_energy(
    vehicle: Vehicle,
    segment: RouteSegment,
    params: PhysicsParams,
    use_per_vehicle_tires: bool = True,
    eta_regen_downhill: float | None = None,
    eta_regen_stop: float | None = None,
) -> RouteEnergyBreakdown:
    """Calculate energy breakdown for a single route segment.

    Args:
        vehicle: Vehicle model.
        segment: Route segment definition.
        params: Physics parameters (rho, c_rr, eta, temperature, etc.).
        use_per_vehicle_tires: Use per-vehicle tire class c_rr.
        eta_regen_downhill: Regeneration efficiency for downhill (0-1). If None, uses params.eta_regen.
        eta_regen_stop: Regeneration efficiency for stop-and-go (0-1). If None, uses params.eta_regen.

    Returns:
        RouteEnergyBreakdown with all energy components in kWh.
    """
    c_rr = vehicle.default_c_rr if use_per_vehicle_tires and vehicle.tire_class is not None else params.c_rr

    regen_downhill = params.eta_regen if eta_regen_downhill is None else eta_regen_downhill
    regen_stop = params.eta_regen if eta_regen_stop is None else eta_regen_stop

    mass_total = vehicle.mass_kg + segment.payload_kg
    distance_m = segment.distance_km * 1000.0
    v_vehicle_ms = kmh_to_ms(segment.avg_speed_kmh)

    v_air_ms = max(0.0, v_vehicle_ms + kmh_to_ms(segment.headwind_kmh))

    cda = vehicle.drag_coefficient_cd * vehicle.frontal_area_m2
    f_aero = 0.5 * params.rho_air * cda * v_air_ms**2
    e_aero_kwh = f_aero * distance_m / JOULES_PER_KWH

    f_roll = c_rr * mass_total * G
    e_roll_kwh = f_roll * distance_m / JOULES_PER_KWH

    drive_time_h = segment.distance_km / segment.avg_speed_kmh
    total_time_h = drive_time_h + segment.dwell_time_min / 60.0

    hp = vehicle.has_heat_pump if vehicle.has_heat_pump is not None else False
    cop = vehicle.hvac_cop_heat if vehicle.hvac_cop_heat is not None else None
    base_aux = segment.aux_power_kw if segment.aux_power_kw is not None else params.p_aux_kw
    vehicle_hvac_kw = hvac_power_kw(
        params.temperature_c,
        params.cabin_target_temp_c,
        has_heat_pump=hp,
        hvac_cop_heat=cop,
    )
    total_aux_kw = base_aux + vehicle_hvac_kw
    e_aux_kwh = total_aux_kw * total_time_h

    e_climb_kwh = mass_total * G * segment.elevation_gain_m / JOULES_PER_KWH

    descent_available_kwh = mass_total * G * segment.elevation_loss_m / JOULES_PER_KWH

    e_descent_recovered_kwh = descent_available_kwh * regen_downhill if vehicle.vehicle_type == VehicleType.ev else 0.0

    stop_speed_kmh = segment.stop_speed_kmh
    if stop_speed_kmh is None:
        stop_speed_kmh = DEFAULT_ROAD_STOP_SPEED.get(segment.road_type, 50.0)
    stop_speed_ms = kmh_to_ms(stop_speed_kmh)

    total_stops = segment.stops * segment.distance_km

    if total_stops > 0 and stop_speed_ms > 0 and vehicle.vehicle_type == VehicleType.ev:
        e_kin_per_stop = 0.5 * mass_total * stop_speed_ms**2
        e_accel_battery = e_kin_per_stop / params.eta_drivetrain
        e_regen_battery = e_kin_per_stop * regen_stop
        e_stop_net_kwh = (e_accel_battery - e_regen_battery) * total_stops / JOULES_PER_KWH
        e_stop_go_kwh = max(0.0, e_stop_net_kwh)
    elif total_stops > 0 and stop_speed_ms > 0:
        e_kin_per_stop = 0.5 * mass_total * stop_speed_ms**2
        e_stop_net_kwh = e_kin_per_stop * total_stops / JOULES_PER_KWH
        e_stop_go_kwh = max(0.0, e_stop_net_kwh)
    else:
        e_stop_go_kwh = 0.0

    e_wheel_positive = e_aero_kwh + e_roll_kwh + e_aux_kwh + e_climb_kwh + e_stop_go_kwh
    e_wheel_net = e_wheel_positive - e_descent_recovered_kwh

    if vehicle.vehicle_type == VehicleType.ev:
        drive_loss = max(0.0, e_wheel_positive - e_descent_recovered_kwh) * (1.0 / params.eta_drivetrain - 1.0)
        total_battery_kwh = e_wheel_net / params.eta_drivetrain + e_stop_go_kwh * 0.0
        total_battery_kwh = max(
            0.0,
            e_aero_kwh / params.eta_drivetrain
            + e_roll_kwh / params.eta_drivetrain
            + e_aux_kwh
            + e_climb_kwh / params.eta_drivetrain
            + e_stop_go_kwh
            - e_descent_recovered_kwh,
        )
    else:
        total_battery_kwh = e_wheel_net
        drive_loss = 0.0

    total_battery_kwh = max(0.0, total_battery_kwh)

    kwh_per_100km = (total_battery_kwh / segment.distance_km * 100.0) if segment.distance_km > 0 else 0.0

    return RouteEnergyBreakdown(
        distance_km=segment.distance_km,
        duration_h=total_time_h,
        aero_kwh=round(e_aero_kwh, 6),
        roll_kwh=round(e_roll_kwh, 6),
        aux_kwh=round(e_aux_kwh, 6),
        climb_kwh=round(e_climb_kwh, 6),
        descent_recovered_kwh=round(e_descent_recovered_kwh, 6),
        stop_go_kwh=round(e_stop_go_kwh, 6),
        drivetrain_loss_kwh=round(drive_loss, 6),
        total_wheel_kwh=round(e_wheel_net, 6),
        total_battery_kwh=round(total_battery_kwh, 6),
        kwh_per_100km=round(kwh_per_100km, 6),
    )


def route_energy(
    vehicle: Vehicle,
    route: Route,
    params: PhysicsParams,
    use_per_vehicle_tires: bool = True,
    eta_regen_downhill: float | None = None,
    eta_regen_stop: float | None = None,
) -> RouteEnergyBreakdown:
    """Calculate energy breakdown for a complete route (sum of segments).

    Returns aggregated breakdown with total distance, duration, and energies.
    """
    if not route.segments:
        return RouteEnergyBreakdown(
            distance_km=0.0,
            duration_h=0.0,
            aero_kwh=0.0,
            roll_kwh=0.0,
            aux_kwh=0.0,
            climb_kwh=0.0,
            descent_recovered_kwh=0.0,
            stop_go_kwh=0.0,
            drivetrain_loss_kwh=0.0,
            total_wheel_kwh=0.0,
            total_battery_kwh=0.0,
            kwh_per_100km=0.0,
        )

    segment_results = [
        segment_energy(vehicle, s, params, use_per_vehicle_tires, eta_regen_downhill, eta_regen_stop)
        for s in route.segments
    ]

    total_distance = sum(r.distance_km for r in segment_results)
    total_duration = sum(r.duration_h for r in segment_results)
    total_aero = sum(r.aero_kwh for r in segment_results)
    total_roll = sum(r.roll_kwh for r in segment_results)
    total_aux = sum(r.aux_kwh for r in segment_results)
    total_climb = sum(r.climb_kwh for r in segment_results)
    total_descent_rec = sum(r.descent_recovered_kwh for r in segment_results)
    total_stop_go = sum(r.stop_go_kwh for r in segment_results)
    total_drive_loss = sum(r.drivetrain_loss_kwh for r in segment_results)
    total_wheel = sum(r.total_wheel_kwh for r in segment_results)
    total_battery = sum(r.total_battery_kwh for r in segment_results)

    kwh_per_100km = (total_battery / total_distance * 100.0) if total_distance > 0 else 0.0

    return RouteEnergyBreakdown(
        distance_km=round(total_distance, 6),
        duration_h=round(total_duration, 6),
        aero_kwh=round(total_aero, 6),
        roll_kwh=round(total_roll, 6),
        aux_kwh=round(total_aux, 6),
        climb_kwh=round(total_climb, 6),
        descent_recovered_kwh=round(total_descent_rec, 6),
        stop_go_kwh=round(total_stop_go, 6),
        drivetrain_loss_kwh=round(total_drive_loss, 6),
        total_wheel_kwh=round(total_wheel, 6),
        total_battery_kwh=round(total_battery, 6),
        kwh_per_100km=round(kwh_per_100km, 6),
    )


def reverse_route(route: Route, invert_wind: bool = True) -> Route:
    """Create the return route by reversing segments and swapping elevation.

    Segments are reversed in order, elevation_gain and elevation_loss are swapped,
    and headwind direction is inverted if invert_wind is True.
    """
    reversed_segments = []
    for seg in reversed(route.segments):
        reversed_segments.append(
            RouteSegment(
                name=f"{seg.name} (return)" if seg.name else "return",
                distance_km=seg.distance_km,
                avg_speed_kmh=seg.avg_speed_kmh,
                road_type=seg.road_type,
                elevation_gain_m=seg.elevation_loss_m,
                elevation_loss_m=seg.elevation_gain_m,
                stops=seg.stops,
                stop_speed_kmh=seg.stop_speed_kmh,
                dwell_time_min=seg.dwell_time_min,
                headwind_kmh=-seg.headwind_kmh if invert_wind else seg.headwind_kmh,
                payload_kg=seg.payload_kg,
                aux_power_kw=seg.aux_power_kw,
            )
        )
    return Route(
        id=f"{route.id}_return",
        name=f"{route.name} (return)",
        description=route.description,
        segments=reversed_segments,
        source_refs=route.source_refs,
        notes=route.notes,
    )


def commute_energy(
    vehicle: Vehicle,
    commute: CommuteScenario,
    params: PhysicsParams,
    use_per_vehicle_tires: bool = True,
    eta_regen_downhill: float | None = None,
    eta_regen_stop: float | None = None,
) -> dict[str, RouteEnergyBreakdown]:
    """Calculate energy for a commute scenario.

    Returns dict with keys:
        'outward': energy for outward trip
        'return': energy for return trip (if DirectionMode.return_trip, else None)
        'total': combined energy for the full commute
    """
    outward = route_energy(vehicle, commute.route, params, use_per_vehicle_tires, eta_regen_downhill, eta_regen_stop)

    if commute.direction_mode == DirectionMode.return_trip:
        return_route = reverse_route(commute.route, invert_wind=commute.invert_wind_on_return)
        return_energy = route_energy(
            vehicle, return_route, params, use_per_vehicle_tires, eta_regen_downhill, eta_regen_stop
        )

        total_distance = outward.distance_km + return_energy.distance_km
        total_duration = outward.duration_h + return_energy.duration_h
        total_battery = outward.total_battery_kwh + return_energy.total_battery_kwh

        combined = RouteEnergyBreakdown(
            distance_km=round(total_distance, 6),
            duration_h=round(total_duration, 6),
            aero_kwh=round(outward.aero_kwh + return_energy.aero_kwh, 6),
            roll_kwh=round(outward.roll_kwh + return_energy.roll_kwh, 6),
            aux_kwh=round(outward.aux_kwh + return_energy.aux_kwh, 6),
            climb_kwh=round(outward.climb_kwh + return_energy.climb_kwh, 6),
            descent_recovered_kwh=round(outward.descent_recovered_kwh + return_energy.descent_recovered_kwh, 6),
            stop_go_kwh=round(outward.stop_go_kwh + return_energy.stop_go_kwh, 6),
            drivetrain_loss_kwh=round(outward.drivetrain_loss_kwh + return_energy.drivetrain_loss_kwh, 6),
            total_wheel_kwh=round(outward.total_wheel_kwh + return_energy.total_wheel_kwh, 6),
            total_battery_kwh=round(total_battery, 6),
            kwh_per_100km=round(total_battery / total_distance * 100.0, 6) if total_distance > 0 else 0.0,
        )
        return {"outward": outward, "return": return_energy, "total": combined}
    else:
        return {"outward": outward, "return": None, "total": outward}


def trips_per_charge(
    breakdown: RouteEnergyBreakdown,
    battery_usable_kwh: float,
    temperature_c: float = 20.0,
) -> float | None:
    """Calculate how many complete trips fit in one battery charge.

    Returns None if battery data is not available or energy is zero/negative.
    """
    if battery_usable_kwh is None or battery_usable_kwh <= 0:
        return None
    cap_factor = battery_capacity_factor(temperature_c)
    effective_battery = battery_usable_kwh * cap_factor
    if breakdown.total_battery_kwh <= 0:
        return None
    return effective_battery / breakdown.total_battery_kwh
