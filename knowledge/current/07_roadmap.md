# 07 - Roadmap

## Phase A - Stabilize current route foundation (DONE)

- [x] Keep manual route planner as `/route/manual`
- [x] Add regression tests around current route_energy behavior
- [x] Add route fixtures
- [x] Add route provider model classes

## Phase B - Map Route MVP without external API (DONE)

- [x] Add `map_route_planner.py`
- [x] Add `ui.leaflet` map display
- [x] Add `DemoRoutingProvider` with 3 fixture routes (city, hilly, highway)
- [x] Draw polyline and markers
- [x] Convert fixture ProviderRoute to RouteSegments
- [x] Calculate energy for selected vehicles
- [x] Show elevation and speed charts
- [x] Show energy breakdown table and stacked bars
- [x] Route cache (file-based, `.cache/routes/`)
- [x] Provider status display
- [x] Round-trip / one-way toggle
- [x] Demo route selection

## Phase C - OpenRouteService integration

- [ ] Add `httpx` dependency
- [ ] Implement ORS geocoder
- [ ] Implement ORS routing provider
- [ ] Implement ORS elevation or elevation enrichment
- [ ] Add env-based API key loading
- [ ] Use route cache for ORS responses
- [ ] Add provider status UI for real provider

## Phase D - OSRM + elevation fallback

- [ ] Implement OSRM route provider
- [ ] Implement Open-Meteo or Open-Elevation provider
- [ ] Add warning when elevation is sampled separately
- [ ] Compare ORS vs OSRM route-derived energy on same start/destination

## Phase E - Better route physics

- [ ] Bearing-based wind projection
- [ ] Return trip as separate route request option
- [ ] Regen power cap on descents
- [ ] Better stop estimation from route steps/road classes
- [ ] Separate speed scenarios: free-flow, typical commute, congestion

## Phase F - Saved commute routes and economics

- [ ] Save named commute routes locally
- [ ] Calculate monthly/yearly energy and cost
- [ ] Add charging cost, home/work tariffs
- [ ] Combine with used/new price data and range-per-euro metrics

## Phase G - GPX import

- [ ] Import GPX track with elevation
- [ ] Optionally map-match or use track geometry
- [ ] Compare recorded route vs provider route

## Current priorities

Next up: Phase C (ORS integration) when ready. No rush — demo provider covers offline use.