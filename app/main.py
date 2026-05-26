"""NiceGUI main application - Vehicle consumption analysis webapp."""

from __future__ import annotations

from nicegui import app, ui

from app.data.models import PhysicsParams
from app.data.repository import VehicleRepository, load_fuel_constants
from app.ui.charts import VEHICLE_COLORS, build_chart, export_chart_png
from app.ui.components.vehicle_selector import (
    get_filtered_makes,
    get_filtered_models,
    make_vehicle_label,
    short_label,
)
from app.ui.layout import nav_bar, page_layout
from app.ui.state import SESSION
from app.ui.tables import (
    IMAGES_DIR,
    SPEED_OPTIONS,
    build_ranking_list,
    build_table,
    build_vehicle_detail_html,
)

REPO = VehicleRepository()
FUEL_CONST = load_fuel_constants()
MAX_COMPARE = 8

app.add_static_files("/images", str(IMAGES_DIR))


@ui.page("/vehicle/{vid}")
def vehicle_detail(vid: str) -> None:
    v = REPO.get(vid)
    nav_bar()

    if not v:
        with page_layout("Vehicle Not Found", show_back=True):
            ui.label("Vehicle not found").style("font-size:1.5em; color:#EF553B;")
        return

    with page_layout(f"🚗 {make_vehicle_label(v)}", show_back=True):
        ui.html(build_vehicle_detail_html(v))


@ui.page("/")
def index(sort: str = "") -> None:
    nav_bar()

    if sort == "range":
        SESSION["ranking_sort"] = True
    elif sort == "consumption":
        SESSION["ranking_sort"] = False

    params = PhysicsParams()
    selected_ids = SESSION["selected"]

    with page_layout("⚡ Vehicle Consumption Analyzer"):
        ui.label("Physics-based EV & ICE comparison").style(
            "font-size:0.85em; color:#888; margin-bottom:8px;"
        )

        with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
            with ui.card().style("min-width:280px; max-width:320px; flex:1; padding:16px;"):
                ui.label("🚗 Vehicle Selection").style("font-weight:700; font-size:1em; margin-bottom:8px;")

                with ui.row().classes("filter-row"):
                    ev_cb = ui.checkbox("EV", value=SESSION["ev_checked"]).style("font-size:0.85em;")
                    ice_cb = ui.checkbox("ICE", value=SESSION["ice_checked"]).style("font-size:0.85em;")

                make_select = ui.select([], label="Make", with_input=True).style("width:100%;")
                make_select.visible = False

                model_select = ui.select(
                    {},
                    multiple=True,
                    label="Models",
                ).style("width:100%;")
                model_select.visible = False

                ui.separator().style("margin:8px 0;")

                ui.label("Selected").style("font-weight:600; font-size:0.85em; color:#555; margin-bottom:4px;")
                selected_list_container = ui.column().style("max-height:180px; overflow-y:auto; gap:2px; width:100%;")

            with ui.card().style("flex:3; min-width:400px; padding:16px;"):
                chart_container = ui.element("div").style("width:100%; min-height:420px;")

        table_container = ui.element("div").style("width:100%;")

        with ui.card().style("padding:16px;"):
            with ui.expansion("⚙️ Settings", icon="settings").style("width:100%;"):
                with ui.row().style("width:100%; gap:24px; flex-wrap:wrap; padding:8px 0;"):
                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("Parameters").style("font-weight:600; font-size:0.85em; color:#666;")
                        rho_input = ui.number(
                            "Air density (kg/m³)",
                            value=params.rho_air,
                            min=0.5,
                            max=1.5,
                            step=0.001,
                            format="%.3f",
                        ).style("width:100%;")
                        crr_input = ui.number(
                            "Rolling resistance",
                            value=params.c_rr,
                            min=0.003,
                            max=0.02,
                            step=0.001,
                            format="%.3f",
                        ).style("width:100%;")
                        use_per_tire_cb = ui.checkbox("Per-vehicle tires", value=True).style(
                            "font-size:0.82em; margin-top:4px;"
                        )
                        use_per_tire_cb.on_value_change(lambda _: crr_input.set_enabled(not use_per_tire_cb.value))
                        crr_input.set_enabled(not use_per_tire_cb.value)
                        aux_input = ui.number(
                            "Aux power (kW)",
                            value=params.p_aux_kw,
                            min=0.0,
                            max=10.0,
                            step=0.1,
                            format="%.1f",
                        ).style("width:100%;")
                        eta_input = ui.number(
                            "Drivetrain η",
                            value=params.eta_drivetrain,
                            min=0.5,
                            max=1.0,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")
                        regen_input = ui.number(
                            "Regen η",
                            value=params.eta_regen,
                            min=0.0,
                            max=1.0,
                            step=0.05,
                            format="%.2f",
                        ).style("width:100%;")
                        charging_eff_input = ui.number(
                            "Charging η",
                            value=params.eta_charging,
                            min=0.7,
                            max=1.0,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")

                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("ICE Comparison").style("font-weight:600; font-size:0.85em; color:#666;")
                        ice_thermal_eff = ui.number(
                            "Thermal efficiency",
                            value=0.30,
                            min=0.1,
                            max=0.5,
                            step=0.01,
                            format="%.2f",
                        ).style("width:100%;")

                    with ui.column().style("gap:8px; min-width:180px;"):
                        ui.label("Environment").style("font-weight:600; font-size:0.85em; color:#666;")
                        ui.label("Temperature (°C)").style("font-size:0.82em;")
                        temp_input = ui.slider(min=-20, max=45, value=int(params.temperature_c), step=1).style(
                            "width:100%;"
                        )
                        temp_label = ui.label(f"{int(params.temperature_c)}°C").style("font-size:0.78em; color:#888;")
                        temp_input.on_value_change(lambda e: temp_label.set_text(f"{int(e.value)}°C"))
                        ui.label("Min (km/h)").style("font-size:0.82em;")
                        speed_min_slider = ui.slider(min=10, max=100, value=30, step=5).style("width:100%;")
                        ui.label("Max (km/h)").style("font-size:0.82em;")
                        speed_max_slider = ui.slider(min=50, max=200, value=160, step=5).style("width:100%;")

            with ui.expansion("📐 Physics Formulas", icon="science").style("width:100%;"):
                ui.markdown(
                    "**Aero:** F = ½ · ρ · Cd · A · v²  →  kWh/100km = F · 100 / 3600\n\n"
                    "**Roll:** F = c<sub>rr</sub> · m · g  →  kWh/100km constant\n\n"
                    "**Aux:** kWh/100km = P<sub>aux</sub> / v · 100  (↓ with speed)\n\n"
                    "**Drivetrain:** Battery = Wheel / η"
                ).style("font-size:0.82em; line-height:1.6;")

        with ui.card().style("padding:16px;"):
            with ui.row().style("align-items:center; gap:16px; margin-bottom:12px;"):
                ui.label("📊 Consumption Ranking").style("font-weight:700; font-size:0.95em;")
                speed_ranking_select = ui.select(
                    {s: f"{s} km/h" for s in SPEED_OPTIONS},
                    value=SPEED_OPTIONS[2],
                    label="Speed",
                ).style("width:140px;")
                ranking_ev_cb = ui.checkbox("EV", value=SESSION["ranking_ev"]).style("font-size:0.85em;")
                ranking_ice_cb = ui.checkbox("ICE", value=SESSION["ranking_ice"]).style("font-size:0.85em;")
                sort_btn = (
                    ui.button(
                        "Sort: Range" if SESSION["ranking_sort"] else "Sort: kWh",
                        on_click=lambda: _toggle_ranking_sort(),
                    )
                    .props("flat dense")
                    .style("font-size:0.82em;")
                )
            ranking_container = ui.element("div").style("width:100%;")

    _make_list: list[str] = []

    def rebuild_make_select() -> None:
        nonlocal _make_list
        _make_list = get_filtered_makes(REPO, ev_cb.value, ice_cb.value)
        if _make_list:
            cur_val = SESSION["current_make"] if SESSION["current_make"] in _make_list else _make_list[0]
            make_select.set_options({m: m for m in _make_list}, value=cur_val)
            SESSION["current_make"] = cur_val
            make_select.visible = True
            model_select.visible = True
        else:
            make_select.visible = False
            model_select.visible = False

    def remove_vehicle(vid: str) -> None:
        if vid in selected_ids:
            selected_ids.remove(vid)
            update_selected_list()
            update_model_list()
            update()

    def add_vehicle(vid: str) -> None:
        if vid not in selected_ids:
            if len(selected_ids) >= MAX_COMPARE:
                ui.notify(f"Maximum {MAX_COMPARE} vehicles for comparison", type="warning", position="top")
                return
            selected_ids.append(vid)
            update_selected_list()
            update_model_list()
            update()

    def _model_selection_changed() -> None:
        new_sel = model_select.value if isinstance(model_select.value, list) else []
        cur_make = make_select.value
        make_vids = (
            {v.id for v in get_filtered_models(REPO, cur_make, ev_cb.value, ice_cb.value)} if cur_make else set()
        )
        for vid in list(selected_ids):
            if vid in make_vids and vid not in new_sel:
                selected_ids.remove(vid)
        for vid in new_sel:
            if vid not in selected_ids:
                if len(selected_ids) >= MAX_COMPARE:
                    ui.notify(f"Maximum {MAX_COMPARE} vehicles for comparison", type="warning", position="top")
                    return
                selected_ids.append(vid)
        update_selected_list()
        update()

    def update_selected_list() -> None:
        selected_list_container.clear()
        if not selected_ids:
            with selected_list_container:
                ui.label("No vehicles selected").style("color:#999; font-size:0.82em; padding:8px 4px;")
            return
        for i, vid in enumerate(selected_ids):
            v = REPO.get(vid)
            if not v:
                continue
            color = VEHICLE_COLORS[i % len(VEHICLE_COLORS)]
            has_img = (IMAGES_DIR / f"{vid}.jpg").exists()
            with selected_list_container:
                with (
                    ui.row()
                    .style(
                        f"width:100%; border-left:3px solid {color}; "
                        f"display:flex; align-items:center; padding:4px 6px; "
                        f"border-radius:6px; gap:6px;"
                    )
                    .classes("sel-item")
                ):
                    if has_img:
                        ui.html(
                            f'<img src="/images/{vid}.jpg" '
                            f'style="width:32px; height:22px; object-fit:contain; '
                            f'border-radius:3px; flex-shrink:0;">'
                        )
                    ui.link(short_label(v), f"/vehicle/{vid}").style(
                        "flex:1; font-size:0.88em; font-weight:500; "
                        "text-decoration:none; color:inherit; overflow:hidden; "
                        "text-overflow:ellipsis; white-space:nowrap;"
                    )
                    db = ui.button(icon="delete", on_click=lambda _, vid=vid: remove_vehicle(vid))
                    db.props("flat dense round size=sm color=grey")

    def update_model_list() -> None:
        cur_make = make_select.value
        if not cur_make:
            model_select.set_options({})
            return

        models = get_filtered_models(REPO, cur_make, ev_cb.value, ice_cb.value)
        opts: dict[str, str] = {}
        for v in models:
            opts[v.id] = f"{make_vehicle_label(v)} ({v.cda_m2:.2f} m² CdA)"
        model_select.set_options(opts)
        model_select.value = [vid for vid in selected_ids if vid in opts]

    def _toggle_ranking_sort() -> None:
        SESSION["ranking_sort"] = not SESSION["ranking_sort"]
        sort_btn.set_text("Sort: Range" if SESSION["ranking_sort"] else "Sort: kWh")
        update_ranking()

    def update() -> None:
        if not selected_ids:
            chart_container.clear()
            with (
                chart_container,
                ui.column().style("align-items:center; justify-content:center; padding:60px 20px; color:#aaa;"),
            ):
                ui.label("📊").style("font-size:3em; margin-bottom:12px;")
                ui.label("Select vehicles to compare").style("font-size:1.1em; color:#888;")
                ui.label("Use the + buttons to add vehicles").style("font-size:0.85em; color:#bbb;")
            table_container.clear()
            ranking_container.clear()
            return

        vehicles = REPO.get_by_ids(selected_ids)
        params.rho_air = rho_input.value
        params.c_rr = crr_input.value
        params.p_aux_kw = aux_input.value
        params.eta_drivetrain = eta_input.value
        params.eta_regen = regen_input.value
        params.eta_charging = charging_eff_input.value
        params.temperature_c = float(temp_input.value)
        params.cabin_target_temp_c = 21.0

        fig = build_chart(
            vehicles,
            params,
            speed_min_slider.value,
            speed_max_slider.value,
            FUEL_CONST,
            ice_thermal_eff.value,
            use_per_tire_cb.value,
        )

        chart_container.clear()
        with chart_container:
            with ui.row().style("gap:8px; margin-bottom:4px;"):
                ui.label("📈 Consumption vs Speed").style("font-weight:700; font-size:0.95em; flex:1;")
                ui.button("⬇ PNG", on_click=lambda: export_chart_png(fig)).props("flat dense size=sm").style(
                    "font-size:0.78em;"
                )
            ui.plotly(fig).style("width:100%; height:450px;")

        table_html = build_table(vehicles, params, FUEL_CONST, ice_thermal_eff.value, use_per_tire_cb.value)
        table_container.clear()
        with table_container, ui.card().style("padding:16px;"):
            ui.label("📋 Consumption Table").style("font-weight:700; font-size:0.95em; margin-bottom:8px;")
            ui.html(table_html)

        update_ranking()

    def update_ranking() -> None:
        params.rho_air = rho_input.value
        params.c_rr = crr_input.value
        params.p_aux_kw = aux_input.value
        params.eta_drivetrain = eta_input.value
        params.eta_regen = regen_input.value
        params.eta_charging = charging_eff_input.value
        params.temperature_c = float(temp_input.value)
        speed = speed_ranking_select.value if speed_ranking_select.value else SPEED_OPTIONS[2]
        html = build_ranking_list(
            params,
            speed,
            ranking_ev_cb.value,
            ranking_ice_cb.value,
            FUEL_CONST,
            ice_thermal_eff.value,
            use_per_tire_cb.value,
            REPO,
            SESSION["ranking_sort"],
        )
        ranking_container.clear()
        with ranking_container:
            ui.html(html)

    def on_filter_change() -> None:
        SESSION["ev_checked"] = ev_cb.value
        SESSION["ice_checked"] = ice_cb.value
        rebuild_make_select()
        update_ranking()

    ev_cb.on_value_change(lambda _: on_filter_change())
    ice_cb.on_value_change(lambda _: on_filter_change())

    def _on_make_change() -> None:
        SESSION["current_make"] = make_select.value or ""
        update_model_list()

    make_select.on_value_change(lambda _: _on_make_change())
    model_select.on_value_change(lambda _: _model_selection_changed())
    ranking_ev_cb.on_value_change(lambda _: (SESSION.update(ranking_ev=ranking_ev_cb.value), update_ranking()))
    ranking_ice_cb.on_value_change(lambda _: (SESSION.update(ranking_ice=ranking_ice_cb.value), update_ranking()))
    speed_ranking_select.on_value_change(lambda _: update_ranking())

    rho_input.on_value_change(lambda _: update())
    crr_input.on_value_change(lambda _: update())
    aux_input.on_value_change(lambda _: update())
    eta_input.on_value_change(lambda _: update())
    regen_input.on_value_change(lambda _: update())
    charging_eff_input.on_value_change(lambda _: update())
    temp_input.on_value_change(lambda _: update())
    speed_min_slider.on_value_change(lambda _: update())
    speed_max_slider.on_value_change(lambda _: update())
    ice_thermal_eff.on_value_change(lambda _: update())
    use_per_tire_cb.on_value_change(lambda _: (update(), update_ranking()))

    rebuild_make_select()
    update_selected_list()
    ui.timer(0.1, update, once=True)


@ui.page("/route")
def map_route_page() -> None:
    from app.ui.pages.map_route_planner import map_route_page

    nav_bar()
    map_route_page()


@ui.page("/route/manual")
def manual_route_page() -> None:
    from app.ui.pages.route_planner import route_page

    nav_bar()
    route_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Vehicle Consumption Analyzer", port=8080, reload=False)
