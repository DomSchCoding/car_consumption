# 07 - Roadmap

## Phase A - Stabilize current route foundation

- Keep manual route planner as `/route/manual`
- Add regression tests around current route_energy behavior
- Add route fixtures
- Add route provider model classes

## Phase B - Map Route MVP without external API

- Add `map_route_planner.py`
- Add `ui.leaflet` map display
- Add `DemoRoutingProvider` with 2-3 fixture routes
- Draw polyline and markers
- Convert fixture ProviderRoute to RouteSegments
- Calculate energy for selected vehicles
- Show elevation and speed charts
- Show energy breakdown table and stacked bars

## Phase C - OpenRouteService integration

- Add `httpx` dependency
- Implement ORS geocoder
- Implement ORS routing provider
- Implement ORS elevation or elevation enrichment
- Add env-based API key loading
- Add route cache
- Add provider status UI

## Phase D - OSRM + elevation fallback

- Implement OSRM route provider
- Implement Open-Meteo or Open-Elevation provider
- Add warning when elevation is sampled separately
- Compare ORS vs OSRM route-derived energy on same start/destination

## Phase E - Better route physics

- Bearing-based wind projection
- Return trip as separate route request option
- Regen power cap on descents
- Better stop estimation from route steps/road classes
- Separate speed scenarios: free-flow, typical commute, congestion

## Phase F - Saved commute routes and economics

- Save named commute routes locally
- Calculate monthly/yearly energy and cost
- Add charging cost, home/work tariffs
- Combine with used/new price data and range-per-euro metrics

## Phase G - GPX import

- Import GPX track with elevation
- Optionally map-match or use track geometry
- Compare recorded route vs provider route

## Prioritized next implementation order

1. provider models
2. cache
3. demo routing provider
4. map page
5. provider route -> segments conversion
6. charts and table
7. tests

Do not start with a live API first. Build demo/offline first, then plug in ORS.