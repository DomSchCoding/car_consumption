"""Smoke tests for UI module imports and basic function signatures."""

from __future__ import annotations

from app.data.models import PhysicsParams, VehicleType
from app.data.repository import VehicleRepository


class TestUIStateImport:
    def test_session_dict_exists(self) -> None:
        from app.ui.state import SESSION

        assert isinstance(SESSION, dict)
        assert "selected" in SESSION
        assert "dark" in SESSION
        assert "ranking_sort" in SESSION

    def test_session_defaults(self) -> None:
        from app.ui.state import SESSION

        assert SESSION["ev_checked"] is True
        assert SESSION["ice_checked"] is False


class TestUIChartsImport:
    def test_build_chart_importable(self) -> None:
        from app.ui.charts import build_chart

        assert callable(build_chart)

    def test_vehicle_colors_importable(self) -> None:
        from app.ui.charts import VEHICLE_COLORS

        assert isinstance(VEHICLE_COLORS, list)
        assert len(VEHICLE_COLORS) > 0

    def test_export_chart_importable(self) -> None:
        from app.ui.charts import export_chart_png

        assert callable(export_chart_png)

    def test_build_chart_produces_figure(self) -> None:
        from app.ui.charts import build_chart

        repo = VehicleRepository()
        evs = repo.get_ev_vehicles()
        if not evs:
            return
        vehicles = evs[:2]
        params = PhysicsParams()
        from app.data.repository import load_fuel_constants

        fuel_const = load_fuel_constants()
        fig = build_chart(vehicles, params, 30, 160, fuel_const, 0.30, True)
        assert fig is not None
        assert len(fig.data) > 0


class TestUITablesImport:
    def test_build_table_importable(self) -> None:
        from app.ui.tables import build_table

        assert callable(build_table)

    def test_build_ranking_list_importable(self) -> None:
        from app.ui.tables import build_ranking_list

        assert callable(build_ranking_list)

    def test_build_vehicle_detail_importable(self) -> None:
        from app.ui.tables import build_vehicle_detail_html

        assert callable(build_vehicle_detail_html)

    def test_speed_options_importable(self) -> None:
        from app.ui.tables import SPEED_OPTIONS

        assert SPEED_OPTIONS == [50, 80, 100, 130]

    def test_build_table_produces_html(self) -> None:
        from app.ui.tables import build_table

        repo = VehicleRepository()
        evs = repo.get_ev_vehicles()
        if not evs:
            return
        vehicles = evs[:2]
        params = PhysicsParams()
        from app.data.repository import load_fuel_constants

        fuel_const = load_fuel_constants()
        html = build_table(vehicles, params, fuel_const, 0.30, True)
        assert "<table" in html
        assert "kWh" in html or "km" in html

    def test_build_ranking_list_produces_html(self) -> None:
        from app.ui.tables import build_ranking_list

        repo = VehicleRepository()
        params = PhysicsParams()
        from app.data.repository import load_fuel_constants

        fuel_const = load_fuel_constants()
        html = build_ranking_list(params, 100, True, False, fuel_const, 0.30, True, repo)
        assert "EV" in html or "km" in html

    def test_build_vehicle_detail_produces_html(self) -> None:
        from app.ui.tables import build_vehicle_detail_html

        repo = VehicleRepository()
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        html = build_vehicle_detail_html(v)
        assert "Hyundai" in html
        assert "Specifications" in html

    def test_confidence_badge(self) -> None:
        from app.data.models import ConfidenceLevel
        from app.ui.tables import build_confidence_badge

        html = build_confidence_badge(ConfidenceLevel.high)
        assert "conf-badge" in html
        assert "high" in html


class TestVehicleSelectorImport:
    def test_make_vehicle_label(self) -> None:
        from app.ui.components.vehicle_selector import make_vehicle_label

        repo = VehicleRepository()
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        label = make_vehicle_label(v)
        assert "Hyundai" in label
        assert "Ioniq" in label

    def test_short_label(self) -> None:
        from app.ui.components.vehicle_selector import short_label

        repo = VehicleRepository()
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        label = short_label(v)
        assert "Hyundai" not in label
        assert "Ioniq" in label

    def test_get_vehicle_c_rr(self) -> None:
        from app.ui.components.vehicle_selector import get_vehicle_c_rr

        repo = VehicleRepository()
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        c_rr_default = get_vehicle_c_rr(v, 0.01, False)
        assert c_rr_default == 0.01

    def test_get_vehicles_by_make(self) -> None:
        from app.ui.components.vehicle_selector import get_vehicles_by_make

        repo = VehicleRepository()
        grouped = get_vehicles_by_make(repo)
        assert isinstance(grouped, dict)
        assert len(grouped) > 0
        for make, vehicles in grouped.items():
            assert make
            assert len(vehicles) > 0

    def test_get_filtered_makes(self) -> None:
        from app.ui.components.vehicle_selector import get_filtered_makes

        repo = VehicleRepository()
        ev_makes = get_filtered_makes(repo, show_ev=True, show_ice=False)
        assert len(ev_makes) > 0
        ice_makes = get_filtered_makes(repo, show_ev=False, show_ice=True)
        assert len(ice_makes) > 0

    def test_get_filtered_models(self) -> None:
        from app.ui.components.vehicle_selector import get_filtered_makes, get_filtered_models

        repo = VehicleRepository()
        makes = get_filtered_makes(repo, show_ev=True, show_ice=False)
        assert len(makes) > 0
        models = get_filtered_models(repo, makes[0], show_ev=True, show_ice=False)
        assert len(models) > 0
        assert all(v.vehicle_type == VehicleType.ev for v in models)

    def test_tire_class_label(self) -> None:
        from app.ui.components.vehicle_selector import tire_class_label

        repo = VehicleRepository()
        for v in repo.get_all():
            label = tire_class_label(v)
            assert isinstance(label, str)

    def test_vehicle_data_quality(self) -> None:
        from app.ui.components.vehicle_selector import vehicle_data_quality

        repo = VehicleRepository()
        v = repo.get("hyundai_ioniq_28")
        assert v is not None
        q = vehicle_data_quality(v)
        assert "mass_kg" in q
        assert "frontal_area_m2" in q
        assert "sources" in q
