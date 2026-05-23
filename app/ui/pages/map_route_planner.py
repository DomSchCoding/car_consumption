"""Map-based route planner page with demo and live provider support."""

from __future__ import annotations

import plotly.graph_objects as go
from nicegui import ui

from app.core.route_energy import commute_energy
from app.core.route_segmentizer import provider_route_to_commute_scenario, provider_route_to_segments
from app.data.models import DirectionMode, PhysicsParams
from app.data.repository import VehicleRepository
from app.services.provider_config import (
    is_live_routing_enabled,
    is_nominatim_enabled,
    is_open_meteo_elevation_enabled,
    is_osrm_enabled,
)
from app.services.provider_models import RouteRequest
from app.services.routing import DemoRoutingProvider, route_live
from app.ui.charts import VEHICLE_COLORS
from app.ui.components.map_widget import (
    clear_route_layer,
    create_route_map,
    draw_route_polyline,
    fit_bounds,
    set_single_marker,
    set_start_end_markers,
)
from app.ui.components.vehicle_selector import make_vehicle_label
from app.ui.state import SESSION

MAX_COMPARE_ROUTE = 8


def _provider_status_text() -> str:
    live = is_live_routing_enabled()
    if not live:
        return "Demo offline mode"
    parts = []
    parts.append(f"Nominatim: {'on' if is_nominatim_enabled() else 'off'}")
    parts.append(f"OSRM: {'on' if is_osrm_enabled() else 'off'}")
    parts.append(f"Elevation: {'on' if is_open_meteo_elevation_enabled() else 'off'}")
    return "Live prototype: " + ", ".join(parts)


def map_route_page() -> None:
    ui.add_css("""
    body { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); min-height: 100vh; }
    .q-card { border-radius: 12px !important; box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important; }
    """)

    repo = VehicleRepository()
    selected_ids: list[str] = list(SESSION.get("selected", []))
    demo_provider = DemoRoutingProvider()

    current_route_result: dict = {"provider_route": None, "segments": None, "messages": []}

    DEMO_ROUTE_ADDRESSES: dict[str, tuple[str, str]] = {
        "city_commute": ("demo city start", "demo city destination"),
        "hilly_commute": ("demo hilly start", "demo hilly destination"),
        "highway_route": ("demo highway start", "demo highway destination"),
    }

    with ui.column().style("gap:16px; padding:20px; max-width:1400px; margin:0 auto; width:100%;"):
        with ui.row().style("width:100%; align-items:center; gap:8px;"):
            ui.link("← Dashboard", "/").style("color:#636EFA; text-decoration:none; font-size:0.9em;")
            ui.link("| Manual Route", "/route/manual").style(
                "color:#888; text-decoration:none; font-size:0.85em; margin-left:8px;"
            )
        ui.label("Map Route Planner").style("font-size:1.5em; font-weight:700; color:#1a1a2e;")
        ui.label("Calculate energy consumption for a route").style("font-size:0.85em; color:#888;")

        with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
            with ui.card().style("min-width:280px; max-width:320px; flex:1; padding:16px;"):
                ui.label("Route Search").style("font-weight:700; font-size:1em; margin-bottom:8px;")

                live_available = is_nominatim_enabled() and is_osrm_enabled()
                provider_options = {"demo": "Demo offline"}
                if live_available:
                    provider_options["live"] = "Live (Nominatim+OSRM+Open-Meteo)"
                elif is_live_routing_enabled():
                    provider_options["live"] = "Live (partially enabled)"
                default_mode = "live" if live_available else "demo"
                provider_mode = ui.select(
                    provider_options,
                    value=default_mode,
                    label="Provider",
                ).style("width:100%;")

                if not live_available:
                    ui.label("Live routing disabled. Set env vars to enable:").style(
                        "font-size:0.78em; color:#FFA15A; margin-top:2px;"
                    )
                    ui.label("CAR_CONSUMPTION_ENABLE_NOMINATIM=true").style(
                        "font-family:monospace; font-size:0.72em; color:#888;"
                    )
                    ui.label("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM=true").style(
                        "font-family:monospace; font-size:0.72em; color:#888;"
                    )
                    ui.label("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION=true").style(
                        "font-family:monospace; font-size:0.72em; color:#888;"
                    )

                start_input = ui.input("Start address", value="Demo city start").style("width:100%;")
                dest_input = ui.input("Destination address", value="Demo city destination").style("width:100%;")

                geocode_status = ui.label("").style("font-size:0.78em; color:#888; margin-top:2px;")

                def try_geocode_addresses() -> None:
                    """Geocode start/destination when in live mode and show markers on map."""
                    if provider_mode.value != "live":
                        geocode_status.set_text("")
                        return
                    from app.services.geocoding import geocode as nominatim_geocode

                    start_val = (start_input.value or "").strip()
                    dest_val = (dest_input.value or "").strip()
                    if not start_val and not dest_val:
                        geocode_status.set_text("Enter start and destination addresses")
                        return
                    start_pt = None
                    dest_pt = None
                    msgs: list[str] = []
                    if start_val:
                        candidates, err = nominatim_geocode(start_val)
                        if candidates:
                            start_pt = candidates[0].point
                            msgs.append(f"Start: {candidates[0].label}")
                        else:
                            msgs.append(f"Start not found: {err}" if err else "Start not found")
                    if dest_val:
                        candidates, err = nominatim_geocode(dest_val)
                        if candidates:
                            dest_pt = candidates[0].point
                            msgs.append(f"Dest: {candidates[0].label}")
                        else:
                            msgs.append(f"Dest not found: {err}" if err else "Dest not found")
                    geocode_status.set_text(" | ".join(msgs) if msgs else "")
                    clear_route_layer(route_map)
                    if start_pt and dest_pt:
                        set_start_end_markers(route_map, (start_pt.lat, start_pt.lon), (dest_pt.lat, dest_pt.lon))
                        fit_bounds(route_map, [(start_pt.lat, start_pt.lon), (dest_pt.lat, dest_pt.lon)])
                    elif start_pt:
                        set_single_marker(route_map, (start_pt.lat, start_pt.lon), title="Start")
                        route_map.set_center((start_pt.lat, start_pt.lon))
                        route_map.set_zoom(13)
                    elif dest_pt:
                        set_single_marker(route_map, (dest_pt.lat, dest_pt.lon), title="Destination")
                        route_map.set_center((dest_pt.lat, dest_pt.lon))
                        route_map.set_zoom(13)

                start_input.on("keydown.enter", lambda: try_geocode_addresses())
                dest_input.on("keydown.enter", lambda: try_geocode_addresses())

                ui.label("Demo Routes").style(
                    "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
                )
                available = demo_provider.list_routes()
                route_options = {r: r.replace("_", " ").title() for r in available}
                demo_select = ui.select(
                    route_options, value=available[0] if available else None, label="Demo route"
                ).style("width:100%;")

                def on_demo_route_change(e) -> None:
                    route_key = e.value
                    if route_key and route_key in DEMO_ROUTE_ADDRESSES:
                        start_addr, dest_addr = DEMO_ROUTE_ADDRESSES[route_key]
                        start_input.set_value(start_addr)
                        dest_input.set_value(dest_addr)
                        calculate_route()

                demo_select.on_value_change(on_demo_route_change)

                def on_provider_change(e) -> None:
                    if e.value == "live":
                        demo_select.disable()
                        start_input.set_value("")
                        dest_input.set_value("")
                        start_input.props('placeholder="z.B. Landstraße 1, 4020 Linz"')
                        dest_input.props('placeholder="z.B. Eidenberger Alm"')
                    else:
                        demo_select.enable()
                        if demo_select.value and demo_select.value in DEMO_ROUTE_ADDRESSES:
                            start_addr, dest_addr = DEMO_ROUTE_ADDRESSES[demo_select.value]
                            start_input.set_value(start_addr)
                            dest_input.set_value(dest_addr)
                        start_input.props('placeholder=""')
                        dest_input.props('placeholder=""')

                provider_mode.on_value_change(on_provider_change)

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

                ui.label(_provider_status_text()).style("font-size:0.78em; color:#888; margin-top:4px;")

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
        mode = provider_mode.value
        messages: list[str] = []

        if mode == "live":
            request = RouteRequest(
                start_text=start_input.value,
                destination_text=dest_input.value,
                profile="car_fastest",
                provider="osrm",
            )
            provider_route, messages = route_live(request)
        else:
            request = RouteRequest(
                start_text=start_input.value,
                destination_text=dest_input.value,
                profile="car_fastest",
                provider="demo",
            )
            provider_route = demo_provider.route(request)
            if provider_route:
                messages = list(provider_route.warnings)

        if provider_route is None:
            route_summary_container.clear()
            with route_summary_container:
                if mode == "live":
                    ui.label("Live routing failed.").style("color:#EF553B; font-weight:600;")
                    nom_on = is_nominatim_enabled()
                    osrm_on = is_osrm_enabled()
                    elev_on = is_open_meteo_elevation_enabled()
                    if not nom_on or not osrm_on:
                        ui.label("Required providers are not enabled. Set these environment variables:").style(
                            "font-size:0.85em; color:#FFA15A;"
                        )
                        if not nom_on:
                            ui.label("CAR_CONSUMPTION_ENABLE_NOMINATIM=true").style(
                                "font-family:monospace; font-size:0.82em; color:#888;"
                            )
                        if not osrm_on:
                            ui.label("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM=true").style(
                                "font-family:monospace; font-size:0.82em; color:#888;"
                            )
                        if not elev_on:
                            ui.label("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION=true (optional)").style(
                                "font-family:monospace; font-size:0.82em; color:#888;"
                            )
                    for msg in messages:
                        ui.label(f"  {msg}").style("font-size:0.82em; color:#FFA15A;")
                    ui.label("Switch to 'Demo offline' mode to use without live providers.").style(
                        "font-size:0.82em; color:#888; margin-top:4px;"
                    )
                else:
                    ui.label("No route found. Try a different search or demo route.").style("color:#EF553B;")
                    for msg in messages:
                        ui.label(f"  {msg}").style("font-size:0.82em; color:#FFA15A;")
            return

        current_route_result["provider_route"] = provider_route
        current_route_result["segments"] = provider_route_to_segments(provider_route)
        current_route_result["messages"] = messages

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
                if messages:
                    with ui.row().style("margin-top:4px;"):
                        for w in messages:
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
        params.temperature_c = temperature.value or 20.0
        params.cabin_target_temp_c = 21.0

        direction_mode = DirectionMode.return_trip if return_cb.value else DirectionMode.one_way

        commute = provider_route_to_commute_scenario(
            provider_route,
            direction_mode=direction_mode,
            invert_wind_on_return=invert_wind_cb.value,
        )

        for seg in commute.route.segments:
            seg.headwind_kmh = headwind.value or 0.0
            seg.payload_kg = payload.value or 0.0

        results = []
        for v in vehicles:
            try:
                result = commute_energy(
                    v,
                    commute,
                    params,
                    eta_regen_downhill=regen_downhill.value or 0.65,
                    eta_regen_stop=regen_downhill.value or 0.65,
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
