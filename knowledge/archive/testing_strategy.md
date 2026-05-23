# Testing Strategy

## Test Organization
```
app/tests/
  test_physics.py      # 35 tests - Core physics calculations
  test_repository.py   # 9 tests - Data loading and models
```

## Running Tests
```bash
.venv/bin/pytest app/tests/ -v       # Verbose
.venv/bin/pytest app/tests/ -q       # Quiet
.venv/bin/pytest app/tests/test_physics.py -v  # Single file
```

## Physics Tests (`test_physics.py`)

### TestUnitConversions (8 tests)
- km/h <-> m/s conversion
- Wh/km <-> kWh/100km conversion
- kWh/100mi <-> kWh/100km conversion
- Roundtrip verification

### TestForceToEnergy (2 tests)
- Force to kWh/100km formula
- Zero force = zero energy

### TestAerodynamics (6 tests)
- Positive force at 100 km/h
- Force scales with v^2
- Consumption scales with v^2
- Zero consumption at zero speed
- Doubling CdA doubles consumption
- Power scales with v^3

### TestRollingResistance (5 tests)
- Positive force
- Speed independence
- Linear mass scaling
- Linear c_rr scaling
- Zero at zero mass

### TestAuxConsumption (3 tests)
- Inverse proportionality to speed
- Zero speed = infinity
- Linear with power

### TestDrivetrainLoss (3 tests)
- Efficiency < 1 increases consumption
- Perfect efficiency = no loss
- Zero efficiency = infinity

### TestTotalConsumption (3 tests)
- Returns ConsumptionBreakdown
- Battery >= wheel at perfect efficiency
- Total = sum of components at wheel

### TestConsumptionCurve (2 tests)
- Correct number of points
- Monotonically increasing at higher speeds (aero dominates)

### TestFuelConversions (3 tests)
- Liters to kWh
- l/100km to kWh/100km
- Wheel energy with thermal efficiency

## Repository Tests (`test_repository.py`)

### TestVehicleRepository (7 tests)
- Loads vehicles from YAML
- Get by ID returns correct vehicle
- Missing ID returns None
- Get by IDs returns correct count
- Filter EV vehicles
- Filter ICE vehicles
- CdA property calculation
- Source refs present

### TestFuelConstants (1 test)
- Loads correct energy densities

## Linting and Formatting
```bash
.venv/bin/ruff check app/           # Lint
.venv/bin/ruff format app/          # Format
.venv/bin/ruff format --check app/  # Check formatting
```

## Type Checking
```bash
.venv/bin/pyright app/
```
Note: pyright may have issues with some NiceGUI types. Focus on core modules.

## Definition of Done (per AGENTS.md)
- Tests added or justified not needed
- `pytest` green
- `ruff check` green
- Type checking green or documented exceptions
- README/comments updated if behavior changed

## Coverage Gaps (Future)
- UI integration tests (NiceGUI testing)
- Model validation edge cases
- Invalid YAML handling
- Plausibility checks for consumption values
- ICE comparison edge cases
