"""Map-based route planner page with demo and live provider support."""

from __future__ import annotations

import asyncio

from nicegui import ui

from app.core.route_energy import commute_energy
from app.core.route_geometry import (
    elevation_stats,
    expected_climb_battery_kwh,
    expected_descent_recovered_kwh,
    potential_energy_kwh,
)
from app.core.route_segmentizer import (
    provider_route_to_commute_scenario,
    provider_route_to_segments,
)
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
from app.ui.components.route_results import (
    render_comparison_table,
    render_energy_breakdown_chart,
    render_energy_table,
    render_elevation_chart,
    render_kv_table,
)
from app.ui.components.vehicle_selector import make_vehicle_label
from app.ui.layout import page_layout
from app.ui.state import SESSION

MAX_COMPARE_ROUTE = 8

_GEOCODE_DEBOUNCE_MS = 1000


class GeocodeStatus:
    unresolved = "unresolved"
    searching = "searching"
    resolved = "resolved"
    not_found = "not found"
    provider_disabled = "provider disabled"


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
    repo = VehicleRepository()
    selected_ids: list[str] = list(SESSION.get("selected", []))
    demo_provider = DemoRoutingProvider()

    current_route_result: dict = {"provider_route": None, "segments": None, "messages": []}

    resolved_start: dict = {"point": None, "label": None, "status": GeocodeStatus.unresolved}
    resolved_dest: dict = {"point": None, "label": None, "status": GeocodeStatus.unresolved}

    DEMO_ROUTE_ADDRESSES: dict[str, tuple[str, str]] = {
        "city_commute": ("demo city start", "demo city destination"),
        "hilly_commute": ("demo hilly start", "demo hilly destination"),
        "highway_route": ("demo highway start", "demo highway destination"),
    }

    with page_layout("🗺️ Map Route Planner"):
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

                start_status_label = ui.label("").style(
                    "font-size:0.75em; color:#888; margin-top:1px; min-height:1.1em;"
                )
                dest_status_label = ui.label("").style(
                    "font-size:0.75em; color:#888; margin-top:1px; min-height:1.1em;"
                )

                geocode_timer = {"start": None, "dest": None}

                def _update_status_labels() -> None:
                    for label, key in [(start_status_label, "start"), (dest_status_label, "dest")]:
                        resolved = resolved_start if key == "start" else resolved_dest
                        status = resolved["status"]
                        name = "Start" if key == "start" else "Destination"
                        if status == GeocodeStatus.resolved:
                            lbl = resolved["label"] or name
                            label.set_text(f"✓ {name}: {lbl}")
                            label.style("font-size:0.75em; color:#2E7D32; margin-top:1px; min-height:1.1em;")
                        elif status == GeocodeStatus.searching:
                            label.set_text(f"◌ {name}: searching...")
                            label.style("font-size:0.75em; color:#1976D2; margin-top:1px; min-height:1.1em;")
                        elif status == GeocodeStatus.not_found:
                            label.set_text(f"✗ {name}: not found")
                            label.style("font-size:0.75em; color:#C62828; margin-top:1px; min-height:1.1em;")
                        elif status == GeocodeStatus.provider_disabled:
                            label.set_text(f"— {name}: provider disabled")
                            label.style("font-size:0.75em; color:#888; margin-top:1px; min-height:1.1em;")
                        else:
                            label.set_text(f"  {name}: unresolved")
                            label.style("font-size:0.75em; color:#888; margin-top:1px; min-height:1.1em;")

                def _update_markers() -> None:
                    clear_route_layer(route_map)
                    start_pt = resolved_start.get("point")
                    dest_pt = resolved_dest.get("point")
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

                async def _geocode_address(address: str, which: str) -> None:
                    if provider_mode.value != "live":
                        return

                    if not is_nominatim_enabled():
                        resolved = resolved_start if which == "start" else resolved_dest
                        resolved["status"] = GeocodeStatus.provider_disabled
                        resolved["point"] = None
                        resolved["label"] = None
                        _update_status_labels()
                        return

                    resolved = resolved_start if which == "start" else resolved_dest
                    address = address.strip()
                    if not address:
                        resolved["status"] = GeocodeStatus.unresolved
                        resolved["point"] = None
                        resolved["label"] = None
                        _update_status_labels()
                        return

                    resolved["status"] = GeocodeStatus.searching
                    _update_status_labels()

                    try:
                        from app.services.geocoding import geocode as nominatim_geocode

                        candidates, err = await asyncio.to_thread(nominatim_geocode, address)
                        if candidates:
                            resolved["point"] = candidates[0].point
                            resolved["label"] = candidates[0].label
                            resolved["status"] = GeocodeStatus.resolved
                        else:
                            resolved["point"] = None
                            resolved["label"] = None
                            resolved["status"] = GeocodeStatus.not_found
                    except Exception:
                        resolved["point"] = None
                        resolved["label"] = None
                        resolved["status"] = GeocodeStatus.not_found

                    _update_status_labels()
                    _update_markers()

                def _schedule_geocode(which: str) -> None:
                    if provider_mode.value != "live":
                        return
                    key = which
                    if geocode_timer[key] is not None:
                        geocode_timer[key].cancel()
                    address = start_input.value if which == "start" else dest_input.value
                    geocode_timer[key] = ui.timer(
                        _GEOCODE_DEBOUNCE_MS / 1000.0,
                        lambda w=which, a=address: _geocode_address(a, w),
                        once=True,
                    )

                start_input.on("keydown.enter", lambda: _geocode_address(start_input.value, "start"))
                dest_input.on("keydown.enter", lambda: _geocode_address(dest_input.value, "dest"))
                start_input.on_value_change(lambda: _schedule_geocode("start"))
                dest_input.on_value_change(lambda: _schedule_geocode("dest"))

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
                        resolved_start["status"] = GeocodeStatus.unresolved
                        resolved_start["point"] = None
                        resolved_start["label"] = None
                        resolved_dest["status"] = GeocodeStatus.unresolved
                        resolved_dest["point"] = None
                        resolved_dest["label"] = None
                        _update_status_labels()
                    else:
                        demo_select.enable()
                        if demo_select.value and demo_select.value in DEMO_ROUTE_ADDRESSES:
                            start_addr, dest_addr = DEMO_ROUTE_ADDRESSES[demo_select.value]
                            start_input.set_value(start_addr)
                            dest_input.set_value(dest_addr)
                        start_input.props('placeholder=""')
                        dest_input.props('placeholder=""')
                        resolved_start["status"] = GeocodeStatus.unresolved
                        resolved_start["point"] = None
                        resolved_start["label"] = None
                        resolved_dest["status"] = GeocodeStatus.unresolved
                        resolved_dest["point"] = None
                        resolved_dest["label"] = None
                        _update_status_labels()

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
            start_coord = resolved_start.get("point")
            dest_coord = resolved_dest.get("point")

            if start_coord is None or dest_coord is None:
                from app.services.geocoding import geocode as nominatim_geocode

                if start_coord is None and start_input.value:
                    resolved_start["status"] = GeocodeStatus.searching
                    _update_status_labels()
                    candidates, geo_err = nominatim_geocode(start_input.value)
                    if candidates:
                        start_coord = candidates[0].point
                        resolved_start["point"] = start_coord
                        resolved_start["label"] = candidates[0].label
                        resolved_start["status"] = GeocodeStatus.resolved
                        messages.append(f"Geocoded start: {candidates[0].label}")
                    else:
                        resolved_start["status"] = GeocodeStatus.not_found
                        detail = geo_err if geo_err else "No results found"
                        messages.append(f"Could not geocode start address '{start_input.value}': {detail}")

                if dest_coord is None and dest_input.value:
                    resolved_dest["status"] = GeocodeStatus.searching
                    _update_status_labels()
                    candidates, geo_err = nominatim_geocode(dest_input.value)
                    if candidates:
                        dest_coord = candidates[0].point
                        resolved_dest["point"] = dest_coord
                        resolved_dest["label"] = candidates[0].label
                        resolved_dest["status"] = GeocodeStatus.resolved
                        messages.append(f"Geocoded destination: {candidates[0].label}")
                    else:
                        resolved_dest["status"] = GeocodeStatus.not_found
                        detail = geo_err if geo_err else "No results found"
                        messages.append(f"Could not geocode destination '{dest_input.value}': {detail}")

                _update_status_labels()

                if start_coord is None or dest_coord is None:
                    route_summary_container.clear()
                    with route_summary_container:
                        ui.label("Live routing failed.").style("color:#EF553B; font-weight:600;")
                        for msg in messages:
                            ui.label(f"  {msg}").style("font-size:0.82em; color:#FFA15A;")
                        ui.label("Switch to 'Demo offline' mode or enter valid addresses.").style(
                            "font-size:0.82em; color:#888; margin-top:4px;"
                        )
                    return

            request = RouteRequest(
                start_text=start_input.value,
                destination_text=dest_input.value,
                start_coord=start_coord,
                destination_coord=dest_coord,
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

            elev_points = [
                (p.distance_from_start_km, p.elevation_m)
                for p in provider_route.geometry
                if p.elevation_m is not None and p.distance_from_start_km is not None
            ]

            # Energy Results as Tabs
            energy_tabs = ui.tabs().props("dense").style("margin-bottom:0;")
            with energy_tabs:
                ui.tab("energy_table", label="📊 Energy Table")
                ui.tab("breakdown", label="📈 Breakdown")
                if return_cb.value:
                    ui.tab("comparison", label="↔️ Outward vs Return")
                if elev_points:
                    ui.tab("elevation", label="⛰️ Elevation")

            energy_panels = ui.tab_panels(energy_tabs, value="energy_table").style("width:100%;")

            with energy_panels, ui.tab_panel("energy_table"):
                with ui.card().style("padding:16px; width:100%;"):
                    render_energy_table(results)

            with energy_panels, ui.tab_panel("breakdown"):
                with ui.card().style("padding:16px; width:100%;"):
                    render_energy_breakdown_chart(results)

            if return_cb.value:
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

                with energy_panels, ui.tab_panel("comparison"):
                    with ui.card().style("padding:16px; width:100%;"):
                        if compare_results:
                            render_comparison_table(compare_results, results)
                        else:
                            ui.label("No return trip data available").style("color:#888;")

            if elev_points:
                with energy_panels, ui.tab_panel("elevation"):
                    with ui.card().style("padding:16px; width:100%;"):
                        render_elevation_chart(elev_points)

            _render_elevation_debug(provider_route, results, params)

    def _render_elevation_debug(provider_route, results: list, params: PhysicsParams) -> None:
        from app.core.route_geometry import (
            elevation_stats,
            expected_climb_battery_kwh,
            expected_descent_recovered_kwh,
            potential_energy_kwh,
        )

        geometry = provider_route.geometry
        stats = elevation_stats(geometry)

        provider_name = provider_route.provider
        elevation_source = "enriched" if any(p.elevation_m is not None for p in geometry) else "none"
        geometry_points = len(geometry)

        start_elev = stats.get("start_elevation")
        end_elev = stats.get("end_elevation")
        net_diff = stats.get("net_elevation_diff")
        min_elev = stats.get("min_elevation")
        max_elev = stats.get("max_elevation")
        acc_gain = stats.get("accumulated_gain") or 0
        acc_loss = stats.get("accumulated_loss") or 0
        sample_count = stats.get("sample_count", 0)

        rows: list[tuple[str, str]] = [
            ("Provider", provider_name),
            ("Elevation source", elevation_source),
            ("Geometry points", str(geometry_points)),
            ("Sample count", str(sample_count)),
            ("Start elevation", f"{start_elev} m" if start_elev is not None else "N/A"),
            ("Destination elevation", f"{end_elev} m" if end_elev is not None else "N/A"),
            ("Net elevation diff", f"{net_diff} m" if net_diff is not None else "N/A"),
            ("Min elevation", f"{min_elev} m" if min_elev is not None else "N/A"),
            ("Max elevation", f"{max_elev} m" if max_elev is not None else "N/A"),
            ("Accumulated gain", f"{acc_gain} m"),
            ("Accumulated loss", f"{acc_loss} m"),
        ]

        if results:
            v = results[0]["vehicle"]
            mass_kg = v.mass_kg + (payload.value or 0)
            eta_dt = params.eta_drivetrain
            eta_regen = regen_downhill.value or 0.65

            height_m = acc_gain if acc_gain else 0
            net_h = abs(end_elev - start_elev) if start_elev is not None and end_elev is not None else 0

            e_pot = potential_energy_kwh(mass_kg, height_m) if height_m else 0
            e_climb_bat = expected_climb_battery_kwh(mass_kg, height_m, eta_dt) if height_m else 0
            e_regen_val = expected_descent_recovered_kwh(mass_kg, acc_loss if acc_loss else 0, eta_regen)

            model_climb = results[0]["breakdown"].climb_kwh
            model_descent = results[0]["breakdown"].descent_recovered_kwh

            rows += [
                ("Vehicle mass (+ payload)", f"{mass_kg:.0f} kg"),
                ("Net elev diff (start/end)", f"{net_h:.0f} m" if net_h else "N/A"),
                ("m·g·h climb (potential)", f"{e_pot:.3f} kWh" if e_pot else "N/A"),
                ("m·g·h / η_dt (battery)", f"{e_climb_bat:.3f} kWh" if e_climb_bat else "N/A"),
                ("Model climb kWh", f"{model_climb:.3f} kWh"),
                ("Model descent recovered", f"{model_descent:.3f} kWh"),
                ("Expected descent recovered", f"{e_regen_val:.3f} kWh"),
                ("η_dt / η_regen", f"{eta_dt} / {eta_regen}"),
            ]

        warnings: list[str] = []
        if start_elev is not None and end_elev is not None and net_diff is not None:
            distance_km = provider_route.summary_distance_km
            if distance_km > 10 and all(p.elevation_m is None for p in geometry):
                warnings.append("Route > 10 km but all elevation values are None")
            if abs(net_diff) > 50 and acc_gain < abs(net_diff) and acc_loss < abs(net_diff):
                warnings.append(
                    f"Start/end elevation difference ({net_diff:.0f} m) exceeds "
                    f"computed gain/loss (gain={acc_gain:.0f}, loss={acc_loss:.0f})"
                )
            if any(p.elevation_m is not None for p in geometry) and acc_gain == 0 and acc_loss == 0:
                warnings.append("Elevation values present but accumulated gain/loss is 0")

        rows.append(("Warnings", "; ".join(warnings) if warnings else "None"))

        render_kv_table(rows, "Elevation / Physics Debug")

    update_vehicle_list()


def _summary_card(title: str, value: str, color: str = "#333") -> None:
    with ui.card().style("min-width:100px; padding:6px 10px; text-align:center;"):
        ui.label(title).style("font-size:0.75em; color:#888; font-weight:600;")
        ui.label(value).style(f"font-size:0.95em; font-weight:700; color:{color};")
