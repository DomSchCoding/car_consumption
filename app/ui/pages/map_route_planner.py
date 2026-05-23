"""Map-based route planner page using demo provider."""

from __future__ import annotations

import plotly.graph_objects as go
from nicegui import ui

from app.core.route_energy import commute_energy
from app.core.route_segmentizer import provider_route_to_commute_scenario, provider_route_to_segments
from app.data.models import DirectionMode, PhysicsParams
from app.data.repository import VehicleRepository
from app.services.provider_models import RouteRequest
from app.services.routing import DemoRoutingProvider
from app.ui.charts import VEHICLE_COLORS
from app.ui.components.map_widget import (
    clear_route_layer,
    create_route_map,
    draw_route_polyline,
    fit_bounds,
    set_start_end_markers,
)
from app.ui.components.vehicle_selector import make_vehicle_label
from app.ui.state import SESSION

MAX_COMPARE_ROUTE = 8


def map_route_page() -> None:
    ui.add_css("""
    body { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); min-height: 100vh; }
    .q-card { border-radius: 12px !important; box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important; }
    """)

    repo = VehicleRepository()
    selected_ids: list[str] = list(SESSION.get("selected", []))
    demo_provider = DemoRoutingProvider()

    current_route_result = {"provider_route": None, "segments": None}

    with ui.column().style("gap:16px; padding:20px; max-width:1400px; margin:0 auto; width:100%;"):
        with ui.row().style("width:100%; align-items:center; gap:8px;"):
            ui.link("← Dashboard", "/").style("color:#636EFA; text-decoration:none; font-size:0.9em;")
            ui.link("| Manual Route", "/route/manual").style(
                "color:#888; text-decoration:none; font-size:0.85em; margin-left:8px;"
            )
        ui.label("Map Route Planner").style("font-size:1.5em; font-weight:700; color:#1a1a2e;")
        ui.label("Calculate energy consumption for a real route (demo mode)").style("font-size:0.85em; color:#888;")

        with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
            with ui.card().style("min-width:280px; max-width:320px; flex:1; padding:16px;"):
                ui.label("Route Search").style("font-weight:700; font-size:1em; margin-bottom:8px;")

                start_input = ui.input("Start address", value="Demo city start").style("width:100%;")
                dest_input = ui.input("Destination address", value="Demo city destination").style("width:100%;")

                ui.label("Demo Routes").style(
                    "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
                )
                available = demo_provider.list_routes()
                route_options = {r: r.replace("_", " ").title() for r in available}
                ui.select(route_options, value=available[0] if available else None, label="Demo route").style(
                    "width:100%;"
                )

                ui.label("Options").style(
                    "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
                )
                return_cb = ui.checkbox("Round trip (there and back)", value=True).style("font-size:0.85em;")
                invert_wind_cb = ui.checkbox("Invert wind on return", value=True).style("font-size:0.85em;")

                with ui.expansion("Advanced settings", icon="settings").style("width:100%;"):
                    temperature = ui.number("Temperature (°C)", value=20, min=-30, max=50, step=1, format="%.0f").style(
                        "width:100%;"
                    )
                    headwind = ui.number("Headwind (km/h)", value=0, min=-50, max=50, step=5, format="%.0f").style(
                        "width:100%;"
                    )
                    payload = ui.number("Payload (kg)", value=0, min=0, max=500, step=10, format="%.0f").style(
                        "width:100%;"
                    )
                    regen_downhill = ui.number(
                        "Regen downhill", value=0.65, min=0, max=1, step=0.05, format="%.2f"
                    ).style("width:100%;")

                ui.button("Calculate Route", on_click=lambda: calculate_route()).props("color=primary").style(
                    "width:100%; margin-top:8px;"
                )

                provider_status = demo_provider.status()
                status_text = f"Provider: {provider_status.name}"
                if provider_status.message:
                    status_text += f" | {provider_status.message}"
                ui.label(status_text).style("font-size:0.78em; color:#888; margin-top:4px;")

                ui.label("Selected Vehicles").style(
                    "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
                )
                vehicle_list = ui.column().style("max-height:180px; overflow-y:auto; gap:2px; width:100%;")

            with ui.card().style("flex:2; min-width:400px; padding:16px;"):
                route_map = create_route_map()

        route_summary_container = ui.element("div").style("width:100%;")
        results_container = ui.element("div").style("width:100%;")

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
        request = RouteRequest(
            start_text=start_input.value,
            destination_text=dest_input.value,
            profile="car_fastest",
            provider="demo",
        )

        provider_route = demo_provider.route(request)
        if provider_route is None:
            route_summary_container.clear()
            with route_summary_container:
                ui.label("No route found. Try a different search.").style("color:#EF553B;")
            return

        current_route_result["provider_route"] = provider_route

        segments = provider_route_to_segments(provider_route)
        current_route_result["segments"] = segments

        route_points = [(p.lat, p.lon) for p in provider_route.geometry]

        clear_route_layer(route_map)
        if route_points:
            draw_route_polyline(route_map, route_points)
            set_start_end_markers(
                route_map,
                (provider_route.start.lat, provider_route.start.lon),
                (provider_route.destination.lat, provider_route.destination.lon),
            )
            fit_bounds(route_map, route_points)

        route_summary_container.clear()
        with route_summary_container:
            dist = provider_route.summary_distance_km
            duration_s = provider_route.summary_duration_s or 0
            duration_min = duration_s / 60
            avg_speed = dist / (duration_s / 3600) if duration_s > 0 else 0
            gain = provider_route.elevation_gain_m or 0
            loss = provider_route.elevation_loss_m or 0

            with ui.card().style("padding:16px;"):
                with ui.row().style("gap:8px; flex-wrap:wrap;"):
                    _summary_card("Distance", f"{dist:.1f} km")
                    _summary_card("Duration", f"{duration_min:.0f} min" if duration_s else "-")
                    _summary_card("Avg Speed", f"{avg_speed:.0f} km/h" if duration_s else "-")
                    _summary_card("Elevation", f"+{gain:.0f} / -{loss:.0f} m")
                    _summary_card("Provider", provider_route.provider)
                if provider_route.warnings:
                    with ui.row().style("margin-top:4px;"):
                        for w in provider_route.warnings:
                            ui.label(f"⚠ {w}").style("font-size:0.78em; color:#FFA15A;")

        _calculate_energy()

    def _calculate_energy() -> None:
        provider_route = current_route_result.get("provider_route")
        if provider_route is None:
            return

        vehicles = repo.get_by_ids(selected_ids[:MAX_COMPARE_ROUTE])
        if not vehicles:
            results_container.clear()
            with results_container:
                ui.label("Select vehicles on the Dashboard first").style(
                    "font-size:1em; color:#888; text-align:center; padding:40px;"
                )
            return

        params = PhysicsParams()
        params.temperature_c = temperature.value
        params.cabin_target_temp_c = 21.0

        direction_mode = DirectionMode.return_trip if return_cb.value else DirectionMode.one_way

        commute = provider_route_to_commute_scenario(
            provider_route,
            direction_mode=direction_mode,
            invert_wind_on_return=invert_wind_cb.value,
        )

        for seg in commute.route.segments:
            seg.headwind_kmh = headwind.value
            seg.payload_kg = payload.value

        results = []
        for v in vehicles:
            try:
                result = commute_energy(
                    v, commute, params, eta_regen_downhill=regen_downhill.value, eta_regen_stop=regen_downhill.value
                )
                results.append(
                    {
                        "vehicle": v,
                        "breakdown": result["total"],
                        "outward": result["outward"],
                        "return_": result["return"],
                    }
                )
            except Exception:
                pass

        results_container.clear()
        with results_container:
            if not results:
                ui.label("No valid results").style("color:#EF553B;")
                return

            direction_label = "Outward + Return" if return_cb.value else "One Way"
            ui.label(direction_label).style("font-weight:700; font-size:0.95em; color:#636EFA; margin-bottom:8px;")

            with ui.card().style("padding:16px; width:100%;"):
                html = _build_energy_table(results)
                ui.html(html)

            if return_cb.value:
                ui.label("Outward vs Return").style("font-weight:700; font-size:0.95em; color:#555; margin-top:12px;")
                compare_results = []
                for entry in results:
                    bd_out = entry["outward"]
                    bd_ret = entry["return_"]
                    if bd_ret is not None:
                        compare_results.append(
                            {
                                "vehicle": entry["vehicle"],
                                "outward_kwh": bd_out.total_battery_kwh,
                                "return_kwh": bd_ret.total_battery_kwh,
                                "total_kwh": entry["breakdown"].total_battery_kwh,
                            }
                        )

                if compare_results:
                    with ui.card().style("padding:16px; width:100%;"):
                        chtml = _build_comparison_table(compare_results, results)
                        ui.html(chtml)

            with ui.card().style("padding:16px; width:100%;"):
                fig = go.Figure()
                for i, entry in enumerate(results):
                    bd = entry["breakdown"]
                    v = entry["vehicle"]
                    color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
                    fig.add_trace(
                        go.Bar(
                            name=make_vehicle_label(v),
                            x=["Aero", "Roll", "Aux", "Climb", "Stop-go", "Descent rec."],
                            y=[
                                bd.aero_kwh,
                                bd.roll_kwh,
                                bd.aux_kwh,
                                bd.climb_kwh,
                                bd.stop_go_kwh,
                                -bd.descent_recovered_kwh,
                            ],
                            marker_color=color,
                        )
                    )
                fig.update_layout(
                    barmode="group",
                    title="Energy Breakdown (kWh)",
                    template="plotly_white",
                    margin=dict(l=50, r=20, t=40, b=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                ui.plotly(fig).style("width:100%; height:400px;")

            elev_points = [
                (p.distance_from_start_km, p.elevation_m)
                for p in provider_route.geometry
                if p.elevation_m is not None and p.distance_from_start_km is not None
            ]
            if elev_points:
                with ui.card().style("padding:16px; width:100%;"):
                    fig_elev = go.Figure()
                    dists = [p[0] for p in elev_points]
                    elevs = [p[1] for p in elev_points]
                    fig_elev.add_trace(
                        go.Scatter(
                            x=dists, y=elevs, mode="lines", name="Elevation", line=dict(color="#00CC96", width=2)
                        )
                    )
                    fig_elev.update_layout(
                        title="Elevation Profile",
                        xaxis_title="Distance (km)",
                        yaxis_title="Elevation (m)",
                        template="plotly_white",
                        margin=dict(l=50, r=20, t=40, b=40),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    ui.plotly(fig_elev).style("width:100%; height:300px;")

    def _build_energy_table(results: list) -> str:
        from app.ui.components.route_summary import build_energy_table

        return build_energy_table(results)

    def _build_comparison_table(compare_results: list, all_results: list) -> str:
        tc = "width:100%; border-collapse: collapse; font-size: 0.85em; font-family: system-ui, sans-serif;"
        th = (
            "border-bottom:2px solid #e0e0e0; padding:6px 8px; "
            "background:#fafafa; color:#555; font-weight:600; text-align:left;"
        )
        td = "padding:6px 8px; border-bottom:1px solid #f0f0f0;"
        nm = "padding:6px 8px; border-bottom:1px solid #f0f0f0; font-weight:600;"
        from app.ui.components.vehicle_selector import make_vehicle_label

        chtml = f'<table style="{tc}"><thead><tr>'
        for h in ["Vehicle", "Outward (kWh)", "Return (kWh)", "Total (kWh)", "Total kWh/100km"]:
            chtml += f'<th style="{th}">{h}</th>'
        chtml += "</tr></thead><tbody>"
        for entry in compare_results:
            v = entry["vehicle"]
            bd_total = all_results[compare_results.index(entry)]["breakdown"]
            chtml += f'<tr><td style="{nm}">{make_vehicle_label(v)}</td>'
            chtml += f'<td style="{td}">{entry["outward_kwh"]:.1f}</td>'
            chtml += f'<td style="{td}">{entry["return_kwh"]:.1f}</td>'
            chtml += f'<td style="{td}">{entry["total_kwh"]:.1f}</td>'
            chtml += f'<td style="{td}">{bd_total.kwh_per_100km:.1f}</td>'
            chtml += "</tr>"
        chtml += "</tbody></table>"
        return chtml

    update_vehicle_list()


def _summary_card(title: str, value: str, color: str = "#333") -> None:
    with ui.card().style("min-width:100px; padding:6px 10px; text-align:center;"):
        ui.label(title).style("font-size:0.75em; color:#888; font-weight:600;")
        ui.label(value).style(f"font-size:0.95em; font-weight:700; color:{color};")
