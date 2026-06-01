"""Native NiceGUI components for route energy results."""

from __future__ import annotations

from nicegui import ui

from app.core.physics import battery_capacity_factor
from app.ui.charts import VEHICLE_COLORS
from app.ui.components.vehicle_selector import make_vehicle_label


def render_energy_table(results: list[dict], temperature_c: float = 20.0) -> None:
    """Render energy breakdown as responsive NiceGUI layout (replaces aggrid).

    Each result dict has: vehicle, breakdown, outward, return_

    On desktop (>768px): compact table-like layout
    On mobile (<=768px): each vehicle as a card with vertical metrics
    """
    # Inject responsive CSS
    ui.add_body_html(
        "<style>"
        ".energy-table-wrap{width:100%;overflow-x:auto;}"
        ".energy-table{width:100%;border-collapse:collapse;font-size:0.82em;font-family:system-ui,sans-serif;}"
        ".energy-table th{border-bottom:2px solid #e0e0e0;padding:6px 4px;background:#fafafa;color:#555;font-weight:600;text-align:left;font-size:0.78em;white-space:nowrap;}"
        ".energy-table td{padding:5px 4px;border-bottom:1px solid #f0f0f0;white-space:nowrap;font-size:0.82em;}"
        ".energy-table tr:nth-child(even){background:#fafafa;}"
        ".energy-card{display:none;padding:12px;border-radius:8px;margin-bottom:8px;border:1px solid #e8e8f0;background:#fff;}"
        ".energy-card-title{font-weight:700;font-size:0.92em;margin-bottom:8px;color:#333;}"
        ".energy-card-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;}"
        ".energy-card-label{font-size:0.78em;color:#888;font-weight:600;}"
        ".energy-card-value{font-size:0.82em;color:#333;font-weight:500;}"
        "@media(max-width:768px){"
        ".energy-table-wrap{display:none !important;}"
        ".energy-card{display:block !important;}"
        "}"
        "</style>"
    )

    cap_factor = battery_capacity_factor(temperature_c)

    rows = []
    for entry in results:
        v = entry["vehicle"]
        bd = entry["breakdown"]
        effective_battery = v.battery_usable_kwh * cap_factor if v.battery_usable_kwh else None
        soc_pct = (bd.total_battery_kwh / effective_battery * 100) if effective_battery else None

        rows.append(
            {
                "vehicle": make_vehicle_label(v),
                "total_kwh": f"{bd.total_battery_kwh:.2f}",
                "kwh_100": f"{bd.kwh_per_100km:.1f}",
                "soc_pct": f"{soc_pct:.1f}%" if soc_pct is not None else "-",
                "aero": f"{bd.aero_kwh:.2f}",
                "roll": f"{bd.roll_kwh:.2f}",
                "aux": f"{bd.aux_kwh:.2f}",
                "climb": f"{bd.climb_kwh:.2f}",
                "stop_go": f"{bd.stop_go_kwh:.2f}",
                "descent": f"{bd.descent_recovered_kwh:.2f}",
                "range_km": f"{v.battery_usable_kwh / bd.kwh_per_100km * 100:.0f}" if v.battery_usable_kwh else "-",
            }
        )

    # Desktop: HTML table
    with ui.element("div").classes("energy-table-wrap"):
        html = '<table class="energy-table"><thead><tr>'
        for col in [
            "vehicle",
            "total_kwh",
            "kwh_100",
            "soc_pct",
            "aero",
            "roll",
            "aux",
            "climb",
            "stop_go",
            "descent",
            "range_km",
        ]:
            labels = {
                "vehicle": "Vehicle",
                "total_kwh": "Total (kWh)",
                "kwh_100": "kWh/100km",
                "soc_pct": "SOC %",
                "aero": "Aero",
                "roll": "Roll",
                "aux": "Aux",
                "climb": "Climb",
                "stop_go": "Stop-Go",
                "descent": "Descent Rec.",
                "range_km": "Range (km)",
            }
            html += f"<th>{labels[col]}</th>"
        html += "</tr></thead><tbody>"
        for row in rows:
            html += "<tr>"
            for col in row:
                html += f"<td>{row[col]}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        ui.html(html)

    # Mobile: Cards (hidden on desktop via CSS)
    for row in rows:
        with ui.element("div").classes("energy-card"):
            ui.label(row["vehicle"]).classes("energy-card-title")
            with ui.element("div").classes("energy-card-grid"):
                labels = {
                    "total_kwh": "Total (kWh)",
                    "kwh_100": "kWh/100km",
                    "soc_pct": "SOC %",
                    "aero": "Aero",
                    "roll": "Roll",
                    "aux": "Aux",
                    "climb": "Climb",
                    "stop_go": "Stop-Go",
                    "descent": "Descent Rec.",
                    "range_km": "Range (km)",
                }
                for col in [
                    "total_kwh",
                    "kwh_100",
                    "soc_pct",
                    "aero",
                    "roll",
                    "aux",
                    "climb",
                    "stop_go",
                    "descent",
                    "range_km",
                ]:
                    ui.label(labels[col]).classes("energy-card-label")
                    ui.label(row[col]).classes("energy-card-value")


def render_comparison_table(compare_results: list[dict], all_results: list[dict]) -> None:
    """Render outward vs return comparison as native NiceGUI table."""
    columns = [
        {"field": "vehicle", "header": "Vehicle", "editable": False},
        {"field": "outward", "header": "Outward (kWh)", "editable": False},
        {"field": "return_", "header": "Return (kWh)", "editable": False},
        {"field": "total", "header": "Total (kWh)", "editable": False},
        {"field": "kwh_100", "header": "kWh/100km", "editable": False},
    ]

    rows = []
    for i, entry in enumerate(compare_results):
        v = entry["vehicle"]
        bd_total = all_results[i]["breakdown"]
        rows.append(
            {
                "vehicle": make_vehicle_label(v),
                "outward": f"{entry['outward_kwh']:.2f}",
                "return_": f"{entry['return_kwh']:.2f}",
                "total": f"{entry['total_kwh']:.2f}",
                "kwh_100": f"{bd_total.kwh_per_100km:.1f}",
            }
        )

    ui.aggrid(
        options={
            "columnDefs": columns,
            "rowData": rows,
            "rowHeight": 32,
            "headerHeight": 28,
            "suppressRowClickSelection": True,
        },
    ).style("width:100%;")


def render_energy_breakdown_chart(results: list[dict]) -> None:
    """Render energy breakdown bar chart with Plotly."""
    import plotly.graph_objects as go

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


def render_elevation_chart(elev_points: list[tuple[float, float]]) -> None:
    """Render elevation profile chart with Plotly."""
    import plotly.graph_objects as go

    fig = go.Figure()
    dists = [p[0] for p in elev_points]
    elevs = [p[1] for p in elev_points]
    fig.add_trace(go.Scatter(x=dists, y=elevs, mode="lines", name="Elevation", line=dict(color="#00CC96", width=2)))
    fig.update_layout(
        title="Elevation Profile",
        xaxis_title="Distance (km)",
        yaxis_title="Elevation (m)",
        template="plotly_white",
        margin=dict(l=50, r=20, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    ui.plotly(fig).style("width:100%; height:300px;")


def render_kv_table(rows: list[tuple[str, str]], title: str = "Details") -> None:
    """Render key-value pairs as native NiceGUI list (replaces HTML debug table)."""
    with ui.expansion(title, icon="science").style("width:100%; margin-top:8px;"):
        with ui.column().style("gap:2px;"):
            for label, value in rows:
                with ui.row().style("gap:8px;"):
                    ui.label(label).style(
                        "font-size:0.8em; font-family:monospace; font-weight:600; color:#555; min-width:220px;"
                    )
                    ui.label(value).style("font-size:0.8em; font-family:monospace; color:#333;")
