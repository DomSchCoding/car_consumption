"""Vehicle filtering, selection helpers, and shared vehicle utilities."""

from __future__ import annotations

from collections import defaultdict

from app.data.models import TireClass, Vehicle, VehicleType
from app.data.repository import VehicleRepository


def make_vehicle_label(v: Vehicle) -> str:
    parts = [v.make, v.model]
    if v.variant:
        parts.append(v.variant)
    return " ".join(parts)


def short_label(v: Vehicle) -> str:
    parts = [v.model]
    if v.variant:
        parts.append(v.variant)
    return " ".join(parts)


def get_vehicle_c_rr(vehicle: Vehicle, global_c_rr: float, use_per_vehicle: bool) -> float:
    if use_per_vehicle and vehicle.tire_class is not None:
        return vehicle.default_c_rr
    return global_c_rr


def tire_class_label(v: Vehicle) -> str:
    if v.tire_class is None:
        return "n/a"
    labels = {
        TireClass.eco_lrr: "Eco LRR",
        TireClass.standard: "Standard",
        TireClass.sport: "Sport",
        TireClass.suv: "SUV",
        TireClass.van_truck: "Van/Truck",
    }
    return labels.get(v.tire_class, v.tire_class.value)


def vehicle_data_quality(v: Vehicle) -> dict[str, bool]:
    """Checks which fields have data vs are missing."""
    checks = {
        "mass_kg": v.mass_kg > 0,
        "frontal_area_m2": v.frontal_area_m2 > 0,
        "drag_coefficient_cd": v.drag_coefficient_cd > 0,
    }
    if v.vehicle_type == VehicleType.ev:
        checks["battery_usable_kwh"] = v.battery_usable_kwh is not None
        checks["wltp_consumption"] = v.wltp_consumption_kwh_100km is not None
    else:
        checks["fuel_type"] = v.fuel_type is not None
        checks["consumption"] = v.real_consumption_l_100km is not None
    checks["sources"] = len(v.source_refs) > 0
    return checks


def get_vehicles_by_make(repo: VehicleRepository) -> dict[str, list[Vehicle]]:
    grouped: dict[str, list[Vehicle]] = defaultdict(list)
    for v in sorted(repo.get_all(), key=lambda x: (x.make, x.model, x.variant)):
        grouped[v.make].append(v)
    return dict(sorted(grouped.items()))


def get_filtered_makes(repo: VehicleRepository, show_ev: bool, show_ice: bool) -> list[str]:
    grouped = get_vehicles_by_make(repo)
    makes = []
    for make, vehicles in grouped.items():
        has_ev = any(v.vehicle_type == VehicleType.ev for v in vehicles)
        has_ice = any(v.vehicle_type != VehicleType.ev for v in vehicles)
        if (show_ev and has_ev) or (show_ice and has_ice):
            makes.append(make)
    return makes


def get_filtered_models(repo: VehicleRepository, make: str, show_ev: bool, show_ice: bool) -> list[Vehicle]:
    vehicles = get_vehicles_by_make(repo).get(make, [])
    result = []
    for v in vehicles:
        if show_ev and v.vehicle_type == VehicleType.ev:
            result.append(v)
        if show_ice and v.vehicle_type != VehicleType.ev:
            result.append(v)
    return result


def passes_vehicle_filters(v: Vehicle, filters: dict) -> bool:
    """Check if a vehicle passes all active filter criteria (AND logic).

    Args:
        v: Vehicle to check.
        filters: Dict with filter values from SESSION.

    Returns:
        True if vehicle passes all active filters.
    """
    # Length filter
    lo = filters.get("filter_length_min")
    hi = filters.get("filter_length_max")
    if v.length_mm is not None:
        if lo is not None and v.length_mm < lo:
            return False
        if hi is not None and v.length_mm > hi:
            return False
    elif lo is not None or hi is not None:
        return False  # data missing but filter active

    # Weight filter
    lo = filters.get("filter_weight_min")
    hi = filters.get("filter_weight_max")
    if lo is not None and v.mass_kg < lo:
        return False
    if hi is not None and v.mass_kg > hi:
        return False

    # Ground clearance filter
    lo = filters.get("filter_clearance_min")
    hi = filters.get("filter_clearance_max")
    if v.ground_clearance_mm is not None:
        if lo is not None and v.ground_clearance_mm < lo:
            return False
        if hi is not None and v.ground_clearance_mm > hi:
            return False
    elif lo is not None or hi is not None:
        return False

    # Drivetrain filter
    selected = filters.get("filter_drivetrain", [])
    if selected and v.drivetrain is not None:
        if v.drivetrain.value not in selected:
            return False
    elif selected and v.drivetrain is None:
        return False

    # Price filter
    lo = filters.get("filter_price_min")
    hi = filters.get("filter_price_max")
    if v.new_price_eur is not None:
        if lo is not None and v.new_price_eur < lo:
            return False
        if hi is not None and v.new_price_eur > hi:
            return False
    elif lo is not None or hi is not None:
        return False

    # Trunk volume filter
    lo = filters.get("filter_trunk_min")
    hi = filters.get("filter_trunk_max")
    if v.trunk_volume_l is not None:
        if lo is not None and v.trunk_volume_l < lo:
            return False
        if hi is not None and v.trunk_volume_l > hi:
            return False
    elif lo is not None or hi is not None:
        return False

    return True


def get_drivetrain_label(v: Vehicle) -> str:
    """Return human-readable drivetrain label."""
    if v.drivetrain is None:
        return "n/a"
    labels = {"fwd": "FWD", "rwd": "RWD", "awd": "AWD"}
    return labels.get(v.drivetrain.value, v.drivetrain.value)


def get_filter_ranges(repo: VehicleRepository) -> dict[str, tuple[float | None, float | None]]:
    """Get min/max values for filter fields across the fleet."""
    all_v = repo.get_all()

    def _range(field: str) -> tuple[float | None, float | None]:
        vals = [getattr(v, field) for v in all_v if getattr(v, field, None) is not None]
        return (min(vals), max(vals)) if vals else (None, None)

    return {
        "length": _range("length_mm"),
        "weight": (min(v.mass_kg for v in all_v), max(v.mass_kg for v in all_v)),
        "clearance": _range("ground_clearance_mm"),
        "price": _range("new_price_eur"),
        "trunk": _range("trunk_volume_l"),
    }
