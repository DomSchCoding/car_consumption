# Physics Module - `app/core/physics.py`

## Purpose
Pure calculation functions for vehicle energy consumption. No external dependencies, no side effects. All functions operate on basic numeric types (float).

## Constants
| Constant | Value | Description |
|----------|-------|-------------|
| `G` | 9.81 | Gravitational acceleration (m/s2) |
| `JOULES_PER_KWH` | 3,600,000 | Joules per kWh |
| `METERS_PER_100KM` | 100,000 | Meters in 100 km |

## Data Classes

### `ConsumptionBreakdown`
Frozen dataclass holding the consumption breakdown at a single speed:
- `aero_kwh_per_100km` - Aerodynamic drag contribution
- `roll_kwh_per_100km` - Rolling resistance contribution
- `aux_kwh_per_100km` - Auxiliary consumers contribution
- `total_wheel_kwh_per_100km` - Sum of above (energy at wheels)
- `total_battery_kwh_per_100km` - Wheel energy / drivetrain efficiency

## Unit Conversion Functions

| Function | Input | Output | Formula |
|----------|-------|--------|---------|
| `kmh_to_ms` | km/h | m/s | `/ 3.6` |
| `ms_to_kmh` | m/s | km/h | `* 3.6` |
| `wh_per_km_to_kwh_per_100km` | Wh/km | kWh/100km | `/ 10` |
| `kwh_per_100km_to_wh_per_km` | kWh/100km | Wh/km | `* 10` |
| `kwh_per_100mi_to_kwh_per_100km` | kWh/100mi | kWh/100km | `/ 1.609344` |
| `kwh_per_100km_to_kwh_per_100mi` | kWh/100km | kWh/100mi | `* 1.609344` |
| `force_to_kwh_per_100km` | Newton | kWh/100km | `F * 100000 / 3600000` |

## Core Physics Functions

### Aerodynamics
```python
aero_force(rho_air, cd, frontal_area_m2, speed_ms) -> float
```
Formula: `F = 0.5 * rho * Cd * A * v^2`

```python
aero_consumption(rho_air, cd, frontal_area_m2, speed_kmh) -> float
```
Returns kWh/100km from aerodynamic drag.

**Key property**: Energy per distance scales with v^2. Power scales with v^3.

### Rolling Resistance
```python
roll_force(mass_kg, c_rr) -> float
```
Formula: `F = c_rr * mass * g`

```python
roll_consumption(mass_kg, c_rr) -> float
```
Returns kWh/100km from rolling resistance.

**Key property**: Independent of speed (for constant c_rr). Scales linearly with mass and c_rr.

### Auxiliary Consumers
```python
aux_consumption(p_aux_kw, speed_kmh) -> float
```
Formula: `kWh/100km = P_aux_kW / speed_kmh * 100`

**Key property**: Inversely proportional to speed. Returns inf at speed=0.

### Drivetrain
```python
drivetrain_loss(wheel_kwh_per_100km, eta_drivetrain) -> float
```
Formula: `battery = wheel / eta`

Returns inf at eta=0.

### Combined Calculation
```python
total_consumption(
    rho_air, cd, frontal_area_m2, mass_kg, c_rr,
    p_aux_kw, speed_kmh, eta_drivetrain=1.0
) -> ConsumptionBreakdown
```
Calculates all components and returns a complete breakdown.

```python
consumption_curve(
    rho_air, cd, frontal_area_m2, mass_kg, c_rr,
    p_aux_kw, speed_min_kmh, speed_max_kmh,
    steps=50, eta_drivetrain=1.0
) -> list[ConsumptionBreakdown]
```
Calculates consumption over a speed range with evenly spaced steps.

## ICE Comparison Functions

```python
fuel_liters_to_kwh(liters, kwh_per_liter) -> float
fuel_consumption_to_kwh_per_100km(liters_per_100km, kwh_per_liter) -> float
fuel_wheel_energy(liters_per_100km, kwh_per_liter, thermal_efficiency) -> float
```

## Test Coverage
35 tests in `app/tests/test_physics.py`:
- Unit conversions (roundtrip tests)
- Force to energy conversion
- Aerodynamics (v^2 scaling, CdA doubling, power v^3)
- Rolling resistance (linear mass/c_rr scaling, speed independence)
- Aux consumption (inverse speed, zero speed = inf)
- Drivetrain (efficiency effects, zero = inf)
- Total consumption (component sum, battery >= wheel)
- Consumption curve (point count, monotonic at higher speeds)
- Fuel conversions

## Entry Points for Other Modules
- `main.py` calls `consumption_curve()` and `total_consumption()`
- No other module imports physics functions directly
