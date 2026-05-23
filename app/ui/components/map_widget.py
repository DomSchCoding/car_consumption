"""Map widget helpers for NiceGUI Leaflet integration.

Wraps ui.leaflet operations to avoid scattering raw JavaScript across pages.
Uses NiceGUI Leaflet layer API (marker, generic_layer) instead of run_method JS.
"""

from __future__ import annotations

import contextlib

from nicegui import ui

_ROUTE_LAYERS_KEY = "_route_layers"


def create_route_map(center: tuple[float, float] = (48.2, 16.37), zoom: int = 10) -> ui.leaflet:
    leaflet = ui.leaflet(center=center, zoom=zoom).classes("w-full").style("height: 400px; border-radius: 8px;")
    leaflet._route_layers = []
    return leaflet


def draw_route_polyline(
    leaflet: ui.leaflet, points: list[tuple[float, float]], color: str = "#636EFA", weight: int = 4
) -> None:
    if not points or len(points) < 2:
        return
    coords = [[lat, lon] for lat, lon in points]
    options = {"color": color, "weight": weight, "opacity": 0.8}
    layer = leaflet.generic_layer(name="polyline", args=[coords, options])
    leaflet._route_layers.append(layer)


def set_start_end_markers(leaflet: ui.leaflet, start: tuple[float, float], end: tuple[float, float]) -> None:
    start_marker = leaflet.marker(latlng=start, options={"title": "Start"})
    end_marker = leaflet.marker(latlng=end, options={"title": "Destination"})
    leaflet._route_layers.append(start_marker)
    leaflet._route_layers.append(end_marker)


def fit_bounds(leaflet: ui.leaflet, points: list[tuple[float, float]], padding: float = 0.01) -> None:
    if not points:
        return
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    min_lat, max_lat = min(lats) - padding, max(lats) + padding
    min_lon, max_lon = min(lons) - padding, max(lons) + padding
    leaflet.run_map_method("fitBounds", [[min_lat, min_lon], [max_lat, max_lon]])


def clear_route_layer(leaflet: ui.leaflet) -> None:
    for layer in getattr(leaflet, "_route_layers", []):
        with contextlib.suppress(ValueError, KeyError):
            leaflet.remove_layer(layer)
    leaflet._route_layers = []
