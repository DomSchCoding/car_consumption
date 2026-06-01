"""Native NiceGUI table and ranking components (replaces HTML tables)."""

from __future__ import annotations

from nicegui import ui

from app.core.physics import (
    battery_capacity_factor,
    hvac_power_kw,
    total_consumption,
)
from app.data.models import (
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
    passes_vehicle_filters,
    tire_class_label,
)


def render_consumption_table(
    vehicles: list[Vehicle],
    params: PhysicsParams,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
) -> None:
    """Render consumption table — vehicles as columns, specs as rows (mobile-friendly)."""
    if not vehicles:
        with ui.column().style("align-items:center; padding:40px; color:#999;"):
            ui.label("No vehicles selected")
        return

    speeds = [50, 80, 100, 130]
    has_ev = any(v.vehicle_type == VehicleType.ev for v in vehicles)
    cap_factor = battery_capacity_factor(params.temperature_c)

    # Pre-compute all values per vehicle
    vdata: list[dict] = []
    for v in vehicles:
        c_rr = get_vehicle_c_rr(v, params.c_rr, use_per_vehicle_tires)
        d: dict = {
            "name": make_vehicle_label(v),
            "vtype": v.vehicle_type.value.upper(),
            "cda": f"{v.cda_m2:.2f}",
            "tire": f"{tire_class_label(v)} ({c_rr:.3f})",
        }
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
                d[f"cons_{s}"] = f"{bc.total_battery_kwh_per_100km:.1f} ({wall_kwh:.1f})"
                if effective_battery:
                    rng = effective_battery / bc.total_battery_kwh_per_100km * 100
                    d[f"range_{s}"] = f"{rng:.0f} km"
                else:
                    d[f"range_{s}"] = "-"
            ct = v.charge_time_20_80_min
            d["charge"] = f"{ct:.0f} min" if ct is not None else "-"
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
                for s in speeds:
                    d[f"cons_{s}"] = f"{chem:.0f}/{wheel:.0f}"
                    d[f"range_{s}"] = "-"
            else:
                for s in speeds:
                    d[f"cons_{s}"] = "N/A"
                    d[f"range_{s}"] = "-"
            d["charge"] = "-"
        vdata.append(d)

    # Build row definitions: (label, key, style_hint)
    row_defs: list[tuple[str, str, str]] = [
        ("Type", "vtype", "badge"),
        ("CdA (m²)", "cda", "normal"),
        ("Tire", "tire", "normal"),
    ]
    for s in speeds:
        row_defs.append((f"{s} km/h", f"cons_{s}", "consumption"))
        row_defs.append(("  Range", f"range_{s}", "range"))
    if has_ev:
        row_defs.append(("DC 20→80%", "charge", "charge"))

    # Build aggrid: first column = "spec", rest = vehicles
    columns: list[dict] = [
        {"field": "spec", "headerName": "", "minWidth": 110, "pinned": "left",
         "cellStyle": {"fontWeight": "600", "color": "#555"}},
    ]
    for i, d in enumerate(vdata):
        columns.append({
            "field": f"v{i}",
            "headerName": d["name"],
            "minWidth": 130,
            "cellStyle": {"textAlign": "center"},
        })

    rows: list[dict] = []
    for label, key, hint in row_defs:
        row: dict = {"spec": label.strip(), "_hint": hint}
        for i, d in enumerate(vdata):
            row[f"v{i}"] = d.get(key, "-")
        rows.append(row)

    ui.aggrid(
        options={
            "columnDefs": columns,
            "rowData": rows,
            "rowHeight": 34,
            "headerHeight": 36,
            "suppressRowClickSelection": True,
            "domLayout": "normal",
            "suppressHorizontalScroll": False,
        },
    ).style("width:100%; font-size:0.82em;")

    # Notes footer
    notes: list[str] = []
    if has_ev:
        notes.append(f"Range at {int(params.temperature_c)}°C (battery {cap_factor:.0%})")
        notes.append("Values: battery kWh (wall kWh incl. charging η)")
        notes.append(f"Wall η={params.eta_charging:.0%}")
        notes.append("20-80% = DC charge time")
    else:
        notes.append("ICE: chemical/wheel (est.) kWh/100km")

    ui.label(" | ".join(notes)).style("margin-top:8px; font-size:0.78em; color:#999;")


def render_ranking_list(
    params: PhysicsParams,
    speed_kmh: float,
    show_ev: bool,
    show_ice: bool,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
    repo: VehicleRepository,
    sort_by_range: bool = False,
    vehicle_filters: dict | None = None,
) -> None:
    """Render fleet ranking using NiceGUI list + linear progress."""
    all_vehicles = repo.get_all()
    if vehicle_filters:
        all_vehicles = [v for v in all_vehicles if passes_vehicle_filters(v, vehicle_filters)]

    entries: list[tuple[str, str, str, float, float | None]] = []

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
            entries.append((v.id, make_vehicle_label(v), "EV", val, rng))
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
                entries.append((v.id, make_vehicle_label(v), "ICE", val, None))

    if sort_by_range:
        entries.sort(key=lambda x: -(x[4] if x[4] is not None else float("-inf")))
    else:
        entries.sort(key=lambda x: x[3])

    if not entries:
        with ui.column().style("padding:40px; text-align:center; color:#999;"):
            ui.label("No vehicles match the selected filters")
        return

    vals = [e[3] for e in entries]
    max_val = max(vals)
    min_val = min(vals)
    range_val = max_val - min_val if max_val != min_val else 1.0

    with ui.list().style("font-family:system-ui, sans-serif;"):
        # Header
        with ui.row().style(
            "align-items:center; gap:10px; padding:6px 8px; "
            "border-bottom:2px solid #e0e0e0; font-size:0.78em; font-weight:600; color:#888;"
        ):
            ui.label("").style("min-width:24px;")
            ui.label("").style("min-width:28px;")
            ui.label("Vehicle").style("flex:1;")
            ui.label("").style("width:120px;")
            cons_label = "kWh/100km"
            rng_label = "Range"
            if not sort_by_range:
                cons_label = f'<span style="color:#636EFA; font-weight:700;">{cons_label}</span>'
            else:
                rng_label = f'<span style="color:#636EFA; font-weight:700;">{rng_label}</span>'
            ui.html(cons_label).style("min-width:65px; text-align:right;")
            ui.html(rng_label).style("min-width:65px; text-align:right;")

        for rank, (vid, name, vtype, val, rng) in enumerate(entries, 1):
            pct = ((val - min_val) / range_val) * 100
            color = "#00CC96" if vtype == "EV" else "#EF553B"
            badge_bg = "#00CC9622" if vtype == "EV" else "#EF553B22"
            badge_color = "#00CC96" if vtype == "EV" else "#EF553B"

            with ui.element("div").style(
                "display:flex; align-items:center; gap:8px; padding:8px 10px; "
                "border-bottom:1px solid #f0f0f0; border-radius:6px; margin-bottom:4px; "
                "background:#fafafa; flex-wrap:wrap;"
            ):
                # Rank + badge row
                ui.label(f"#{rank}").style(
                    "min-width:28px; color:#666; font-size:0.78em; font-weight:700; text-align:center;"
                )
                ui.html(vtype).style(
                    f"min-width:28px; font-size:0.7em; font-weight:700; "
                    f"padding:2px 6px; border-radius:4px; text-align:center; "
                    f"background:{badge_bg}; color:{badge_color};"
                )

                # Vehicle name - clickable link to detail page
                ui.link(name, f"/vehicle/{vid}").style(
                    "flex:1; min-width:120px; font-size:0.9em; font-weight:600; "
                    "white-space:nowrap; overflow:hidden; text-overflow:ellipsis; "
                    "text-decoration:none; color:inherit; cursor:pointer;"
                )

                # Consumption value with slim progress bar underneath
                with ui.column().style("align-items:flex-end; gap:2px; min-width:80px;"):
                    ui.label(f"{val:.1f} kWh").style("font-size:0.85em; font-weight:700; color:" + color + ";")
                    # Slim progress bar - only 80px wide
                    with ui.element("div").style(
                        "width:80px; height:6px; background:#e0e0e0; border-radius:3px; overflow:hidden;"
                    ):
                        ui.element("div").style(
                            f"width:{100 - pct:.0f}%; height:100%; background:{color}; border-radius:3px;"
                        )
                    if rng is not None:
                        ui.label(f"{rng:.0f} km").style("font-size:0.75em; color:#888; font-weight:500;")

    # Footer
    cap_pct = battery_capacity_factor(params.temperature_c) * 100
    footer_parts = [f"At {int(params.temperature_c)}°C, battery {cap_pct:.0f}%"]
    hp_count = sum(1 for v in all_vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump)
    no_hp_count = sum(1 for v in all_vehicles if v.vehicle_type == VehicleType.ev and v.has_heat_pump is False)
    if hp_count:
        footer_parts.append(f"{hp_count} heat pump")
    if no_hp_count:
        footer_parts.append(f"{no_hp_count} resistive")

    ui.label(" | ".join(footer_parts)).style("margin-top:6px; font-size:0.78em; color:#999;")
