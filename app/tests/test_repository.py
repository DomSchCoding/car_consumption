"""Tests for app.data.repository module."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.data.models import VehicleType
from app.data.repository import VehicleRepository, load_fuel_constants

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
VEHICLES_DIR = ASSETS_DIR / "vehicles"


class TestVehicleRepository:
    @pytest.fixture
    def repo(self) -> VehicleRepository:
        return VehicleRepository()

    def test_loads_vehicles_from_directory(self, repo: VehicleRepository) -> None:
        assert len(repo.get_all()) > 0

    def test_get_by_id(self, repo: VehicleRepository) -> None:
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        assert v.make == "Hyundai"
        assert v.model == "Ioniq Electric"

    def test_get_missing_id(self, repo: VehicleRepository) -> None:
        assert repo.get("nonexistent") is None

    def test_get_by_ids(self, repo: VehicleRepository) -> None:
        vehicles = repo.get_by_ids(["hyundai_ioniq_28", "tesla_model3_rwd"])
        assert len(vehicles) == 2

    def test_get_ev_vehicles(self, repo: VehicleRepository) -> None:
        evs = repo.get_ev_vehicles()
        assert all(v.vehicle_type == VehicleType.ev for v in evs)
        assert len(evs) >= 3

    def test_get_ice_vehicles(self, repo: VehicleRepository) -> None:
        ices = repo.get_ice_vehicles()
        assert all(v.vehicle_type == VehicleType.ice for v in ices)
        assert len(ices) >= 1

    def test_vehicle_cda_property(self, repo: VehicleRepository) -> None:
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        expected = v.drag_coefficient_cd * v.frontal_area_m2
        assert v.cda_m2 == pytest.approx(expected)

    def test_vehicle_has_source_refs(self, repo: VehicleRepository) -> None:
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        assert len(v.source_refs) > 0

    def test_hyundai_variants_loaded(self, repo: VehicleRepository) -> None:
        assert repo.get("hyundai_ioniq_38") is not None
        assert repo.get("hyundai_kona_ev_39") is not None
        assert repo.get("hyundai_kona_ev_fl_48") is not None
        assert repo.get("hyundai_kona_ev_fl_65") is not None
        assert repo.get("hyundai_kona_ev_48_n") is not None
        assert repo.get("hyundai_kona_ev_65_n") is not None

    def test_many_makes_loaded(self, repo: VehicleRepository) -> None:
        makes = {v.make for v in repo.get_all()}
        assert len(makes) >= 15

    def test_legacy_path_still_works(self) -> None:
        single_file = VEHICLES_DIR.parent / "sample_vehicles.yaml"
        if single_file.exists():
            repo = VehicleRepository(single_file)
            assert len(repo.get_all()) > 0


class TestFuelConstants:
    def test_load_fuel_constants(self) -> None:
        fc = load_fuel_constants(ASSETS_DIR / "fuel_constants.yaml")
        assert fc.gasoline_kwh_per_liter == pytest.approx(8.9)
        assert fc.diesel_kwh_per_liter == pytest.approx(9.7)
