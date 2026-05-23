# Vehicle Consumption Analyzer

Physics-based web application for analyzing and comparing vehicle energy
consumption, with focus on electric vehicles, aerodynamics, rolling resistance,
auxiliary consumers, and ICE comparison.

## Quick Start

```bash
# Create virtual environment (if not already done)
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start the web application
python -m app.main
```

Open http://localhost:8080 in your browser.

## Project Structure

```
app/
  main.py                # NiceGUI web application entry point
  core/
    physics.py           # Pure physics calculation functions
    route_energy.py      # Route energy calculation, commute scenarios
  data/
    models.py            # Pydantic data models (Vehicle, Route, PhysicsParams, ...)
    repository.py         # Vehicle data loading from YAML
  ui/
    charts.py            # Plotly chart construction
    state.py             # Session state management
    tables.py            # HTML table construction
    components/
      vehicle_selector.py # Reusable vehicle selection component
    pages/
      route_planner.py   # Manual/expert route planner (current /route)
  tests/
    test_physics.py       # Physics module tests
    test_repository.py    # Repository tests
    test_route_energy.py  # Route energy tests
    test_ui_smoke.py      # UI smoke tests
  assets/
    sample_vehicles.yaml  # Demo vehicle data
    fuel_constants.yaml   # Fuel energy densities
knowledge/
  current/                # Authoritative agent context (see AGENTS.md)
  archive/                # Historical knowledge files
AGENTS.md                  # Agent guidance and project rules
```

## Route Planner

### Current: Manual Route Planner (`/route`)

Enter route parameters directly:

- distance, average speed, elevation gain/loss per segment
- stops per km, dwell time, wind, temperature
- one-way or return trip with wind inversion
- segment editor for detailed routes
- energy breakdown: aero, roll, aux, climb, stop-go, regen, drivetrain loss

### Planned: Map Route Planner (`/route`, replacing manual)

Google-Maps-like experience:

- enter start and destination addresses
- see route on map with automatic distance, elevation, speed derivation
- one-way / round-trip toggle
- manual route planner remains at `/route/manual` for experts

## Physics Model

### Aerodynamic Drag

```
F_aero = 0.5 * rho_air * Cd * A * v^2
```

- `rho_air`: Air density (default 1.225 kg/m3 at 15C, sea level)
- `Cd`: Drag coefficient (cw value)
- `A`: Frontal area in m2
- `v`: Speed in m/s

Energy per 100 km: `F_aero * 100000 / 3_600_000` kWh

Aerodynamic energy scales with **v^2** per distance. Power scales with **v^3**.

### Rolling Resistance

```
F_roll = c_rr * mass * g
```

- `c_rr`: Rolling resistance coefficient (default 0.009)
- `mass`: Vehicle mass in kg
- `g`: Gravitational acceleration (9.81 m/s2)

Energy per 100 km: `F_roll * 100000 / 3_600_000` kWh

Rolling resistance is **independent of speed** for constant c_rr.

### Auxiliary Consumers

```
kWh/100km = P_aux_kW / speed_kmh * 100
```

- `P_aux_kW`: Auxiliary power in kW (climate, electronics, etc.)

Auxiliary consumption is **inversely proportional to speed** at constant power.

### Drivetrain Efficiency

```
battery_kWh = wheel_kWh / eta_drivetrain
```

- `eta_drivetrain`: Drivetrain efficiency (default 0.92)

### ICE Comparison

Chemical energy from fuel:

```
kWh/100km = liters/100km * kWh_per_liter
```

Estimated wheel energy:

```
wheel_kWh = chemical_kWh * thermal_efficiency
```

- Gasoline: ~8.9 kWh/liter (LHV)
- Diesel: ~9.7 kWh/liter (LHV)
- Typical thermal efficiency: 0.25-0.40 (Otto), 0.35-0.45 (Diesel)

**Important**: 1 l/100 km is NOT directly comparable to battery kWh/100 km
because thermal efficiency differs significantly.

### Route Energy

The route model extends the basic physics with:

- Per-segment calculation (distance, speed, elevation, stops, wind)
- Elevation gain/loss with regenerative recovery
- Stop-and-go energy modeling
- One-way and return-trip modes (return swaps gain/loss)
- Wind component per segment

## Unit Conversions

| From | To | Formula |
|------|-----|---------|
| km/h | m/s | / 3.6 |
| m/s | km/h | * 3.6 |
| Wh/km | kWh/100 km | / 10 |
| kWh/100 km | Wh/km | * 10 |
| kWh/100 mi | kWh/100 km | / 1.609344 |
| kWh/100 km | kWh/100 mi | * 1.609344 |

## Sample Vehicles

The included `sample_vehicles.yaml` contains demo data for:

- **Hyundai Ioniq 28 kWh** - Compact, efficient EV
- **Tesla Model 3 RWD** - Mid-size efficient sedan
- **VW ID.3 Pro** - Compact EV, higher frontal area
- **VW ID. Buzz** - Electric van/bus, large frontal area
- **VW Golf 2.0 TDI** - Diesel ICE reference
- **VW Crafter 35** - Delivery van reference

Values without verified sources are marked as "demo" and should be treated as
conservative estimates.

## Configuration

All physics parameters are editable in the UI:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Air density | 1.225 kg/m3 | 0.5-1.5 | Depends on altitude, temperature |
| c_rr | 0.009 | 0.003-0.020 | Rolling resistance coefficient |
| Aux power | 1.5 kW | 0-10 | Climate, electronics, etc. |
| Drivetrain eta | 0.92 | 0.5-1.0 | Motor + inverter + gearbox |
| ICE thermal eff | 0.30 | 0.1-0.5 | Engine thermal efficiency |

## Development

```bash
# Run tests
pytest

# Lint
ruff check app/

# Format
ruff format app/

# Type check
pyright app/
```

## Data Sources Strategy

1. Official manufacturer data (preferred for Cd, dimensions, mass, battery)
2. EPA/fueleconomy.gov (official US consumption data)
3. EV Database (real-world EV consumption, check terms of use)
4. Wikipedia/Automobil-Guru (supplementary Cd/frontal area, lower confidence)
5. Community/test data (only with documented conditions)

**Never scrape blindly** - always check robots.txt, terms of use, and license.

## Agent Context

The `knowledge/current/` directory contains the authoritative knowledge base
for agentic development. See `AGENTS.md` for the full index and mandatory
agent principles.

## Planned Features

- Map-based route planner with geocoding and elevation
- Real route providers (OpenRouteService, OSRM)
- Route caching and offline demo mode
- Acceleration profiles and regenerative braking
- Temperature effects on battery and consumption
- Wind and elevation profiles from route geometry
- Tire model selection
- Payload effects
- GPX/CSV import