# Project Overview - Vehicle Consumption Analyzer

## Project Goal
A physics-based NiceGUI web application for analyzing and comparing vehicle energy consumption, focusing on electric vehicles. The app calculates theoretical minimum energy consumption from vehicle parameters (aerodynamics, rolling resistance, auxiliary consumers) and compares them with real-world WLTP/EPA data and ICE vehicles.

## Core Principles
- Physics first, real data second for plausibility checks
- Every data point has source, date, unit, confidence level
- No silent assumptions - defaults must be visible and editable
- Reproducibility - calculations and UI state should be testable
- Local development without external services

## Architecture Overview

```
app/
  main.py              # NiceGUI entry point - UI orchestration
  core/
    physics.py         # Pure calculation functions (no dependencies)
  data/
    models.py          # Pydantic data models (Vehicle, SourceRef, etc.)
    repository.py      # YAML data loading and vehicle queries
  assets/
    sample_vehicles.yaml  # 6 demo vehicles with source references
    fuel_constants.yaml   # Gasoline/Diesel energy densities
  tests/
    test_physics.py    # 35 physics calculation tests
    test_repository.py # 9 data loading tests
```

### Module Dependencies
```
main.py
  -> core/physics.py (calculations)
  -> data/models.py (types: Vehicle, PhysicsParams, FuelConstants)
  -> data/repository.py (VehicleRepository, load_fuel_constants)

data/repository.py
  -> data/models.py (Vehicle, FuelConstants)
  -> app/assets/*.yaml (data files)

core/physics.py
  -> (no internal dependencies - pure functions)
```

### Data Flow
1. YAML files -> VehicleRepository -> Vehicle objects
2. UI selects vehicles + sets parameters
3. physics.py calculates consumption curves
4. Plotly renders chart, HTML renders table

## Technology Stack
- Python 3.12+
- NiceGUI 3.x (web UI)
- Plotly (interactive charts)
- Pydantic 2.x (data validation)
- PyYAML (data files)
- pytest (testing)
- ruff (linting/formatting)
- pyright (type checking)

## Current Status (Sprint 2 Complete)
- [x] Project structure and pyproject.toml
- [x] Python 3.12 venv in `.venv/`
- [x] Physics module with 35 passing tests
- [x] Pydantic data models (with YAML int->str coercion)
- [x] YAML sample data (60 vehicles, 22 brands)
- [x] Vehicle repository
- [x] NiceGUI MVP with modern UI:
  - ⚙️ Settings-Menü (ausklappbar): Parameters, Speed Range, ICE Comparison
  - 🚗 Vehicle Selection Card:
    - EV/ICE Checkboxen (Filter)
    - Marken-Dropdown (gefiltert nach EV/ICE)
    - Modell-Liste mit +/- Buttons (scrollbar)
    - Ausgewählte Fahrzeuge mit 🗑️ Remove (scrollbar)
  - Chart: Clean total-consumption curves, hover breakdown
  - Table: Consumption at 50/80/100/130 km/h
  - 📊 Consumption Ranking: Speed dropdown, EV/ICE filter, sorted bar list
- [x] ICE comparison (chemical vs wheel energy)
- [x] README.md
- [x] Ruff lint + format clean
- [x] 44 tests passing
- [x] Knowledge docs (6 files)

## Pending Tasks
- [ ] Phase 2: Acceleration profiles, regenerative braking
- [ ] Temperature effects on battery and consumption
- [ ] Wind and elevation profiles
- [ ] Tire model selection
- [ ] Payload effects
- [ ] Data import from EPA/fueleconomy.gov
- [ ] Data quality dashboard
- [ ] More vehicles with verified sources
- [ ] Scenario editor page
- [ ] Vehicle detail page with sources

## Quick Start
```bash
source .venv/bin/activate
python -m app.main
# Open http://localhost:8080
```

## Knowledge Files
- [Physics Module](physics_module.md) - Core calculation functions
- [Data Module](data_module.md) - Models, repository, YAML structure
- [UI Module](ui_module.md) - NiceGUI frontend architecture
- [Testing Strategy](testing_strategy.md) - Test organization and coverage
