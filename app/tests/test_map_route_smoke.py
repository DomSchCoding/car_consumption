"""Smoke tests for map route planner UI modules."""

from __future__ import annotations


class TestMapRoutePageImport:
    def test_map_route_page_imports(self) -> None:
        from app.ui.pages.map_route_planner import map_route_page

        assert callable(map_route_page)

    def test_manual_route_page_still_imports(self) -> None:
        from app.ui.pages.route_planner import route_page

        assert callable(route_page)

    def test_route_controls_construct_without_provider(self) -> None:
        from app.services.routing import DemoRoutingProvider

        provider = DemoRoutingProvider()
        status = provider.status()
        assert status.name == "demo"
        assert status.available is True

    def test_map_widget_imports(self) -> None:
        from app.ui.components.map_widget import (
            create_route_map,
            draw_route_polyline,
        )

        assert callable(create_route_map)
        assert callable(draw_route_polyline)

    def test_route_summary_imports(self) -> None:
        from app.ui.components.route_summary import build_energy_table

        assert callable(build_energy_table)
