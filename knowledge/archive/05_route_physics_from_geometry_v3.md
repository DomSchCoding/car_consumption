# 05 - Route physics from geometry v3

## Goal

Turn a real routed polyline into physically useful route segments without overclaiming precision.

## Required calculations

### Distance

Use haversine distance between consecutive geometry points for internal validation, but prefer provider summary distance if available. Store both if they differ significantly.

### Elevation gain/loss

For consecutive points with elevation:

```text
delta_h = h[i+1] - h[i]
if delta_h > threshold: gain += delta_h
if delta_h < -threshold: loss += abs(delta_h)
```

Use a small threshold or smoothing to avoid noisy DEM oscillations. Start conservative, e.g. ignore changes below 1-2 m per sample.

### Speed profile

Priority:

1. provider step duration and distance -> average speed per step
2. provider annotations if available -> detailed speed
3. whole route duration and distance -> average speed fallback
4. road-type default speeds as last fallback

Do not label speed as exact if it is derived.

### Stop frequency

MVP:

- infer rough stops per km from road type and low speed sections
- city: higher default
- rural: low default
- highway: zero default

Future:

- use intersections/traffic signals from OSM if a provider exposes them
- allow manual stop multiplier

### Elevation energy

Use existing logic:

```text
E_climb = m * g * elevation_gain / 3_600_000
E_descent_available = m * g * elevation_loss / 3_600_000
E_descent_recovered = E_descent_available * eta_regen_downhill
```

Return trip with same reversed route:

- geometry order reversed
- gain/loss swapped per segment
- wind can optionally invert
- route distance remains the same

Future return-trip mode:

- request a separate route from destination to start, because real roads can be asymmetric.

## Route segmentization

The segmentizer should avoid both extremes:

- one huge average segment hides speed/elevation detail
- thousands of tiny segments make UI and tests noisy

Recommended default:

```text
sample route every 100-250 m for elevation/profile charts
aggregate physics segments around 0.5-2.0 km or by step boundaries
split when slope or speed changes materially
```

## Energy accuracy caveats

The route model can explain relative differences very well, but absolute values depend on:

- real driving speed vs provider duration
- traffic
- stops
- wind direction vs route bearing
- temperature and HVAC
- tire pressure and road surface
- payload
- battery temperature and SoC
- driver behavior

UI must expose these caveats in a concise way.

## Future physics extensions

1. Wind by route bearing:
   - compute bearing per segment
   - project wind vector onto route direction
   - use effective headwind in aero formula

2. Acceleration model:
   - not just stop count, but acceleration phases
   - support urban route with many low-speed starts

3. Regen limits:
   - lower regen when battery cold or SoC high
   - cap downhill regen by max regen power
   - friction braking fallback on steep descents

4. Road grade effects:
   - steep climbs increase energy immediately
   - steep descents may exceed regen cap

5. Weather/air density:
   - altitude and temperature-derived air density
   - rain/wet road rolling penalty

6. Traffic scenarios:
   - free-flow vs typical commute vs congestion
   - same route with different speed profiles
