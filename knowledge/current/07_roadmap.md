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

## Phase C - Live route prototype: Nominatim + OSRM + Open-Meteo (DONE)

- [x] Add `httpx` and `geopy` dependencies
- [x] Implement Nominatim geocoding (rate-limited to 1 req/s, cached)
- [x] Implement OSRM routing provider (cached, GeoJSON parsing)
- [x] Implement Open-Meteo elevation provider (resampled, capped at 50 pts, cached)
- [x] Add env-based feature flags (all disabled by default)
- [x] Chain geocode → route → elevation in `route_live()`
- [x] Provider mode selector in UI (Demo offline / Live prototype)
- [x] Provider warnings and attribution in UI
- [x] 42 new tests (config, parsing, caching, disabled providers, demo back-compat)

## Phase D - ORS integration (future)

- [ ] Implement ORS routing provider (requires API key)
- [ ] Implement ORS elevation or elevation enrichment
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

Phase C complete. Next: Phase D (ORS with API key) or Phase E (better physics).