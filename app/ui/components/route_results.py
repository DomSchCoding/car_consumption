"""Native NiceGUI components for route energy results."""

from __future__ import annotations

from nicegui import ui

from app.ui.charts import VEHICLE_COLORS
from app.ui.components.vehicle_selector import make_vehicle_label


def render_energy_table(results: list[dict]) -> None:
    """Render energy breakdown as native NiceGUI table (replaces _build_energy_table HTML).

    Each result dict has: vehicle, breakdown, outward, return_
    """
    columns = [
        {"field": "vehicle", "header": "Vehicle", "editable": False},
        {"field": "total_kwh", "header": "Total (kWh)", "editable": False},
        {"field": "kwh_100", "header": "kWh/100km", "editable": False},
        {"field": "aero", "header": "Aero", "editable": False},
        {"field": "roll", "header": "Roll", "editable": False},
        {"field": "aux", "header": "Aux", "editable": False},
        {"field": "climb", "header": "Climb", "editable": False},
        {"field": "stop_go", "header": "Stop-Go", "editable": False},
        {"field": "descent", "header": "Descent Rec.", "editable": False},
        {"field": "range_km", "header": "Range (km)", "editable": False},
    ]

    rows = []
    for entry in results:
        v = entry["vehicle"]
        bd = entry["breakdown"]
        rows.append({
            "vehicle": make_vehicle_label(v),
            "total_kwh": f"{bd.total_battery_kwh:.2f}",
            "kwh_100": f"{bd.kwh_per_100km:.1f}",
            "aero": f"{bd.aero_kwh:.2f}",
            "roll": f"{bd.roll_kwh:.2f}",
            "aux": f"{bd.aux_kwh:.2f}",
            "climb": f"{bd.climb_kwh:.2f}",
            "stop_go": f"{bd.stop_go_kwh:.2f}",
            "descent": f"{bd.descent_recovered_kwh:.2f}",
            "range_km": f"{v.battery_capacity_kwh / bd.kwh_per_100km * 100:.0f}",
        })

    ui.aggrid(
        options={
            "columnDefs": columns,
            "rowData": rows,
            "rowHeight": 32,
            "headerHeight": 28,
            "suppressRowClickSelection": True,
            "domLayout": "normal",
        },
    ).style("width:100%;")


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
        rows.append({
            "vehicle": make_vehicle_label(v),
            "outward": f"{entry['outward_kwh']:.2f}",
            "return_": f"{entry['return_kwh']:.2f}",
            "total": f"{entry['total_kwh']:.2f}",
            "kwh_100": f"{bd_total.kwh_per_100km:.1f}",
        })

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
    fig.add_trace(
        go.Scatter(
            x=dists, y=elevs, mode="lines", name="Elevation", line=dict(color="#00CC96", width=2)
        )
    )
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
