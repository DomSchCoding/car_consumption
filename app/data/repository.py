"""Vehicle data repository - loads and manages vehicle data from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.data.models import FuelConstants, Vehicle

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
VEHICLES_DIR = ASSETS_DIR / "vehicles"


class VehicleRepository:
    """Loads and provides access to vehicle data."""

    def __init__(self, vehicles_path: Path | None = None) -> None:
        if vehicles_path is not None:
            self._vehicles_path = vehicles_path
            self._vehicles_dir = None
        else:
            self._vehicles_path = None
            self._vehicles_dir = VEHICLES_DIR
        self._vehicles: dict[str, Vehicle] = {}
        self._load()

    def _load(self) -> None:
        self._vehicles = {}
        paths: list[Path] = []

        if self._vehicles_dir is not None and self._vehicles_dir.is_dir():
            paths = sorted(self._vehicles_dir.glob("*.yaml"))
        elif self._vehicles_path is not None:
            paths = [self._vehicles_path]

        for path in paths:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data is None:
                continue
            for vdata in data.get("vehicles", []):
                vehicle = Vehicle.model_validate(vdata)
                self._vehicles[vehicle.id] = vehicle

    @property
    def vehicles(self) -> dict[str, Vehicle]:
        return dict(self._vehicles)

    def get(self, vehicle_id: str) -> Vehicle | None:
        return self._vehicles.get(vehicle_id)

    def get_all(self) -> list[Vehicle]:
        return list(self._vehicles.values())

    def get_by_ids(self, ids: list[str]) -> list[Vehicle]:
        return [self._vehicles[i] for i in ids if i in self._vehicles]

    def get_ev_vehicles(self) -> list[Vehicle]:
        from app.data.models import VehicleType

        return [v for v in self._vehicles.values() if v.vehicle_type == VehicleType.ev]

    def get_ice_vehicles(self) -> list[Vehicle]:
        from app.data.models import VehicleType

        return [v for v in self._vehicles.values() if v.vehicle_type == VehicleType.ice]


def load_fuel_constants(path: Path | None = None) -> FuelConstants:
    fuel_path = path or ASSETS_DIR / "fuel_constants.yaml"
    with open(fuel_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return FuelConstants(
        gasoline_kwh_per_liter=data.get("gasoline_kwh_per_liter", 8.9),
        diesel_kwh_per_liter=data.get("diesel_kwh_per_liter", 9.7),
    )
