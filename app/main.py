"""NiceGUI main application - Vehicle consumption analysis webapp."""

from __future__ import annotations

from nicegui import app, ui

from app.data.models import PhysicsParams
from app.data.repository import VehicleRepository, load_fuel_constants
from app.ui.charts import VEHICLE_COLORS, build_chart, export_chart_png
from app.ui.components.vehicle_selector import (
    get_filter_ranges,
    get_filtered_makes,
    get_filtered_models,
    make_vehicle_label,
    short_label,
)
from app.ui.layout import page_layout
from app.ui.nicegui_tables import (
    render_consumption_table,
    render_ranking_list,
)
from app.ui.state import SESSION
from app.ui.tables import (
    IMAGES_DIR,
    SPEED_OPTIONS,
    build_vehicle_detail_html,
)

REPO = VehicleRepository()
FUEL_CONST = load_fuel_constants()
MAX_COMPARE = 8

app.add_static_files("/images", str(IMAGES_DIR))


@ui.page("/vehicle/{vid}")
def vehicle_detail(vid: str) -> None:
    v = REPO.get(vid)

    if not v:
        with page_layout("Vehicle Not Found", show_back=True):
            ui.label("Vehicle not found").style("font-size:1.5em; color:#EF553B;")
        return

    with page_layout(f"🚗 {make_vehicle_label(v)}", show_back=True):
        ui.link("← Back to Ranking", "/").style(
            "display:inline-block; margin-bottom:12px; font-size:0.85em; "
            "color:#636EFA; text-decoration:none; cursor:pointer;"
        )
        ui.html(build_vehicle_detail_html(v))


@ui.page("/")
def index(sort: str = "") -> None:
    if sort == "range":
        SESSION["ranking_sort"] = True
    elif sort == "consumption":
        SESSION["ranking_sort"] = False

    params = PhysicsParams()
    selected_ids = SESSION["selected"]

    with page_layout("⚡ Vehicle Consumption Analyzer"):
        dashboard_tabs = ui.tabs().props("dense").style("margin-bottom:0;")
        with dashboard_tabs:
            ui.tab("compare", label="📊 Compare")
            ui.tab("table", label="📋 Table")
            ui.tab("ranking", label="🏆 Ranking")
            ui.tab("settings", label="⚙️ Settings")
            # Route tab — navigates to /route on click
            route_tab = ui.tab("route", label="🗺️ Route Planner")

        def _go_to_route() -> None:
            ui.navigate.to("/route")

        route_tab.on("click", _go_to_route)

        dashboard_panels = ui.tab_panels(dashboard_tabs, value="compare").style("width:100%;")

        # --- COMPARE TAB ---
        with dashboard_panels, ui.tab_panel("compare"):
            # Header bar with title, filters, and controls
            with ui.element("div").style(
                "display:flex; align-items:center; justify-content:space-between; "
                "gap:12px; padding:12px 16px; margin-bottom:12px; "
                "background:linear-gradient(135deg, #f8f9fc 0%, #f0f2f8 100%); "
                "border-radius:12px; flex-wrap:wrap; border:1px solid #e8e8f0;"
            ):
                # Left: Title + filter chips
                with ui.row().style("align-items:center; gap:10px; flex-wrap:wrap;"):
                    ui.label("🚗 Vehicle Selection").style("font-weight:700; font-size:0.95em; white-space:nowrap;")
                    # EV/ICE as toggle chips instead of checkboxes
                    ev_toggle = (
                        ui.button(
                            "⚡ EV" if SESSION["ev_checked"] else "EV",
                            on_click=None,
                        )
                        .props("flat dense" if not SESSION["ev_checked"] else "unelevated dense color=primary")
                        .style(
                            "min-width:60px; font-size:0.82em; border-radius:20px; text-transform:none; cursor:pointer;"
                            + (" background:#636EFA; color:white;" if SESSION["ev_checked"] else " color:#888;")
                        )
                    )
                    ice_toggle = (
                        ui.button(
                            "⛽ ICE" if SESSION["ice_checked"] else "ICE",
                            on_click=None,
                        )
                        .props("flat dense" if not SESSION["ice_checked"] else "unelevated dense color=negative")
                        .style(
                            "min-width:60px; font-size:0.82em; border-radius:20px; text-transform:none; cursor:pointer;"
                            + (" background:#EF553B; color:white;" if SESSION["ice_checked"] else " color:#888;")
                        )
                    )
                    # Hidden checkboxes — keep compatibility with existing code
                    ev_cb = ui.checkbox("EV", value=SESSION["ev_checked"]).style("display:none;")
                    ice_cb = ui.checkbox("ICE", value=SESSION["ice_checked"]).style("display:none;")

                    def _sync_toggle(btn, cb, key) -> None:
                        cb.value = not cb.value
                        SESSION[key] = cb.value
                        active = cb.value
                        if key == "ev":
                            btn.text = "⚡ EV" if active else "EV"
                            btn.props("unelevated dense color=primary" if active else "flat dense")
                            btn.style("background:#636EFA; color:white;" if active else "color:#888;")
                        else:
                            btn.text = "⛽ ICE" if active else "ICE"
                            btn.props("unelevated dense color=negative" if active else "flat dense")
                            btn.style("background:#EF553B; color:white;" if active else "color:#888;")
                        on_filter_change()  # NiceGUI on_value_change does NOT fire on programmatic value set

                    ev_toggle.on_click(lambda: _sync_toggle(ev_toggle, ev_cb, "ev"))
                    ice_toggle.on_click(lambda: _sync_toggle(ice_toggle, ice_cb, "ice"))

            with ui.row().style("width:100%; gap:16px; flex-wrap:wrap; align-items:stretch;"):
                with ui.card().style("min-width:280px; max-width:320px; flex:1; padding:16px;"):
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
                    selected_list_container = ui.column().style(
                        "max-height:180px; overflow-y:auto; gap:2px; width:100%;"
                    )

                with ui.card().style("flex:3; min-width:400px; padding:16px;"):
                    chart_container = ui.element("div").style("width:100%; min-height:420px;")

        # --- TABLE TAB ---
        with dashboard_panels, ui.tab_panel("table"):
            with ui.card().style("padding:16px; width:100%;"):
                ui.label("📋 Consumption Table").style("font-weight:700; font-size:0.95em; margin-bottom:8px;")
                table_container = ui.element("div").style("width:100%;")

        # --- RANKING TAB ---
        with dashboard_panels, ui.tab_panel("ranking"):
            with ui.card().style("padding:16px; width:100%;"):
                # Header bar for ranking controls
                with ui.element("div").style(
                    "display:flex; align-items:center; gap:12px; margin-bottom:12px; "
                    "flex-wrap:wrap; padding-bottom:8px; border-bottom:1px solid #f0f0f0;"
                ):
                    ui.label("🏆 Ranking").style("font-weight:700; font-size:0.95em; white-space:nowrap;")
                    speed_ranking_select = ui.select(
                        {s: f"{s} km/h" for s in SPEED_OPTIONS},
                        value=SPEED_OPTIONS[2],
                        label="Speed",
                    ).style("width:140px;")
                    # EV/ICE toggle chips for ranking
                    ranking_ev_toggle = (
                        ui.button(
                            "⚡ EV" if SESSION["ranking_ev"] else "EV",
                        )
                        .props("flat dense" if not SESSION["ranking_ev"] else "unelevated dense color=primary")
                        .style(
                            "min-width:60px; font-size:0.82em; border-radius:20px; text-transform:none; cursor:pointer;"
                            + (" background:#636EFA; color:white;" if SESSION["ranking_ev"] else " color:#888;")
                        )
                    )
                    ranking_ice_toggle = (
                        ui.button(
                            "⛽ ICE" if SESSION["ranking_ice"] else "ICE",
                        )
                        .props("flat dense" if not SESSION["ranking_ice"] else "unelevated dense color=negative")
                        .style(
                            "min-width:60px; font-size:0.82em; border-radius:20px; text-transform:none; cursor:pointer;"
                            + (" background:#EF553B; color:white;" if SESSION["ranking_ice"] else " color:#888;")
                        )
                    )
                    sort_btn = (
                        ui.button(
                            "Sort: Range" if SESSION["ranking_sort"] else "Sort: kWh",
                            on_click=lambda: _toggle_ranking_sort(),
                        )
                        .props("flat dense")
                        .style("font-size:0.82em; border-radius:20px;")
                    )
                    # Hidden checkboxes — ranking uses separate EV/ICE state
                    ranking_ev_cb = ui.checkbox("EV", value=SESSION["ranking_ev"]).style("display:none;")
                    ranking_ice_cb = ui.checkbox("ICE", value=SESSION["ranking_ice"]).style("display:none;")

                    def _sync_ranking_toggle(btn, cb, key) -> None:
                        cb.value = not cb.value
                        SESSION[key] = cb.value
                        active = cb.value
                        if key == "ranking_ev":
                            btn.text = "⚡ EV" if active else "EV"
                            btn.props("unelevated dense color=primary" if active else "flat dense")
                            btn.style("background:#636EFA; color:white;" if active else "color:#888;")
                        else:
                            btn.text = "⛽ ICE" if active else "ICE"
                            btn.props("unelevated dense color=negative" if active else "flat dense")
                            btn.style("background:#EF553B; color:white;" if active else "color:#888;")
                        update_ranking()  # NiceGUI on_value_change does NOT fire on programmatic value set

                    ranking_ev_toggle.on_click(
                        lambda: _sync_ranking_toggle(ranking_ev_toggle, ranking_ev_cb, "ranking_ev")
                    )
                    ranking_ice_toggle.on_click(
                        lambda: _sync_ranking_toggle(ranking_ice_toggle, ranking_ice_cb, "ranking_ice")
                    )

                # --- VEHICLE FILTERS (collapsible) ---
                _franges = get_filter_ranges(REPO)

                def _filter_val(key: str):
                    return SESSION.get(key)

                def _update_filter_num(key: str, value):
                    SESSION[key] = value if value else None
                    update_ranking()

                with ui.expansion("🔍 Vehicle Filters", icon="filter_list").style("width:100%; margin-bottom:8px;"):
                    with ui.row().style("gap:16px; flex-wrap:wrap; padding:8px 0;"):
                        # Weight
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Weight (kg)").style("font-size:0.78em; font-weight:600; color:#666;")
                            _wmin, _wmax = _franges.get("weight", (None, None))
                            with ui.row().style("gap:4px;"):
                                filter_weight_min = (
                                    ui.number(
                                        "Min",
                                        value=SESSION["filter_weight_min"],
                                        min=int(_wmin or 0),
                                        max=int(_wmax or 99999),
                                        step=100,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )
                                filter_weight_max = (
                                    ui.number(
                                        "Max",
                                        value=SESSION["filter_weight_max"],
                                        min=int(_wmin or 0),
                                        max=int(_wmax or 99999),
                                        step=100,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )

                        # Length
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Length (mm)").style("font-size:0.78em; font-weight:600; color:#666;")
                            _lmin, _lmax = _franges.get("length", (None, None))
                            with ui.row().style("gap:4px;"):
                                filter_length_min = (
                                    ui.number(
                                        "Min",
                                        value=SESSION["filter_length_min"],
                                        min=int(_lmin or 0),
                                        max=int(_lmax or 99999),
                                        step=100,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )
                                filter_length_max = (
                                    ui.number(
                                        "Max",
                                        value=SESSION["filter_length_max"],
                                        min=int(_lmin or 0),
                                        max=int(_lmax or 99999),
                                        step=100,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )

                        # Ground clearance
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Clearance (mm)").style("font-size:0.78em; font-weight:600; color:#666;")
                            _cmin, _cmax = _franges.get("clearance", (None, None))
                            with ui.row().style("gap:4px;"):
                                filter_clearance_min = (
                                    ui.number(
                                        "Min",
                                        value=SESSION["filter_clearance_min"],
                                        min=int(_cmin or 0),
                                        max=int(_cmax or 99999),
                                        step=5,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )
                                filter_clearance_max = (
                                    ui.number(
                                        "Max",
                                        value=SESSION["filter_clearance_max"],
                                        min=int(_cmin or 0),
                                        max=int(_cmax or 99999),
                                        step=5,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )

                    with ui.row().style("gap:16px; flex-wrap:wrap; padding:8px 0;"):
                        # Drivetrain
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Drivetrain").style("font-size:0.78em; font-weight:600; color:#666;")
                            _dt_selected = SESSION["filter_drivetrain"]
                            with ui.row().style("gap:4px;"):
                                dt_fwd_btn = (
                                    ui.button(
                                        "FWD" if "fwd" in _dt_selected else "FWD",
                                    )
                                    .props(
                                        "flat dense" if "fwd" not in _dt_selected else "unelevated dense color=primary"
                                    )
                                    .style(
                                        "font-size:0.78em; min-width:46px; border-radius:16px;"
                                        + (
                                            " background:#1976D2; color:white;"
                                            if "fwd" in _dt_selected
                                            else " color:#888;"
                                        )
                                    )
                                )
                                dt_rwd_btn = (
                                    ui.button(
                                        "RWD",
                                    )
                                    .props(
                                        "flat dense" if "rwd" not in _dt_selected else "unelevated dense color=primary"
                                    )
                                    .style(
                                        "font-size:0.78em; min-width:46px; border-radius:16px;"
                                        + (
                                            " background:#1976D2; color:white;"
                                            if "rwd" in _dt_selected
                                            else " color:#888;"
                                        )
                                    )
                                )
                                dt_awd_btn = (
                                    ui.button(
                                        "AWD",
                                    )
                                    .props(
                                        "flat dense" if "awd" not in _dt_selected else "unelevated dense color=primary"
                                    )
                                    .style(
                                        "font-size:0.78em; min-width:46px; border-radius:16px;"
                                        + (
                                            " background:#1976D2; color:white;"
                                            if "awd" in _dt_selected
                                            else " color:#888;"
                                        )
                                    )
                                )

                        # Price
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Price (EUR)").style("font-size:0.78em; font-weight:600; color:#666;")
                            _pmin, _pmax = _franges.get("price", (None, None))
                            with ui.row().style("gap:4px;"):
                                filter_price_min = (
                                    ui.number(
                                        "Min",
                                        value=SESSION["filter_price_min"],
                                        min=int(_pmin or 0),
                                        max=int(_pmax or 999999),
                                        step=5000,
                                        format="%.0f",
                                    )
                                    .style("width:90px;")
                                    .props("dense outlined")
                                )
                                filter_price_max = (
                                    ui.number(
                                        "Max",
                                        value=SESSION["filter_price_max"],
                                        min=int(_pmin or 0),
                                        max=int(_pmax or 999999),
                                        step=5000,
                                        format="%.0f",
                                    )
                                    .style("width:90px;")
                                    .props("dense outlined")
                                )

                        # Trunk volume
                        with ui.column().style("gap:2px; min-width:140px;"):
                            ui.label("Trunk (L)").style("font-size:0.78em; font-weight:600; color:#666;")
                            _tmin, _tmax = _franges.get("trunk", (None, None))
                            with ui.row().style("gap:4px;"):
                                filter_trunk_min = (
                                    ui.number(
                                        "Min",
                                        value=SESSION["filter_trunk_min"],
                                        min=int(_tmin or 0),
                                        max=int(_tmax or 99999),
                                        step=50,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )
                                filter_trunk_max = (
                                    ui.number(
                                        "Max",
                                        value=SESSION["filter_trunk_max"],
                                        min=int(_tmin or 0),
                                        max=int(_tmax or 99999),
                                        step=50,
                                        format="%.0f",
                                    )
                                    .style("width:80px;")
                                    .props("dense outlined")
                                )

                        # Reset button
                        with ui.column().style("justify-content:flex-end;"):
                            reset_filters_btn = (
                                ui.button(
                                    "Reset filters",
                                    icon="restart_alt",
                                )
                                .props("flat dense")
                                .style("font-size:0.78em; color:#EF553B;")
                            )

                ranking_container = ui.element("div").style("width:100%;")

        # --- SETTINGS TAB ---
        with dashboard_panels, ui.tab_panel("settings"):
            with ui.card().style("padding:16px; width:100%;"):
                with ui.column().style("gap:24px;"):
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

        table_container.clear()
        with table_container:
            render_consumption_table(vehicles, params, FUEL_CONST, ice_thermal_eff.value, use_per_tire_cb.value)

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
        # Build filter dict from SESSION
        vfilters: dict = {
            k: SESSION[k]
            for k in (
                "filter_length_min",
                "filter_length_max",
                "filter_weight_min",
                "filter_weight_max",
                "filter_clearance_min",
                "filter_clearance_max",
                "filter_drivetrain",
                "filter_price_min",
                "filter_price_max",
                "filter_trunk_min",
                "filter_trunk_max",
            )
        }
        ranking_container.clear()
        with ranking_container:
            render_ranking_list(
                params,
                speed,
                ranking_ev_cb.value,
                ranking_ice_cb.value,
                FUEL_CONST,
                ice_thermal_eff.value,
                use_per_tire_cb.value,
                REPO,
                bool(SESSION["ranking_sort"]),
                vehicle_filters=vfilters,
            )

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

    # --- Filter event handlers ---
    def _on_filter_num(key: str, value) -> None:
        SESSION[key] = value if value else None
        update_ranking()

    filter_weight_min.on_value_change(lambda e: _on_filter_num("filter_weight_min", e.value))
    filter_weight_max.on_value_change(lambda e: _on_filter_num("filter_weight_max", e.value))
    filter_length_min.on_value_change(lambda e: _on_filter_num("filter_length_min", e.value))
    filter_length_max.on_value_change(lambda e: _on_filter_num("filter_length_max", e.value))
    filter_clearance_min.on_value_change(lambda e: _on_filter_num("filter_clearance_min", e.value))
    filter_clearance_max.on_value_change(lambda e: _on_filter_num("filter_clearance_max", e.value))
    filter_price_min.on_value_change(lambda e: _on_filter_num("filter_price_min", e.value))
    filter_price_max.on_value_change(lambda e: _on_filter_num("filter_price_max", e.value))
    filter_trunk_min.on_value_change(lambda e: _on_filter_num("filter_trunk_min", e.value))
    filter_trunk_max.on_value_change(lambda e: _on_filter_num("filter_trunk_max", e.value))

    def _toggle_drivetrain(dt_val: str, btn) -> None:
        sel: list[str] = SESSION.get("filter_drivetrain", [])  # type: ignore[assignment]
        if dt_val in sel:
            sel.remove(dt_val)
            btn.props("flat dense")
            btn.style("font-size:0.78em; min-width:46px; border-radius:16px; color:#888;")
        else:
            sel.append(dt_val)
            btn.props("unelevated dense color=primary")
            btn.style("font-size:0.78em; min-width:46px; border-radius:16px; background:#1976D2; color:white;")
        update_ranking()

    dt_fwd_btn.on_click(lambda: _toggle_drivetrain("fwd", dt_fwd_btn))
    dt_rwd_btn.on_click(lambda: _toggle_drivetrain("rwd", dt_rwd_btn))
    dt_awd_btn.on_click(lambda: _toggle_drivetrain("awd", dt_awd_btn))

    def _reset_filters() -> None:
        SESSION["filter_length_min"] = None
        SESSION["filter_length_max"] = None
        SESSION["filter_weight_min"] = None
        SESSION["filter_weight_max"] = None
        SESSION["filter_clearance_min"] = None
        SESSION["filter_clearance_max"] = None
        SESSION["filter_drivetrain"] = []
        SESSION["filter_price_min"] = None
        SESSION["filter_price_max"] = None
        SESSION["filter_trunk_min"] = None
        SESSION["filter_trunk_max"] = None
        # Reset UI inputs
        filter_weight_min.set_value(None)
        filter_weight_max.set_value(None)
        filter_length_min.set_value(None)
        filter_length_max.set_value(None)
        filter_clearance_min.set_value(None)
        filter_clearance_max.set_value(None)
        filter_price_min.set_value(None)
        filter_price_max.set_value(None)
        filter_trunk_min.set_value(None)
        filter_trunk_max.set_value(None)
        # Reset drivetrain buttons
        for btn in (dt_fwd_btn, dt_rwd_btn, dt_awd_btn):
            btn.props("flat dense")
            btn.style("font-size:0.78em; min-width:46px; border-radius:16px; color:#888;")
        update_ranking()

    reset_filters_btn.on_click(_reset_filters)

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

    map_route_page()


@ui.page("/route/manual")
def manual_route_page() -> None:
    from app.ui.pages.route_planner import route_page

    route_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Vehicle Consumption Analyzer", port=8080, reload=False)
