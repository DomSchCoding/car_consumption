"""NiceGUI main application - Vehicle consumption analysis webapp."""

from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from pathlib import Path

import plotly.graph_objects as go
from nicegui import app, ui

from app.core.physics import (
    battery_capacity_factor,
    charging_curve_points,
    consumption_curve,
    hvac_power_kw,
    total_consumption,
)
from app.data.models import (
    ConfidenceLevel,
    FuelConstants,
    FuelType,
    PhysicsParams,
    TireClass,
    Vehicle,
    VehicleType,
)
from app.data.repository import VehicleRepository, load_fuel_constants

IMAGES_DIR = Path(__file__).resolve().parent / "assets" / "images"

REPO = VehicleRepository()
FUEL_CONST = load_fuel_constants()

app.add_static_files("/images", str(IMAGES_DIR))

SESSION = {
    "selected": [],
    "dark": False,
    "ranking_sort": False,
    "current_make": "",
    "ev_checked": True,
    "ice_checked": False,
    "ranking_ev": True,
    "ranking_ice": False,
}

VEHICLE_COLORS = [
    "#636EFA",
    "#EF553B",
    "#00CC96",
    "#AB63FA",
    "#FFA15A",
    "#19D3F3",
    "#FF6692",
    "#B6E880",
    "#FF97FF",
    "#FECB52",
    "#FFABAB",
    "#A0D2EB",
    "#E2F0CB",
    "#FFD3B6",
    "#D4A5A5",
]


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


SPEED_OPTIONS = [50, 80, 100, 130]
MAX_COMPARE = 8

CONFIDENCE_COLORS = {
    ConfidenceLevel.high: "#00CC96",
    ConfidenceLevel.medium: "#FFA15A",
    ConfidenceLevel.low: "#EF553B",
}

DARK_CSS = """
body.dark {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
    color: #cdd6f4;
}
body.dark .q-card {
    background: #1e1e2e !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}
body.dark label, body.dark .text-grey { color: #a6adc8 !important; }
"""

LIGHT_CSS = """
body {
    background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    min-height: 100vh;
}
.q-card {
    border-radius: 12px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
}
"""

SHARED_CSS = """
.sel-item {
    display: flex; align-items: center; padding: 4px 6px;
    border-radius: 6px; font-size: 0.82em;
}
.sel-item:hover { background: var(--hover-bg, #f5f5f5); }
.add-btn {
    font-size: 0.78em; padding: 3px 8px; border-radius: 6px;
    border: 1px solid #e0e0e0; background: #fff;
    cursor: pointer; transition: all 0.15s ease;
    width: 100%; text-align: left;
}
.add-btn:hover { background: #f0f4ff; border-color: #636EFA; }
.add-btn.selected {
    background: #636EFA22; border-color: #636EFA44; color: #636EFA;
}
.filter-row {
    display: flex; gap: 12px; align-items: center; margin-bottom: 8px;
}
.conf-badge {
    display: inline-block; padding: 1px 6px; border-radius: 4px;
    font-size: 0.7em; font-weight: 700; text-transform: uppercase;
}
.detail-card {
    padding: 16px; margin-bottom: 12px;
}
.detail-header {
    font-weight: 700; font-size: 0.85em; color: #888;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
}
.detail-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid #f0f0f0;
}
.detail-label { color: #888; font-size: 0.88em; }
.detail-value { font-weight: 600; font-size: 0.88em; }
.missing-tag {
    display: inline-block; font-size: 0.68em; padding: 1px 5px;
    border-radius: 3px; background: #FFA15A22; color: #FFA15A;
    margin-left: 4px; font-weight: 600;
}
"""


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


def get_vehicles_by_make() -> dict[str, list[Vehicle]]:
    grouped: dict[str, list[Vehicle]] = defaultdict(list)
    for v in sorted(REPO.get_all(), key=lambda x: (x.make, x.model, x.variant)):
        grouped[v.make].append(v)
    return dict(sorted(grouped.items()))


def get_filtered_makes(show_ev: bool, show_ice: bool) -> list[str]:
    grouped = get_vehicles_by_make()
    makes = []
    for make, vehicles in grouped.items():
        has_ev = any(v.vehicle_type == VehicleType.ev for v in vehicles)
        has_ice = any(v.vehicle_type != VehicleType.ev for v in vehicles)
        if (show_ev and has_ev) or (show_ice and has_ice):
            makes.append(make)
    return makes


def get_filtered_models(make: str, show_ev: bool, show_ice: bool) -> list[Vehicle]:
    vehicles = get_vehicles_by_make().get(make, [])
    result = []
    for v in vehicles:
        if show_ev and v.vehicle_type == VehicleType.ev:
            result.append(v)
        if show_ice and v.vehicle_type != VehicleType.ev:
            result.append(v)
    return result


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


def build_chart(
    vehicles: list[Vehicle],
    params: PhysicsParams,
    speed_min: float,
    speed_max: float,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
) -> go.Figure:
    fig = go.Figure()

    cap_factor = battery_capacity_factor(params.temperature_c)

    for idx, vehicle in enumerate(vehicles):
        color = VEHICLE_COLORS[idx % len(VEHICLE_COLORS)]
        c_rr = get_vehicle_c_rr(vehicle, params.c_rr, use_per_vehicle_tires)
        hp = vehicle.has_heat_pump if vehicle.has_heat_pump is not None else False
        cop = vehicle.hvac_cop_heat if vehicle.hvac_cop_heat is not None else None
        vehicle_hvac = hvac_power_kw(params.temperature_c, params.cabin_target_temp_c, has_heat_pump=hp, hvac_cop_heat=cop)
        curve = consumption_curve(
            rho_air=params.rho_air,
            cd=vehicle.drag_coefficient_cd,
            frontal_area_m2=vehicle.frontal_area_m2,
            mass_kg=vehicle.mass_kg,
            c_rr=c_rr,
            p_aux_kw=vehicle_hvac,
            speed_min_kmh=speed_min,
            speed_max_kmh=speed_max,
            steps=80,
            eta_drivetrain=params.eta_drivetrain,
        )
        speeds = [speed_min + (speed_max - speed_min) * i / (len(curve) - 1) for i in range(len(curve))]
        label = make_vehicle_label(vehicle)

        if vehicle.vehicle_type == VehicleType.ev:
            y_total = [c.total_battery_kwh_per_100km for c in curve]
            effective_battery = vehicle.battery_usable_kwh * cap_factor if vehicle.battery_usable_kwh else None
            hover_texts = []
            for i, c in enumerate(curve):
                ht = (
                    f"<b>{label}</b><br>"
                    f"Speed: {speeds[i]:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"💨 Aero: {c.aero_kwh_per_100km:.1f} kWh/100km<br>"
                    f"🛞 Roll: {c.roll_kwh_per_100km:.1f} kWh/100km<br>"
                    f"⚡ HVAC: {c.aux_kwh_per_100km:.1f} kWh/100km<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"🔋 Total: {c.total_battery_kwh_per_100km:.1f} kWh/100km"
                )
                if effective_battery:
                    rng = effective_battery / c.total_battery_kwh_per_100km * 100
                    ht += f"<br>📏 Range: {rng:.0f} km"
                hover_texts.append(ht)
            fig.add_trace(
                go.Scatter(
                    x=speeds,
                    y=y_total,
                    mode="lines",
                    name=label,
                    line=dict(color=color, width=3),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover_texts,
                    legendgroup=label,
                    showlegend=True,
                )
            )
            if effective_battery:
                y_range = [effective_battery / c.total_battery_kwh_per_100km * 100 for c in curve]
                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_range,
                        mode="lines",
                        name=f"{label} Range",
                        line=dict(color=color, width=2, dash="dot"),
                        yaxis="y2",
                        legendgroup=label,
                        showlegend=False,
                        hovertemplate=f"%{{y:.0f}} km at %{{x:.0f}} km/h<extra>{label}</extra>",
                    )
                )
        else:
            l_per_100km = vehicle.real_consumption_l_100km
            if l_per_100km is not None:
                kwh_per_l = (
                    fuel_const.diesel_kwh_per_liter
                    if vehicle.fuel_type == FuelType.diesel
                    else fuel_const.gasoline_kwh_per_liter
                )
                chem_kwh = l_per_100km.value * kwh_per_l
                wheel_kwh = chem_kwh * ice_thermal_eff
                y_chem = [chem_kwh] * len(speeds)
                y_wheel = [wheel_kwh] * len(speeds)

                hover_texts_chem = [
                    f"<b>{label}</b><br>Speed: {s:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"⛽ Chemical: {chem_kwh:.0f} kWh/100km<br>"
                    f"🔧 Wheel est.: {wheel_kwh:.0f} kWh/100km"
                    for s in speeds
                ]
                hover_texts_wheel = [
                    f"<b>{label}</b><br>Speed: {s:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"⛽ Chemical: {chem_kwh:.0f} kWh/100km<br>"
                    f"🔧 Wheel est.: {wheel_kwh:.0f} kWh/100km<br>"
                    f"(at {ice_thermal_eff:.0%} thermal efficiency)"
                    for s in speeds
                ]

                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_chem,
                        mode="lines",
                        name=f"{label} (chem)",
                        line=dict(color=color, width=3),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover_texts_chem,
                        legendgroup=label,
                        showlegend=True,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_wheel,
                        mode="lines",
                        name=f"{label} (wheel)",
                        line=dict(color=color, width=2, dash="dash"),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover_texts_wheel,
                        legendgroup=label,
                        showlegend=False,
                    )
                )

    fig.update_layout(
        title=None,
        xaxis_title="Speed (km/h)",
        yaxis_title="kWh / 100 km",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1e1e2e", font=dict(color="#cdd6f4", size=12), bordercolor="#45475a"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        template="plotly_white",
        margin=dict(l=50, r=60, t=20, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#e5e5e5", zerolinecolor="#e5e5e5"),
        yaxis=dict(gridcolor="#e5e5e5", zerolinecolor="#e5e5e5"),
        yaxis2=dict(
            title=dict(text="Range (km)", font=dict(color="#00CC96")),
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
            zerolinecolor="rgba(0,0,0,0)",
            showgrid=False,
            tickfont=dict(color="#00CC96"),
        ),
    )

    return fig


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
            vehicle_hvac = hvac_power_kw(params.temperature_c, params.cabin_target_temp_c, has_heat_pump=hp, hvac_cop_heat=cop)
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
    for i, h in enumerate(header):
        if h == "Range":
            html += f'<th style="{th_style} text-align:right; font-weight:400; font-size:0.75em; color:#636EFA;">km</th>'
        elif h == "20-80%":
            html += f'<th style="{th_style} text-align:center; font-weight:400; font-size:0.75em; color:#00CC96;">DC ⚡</th>'
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
    sort_by_range: bool = False,
) -> str:
    all_vehicles = REPO.get_all()
    entries: list[tuple[str, str, float, str, float | None, str, float | None]] = []

    for v in sorted(all_vehicles, key=lambda x: (x.make, x.model)):
        c_rr = get_vehicle_c_rr(v, params.c_rr, use_per_vehicle_tires)
        if show_ev and v.vehicle_type == VehicleType.ev:
            hp = v.has_heat_pump if v.has_heat_pump is not None else False
            cop = v.hvac_cop_heat if v.hvac_cop_heat is not None else None
            vehicle_hvac = hvac_power_kw(params.temperature_c, params.cabin_target_temp_c, has_heat_pump=hp, hvac_cop_heat=cop)
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
        else:
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


def build_confidence_badge(level: ConfidenceLevel) -> str:
    color = CONFIDENCE_COLORS.get(level, "#888")
    s = f"background:{color}22; color:{color}; border:1px solid {color}44;"
    return f'<span class="conf-badge" style="{s}">{level.value}</span>'


_DC = "background:#fff; border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.06);"


def build_vehicle_detail_html(v: Vehicle) -> str:
    q = vehicle_data_quality(v)
    missing_count = sum(1 for ok in q.values() if not ok)
    completeness = (len(q) - missing_count) / len(q) * 100

    img_path = IMAGES_DIR / f"{v.id}.jpg"
    has_image = img_path.exists()

    html = '<div style="font-family:system-ui, sans-serif;">'

    html += f'<div class="detail-card" style="{_DC} display:flex; gap:20px; align-items:flex-start;">'
    if has_image:
        html += (
            f'<div style="flex-shrink:0; width:240px; height:160px; '
            f'background:#f5f5f5; border-radius:8px; overflow:hidden; '
            f'display:flex; align-items:center; justify-content:center;">'
            f'<img src="/images/{v.id}.jpg" '
            f'style="max-width:100%; max-height:100%; object-fit:contain;" '
            f'alt="{make_vehicle_label(v)}">'
            f'</div>'
        )
    html += '<div style="flex:1; min-width:0;">'
    html += f'<h2 style="margin:0 0 4px 0; font-size:1.4em;">{make_vehicle_label(v)}</h2>'
    html += (
        f'<div style="color:#888; font-size:0.9em; margin-bottom:8px;">'
        f'{v.make} · {v.vehicle_type.value.upper()}'
        f'</div>'
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


@ui.page("/vehicle/{vid}")
def vehicle_detail(vid: str) -> None:
    v = REPO.get(vid)
    ui.add_css(LIGHT_CSS + SHARED_CSS + DARK_CSS)

    if not v:
        with ui.column().style("max-width:800px; margin:40px auto; padding:20px;"):
            ui.label("Vehicle not found").style("font-size:1.5em; color:#EF553B;")
            ui.link("Back to overview", "/").style("color:#636EFA;")
        return

    with ui.column().style("max-width:800px; margin:20px auto; padding:20px; gap:8px;"):
        with ui.row().style("justify-content:space-between; align-items:center; width:100%;"):
            ui.link("← Back to overview", "/").style("color:#636EFA; text-decoration:none; font-size:0.9em;")

        ui.html(build_vehicle_detail_html(v))


@ui.page("/")
def index(sort: str = "") -> None:
    ui.add_css(LIGHT_CSS + SHARED_CSS + DARK_CSS)

    if sort == "range":
        SESSION["ranking_sort"] = True
    elif sort == "consumption":
        SESSION["ranking_sort"] = False

    params = PhysicsParams()
    selected_ids = SESSION["selected"]

    with ui.column().style("gap:16px; padding:20px; max-width:1400px; margin:0 auto; width:100%;"):
        with ui.row().style("width:100%; align-items:center; justify-content:space-between;"):
            with ui.row().style("align-items:center; gap:8px;"):
                ui.label("⚡").style("font-size:1.8em;")
                with ui.column().style("gap:0;"):
                    ui.label("Vehicle Consumption Analyzer").style(
                        "font-size:1.5em; font-weight:700; line-height:1.1; color:#1a1a2e;"
                    )
                    ui.label("Physics-based EV & ICE comparison").style(
                        "font-size:0.85em; color:#888; line-height:1.1;"
                    )

            def toggle_dark() -> None:
                SESSION["dark"] = not SESSION["dark"]
                if SESSION["dark"]:
                    ui.query("body").classes("dark")
                else:
                    ui.query("body").classes(remove="dark")

            dark_switch = ui.switch("Dark", value=SESSION["dark"], on_change=lambda _: toggle_dark())
            dark_switch.style("font-size:0.85em;")
        if SESSION["dark"]:
            ui.query("body").classes("dark")

        with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
            with ui.card().style("min-width:280px; max-width:320px; flex:1; padding:16px;"):
                ui.label("🚗 Vehicle Selection").style("font-weight:700; font-size:1em; margin-bottom:8px;")

                with ui.row().classes("filter-row"):
                    ev_cb = ui.checkbox("EV", value=SESSION["ev_checked"]).style("font-size:0.85em;")
                    ice_cb = ui.checkbox("ICE", value=SESSION["ice_checked"]).style("font-size:0.85em;")

                make_select = ui.select([], label="Make", with_input=True).style("width:100%;")
                make_select.visible = False

                model_select = ui.select(
                    {},
                    multiple=True,
                    label="Models",
                ).style("width:100%;")
                model_select.visible = False

                ui.separator().style("margin:8px 0;")

                ui.label("Selected").style("font-weight:600; font-size:0.85em; color:#555; margin-bottom:4px;")
                selected_list_container = ui.column().style("max-height:180px; overflow-y:auto; gap:2px; width:100%;")

            with ui.card().style("flex:3; min-width:400px; padding:16px;"):
                chart_container = ui.element("div").style("width:100%; min-height:420px;")

        table_container = ui.element("div").style("width:100%;")

        with ui.card().style("padding:16px;"):
            with ui.expansion("⚙️ Settings", icon="settings").style("width:100%;"):
                with ui.row().style("width:100%; gap:24px; flex-wrap:wrap; padding:8px 0;"):
                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("Parameters").style("font-weight:600; font-size:0.85em; color:#666;")
                        rho_input = ui.number(
                            "Air density (kg/m³)",
                            value=params.rho_air,
                            min=0.5,
                            max=1.5,
                            step=0.001,
                            format="%.3f",
                        ).style("width:100%;")
                        crr_input = ui.number(
                            "Rolling resistance",
                            value=params.c_rr,
                            min=0.003,
                            max=0.02,
                            step=0.001,
                            format="%.3f",
                        ).style("width:100%;")
                        use_per_tire_cb = ui.checkbox("Per-vehicle tires", value=True).style(
                            "font-size:0.82em; margin-top:4px;"
                        )
                        use_per_tire_cb.on_value_change(lambda _: crr_input.set_enabled(not use_per_tire_cb.value))
                        crr_input.set_enabled(not use_per_tire_cb.value)
                        aux_input = ui.number(
                            "Aux power (kW)",
                            value=params.p_aux_kw,
                            min=0.0,
                            max=10.0,
                            step=0.1,
                            format="%.1f",
                        ).style("width:100%;")
                        eta_input = ui.number(
                            "Drivetrain η",
                            value=params.eta_drivetrain,
                            min=0.5,
                            max=1.0,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")
                        regen_input = ui.number(
                            "Regen η",
                            value=params.eta_regen,
                            min=0.0,
                            max=1.0,
                            step=0.05,
                            format="%.2f",
                        ).style("width:100%;")
                        charging_eff_input = ui.number(
                            "Charging η",
                            value=params.eta_charging,
                            min=0.7,
                            max=1.0,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")

                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("ICE Comparison").style("font-weight:600; font-size:0.85em; color:#666;")
                        ice_thermal_eff = ui.number(
                            "Thermal efficiency",
                            value=0.30,
                            min=0.1,
                            max=0.5,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")

                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("Environment").style("font-weight:600; font-size:0.85em; color:#666;")
                        ui.label("Temperature (°C)").style("font-size:0.82em;")
                        temp_input = ui.slider(min=-20, max=45, value=int(params.temperature_c), step=1).style("width:100%;")
                        temp_label = ui.label(f"{int(params.temperature_c)}°C").style("font-size:0.78em; color:#888;")
                        temp_input.on_value_change(lambda e: temp_label.set_text(f"{int(e.value)}°C"))
                        ui.label("Min (km/h)").style("font-size:0.82em;")
                        speed_min_slider = ui.slider(min=10, max=100, value=30, step=5).style("width:100%;")
                        ui.label("Max (km/h)").style("font-size:0.82em;")
                        speed_max_slider = ui.slider(min=50, max=200, value=160, step=5).style("width:100%;")

            with ui.expansion("📐 Physics Formulas", icon="science").style("width:100%;"):
                ui.markdown(
                    "**Aero:** F = ½ · ρ · Cd · A · v²  →  kWh/100km = F · 100 / 3600\n\n"
                    "**Roll:** F = c<sub>rr</sub> · m · g  →  kWh/100km constant\n\n"
                    "**Aux:** kWh/100km = P<sub>aux</sub> / v · 100  (↓ with speed)\n\n"
                    "**Drivetrain:** Battery = Wheel / η"
                ).style("font-size:0.82em; line-height:1.6;")

        with ui.card().style("padding:16px;"):
            with ui.row().style("align-items:center; gap:16px; margin-bottom:12px;"):
                ui.label("📊 Consumption Ranking").style("font-weight:700; font-size:0.95em;")
                speed_ranking_select = ui.select(
                    {s: f"{s} km/h" for s in SPEED_OPTIONS},
                    value=SPEED_OPTIONS[2],
                    label="Speed",
                ).style("width:140px;")
                ranking_ev_cb = ui.checkbox("EV", value=SESSION["ranking_ev"]).style("font-size:0.85em;")
                ranking_ice_cb = ui.checkbox("ICE", value=SESSION["ranking_ice"]).style("font-size:0.85em;")
                sort_btn = (
                    ui.button(
                        "Sort: Range" if SESSION["ranking_sort"] else "Sort: kWh",
                        on_click=lambda: _toggle_ranking_sort(),
                    )
                    .props("flat dense")
                    .style("font-size:0.82em;")
                )
            ranking_container = ui.element("div").style("width:100%;")

    _make_list: list[str] = []

    def rebuild_make_select() -> None:
        nonlocal _make_list
        _make_list = get_filtered_makes(ev_cb.value, ice_cb.value)
        if _make_list:
            cur_val = SESSION["current_make"] if SESSION["current_make"] in _make_list else _make_list[0]
            make_select.set_options({m: m for m in _make_list}, value=cur_val)
            SESSION["current_make"] = cur_val
            make_select.visible = True
            model_select.visible = True
        else:
            make_select.visible = False
            model_select.visible = False

    def remove_vehicle(vid: str) -> None:
        if vid in selected_ids:
            selected_ids.remove(vid)
            update_selected_list()
            update_model_list()
            update()

    def add_vehicle(vid: str) -> None:
        if vid not in selected_ids:
            if len(selected_ids) >= MAX_COMPARE:
                ui.notify(f"Maximum {MAX_COMPARE} vehicles for comparison", type="warning", position="top")
                return
            selected_ids.append(vid)
            update_selected_list()
            update_model_list()
            update()

    def _model_selection_changed() -> None:
        new_sel = model_select.value if isinstance(model_select.value, list) else []
        cur_make = make_select.value
        make_vids = {v.id for v in get_filtered_models(cur_make, ev_cb.value, ice_cb.value)} if cur_make else set()
        for vid in list(selected_ids):
            if vid in make_vids and vid not in new_sel:
                selected_ids.remove(vid)
        for vid in new_sel:
            if vid not in selected_ids:
                if len(selected_ids) >= MAX_COMPARE:
                    ui.notify(f"Maximum {MAX_COMPARE} vehicles for comparison", type="warning", position="top")
                    return
                selected_ids.append(vid)
        update_selected_list()
        update()

    def update_selected_list() -> None:
        selected_list_container.clear()
        if not selected_ids:
            with selected_list_container:
                ui.label("No vehicles selected").style(
                    "color:#999; font-size:0.82em; padding:8px 4px;"
                )
            return
        for i, vid in enumerate(selected_ids):
            v = REPO.get(vid)
            if not v:
                continue
            color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
            has_img = (IMAGES_DIR / f"{vid}.jpg").exists()
            with selected_list_container:
                with ui.row().style(
                    f"width:100%; border-left:3px solid {color}; "
                    f"display:flex; align-items:center; padding:4px 6px; "
                    f"border-radius:6px; gap:6px;"
                ).classes("sel-item"):
                    if has_img:
                        ui.html(
                            f'<img src="/images/{vid}.jpg" '
                            f'style="width:32px; height:22px; object-fit:contain; '
                            f'border-radius:3px; flex-shrink:0;">'
                        )
                    ui.link(short_label(v), f"/vehicle/{vid}").style(
                        "flex:1; font-size:0.88em; font-weight:500; "
                        "text-decoration:none; color:inherit; overflow:hidden; "
                        "text-overflow:ellipsis; white-space:nowrap;"
                    )
                    db = ui.button(icon="delete", on_click=lambda _, vid=vid: remove_vehicle(vid))
                    db.props("flat dense round size=sm color=grey")

    def update_model_list() -> None:
        cur_make = make_select.value
        if not cur_make:
            model_select.set_options({})
            return

        models = get_filtered_models(cur_make, ev_cb.value, ice_cb.value)
        opts: dict[str, str] = {}
        for v in models:
            opts[v.id] = f"{make_vehicle_label(v)} ({v.cda_m2:.2f} m² CdA)"
        model_select.set_options(opts)
        model_select.value = [vid for vid in selected_ids if vid in opts]

    def _toggle_ranking_sort() -> None:
        SESSION["ranking_sort"] = not SESSION["ranking_sort"]
        sort_btn.set_text("Sort: Range" if SESSION["ranking_sort"] else "Sort: kWh")
        update_ranking()

    def update() -> None:
        if not selected_ids:
            chart_container.clear()
            with (
                chart_container,
                ui.column().style("align-items:center; justify-content:center; padding:60px 20px; color:#aaa;"),
            ):
                ui.label("📊").style("font-size:3em; margin-bottom:12px;")
                ui.label("Select vehicles to compare").style("font-size:1.1em; color:#888;")
                ui.label("Use the + buttons to add vehicles").style("font-size:0.85em; color:#bbb;")
            table_container.clear()
            ranking_container.clear()
            return

        vehicles = REPO.get_by_ids(selected_ids)
        params.rho_air = rho_input.value
        params.c_rr = crr_input.value
        params.p_aux_kw = aux_input.value
        params.eta_drivetrain = eta_input.value
        params.eta_regen = regen_input.value
        params.eta_charging = charging_eff_input.value
        params.temperature_c = float(temp_input.value)
        params.cabin_target_temp_c = 21.0

        fig = build_chart(
            vehicles,
            params,
            speed_min_slider.value,
            speed_max_slider.value,
            FUEL_CONST,
            ice_thermal_eff.value,
            use_per_tire_cb.value,
        )

        chart_container.clear()
        with chart_container:
            with ui.row().style("gap:8px; margin-bottom:4px;"):
                ui.label("📈 Consumption vs Speed").style("font-weight:700; font-size:0.95em; flex:1;")
                ui.button("⬇ PNG", on_click=lambda: _export_chart_png(fig)).props("flat dense size=sm").style(
                    "font-size:0.78em;"
                )
            ui.plotly(fig).style("width:100%; height:450px;")

        table_html = build_table(vehicles, params, FUEL_CONST, ice_thermal_eff.value, use_per_tire_cb.value)
        table_container.clear()
        with table_container, ui.card().style("padding:16px;"):
            ui.label("📋 Consumption Table").style("font-weight:700; font-size:0.95em; margin-bottom:8px;")
            ui.html(table_html)

        update_ranking()

    def update_ranking() -> None:
        params.rho_air = rho_input.value
        params.c_rr = crr_input.value
        params.p_aux_kw = aux_input.value
        params.eta_drivetrain = eta_input.value
        params.eta_regen = regen_input.value
        params.eta_charging = charging_eff_input.value
        params.temperature_c = float(temp_input.value)
        speed = speed_ranking_select.value if speed_ranking_select.value else SPEED_OPTIONS[2]
        html = build_ranking_list(
            params,
            speed,
            ranking_ev_cb.value,
            ranking_ice_cb.value,
            FUEL_CONST,
            ice_thermal_eff.value,
            use_per_tire_cb.value,
            SESSION["ranking_sort"],
        )
        ranking_container.clear()
        with ranking_container:
            ui.html(html)

    def on_filter_change() -> None:
        SESSION["ev_checked"] = ev_cb.value
        SESSION["ice_checked"] = ice_cb.value
        rebuild_make_select()
        update_ranking()

    ev_cb.on_value_change(lambda _: on_filter_change())
    ice_cb.on_value_change(lambda _: on_filter_change())

    def _on_make_change() -> None:
        SESSION["current_make"] = make_select.value or ""
        update_model_list()

    make_select.on_value_change(lambda _: _on_make_change())
    model_select.on_value_change(lambda _: _model_selection_changed())
    ranking_ev_cb.on_value_change(lambda _: (SESSION.update(ranking_ev=ranking_ev_cb.value), update_ranking()))
    ranking_ice_cb.on_value_change(lambda _: (SESSION.update(ranking_ice=ranking_ice_cb.value), update_ranking()))
    speed_ranking_select.on_value_change(lambda _: update_ranking())

    rho_input.on_value_change(lambda _: update())
    crr_input.on_value_change(lambda _: update())
    aux_input.on_value_change(lambda _: update())
    eta_input.on_value_change(lambda _: update())
    regen_input.on_value_change(lambda _: update())
    charging_eff_input.on_value_change(lambda _: update())
    temp_input.on_value_change(lambda _: update())
    speed_min_slider.on_value_change(lambda _: update())
    speed_max_slider.on_value_change(lambda _: update())
    ice_thermal_eff.on_value_change(lambda _: update())
    use_per_tire_cb.on_value_change(lambda _: (update(), update_ranking()))

    rebuild_make_select()
    update_selected_list()
    ui.timer(0.1, update, once=True)


def _export_chart_png(fig: go.Figure) -> None:
    try:
        buf = BytesIO()
        fig.write_image(buf, format="png", scale=2, width=1200, height=600)
        buf.seek(0)
        ui.download(buf.read(), filename="consumption_chart.png", media_type="image/png")
    except Exception:
        ui.notify("PNG export requires kaleido. Install with: pip install kaleido", type="warning", position="top")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Vehicle Consumption Analyzer", port=8080, reload=False)
