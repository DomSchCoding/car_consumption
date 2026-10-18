"""Native NiceGUI vehicle detail rendering (UI redesign phase 5).

Replaces the HTML-string approach with native components so the page
inherits dark mode, accessibility and the shared theme automatically.
Layout:

- Header card: image (left) + identity / completeness (right)
- Two-column grid on desktop (single column on mobile via CSS):
  * Specifications card
  * Consumption + Charging card
- Sources card: one expandable list item per source
- Optional Notes card

The legacy `build_vehicle_detail_html` is kept for backward compatibility
and its tests; this module is the renderer used by the live page.
"""

from __future__ import annotations

from nicegui import ui

from app.data.models import Vehicle, VehicleType
from app.ui.components.vehicle_selector import (
    get_drivetrain_label,
    make_vehicle_label,
    vehicle_data_quality,
)
from app.ui.tables import IMAGES_DIR

# Colors for confidence badges (kept in sync with tables.CONFIDENCE_COLORS)
CONFIDENCE_COLORS = {
    "high": "#2E7D32",
    "medium": "#1976D2",
    "low": "#C62828",
}


def _completeness(v: Vehicle) -> float:
    q = vehicle_data_quality(v)
    if not q:
        return 100.0
    missing = sum(1 for ok in q.values() if not ok)
    return (len(q) - missing) / len(q) * 100


def _confidence_badge(level) -> ui.element:
    color = CONFIDENCE_COLORS.get(getattr(level, "value", str(level)), "#888")
    return ui.label(getattr(level, "value", str(level))).style(
        f"background:{color}22; color:{color}; border:1px solid {color}44; "
        "border-radius:8px; padding:0 6px; font-size:0.72em; font-weight:600;"
    )


def _spec_row(label: str, value: str, missing: bool = False) -> None:
    """One label/value row inside a detail card."""
    with ui.row().classes("w-full items-center justify-between gap-2 detail-row"):
        ui.label(label).classes("detail-label")
        with ui.row().classes("items-center gap-1"):
            ui.label(value).classes("detail-value")
            if missing:
                ui.label("missing").classes("detail-missing")


def _year_span(v: Vehicle) -> str:
    if not v.year_from:
        return ""
    s = str(v.year_from)
    if v.year_to:
        s += f"-{v.year_to}"
    return s


def render_vehicle_detail(v: Vehicle) -> None:
    """Render the full vehicle detail page content natively."""
    completeness = _completeness(v)
    has_image = (IMAGES_DIR / f"{v.id}.jpg").exists()

    # ── Header card ──────────────────────────────────────────────────────
    with ui.card().classes("q-card detail-card").style("gap:16px; align-items:flex-start;"):
        if has_image:
            ui.image(f"/images/{v.id}.jpg").classes("detail-img").style("object-fit:contain; background:#f5f5f5;")
        with ui.column().classes("gap-1 min-w-0 flex-grow"):
            ui.label(make_vehicle_label(v)).style("font-size:1.35em; font-weight:800;")
            ui.label(f"{v.make} · {v.vehicle_type.value.upper()}").classes("detail-sub")
            with ui.row().classes("items-center gap-2"):
                ui.linear_progress(value=completeness / 100).props("rounded size=sm color=primary").style(
                    "width:140px;"
                )
                ui.label(f"Data completeness: {completeness:.0f}%").classes("detail-sub")
            years = _year_span(v)
            if years:
                ui.label(f"Years: {years}").classes("detail-sub")

    # ── Two-column grid: specs | consumption ─────────────────────────────
    with ui.row().classes("detail-grid w-full items-stretch"):
        # Specifications
        with ui.card().classes("q-card detail-card detail-col"):
            ui.label("Specifications").classes("detail-header")
            rows: list[tuple[str, str, bool]] = [
                ("Mass", f"{v.mass_kg:.0f} kg", True),
                ("Frontal Area", f"{v.frontal_area_m2:.2f} m²", True),
                ("Drag Coefficient (Cd)", f"{v.drag_coefficient_cd:.3f}", True),
                ("CdA", f"{v.cda_m2:.4f} m²", True),
            ]
            if v.length_mm is not None:
                rows.append(("Length", f"{v.length_mm:.0f} mm", True))
            if v.ground_clearance_mm is not None:
                rows.append(("Ground Clearance", f"{v.ground_clearance_mm:.0f} mm", True))
            if v.drivetrain is not None:
                rows.append(("Drivetrain", get_drivetrain_label(v), True))
            if v.new_price_eur is not None:
                rows.append(("MSRP (new)", f"€{v.new_price_eur:,.0f}", True))
            if v.trunk_volume_l is not None:
                rows.append(("Trunk Volume", f"{v.trunk_volume_l:.0f} L", True))
            if v.vehicle_type == VehicleType.ev:
                if v.battery_usable_kwh:
                    rows.append(("Battery", f"{v.battery_usable_kwh:.1f} kWh", True))
                else:
                    rows.append(("Battery", "N/A", False))
                if v.ac_charging_kw:
                    rows.append(("AC Charging", f"{v.ac_charging_kw:.1f} kW", True))
                if v.dc_charging_kw:
                    rows.append(("DC Charging (peak)", f"{v.dc_charging_kw:.0f} kW", True))
                ct = v.charge_time_20_80_min
                if ct is not None:
                    rows.append(("20→80% DC", f"{ct:.0f} min", True))
                if v.has_heat_pump is not None:
                    rows.append(("Heat Pump", "✓ Heat Pump" if v.has_heat_pump else "✗ No Heat Pump", True))
                else:
                    rows.append(("Heat Pump", "unknown", False))
                if v.hvac_cop_heat is not None:
                    rows.append(("HVAC COP (heat)", f"{v.hvac_cop_heat:.1f}", True))
                elif v.has_heat_pump:
                    rows.append(("HVAC COP (heat)", "2.5 (default)", False))
            else:
                rows.append(("Fuel Type", v.fuel_type.value if v.fuel_type else "N/A", v.fuel_type is not None))
            for lab, val, ok in rows:
                _spec_row(lab, val, missing=not ok)

        # Consumption
        with ui.card().classes("q-card detail-card detail-col"):
            ui.label("Consumption Data").classes("detail-header")
            if v.vehicle_type == VehicleType.ev:
                if v.wltp_consumption_kwh_100km:
                    _spec_row("WLTP", f"{v.wltp_consumption_kwh_100km.value:.1f} kWh/100km")
                else:
                    _spec_row("WLTP", "N/A", missing=True)
                if v.epa_consumption_kwh_100km:
                    _spec_row("EPA", f"{v.epa_consumption_kwh_100km.value:.1f} kWh/100km")
                for rc in v.real_consumption_kwh_100km:
                    _spec_row("Real-world", f"{rc.value:.1f} kWh/100km")
            else:
                if v.real_consumption_l_100km:
                    _spec_row("Real-world", f"{v.real_consumption_l_100km.value:.1f} L/100km")
                else:
                    _spec_row("Real-world", "N/A", missing=True)

    # ── Sources (expandable list items) ──────────────────────────────────
    with ui.card().classes("q-card detail-card"):
        ui.label("Sources").classes("detail-header")
        if v.source_refs:
            for _key, src in v.source_refs.items():
                with ui.expansion().props("dense") as exp:
                    with ui.row().classes("w-full items-center justify-between gap-2"):
                        with ui.row().classes("items-center gap-2 min-w-0"):
                            ui.label(src.name).style("font-weight:600;")
                            _confidence_badge(src.confidence)
                        if src.url:
                            ui.link("link ↗", src.url).new_tab().props("color=primary")
                    with ui.column().classes("w-full gap-1"):
                        if src.field_names:
                            ui.label("Fields: " + ", ".join(src.field_names)).classes("detail-sub")
                        if src.license_note:
                            ui.label(src.license_note).classes("detail-sub")
                        if src.comment:
                            ui.label(src.comment).classes("detail-sub")
                # First source expanded by default
                if _key == next(iter(v.source_refs)):
                    exp.value = True
        else:
            ui.label("no sources").classes("detail-missing")

    # ── Notes ────────────────────────────────────────────────────────────
    if v.notes:
        with ui.card().classes("q-card detail-card"):
            ui.label("Notes").classes("detail-header")
            ui.label(v.notes).classes("detail-notes")
