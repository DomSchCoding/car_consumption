"""Route controls component for the map route planner."""

from __future__ import annotations

from nicegui import ui

from app.services.routing import DemoRoutingProvider


def build_route_controls(
    demo_provider: DemoRoutingProvider,
    on_calculate: any = None,
) -> dict:
    controls: dict = {}

    with ui.card().style("min-width:280px; padding:16px;"):
        ui.label("Route Search").style("font-weight:700; font-size:1em; margin-bottom:8px;")

        controls["start_input"] = ui.input("Start address", value="Demo city start").style("width:100%;")
        controls["dest_input"] = ui.input("Destination address", value="Demo city destination").style("width:100%;")

        ui.label("Demo Routes").style(
            "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
        )
        available = demo_provider.list_routes()
        route_options = {r: r.replace("_", " ").title() for r in available}
        controls["demo_select"] = ui.select(
            route_options, value=available[0] if available else None, label="Demo route"
        ).style("width:100%;")

        ui.label("Route Options").style(
            "font-weight:600; font-size:0.85em; color:#555; margin-top:8px; margin-bottom:4px;"
        )
        controls["return_cb"] = ui.checkbox("Round trip (there and back)", value=True).style("font-size:0.85em;")
        controls["invert_wind_cb"] = ui.checkbox("Invert wind on return", value=True).style("font-size:0.85em;")

        with ui.expansion("Advanced settings", icon="settings").style("width:100%;"):
            controls["temperature"] = ui.number(
                "Temperature (°C)", value=20, min=-30, max=50, step=1, format="%.0f"
            ).style("width:100%;")
            controls["headwind"] = ui.number("Headwind (km/h)", value=0, min=-50, max=50, step=5, format="%.0f").style(
                "width:100%;"
            )
            controls["payload"] = ui.number("Payload (kg)", value=0, min=0, max=500, step=10, format="%.0f").style(
                "width:100%;"
            )
            controls["regen_downhill"] = ui.number(
                "Regen downhill", value=0.65, min=0, max=1, step=0.05, format="%.2f"
            ).style("width:100%;")
            controls["regen_stop"] = ui.number(
                "Regen stop-go", value=0.65, min=0, max=1, step=0.05, format="%.2f"
            ).style("width:100%;")

        controls["calculate_btn"] = (
            ui.button("Calculate Route", on_click=on_calculate)
            .props("color=primary")
            .style("width:100%; margin-top:8px;")
        )

        provider_status = demo_provider.status()
        status_text = f"Provider: {provider_status.name}"
        if provider_status.message:
            status_text += f" | {provider_status.message}"
        ui.label(status_text).style("font-size:0.78em; color:#888; margin-top:4px;")

    return controls
