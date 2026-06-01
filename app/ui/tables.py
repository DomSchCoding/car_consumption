"""HTML table and ranking generation for the Vehicle Consumption Analyzer."""

from __future__ import annotations

from pathlib import Path

from app.core.physics import (
    battery_capacity_factor,
    hvac_power_kw,
    total_consumption,
)
from app.data.models import (
    ConfidenceLevel,
    FuelConstants,
    FuelType,
    PhysicsParams,
    Vehicle,
    VehicleType,
)
from app.data.repository import VehicleRepository
from app.ui.components.vehicle_selector import (
    get_vehicle_c_rr,
    make_vehicle_label,
    tire_class_label,
    vehicle_data_quality,
)

IMAGES_DIR = Path(__file__).resolve().parent.parent / "assets" / "images"

SPEED_OPTIONS = [50, 80, 100, 130]

CONFIDENCE_COLORS = {
    ConfidenceLevel.high: "#00CC96",
    ConfidenceLevel.medium: "#FFA15A",
    ConfidenceLevel.low: "#EF553B",
}

_DC = "background:#fff; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.06);"


def build_confidence_badge(level: ConfidenceLevel) -> str:
    color = CONFIDENCE_COLORS.get(level, "#888")
    s = f"background:{color}22; color:{color}; border:1px solid {color}44;"
    return f'<span class="conf-badge" style="{s}">{level.value}</span>'


def build_table(
    vehicles: list[Vehicle],
    params: PhysicsParams,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
) -> str:
    speeds = [50, 80, 100, 130]
    header = ["Vehicle", "Type", "CdA", "Tire"]
    for s in speeds:
        header.append(f"{s} km/h")
        header.append("Range")
    header.append("20-80%")
    has_ev = any(v.vehicle_type == VehicleType.ev for v in vehicles)

    cap_factor = battery_capacity_factor(params.temperature_c)

    rows: list[list[str]] = []
    for v in vehicles:
        c_rr = get_vehicle_c_rr(v, params.c_rr, use_per_vehicle_tires)
        cda = f"{v.cda_m2:.2f}"
        tire = f"{tire_class_label(v)} ({c_rr:.3f})"
        row = [make_vehicle_label(v), v.vehicle_type.value.upper(), cda, tire]
        if v.vehicle_type == VehicleType.ev:
            hp = v.has_heat_pump if v.has_heat_pump is not None else False
            cop = v.hvac_cop_heat if v.hvac_cop_heat is not None else None
            vehicle_hvac = hvac_power_kw(
                params.temperature_c,
                params.cabin_target_temp_c,
                has_heat_pump=hp,
                hvac_cop_heat=cop,
            )
            effective_battery = v.battery_usable_kwh * cap_factor if v.battery_usable_kwh else None
            for s in speeds:
                bc = total_consumption(
                    rho_air=params.rho_air,
                    cd=v.drag_coefficient_cd,
                    frontal_area_m2=v.frontal_area_m2,
                    mass_kg=v.mass_kg,
                    c_rr=c_rr,
                    p_aux_kw=vehicle_hvac,
                    speed_kmh=s,
                    eta_drivetrain=params.eta_drivetrain,
                )
                wall_kwh = bc.total_battery_kwh_per_100km / params.eta_charging
                row.append(f"{bc.total_battery_kwh_per_100km:.1f} ({wall_kwh:.1f})")
                if effective_battery:
                    rng = effective_battery / bc.total_battery_kwh_per_100km * 100
                    row.append(f"{rng:.0f} km")
                else:
                    row.append("-")
            ct = v.charge_time_20_80_min
            row.append(f"{ct:.0f} min" if ct is not None else "-")
        else:
            l_100 = v.real_consumption_l_100km
            if l_100:
                kwh_per_l = (
                    fuel_const.diesel_kwh_per_liter
                    if v.fuel_type == FuelType.diesel
                    else fuel_const.gasoline_kwh_per_liter
                )
                chem = l_100.value * kwh_per_l
                wheel = chem * ice_thermal_eff
                for _ in speeds:
                    row.append(f"{chem:.0f}/{wheel:.0f}")
                    row.append("-")
            else:
                for _ in speeds:
                    row.append("N/A")
                    row.append("-")
            row.append("-")
        rows.append(row)

    t_style = "width:100%; border-collapse: collapse; font-size: 0.82em; font-family: system-ui, sans-serif;"
    th_style = (
        "border-bottom:2px solid #e0e0e0; padding:8px 6px;"
        " background:#fafafa; color:#555; font-weight:600; text-align:left;"
    )
    td_style = "padding:8px 6px; border-bottom:1px solid #f0f0f0;"
    td_range = "padding:8px 6px; border-bottom:1px solid #f0f0f0; color:#636EFA; font-size:0.78em; font-weight:600;"
    td_charge = "padding:8px 6px; border-bottom:1px solid #f0f0f0; color:#00CC96; font-size:0.78em; font-weight:600;"

    html = f'<table style="{t_style}"><thead><tr>'
    for _i, h in enumerate(header):
        if h == "Range":
            html += (
                f'<th style="{th_style} text-align:right; font-weight:400; font-size:0.75em; color:#636EFA;">km</th>'
            )
        elif h == "20-80%":
            dc_header_style = f"{th_style} text-align:center; font-weight:400; font-size:0.75em; color:#00CC96;"
            html += f'<th style="{dc_header_style}">DC ⚡</th>'
        else:
            html += f'<th style="{th_style}">{h}</th>'
    html += "</tr></thead><tbody>"
    for ri, row in enumerate(rows):
        bg = "#fafafa" if ri % 2 == 0 else "#fff"
        html += f'<tr style="background:{bg};">'
        for ci, cell in enumerate(row):
            is_range = (ci >= 4) and (ci < len(row) - 1) and ((ci - 4) % 2 == 1)
            is_charge = ci == len(row) - 1
            if is_charge:
                html += f'<td style="{td_charge} text-align:center;">{cell}</td>'
            elif is_range:
                html += f'<td style="{td_range} text-align:right;">{cell}</td>'
            else:
                align = "center" if ci >= 2 else "left"
                weight = "600" if ci == 0 else "400"
                html += f'<td style="{td_style} text-align:{align}; font-weight:{weight};">{cell}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    notes = []
    if has_ev:
        has_hp = sum(1 for v in vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump)
        no_hp = sum(1 for v in vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump is False)
        notes.append(f"Range at {int(params.temperature_c)}°C (battery {cap_factor:.0%})")
        hp_str = f"HP: {has_hp} yes" if has_hp else ""
        if no_hp:
            hp_str += f", {no_hp} resistive" if hp_str else f"Resistive: {no_hp}"
        if hp_str:
            notes.append(hp_str)
        notes.append("Values: battery kWh (wall kWh incl. charging η)")
        notes.append(f"Wall η={params.eta_charging:.0%}")
        notes.append("20-80% = DC charge time")
    else:
        notes.append("ICE: chemical/wheel (est.) kWh/100km")
    html += f'<div style="margin-top:8px; font-size:0.78em; color:#999;">{" | ".join(notes)}</div>'
    return html


def build_ranking_list(
    params: PhysicsParams,
    speed_kmh: float,
    show_ev: bool,
    show_ice: bool,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
    repo: VehicleRepository,
    sort_by_range: bool = False,
) -> str:
    all_vehicles = repo.get_all()
    entries: list[tuple[str, str, float, str, float | None, str, float | None]] = []

    for v in sorted(all_vehicles, key=lambda x: (x.make, x.model)):
        c_rr = get_vehicle_c_rr(v, params.c_rr, use_per_vehicle_tires)
        if show_ev and v.vehicle_type == VehicleType.ev:
            hp = v.has_heat_pump if v.has_heat_pump is not None else False
            cop = v.hvac_cop_heat if v.hvac_cop_heat is not None else None
            vehicle_hvac = hvac_power_kw(
                params.temperature_c,
                params.cabin_target_temp_c,
                has_heat_pump=hp,
                hvac_cop_heat=cop,
            )
            bc = total_consumption(
                rho_air=params.rho_air,
                cd=v.drag_coefficient_cd,
                frontal_area_m2=v.frontal_area_m2,
                mass_kg=v.mass_kg,
                c_rr=c_rr,
                p_aux_kw=vehicle_hvac,
                speed_kmh=speed_kmh,
                eta_drivetrain=params.eta_drivetrain,
            )
            val = bc.total_battery_kwh_per_100km
            cap = battery_capacity_factor(params.temperature_c)
            effective_battery = v.battery_usable_kwh * cap if v.battery_usable_kwh else None
            rng = (effective_battery / val * 100) if effective_battery else None
            entries.append((make_vehicle_label(v), "EV", val, make_vehicle_label(v), None, "kWh", rng))
        elif show_ice and v.vehicle_type != VehicleType.ev:
            l_100 = v.real_consumption_l_100km
            if l_100:
                kwh_per_l = (
                    fuel_const.diesel_kwh_per_liter
                    if v.fuel_type == FuelType.diesel
                    else fuel_const.gasoline_kwh_per_liter
                )
                chem = l_100.value * kwh_per_l
                val = chem * ice_thermal_eff
                entries.append((make_vehicle_label(v), "ICE", val, make_vehicle_label(v), chem, "kWh", None))

    if sort_by_range:
        entries.sort(key=lambda x: -(x[6] if x[6] is not None else float("-inf")))
    else:
        entries.sort(key=lambda x: x[2])

    if not entries:
        return '<div style="padding:20px; text-align:center; color:#999;">No vehicles match the selected filters</div>'

    vals = [e[2] for e in entries]
    max_val = max(vals)
    min_val = min(vals)
    range_val = max_val - min_val if max_val != min_val else 1.0

    def _hd(text: str, active: bool) -> str:
        if active:
            return f'<span style="color:#636EFA; font-weight:700;">{text}</span>'
        return f'<span style="color:#888;">{text}</span>'

    sort_active = "range" if sort_by_range else "consumption"
    header = (
        '<div style="display:flex; align-items:center; gap:10px;'
        " padding:6px 8px; border-bottom:2px solid #e0e0e0;"
        ' font-size:0.78em; font-weight:600; color:#888; margin-bottom:4px;">'
        '<span style="min-width:24px;">#</span>'
        '<span style="min-width:28px;"></span>'
        f'<span style="flex:1;">Vehicle</span>'
        '<span style="width:120px;"></span>'
        f'<span style="min-width:65px; text-align:right;">'
        f"{_hd('kWh/100km', sort_active == 'consumption')}</span>"
        f'<span style="min-width:65px; text-align:right;">'
        f"{_hd('Range', sort_active == 'range')}</span>"
        "</div>"
    )

    html = '<div style="font-family:system-ui, sans-serif;">' + header
    for rank, (_n, vtype, val, label, detail, unit, rng) in enumerate(entries, 1):
        pct = ((val - min_val) / range_val) * 100
        color = "#00CC96" if vtype == "EV" else "#EF553B"
        badge_bg = "#00CC9622" if vtype == "EV" else "#EF553B22"
        badge_color = "#00CC96" if vtype == "EV" else "#EF553B"

        row = "display:flex; align-items:center; gap:10px; padding:6px 8px; border-bottom:1px solid #f0f0f0;"
        html += f'<div style="{row}">'
        html += f'<span style="min-width:24px; color:#999; font-size:0.82em; text-align:right;">{rank}.</span>'
        badge = (
            f"min-width:28px; font-size:0.7em; font-weight:700;"
            f" padding:2px 5px; border-radius:4px; text-align:center;"
            f" background:{badge_bg}; color:{badge_color};"
        )
        html += f'<span style="{badge}">{vtype}</span>'
        name = "flex:1; font-size:0.88em; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"
        html += f'<span style="{name}">{label}</span>'
        bar = "width:120px; height:8px; background:#f0f0f0; border-radius:4px; overflow:hidden;"
        html += (
            f'<div style="{bar}">'
            f'<div style="width:{pct:.0f}%; height:100%;'
            f' background:{color}; border-radius:4px;"></div></div>'
        )
        val_s = "min-width:65px; text-align:right; font-size:0.85em; font-weight:600; color:#333;"
        html += f'<span style="{val_s}">{val:.1f} {unit}</span>'
        rng_s = "min-width:65px; text-align:right; font-size:0.85em; font-weight:600; color:#333;"
        if rng is not None:
            html += f'<span style="{rng_s}">{rng:.0f} km</span>'
        else:
            html += '<span style="min-width:65px; text-align:right; font-size:0.78em; color:#bbb;">-</span>'
        if detail is not None:
            html += (
                f'<span style="min-width:55px; text-align:right;'
                f' font-size:0.78em; color:#999;">'
                f"({detail:.0f} chem)</span>"
            )
        html += "</div>"
    html += "</div>"
    cap_pct = battery_capacity_factor(params.temperature_c) * 100
    hp_count = sum(1 for v in all_vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump)
    no_hp_count = sum(1 for v in all_vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump is False)
    footer = f"At {int(params.temperature_c)}°C, battery {cap_pct:.0f}%"
    if hp_count:
        footer += f" | {hp_count} heat pump"
    if no_hp_count:
        footer += f", {no_hp_count} resistive"
    html += f'<div style="margin-top:6px; font-size:0.78em; color:#999; padding:4px 8px;">{footer}</div>'
    return html


def build_vehicle_detail_html(v: Vehicle) -> str:
    q = vehicle_data_quality(v)
    missing_count = sum(1 for ok in q.values() if not ok)
    completeness = (len(q) - missing_count) / len(q) * 100

    img_path = IMAGES_DIR / f"{v.id}.jpg"
    has_image = img_path.exists()

    html = '<div style="font-family:system-ui, sans-serif;">'

    # Inline CSS for tabular detail layout
    html += "<style>"
    html += ".detail-row{display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0f0f0;}"
    html += ".detail-label{font-weight:600;color:#555;font-size:0.88em;min-width:180px;flex-shrink:0;}"
    html += ".detail-value{text-align:right;font-size:0.88em;color:#333;font-weight:500;}"
    html += ".detail-header{font-weight:700;font-size:1em;color:#333;padding:8px 0 4px 0;border-bottom:2px solid #e0e0e0;margin-bottom:4px;}"
    html += ".missing-tag{font-size:0.72em;color:#EF553B;margin-left:4px;}"
    html += "</style>"

    html += f'<div class="detail-card" style="{_DC} display:flex; gap:20px; align-items:flex-start;">'
    if has_image:
        html += (
            f'<div style="flex-shrink:0; width:240px; height:160px; '
            f"background:#f5f5f5; border-radius:8px; overflow:hidden; "
            f'display:flex; align-items:center; justify-content:center;">'
            f'<img src="/images/{v.id}.jpg" '
            f'style="max-width:100%; max-height:100%; object-fit:contain;" '
            f'alt="{make_vehicle_label(v)}">'
            f"</div>"
        )
    html += '<div style="flex:1; min-width:0;">'
    html += f'<h2 style="margin:0 0 4px 0; font-size:1.4em;">{make_vehicle_label(v)}</h2>'
    html += (
        f'<div style="color:#888; font-size:0.9em; margin-bottom:8px;">{v.make} · {v.vehicle_type.value.upper()}</div>'
    )
    html += f'<div style="margin-bottom:4px;">Data completeness: {completeness:.0f}%</div>'
    year_str = ""
    if v.year_from:
        year_str = str(v.year_from)
        if v.year_to:
            year_str += f"-{v.year_to}"
    if year_str:
        html += f'<div style="color:#888; font-size:0.85em;">Years: {year_str}</div>'
    html += "</div></div>"

    html += f'<div class="detail-card" style="{_DC}">'
    html += '<div class="detail-header">Specifications</div>'

    rows: list[tuple[str, str, bool]] = [
        ("Mass", f"{v.mass_kg:.0f} kg", q["mass_kg"]),
        ("Frontal Area", f"{v.frontal_area_m2:.2f} m²", q["frontal_area_m2"]),
        ("Drag Coefficient (Cd)", f"{v.drag_coefficient_cd:.3f}", q["drag_coefficient_cd"]),
        ("CdA", f"{v.cda_m2:.4f} m²", True),
    ]
    if v.vehicle_type == VehicleType.ev:
        if v.battery_usable_kwh:
            rows.append(("Battery", f"{v.battery_usable_kwh:.1f} kWh", q.get("battery_usable_kwh", True)))
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
            hp_label = "✓ Heat Pump" if v.has_heat_pump else "✗ No Heat Pump"
            rows.append(("Heat Pump", hp_label, True))
        else:
            rows.append(("Heat Pump", "unknown", False))
        if v.hvac_cop_heat is not None:
            rows.append(("HVAC COP (heat)", f"{v.hvac_cop_heat:.1f}", True))
        elif v.has_heat_pump:
            rows.append(("HVAC COP (heat)", "2.5 (default)", False))
    else:
        rows.append(("Fuel Type", v.fuel_type.value if v.fuel_type else "N/A", q.get("fuel_type", False)))

    for lab, val, ok in rows:
        tag = "" if ok else '<span class="missing-tag">missing</span>'
        html += (
            f'<div class="detail-row">'
            f'<span class="detail-label">{lab}</span>'
            f'<span class="detail-value">{val} {tag}</span></div>'
        )
    html += "</div>"

    html += f'<div class="detail-card" style="{_DC}">'
    html += '<div class="detail-header">Consumption Data</div>'

    if v.vehicle_type == VehicleType.ev:
        if v.wltp_consumption_kwh_100km:
            wltp = v.wltp_consumption_kwh_100km.value
            html += (
                f'<div class="detail-row">'
                f'<span class="detail-label">WLTP</span>'
                f'<span class="detail-value">{wltp:.1f} kWh/100km</span></div>'
            )
        else:
            html += (
                '<div class="detail-row"><span class="detail-label">WLTP</span>'
                '<span class="detail-value"><span class="missing-tag">missing</span></span></div>'
            )
        if v.epa_consumption_kwh_100km:
            epa = v.epa_consumption_kwh_100km.value
            html += (
                f'<div class="detail-row">'
                f'<span class="detail-label">EPA</span>'
                f'<span class="detail-value">{epa:.1f} kWh/100km</span></div>'
            )
        for rc in v.real_consumption_kwh_100km:
            html += (
                f'<div class="detail-row">'
                f'<span class="detail-label">Real-world</span>'
                f'<span class="detail-value">{rc.value:.1f} kWh/100km</span></div>'
            )
    else:
        if v.real_consumption_l_100km:
            rl = v.real_consumption_l_100km.value
            html += (
                f'<div class="detail-row">'
                f'<span class="detail-label">Real-world</span>'
                f'<span class="detail-value">{rl:.1f} L/100km</span></div>'
            )
    html += "</div>"

    if v.source_refs:
        html += f'<div class="detail-card" style="{_DC}">'
        html += '<div class="detail-header">Sources</div>'
        for _key, src in v.source_refs.items():
            badge = build_confidence_badge(src.confidence)
            html += '<div class="detail-row">'
            html += f'<span class="detail-label">{src.name} {badge}</span>'
            if src.url:
                html += f'<a href="{src.url}" target="_blank" style="font-size:0.78em; color:#636EFA;">link</a>'
            html += "</div>"
            if src.comment:
                html += f'<div style="font-size:0.78em; color:#999; padding:2px 0 4px 0;">{src.comment}</div>'
        html += "</div>"
    else:
        html += f'<div class="detail-card" style="{_DC}">'
        html += '<div class="detail-header">Sources</div>'
        html += '<span class="missing-tag">no sources</span>'
        html += "</div>"

    if v.notes:
        html += f'<div class="detail-card" style="{_DC}">'
        html += f'<div class="detail-header">Notes</div><div style="font-size:0.88em; color:#555;">{v.notes}</div>'
        html += "</div>"

    html += "</div>"
    return html
