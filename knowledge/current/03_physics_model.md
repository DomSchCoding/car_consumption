# 03 - Physics Model

## Energy levels

Always distinguish:

1. Wheel energy / mechanical work
2. Battery energy (EV)
3. Grid energy including charging losses (optional)
4. Chemical energy in fuel (ICE)
5. Useful energy at wheel (ICE)

## Aerodynamic drag

```text
v_vehicle = avg_speed_kmh / 3.6
v_air = max(0, v_vehicle + headwind_component)
F_aero = 0.5 * rho_air * CdA * v_air^2
E_aero = F_aero * distance_m
```

Aero consumption scales with v^2 per distance. Power scales with v^3.

## Rolling resistance

```text
F_roll = c_rr * mass_total * g
E_roll = F_roll * distance_m
```

MVP: constant c_rr. Tire classes eco_lrr/standard/sport/suv/van_truck available.

## Auxiliary consumers

```text
time_total_h = distance_km / avg_speed_kmh + dwell_time_min / 60
E_aux_kWh = P_aux_kW * time_total_h
```

## Drivetrain efficiency

```text
E_battery_drive = E_wheel_positive / eta_drivetrain
```

MVP: constant efficiency. Later: speed/load-dependent map.

## Elevation energy

```text
E_climb = mass_total * g * elevation_gain_m / 3_600_000
E_descent_available = mass_total * g * elevation_loss_m / 3_600_000
E_descent_recovered = E_descent_available * eta_regen_downhill
```

Key insight: return trip has net-zero elevation difference, but positive energy loss because downhill recovery is incomplete.

MVP: eta_regen_downhill editable, conservative default 0.50-0.70. Zero for non-hybrid ICE.

## Stop-and-go

```text
E_kin_per_stop = 0.5 * mass_total * v_stop^2
E_accel_from_battery = E_kin_per_stop / eta_drive
E_recovered = E_kin_per_stop * eta_regen_stop
E_stop_net = E_accel_from_battery - E_recovered
E_stop_go = stops * max(0, E_stop_net)
```

Default stop speed by road type:

```text
city: 35 km/h
suburban: 50 km/h
rural: 70 km/h
highway: 0 stops (or very few)
```

## Stop frequency estimation for map routes

When speed profile is not detailed:

```text
city: ~2 stops per km
rural: ~0.2 stops per km
highway: ~0 stops per km
```

Future: use intersections/traffic signals from OSM if provider exposes them.

## Route segment calculation

Per segment:

```text
time_h = distance_km / avg_speed_kmh
aero, roll, aux, climb, descent recovery, stop-go, drivetrain loss
total_wheel_kWh = aero + roll + aux + climb + stop_go - descent_recovered
total_battery_kWh = positive_wheel_energy / eta_drivetrain + aux - stop_regen_recovered_already_accounted
```

Sum across segments for route total.

## Return trip

Return route reverses segment order and swaps:

```text
return_segment.elevation_gain = segment.elevation_loss
return_segment.elevation_loss = segment.elevation_gain
return_segment.headwind = -segment.headwind  # optional
return_segment.distance = segment.distance      # same
return_segment.avg_speed = segment.avg_speed    # same unless overridden
```

Future: request separate return route from provider for asymmetric real roads.

## Wind projection from route bearing (future)

```text
bearing per segment from geometry points
project wind vector onto route direction
effective headwind = wind_speed * cos(bearing_segment - wind_direction)
```

## Model limitations

Do not overclaim precision. Results depend on:

- real driving speed vs provider duration
- traffic conditions
- stop frequency estimation
- wind direction vs route bearing
- temperature and HVAC
- tire pressure and road surface
- payload
- battery temperature and SoC
- driver behavior

Label estimated values as estimated in UI.