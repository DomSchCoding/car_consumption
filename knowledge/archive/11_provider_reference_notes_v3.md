# 11 - Provider reference notes v3

These notes guide implementation; always verify current API docs when coding.

## NiceGUI Leaflet

NiceGUI has a `ui.leaflet` element for Leaflet maps. It supports map options and draw controls. Use it as the first map implementation because the project already uses NiceGUI.

## OpenRouteService

OpenRouteService and `openrouteservice-py` can access directions, isochrones, matrix calculations, places, elevation and Pelias geocoding/autocomplete. This makes it the best first real provider candidate.

## OSRM

OSRM is a fast route engine and exposes route APIs with geometry, duration, steps and distance. It does not solve elevation by itself in the standard API path, so pair it with an elevation provider.

## Elevation providers

Options:

- OpenRouteService elevation service
- Open-Meteo Elevation API
- Open-Elevation
- OpenTopoData self-hosting
- Valhalla elevation if Valhalla is used

Elevation providers differ in quota, attribution, resolution and self-hosting options. The app must show warnings and provider status.

## Valhalla

Valhalla is an interesting future option because route responses can include shape and elevation-related options. Treat it as Phase D/E unless there is a strong reason to implement it earlier.
