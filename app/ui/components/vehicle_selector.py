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
