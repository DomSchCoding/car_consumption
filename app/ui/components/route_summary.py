"""Route summary cards component for the map route planner."""

from __future__ import annotations

from nicegui import ui

from app.services.provider_models import ProviderRoute


def build_route_summary(provider_route: ProviderRoute) -> None:
    dist = provider_route.summary_distance_km
    duration_s = provider_route.summary_duration_s or 0
    duration_min = duration_s / 60
    avg_speed = dist / (duration_s / 3600) if duration_s > 0 else 0
    gain = provider_route.elevation_gain_m or 0
    loss = provider_route.elevation_loss_m or 0

    with ui.row().style("gap:8px; flex-wrap:wrap;"):
        _summary_card("Distance", f"{dist:.1f} km")
        _summary_card("Duration", f"{duration_min:.0f} min" if duration_s else "-")
        _summary_card("Avg Speed", f"{avg_speed:.0f} km/h" if duration_s else "-")
        _summary_card("Elevation", f"+{gain:.0f} / -{loss:.0f} m")
        _summary_card("Provider", provider_route.provider)
        if provider_route.warnings:
            _summary_card("Warnings", "; ".join(provider_route.warnings), color="#FFA15A")


def build_energy_table(results: list[dict]) -> str:
    header = [
        "Vehicle",
        "kWh/trip",
        "kWh/100km",
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

    from app.ui.components.vehicle_selector import make_vehicle_label

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


def _summary_card(title: str, value: str, color: str = "#333") -> None:
    with ui.card().style("min-width:120px; padding:8px 12px; text-align:center;"):
        ui.label(title).style("font-size:0.75em; color:#888; font-weight:600;")
        ui.label(value).style(f"font-size:0.95em; font-weight:700; color:{color};")
