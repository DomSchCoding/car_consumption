# 01 - Product Vision

## Core idea

Physics-based vehicle consumption analyzer that answers:

> Why does this car consume so much on my commute in winter, while another car with similar WLTP figures is much better?

Not just "which car consumes what at 100 km/h" but real route-based analysis.

## Two route concepts

### v2 Route = Expert Mode (implemented)

Manual parameter input for expert users:

- distance, average speed, elevation gain/loss, stops, wind, temperature
- segment editor for detailed routes
- one-way or return trip with wind inversion
- useful for debugging, verified scenarios, and quick estimates

### v3 Route = Map Route (target)

Google-Maps-like UX for end users:

- enter start and destination addresses
- see route on map
- automatic distance, elevation, speed derivation
- one-way / round-trip toggle
- energy breakdown using existing physics core

The manual route planner stays as `/route/manual`. The map route planner becomes `/route`.

## Target users

1. **Technically curious EV drivers** - want to understand consumption variation
2. **Car buyers** - want real range estimates for specific commute, winter, highway
3. **Didactic users** - want to understand aero, mass, temperature, regen physics
4. **Data/tech users** - want to add vehicles, import routes, check sources

## Product principles

- Physically traceable, not a black box
- Defaults visible and editable
- Sources and confidence visible
- Demo data clearly marked
- Charts explain, not just impress
- Route planner feels like a route planner, not a physics form

## Energy output per route

For each selected vehicle on a route:

```text
kWh one-way
kWh return trip
kWh/100 km route-normalized
battery percent per trip
trips per charge
estimated cost per trip
breakdown: aero, roll, aux, climb, stop-go, recovered descent, drivetrain losses
```

## Warnings (not hidden)

```text
Elevation unavailable: using flat route.
Speed profile unavailable: using average speed from route duration.
Stop frequency estimated from road classes/intersections.
Return route is approximated by reversing outward route.
External provider unavailable: using cached result / demo route.
```