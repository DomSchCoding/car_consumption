"""Route / Commute planner page for the Vehicle Consumption Analyzer."""

from __future__ import annotations

from nicegui import ui

from app.core.physics import battery_capacity_factor
from app.core.route_energy import commute_energy
from app.data.models import (
    CommuteScenario,
    DirectionMode,
    PhysicsParams,
    RoadType,
    Route,
    RouteSegment,
    VehicleType,
)
from app.data.repository import VehicleRepository
from app.ui.components.vehicle_selector import (
    make_vehicle_label,
)
from app.ui.state import SESSION

MAX_COMPARE_ROUTE = 8


def build_route_breakdown_table(results: list[dict], vehicles: list) -> str:
    """Build HTML table for route energy comparison."""
    header = [
        "Vehicle",
        "kWh/trip",
        "kWh/100km",
        "Range/trips",
        "Duration",
        "Aero",
        "Roll",
        "Aux",
        "Climb",
        "Descent rec.",
        "Stop-go",
    ]
    t_style = "width:100%; border-collapse: collapse; font-size: 0.82em; font-family: system-ui, sans-serif;"
    th_style = (
        "border-bottom:2px solid #e0e0e0; padding:8px 6px; "
        "background:#fafafa; color:#555; font-weight:600; text-align:left;"
    )
    td_style = "padding:6px 8px; border-bottom:1px solid #f0f0f0;"
    nm_style = (
        "padding:6px 8px; border-bottom:1px solid #f0f0f0; font-weight:600; "
        "max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;"
    )

    html = f'<table style="{t_style}"><thead><tr>'
    for h in header:
        html += f'<th style="{th_style}">{h}</th>'
    html += "</tr></thead><tbody>"

    for entry in results:
        v = entry["vehicle"]
        bd = entry["breakdown"]
        bg = "#fafafa" if results.index(entry) % 2 == 0 else "#fff"
        html += f'<tr style="background:{bg};">'
        html += f'<td style="{nm_style}">{make_vehicle_label(v)}</td>'
        html += f'<td style="{td_style}">{bd.total_battery_kwh:.1f}</td>'
        html += f'<td style="{td_style}">{bd.kwh_per_100km:.1f}</td>'
        if v.vehicle_type == VehicleType.ev and v.battery_usable_kwh:
            cap = battery_capacity_factor(SESSION.get("_route_temp", 20.0))
            eff = v.battery_usable_kwh * cap
            n_trips = eff / bd.total_battery_kwh if bd.total_battery_kwh > 0 else 0
            html += f'<td style="{td_style}">{n_trips:.1f}</td>'
        else:
            html += f'<td style="{td_style}">-</td>'
        html += f'<td style="{td_style}">{bd.duration_h * 60:.0f} min</td>'
        html += f'<td style="{td_style}">{bd.aero_kwh:.2f}</td>'
        html += f'<td style="{td_style}">{bd.roll_kwh:.2f}</td>'
        html += f'<td style="{td_style}">{bd.aux_kwh:.2f}</td>'
        html += f'<td style="{td_style}">{bd.climb_kwh:.2f}</td>'
        html += f'<td style="{td_style}">{bd.descent_recovered_kwh:.2f}</td>'
        html += f'<td style="{td_style}">{bd.stop_go_kwh:.2f}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    return html


def route_page() -> None:
    """Render the Route / Commute planner page."""
    from app.ui.charts import VEHICLE_COLORS

    ui.add_css("""
    body {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
        min-height: 100vh;
    }
    .q-card {
        border-radius: 12px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
    }
    """)

    repo = VehicleRepository()
    selected_ids: list[str] = list(SESSION.get("selected", []))

    with ui.column().style("gap:16px; padding:20px; max-width:1400px; margin:0 auto; width:100%;"):
        ui.link("← Back to Dashboard", "/").style("color:#636EFA; text-decoration:none; font-size:0.9em;")
        ui.label("🗺️ Route / Commute Planner").style("font-size:1.5em; font-weight:700; color:#1a1a2e;")
        ui.label("Calculate energy consumption for a specific route").style("font-size:0.85em; color:#888;")

        with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
            with ui.card().style("min-width:300px; max-width:360px; flex:1; padding:16px;"):
                ui.label("Route Parameters").style("font-weight:700; font-size:1em; margin-bottom:8px;")

                dist_input = ui.number("Distance (km)", value=25.0, min=0.1, max=500, step=1, format="%.1f").style(
                    "width:100%;"
                )
                speed_input = ui.number("Avg speed (km/h)", value=80.0, min=10, max=200, step=5, format="%.0f").style(
                    "width:100%;"
                )
                elevation_input = ui.number("Net elevation gain (m)", value=0, step=10, format="%.0f").style(
                    "width:100%;"
                )
                ui.label("(Positive = uphill to destination)").style("font-size:0.78em; color:#888; margin-top:-8px;")

                with ui.expansion("Detailed elevation & stops", icon="terrain").style("width:100%;"):
                    gain_input = ui.number("Elevation gain uphill (m)", value=0, min=0, step=10, format="%.0f").style(
                        "width:100%;"
                    )
                    loss_input = ui.number("Elevation loss downhill (m)", value=0, min=0, step=10, format="%.0f").style(
                        "width:100%;"
                    )
                    stops_input = ui.number("Stops per km", value=0.0, min=0, max=10, step=0.1, format="%.1f").style(
                        "width:100%;"
                    )
                    dwell_input = ui.number(
                        "Dwell/stand time (min)", value=0.0, min=0, max=60, step=1, format="%.0f"
                    ).style("width:100%;")
                    wind_input = ui.number("Headwind (km/h)", value=0.0, min=-50, max=50, step=5, format="%.0f").style(
                        "width:100%;"
                    )

                temp_route = ui.number("Temperature (°C)", value=20.0, min=-30, max=50, step=1, format="%.0f").style(
                    "width:100%;"
                )
                return_cb = ui.checkbox("Round trip (there and back)", value=True).style("font-size:0.85em;")
                wind_invert_cb = ui.checkbox("Invert wind on return", value=True).style("font-size:0.85em;")

                ui.label("Selected Vehicles").style(
                    "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
                )
                vehicle_list = ui.column().style("max-height:200px; overflow-y:auto; gap:2px; width:100%;")

            with ui.card().style("flex:2; min-width:400px; padding:16px;"):
                result_container = ui.element("div").style("width:100%;")

    def update_vehicle_list() -> None:
        vehicle_list.clear()
        if not selected_ids:
            with vehicle_list:
                ui.label("Select vehicles on the Dashboard first").style("color:#999; font-size:0.82em;")
            return
        for i, vid in enumerate(selected_ids[:MAX_COMPARE_ROUTE]):
            v = repo.get(vid)
            if not v:
                continue
            color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
            with vehicle_list:
                ui.label(f"▸ {make_vehicle_label(v)}").style(
                    f"font-size:0.85em; font-weight:500; border-left:3px solid {color}; padding-left:6px; margin:2px 0;"
                )

    def calculate_route() -> None:
        if not selected_ids:
            result_container.clear()
            with result_container:
                ui.label("Select vehicles on the Dashboard first").style(
                    "font-size:1em; color:#888; text-align:center; padding:40px;"
                )
            return

        vehicles = repo.get_by_ids(selected_ids[:MAX_COMPARE_ROUTE])
        if not vehicles:
            result_container.clear()
            return

        params = PhysicsParams()
        params.temperature_c = temp_route.value or 20.0
        params.cabin_target_temp_c = 21.0
        SESSION["_route_temp"] = params.temperature_c

        distance_km = dist_input.value or 25.0
        speed_kmh = speed_input.value or 80.0
        net_elevation = elevation_input.value or 0

        gain_m = gain_input.value if (gain_input.value is not None and gain_input.value > 0) else max(0, net_elevation)
        loss_m = loss_input.value if (loss_input.value is not None and loss_input.value > 0) else max(0, -net_elevation)

        segment = RouteSegment(
            name="Main segment",
            distance_km=distance_km,
            avg_speed_kmh=speed_kmh,
            road_type=RoadType.mixed,
            elevation_gain_m=gain_m,
            elevation_loss_m=loss_m,
            stops=stops_input.value or 0.0,
            stop_speed_kmh=None,
            dwell_time_min=dwell_input.value or 0.0,
            headwind_kmh=wind_input.value or 0.0,
            payload_kg=0.0,
            aux_power_kw=None,
        )

        route = Route(
            id="user_route",
            name="User Route",
            segments=[segment],
        )

        direction_mode = DirectionMode.return_trip if return_cb.value else DirectionMode.one_way

        commute = CommuteScenario(
            route=route,
            direction_mode=direction_mode,
            invert_wind_on_return=wind_invert_cb.value,
        )

        results = []
        for v in vehicles:
            try:
                commute_result = commute_energy(v, commute, params)
                results.append(
                    {
                        "vehicle": v,
                        "breakdown": commute_result["total"],
                        "outward": commute_result["outward"],
                        "return_": commute_result["return"],
                    }
                )
            except Exception:
                pass

        result_container.clear()
        with result_container:
            if not results:
                ui.label("No valid results").style("color:#EF553B;")
                return

            route_desc = f"📍 {distance_km:.0f} km at {speed_kmh:.0f} km/h"
            if net_elevation != 0:
                route_desc += f", {net_elevation:+.0f}m net"
            if return_cb.value:
                route_desc += f", round trip ({distance_km * 2:.0f} km total)"
            ui.label(route_desc).style("font-weight:600; font-size:0.95em; margin-bottom:8px;")

            if return_cb.value:
                ui.label("Outward + Return").style(
                    "font-weight:700; font-size:0.95em; color:#636EFA; margin-bottom:4px;"
                )
            else:
                ui.label("One Way").style("font-weight:700; font-size:0.95em; color:#636EFA; margin-bottom:4px;")

            html = build_route_breakdown_table(results, vehicles)
            ui.html(html)

            if return_cb.value:
                ui.label("Outward vs Return").style("font-weight:700; font-size:0.95em; color:#555; margin-top:12px;")
                compare_results = []
                for entry in results:
                    bd_out = entry["outward"]
                    bd_ret = entry["return_"]
                    if bd_ret:
                        compare_results.append(
                            {
                                "vehicle": entry["vehicle"],
                                "outward_kwh": bd_out.total_battery_kwh,
                                "return_kwh": bd_ret.total_battery_kwh,
                                "total_kwh": entry["breakdown"].total_battery_kwh,
                            }
                        )

                if compare_results:
                    tc = "width:100%; border-collapse: collapse; font-size: 0.85em; font-family: system-ui, sans-serif;"
                    th = (
                        "border-bottom:2px solid #e0e0e0; padding:6px 8px; "
                        "background:#fafafa; color:#555; font-weight:600; text-align:left;"
                    )
                    td = "padding:6px 8px; border-bottom:1px solid #f0f0f0;"
                    nm = "padding:6px 8px; border-bottom:1px solid #f0f0f0; font-weight:600;"
                    chtml = f'<table style="{tc}"><thead><tr>'
                    for h in ["Vehicle", "Outward (kWh)", "Return (kWh)", "Total (kWh)", "Total kWh/100km"]:
                        chtml += f'<th style="{th}">{h}</th>'
                    chtml += "</tr></thead><tbody>"
                    for entry in compare_results:
                        v = entry["vehicle"]
                        bd_total = results[compare_results.index(entry)]["breakdown"]
                        chtml += f'<tr><td style="{nm}">{make_vehicle_label(v)}</td>'
                        chtml += f'<td style="{td}">{entry["outward_kwh"]:.1f}</td>'
                        chtml += f'<td style="{td}">{entry["return_kwh"]:.1f}</td>'
                        chtml += f'<td style="{td}">{entry["total_kwh"]:.1f}</td>'
                        chtml += f'<td style="{td}">{bd_total.kwh_per_100km:.1f}</td>'
                        chtml += "</tr>"
                    chtml += "</tbody></table>"
                    ui.html(chtml)

    update_vehicle_list()

    ui.button("Calculate", on_click=lambda: calculate_route()).props("color=primary").style(
        "width:100%; margin-top:8px;"
    )

    dist_input.on_value_change(lambda _: calculate_route())
    speed_input.on_value_change(lambda _: calculate_route())
    elevation_input.on_value_change(lambda _: calculate_route())
    gain_input.on_value_change(lambda _: calculate_route())
    loss_input.on_value_change(lambda _: calculate_route())
    stops_input.on_value_change(lambda _: calculate_route())
    dwell_input.on_value_change(lambda _: calculate_route())
    wind_input.on_value_change(lambda _: calculate_route())
    temp_route.on_value_change(lambda _: calculate_route())
    return_cb.on_value_change(lambda _: calculate_route())
    wind_invert_cb.on_value_change(lambda _: calculate_route())

    ui.timer(0.2, calculate_route, once=True)
