# 03 - Map route feature specification v3

## Product vision

The user experience should feel like a simplified route planner:

```text
Start eingeben -> Ziel eingeben -> Route berechnen -> Karte sehen -> Verbrauch fuer ausgewaehlte Autos sehen
```

The user should not need to know distance, average speed or elevation beforehand. The app derives them.

## Primary user flow

1. User selects one or more vehicles on the dashboard.
2. User opens `Route`.
3. User enters start and destination text fields.
4. User clicks `Find route`.
5. App geocodes start/destination and shows candidates if ambiguous.
6. App calculates a route.
7. App displays:
   - map with start marker, destination marker, route polyline
   - route summary: distance, duration, average speed, elevation gain/loss
   - one-way / return-trip toggle
   - energy comparison table
   - energy breakdown stacked chart
   - elevation profile and speed profile
8. User changes vehicle selection or physics/environment settings and results update without re-fetching route.

## Required UI controls

### Basic controls

```text
Start address / place
Destination address / place
Route profile: car fastest, car shorter, highway avoid later
Button: Calculate route
Checkbox: Return trip
Checkbox: Recalculate return route separately (future)
Checkbox: Use same route reversed for return (MVP)
```

### Advanced controls

```text
Provider: Demo / ORS / OSRM / Valhalla
Temperature [C]
Headwind along route [km/h] or simple outward headwind
Payload [kg]
Aux override [kW]
Regeneration efficiency downhill
Regeneration efficiency stop-go
Segmentization resolution [m]
Force refresh / use cache
```

## Map interactions

MVP:

- show map centered on route
- show start and end markers
- show route polyline
- allow address text input

Phase 2:

- click map to set start/destination
- draggable markers
- optional via points
- route alternatives
- save favorite commute routes

## Route result cards

Top cards should show:

```text
Distance: 23.4 km
Duration: 31 min
Average speed: 45 km/h
Elevation gain/loss: +280 m / -120 m
Return mode: one-way / there-and-back
Provider: ORS, cache hit/miss
Data quality: speed estimated, elevation sampled every X m
```

## Energy output

For each selected vehicle:

```text
kWh one-way
kWh return trip
kWh/100 km route-normalized
battery percent per trip
trips per charge
estimated cost per trip
breakdown: aero, roll, aux, climb, stop-go, recovered descent, drivetrain losses
```

## Warnings

Show warnings, not hidden logs:

```text
Elevation unavailable: using flat route.
Speed profile unavailable: using average speed from route duration.
Stop frequency estimated from road classes/intersections.
Return route is approximated by reversing outward route.
External provider unavailable: using cached result / demo route.
```

## Acceptance criteria

- A non-technical user can enter start and destination and get a map route.
- The old manual route planner remains accessible.
- No API key is required to see a demo route and UI behavior.
- Route-derived speed/elevation can be inspected and manually overridden later.
- Energy results are traceable to route segments.
