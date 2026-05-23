"""Chart generation for the Vehicle Consumption Analyzer."""

from __future__ import annotations

import plotly.graph_objects as go

from app.core.physics import (
    battery_capacity_factor,
    consumption_curve,
    hvac_power_kw,
)
from app.data.models import (
    FuelConstants,
    FuelType,
    PhysicsParams,
    Vehicle,
    VehicleType,
)
from app.ui.components.vehicle_selector import get_vehicle_c_rr, make_vehicle_label

VEHICLE_COLORS = [
    "#636EFA",
    "#EF553B",
    "#00CC96",
    "#AB63FA",
    "#FFA15A",
    "#19D3F3",
    "#FF6692",
    "#B6E880",
    "#FF97FF",
    "#FECB52",
    "#FFABAB",
    "#A0D2EB",
    "#E2F0CB",
    "#FFD3B6",
    "#D4A5A5",
]


def build_chart(
    vehicles: list[Vehicle],
    params: PhysicsParams,
    speed_min: float,
    speed_max: float,
    fuel_const: FuelConstants,
    ice_thermal_eff: float,
    use_per_vehicle_tires: bool,
) -> go.Figure:
    fig = go.Figure()

    cap_factor = battery_capacity_factor(params.temperature_c)

    for idx, vehicle in enumerate(vehicles):
        color = VEHICLE_COLORS[idx % len(VEHICLE_COLORS)]
        c_rr = get_vehicle_c_rr(vehicle, params.c_rr, use_per_vehicle_tires)
        hp = vehicle.has_heat_pump if vehicle.has_heat_pump is not None else False
        cop = vehicle.hvac_cop_heat if vehicle.hvac_cop_heat is not None else None
        vehicle_hvac = hvac_power_kw(
            params.temperature_c,
            params.cabin_target_temp_c,
            has_heat_pump=hp,
            hvac_cop_heat=cop,
        )
        curve = consumption_curve(
            rho_air=params.rho_air,
            cd=vehicle.drag_coefficient_cd,
            frontal_area_m2=vehicle.frontal_area_m2,
            mass_kg=vehicle.mass_kg,
            c_rr=c_rr,
            p_aux_kw=vehicle_hvac,
            speed_min_kmh=speed_min,
            speed_max_kmh=speed_max,
            steps=80,
            eta_drivetrain=params.eta_drivetrain,
        )
        speeds = [speed_min + (speed_max - speed_min) * i / (len(curve) - 1) for i in range(len(curve))]
        label = make_vehicle_label(vehicle)

        if vehicle.vehicle_type == VehicleType.ev:
            y_total = [c.total_battery_kwh_per_100km for c in curve]
            effective_battery = vehicle.battery_usable_kwh * cap_factor if vehicle.battery_usable_kwh else None
            hover_texts = []
            for i, c in enumerate(curve):
                ht = (
                    f"<b>{label}</b><br>"
                    f"Speed: {speeds[i]:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"💨 Aero: {c.aero_kwh_per_100km:.1f} kWh/100km<br>"
                    f"🛞 Roll: {c.roll_kwh_per_100km:.1f} kWh/100km<br>"
                    f"⚡ HVAC: {c.aux_kwh_per_100km:.1f} kWh/100km<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"🔋 Total: {c.total_battery_kwh_per_100km:.1f} kWh/100km"
                )
                if effective_battery:
                    rng = effective_battery / c.total_battery_kwh_per_100km * 100
                    ht += f"<br>📏 Range: {rng:.0f} km"
                hover_texts.append(ht)
            fig.add_trace(
                go.Scatter(
                    x=speeds,
                    y=y_total,
                    mode="lines",
                    name=label,
                    line=dict(color=color, width=3),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover_texts,
                    legendgroup=label,
                    showlegend=True,
                )
            )
            if effective_battery:
                y_range = [effective_battery / c.total_battery_kwh_per_100km * 100 for c in curve]
                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_range,
                        mode="lines",
                        name=f"{label} Range",
                        line=dict(color=color, width=2, dash="dot"),
                        yaxis="y2",
                        legendgroup=label,
                        showlegend=False,
                        hovertemplate=f"%{{y:.0f}} km at %{{x:.0f}} km/h<extra>{label}</extra>",
                    )
                )
        else:
            l_per_100km = vehicle.real_consumption_l_100km
            if l_per_100km is not None:
                kwh_per_l = (
                    fuel_const.diesel_kwh_per_liter
                    if vehicle.fuel_type == FuelType.diesel
                    else fuel_const.gasoline_kwh_per_liter
                )
                chem_kwh = l_per_100km.value * kwh_per_l
                wheel_kwh = chem_kwh * ice_thermal_eff
                y_chem = [chem_kwh] * len(speeds)
                y_wheel = [wheel_kwh] * len(speeds)

                hover_texts_chem = [
                    f"<b>{label}</b><br>Speed: {s:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"⛽ Chemical: {chem_kwh:.0f} kWh/100km<br>"
                    f"🔧 Wheel est.: {wheel_kwh:.0f} kWh/100km"
                    for s in speeds
                ]
                hover_texts_wheel = [
                    f"<b>{label}</b><br>Speed: {s:.0f} km/h<br>"
                    f"━━━━━━━━━━━━━━━<br>"
                    f"⛽ Chemical: {chem_kwh:.0f} kWh/100km<br>"
                    f"🔧 Wheel est.: {wheel_kwh:.0f} kWh/100km<br>"
                    f"(at {ice_thermal_eff:.0%} thermal efficiency)"
                    for s in speeds
                ]

                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_chem,
                        mode="lines",
                        name=f"{label} (chem)",
                        line=dict(color=color, width=3),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover_texts_chem,
                        legendgroup=label,
                        showlegend=True,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=speeds,
                        y=y_wheel,
                        mode="lines",
                        name=f"{label} (wheel)",
                        line=dict(color=color, width=2, dash="dash"),
                        hovertemplate="%{customdata}<extra></extra>",
                        customdata=hover_texts_wheel,
                        legendgroup=label,
                        showlegend=False,
                    )
                )

    fig.update_layout(
        title=None,
        xaxis_title="Speed (km/h)",
        yaxis_title="kWh / 100 km",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1e1e2e", font=dict(color="#cdd6f4", size=12), bordercolor="#45475a"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        template="plotly_white",
        margin=dict(l=50, r=60, t=20, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#e5e5e5", zerolinecolor="#e5e5e5"),
        yaxis=dict(gridcolor="#e5e5e5", zerolinecolor="#e5e5e5"),
        yaxis2=dict(
            title=dict(text="Range (km)", font=dict(color="#00CC96")),
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
            zerolinecolor="rgba(0,0,0,0)",
            showgrid=False,
            tickfont=dict(color="#00CC96"),
        ),
    )

    return fig


def export_chart_png(fig: go.Figure) -> None:
    from io import BytesIO

    from nicegui import ui

    try:
        buf = BytesIO()
        fig.write_image(buf, format="png", scale=2, width=1200, height=600)
        buf.seek(0)
        ui.download(buf.read(), filename="consumption_chart.png", media_type="image/png")
    except Exception:
        ui.notify("PNG export requires kaleido. Install with: pip install kaleido", type="warning", position="top")
