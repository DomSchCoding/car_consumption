"""Route / Commute planner page for the Vehicle Consumption Analyzer."""

from __future__ import annotations

from nicegui import ui

from app.core.route_energy import commute_energy
from app.data.models import (
    CommuteScenario,
    DirectionMode,
    PhysicsParams,
    RoadType,
    Route,
    RouteSegment,
)
from app.data.repository import VehicleRepository
from app.ui.components.route_results import (
    render_comparison_table,
    render_energy_breakdown_chart,
    render_energy_table,
)
from app.ui.components.vehicle_selector import (
    make_vehicle_label,
)
from app.ui.layout import page_layout
from app.ui.state import SESSION

MAX_COMPARE_ROUTE = 8


def route_page() -> None:
    """Render the Route / Commute planner page."""
    from app.ui.charts import VEHICLE_COLORS

    repo = VehicleRepository()
    selected_ids: list[str] = list(SESSION.get("selected") or [])

    with page_layout("🗺️ Route / Commute Planner"):
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

                ui.button("Calculate", on_click=lambda: calculate_route()).props("color=primary").style(
                    "width:100%; margin-top:8px;"
                )

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

            # Energy Results as Tabs
            energy_tabs = ui.tabs().props("dense").style("margin-bottom:0;")
            with energy_tabs:
                ui.tab("energy_table", label="📊 Energy Table")
                ui.tab("breakdown", label="📈 Breakdown")
                if return_cb.value:
                    ui.tab("comparison", label="↔️ Outward vs Return")

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

    update_vehicle_list()

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
