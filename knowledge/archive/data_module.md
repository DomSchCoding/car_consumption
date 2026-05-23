# Data Module - `app/data/`

## Purpose
Data models, validation, and repository for vehicle data. Uses Pydantic for validation and YAML for data storage.

## Files
- `models.py` - Pydantic data models
- `repository.py` - YAML loading and vehicle queries

## Models (`models.py`)

### Enums
| Enum | Values |
|------|--------|
| `ConfidenceLevel` (StrEnum) | high, medium, low |
| `VehicleType` (StrEnum) | ev, ice, phev, van, bus, truck |
| `FuelType` (StrEnum) | gasoline, diesel |

### `SourceRef`
Reference to a data source:
- `name: str` - Source name
- `url: str | None` - URL
- `accessed_at: date | None` - Access date
- `field_names: list[str]` - Which fields this source covers
- `confidence: ConfidenceLevel` - Data confidence
- `license_note: str | None` - License restrictions
- `comment: str | None` - Additional notes

### `ConsumptionValue`
A consumption value with context:
- `value: float` - The numeric value
- `source_ref: str | None` - Key into vehicle.source_refs
- `comment: str | None` - Context (conditions, temperature, etc.)

### `Vehicle`
Main vehicle model with validation:
- `id: str` - Unique identifier
- `make: str`, `model: str`, `variant: str` - Identification
- `year_from/year_to: int | None` - Production years
- `vehicle_type: VehicleType` - Vehicle category
- `mass_kg: float` - Vehicle mass
- `frontal_area_m2: float` - Frontal area
- `drag_coefficient_cd: float` - cw value
- `battery_usable_kwh: float | None` - EV battery capacity
- `wltp_consumption_kwh_100km: ConsumptionValue | None`
- `epa_consumption_kwh_100km: ConsumptionValue | None`
- `real_consumption_kwh_100km: list[ConsumptionValue]`
- `fuel_type: FuelType | None` - For ICE vehicles
- `real_consumption_l_100km: ConsumptionValue | None`
- `source_refs: dict[str, SourceRef]` - Named sources
- `notes: str | None` - General notes

**Computed property**: `cda_m2` = Cd * frontal_area

**Validation** (model_validator):
- Cd must be 0.1-0.6
- Frontal area must be 1.0-5.0 m2
- Mass must be positive

### `PhysicsParams`
Editable physics parameters:
- `rho_air: float = 1.225`
- `c_rr: float = 0.009`
- `p_aux_kw: float = 1.5`
- `eta_drivetrain: float = 0.92`

### `FuelConstants`
- `gasoline_kwh_per_liter: float = 8.9`
- `diesel_kwh_per_liter: float = 9.7`

## Repository (`repository.py`)

### `VehicleRepository`
```python
repo = VehicleRepository(vehicles_path=None)  # defaults to sample_vehicles.yaml
```

**Methods**:
- `vehicles` -> `dict[str, Vehicle]` - All vehicles by ID
- `get(id)` -> `Vehicle | None` - Single vehicle
- `get_all()` -> `list[Vehicle]` - All vehicles
- `get_by_ids(ids)` -> `list[Vehicle]` - Multiple vehicles
- `get_ev_vehicles()` -> `list[Vehicle]` - EVs only
- `get_ice_vehicles()` -> `list[Vehicle]` - ICE only

### `load_fuel_constants(path=None)` -> `FuelConstants`
Loads from `fuel_constants.yaml`.

## YAML Structure (`sample_vehicles.yaml`)
```yaml
vehicles:
  - id: unique_id
    make: Manufacturer
    model: Model name
    variant: "Variant"
    vehicle_type: ev
    mass_kg: 1500
    frontal_area_m2: 2.3
    drag_coefficient_cd: 0.25
    source_refs:
      key_name:
        name: "Source name"
        confidence: high
    wltp_consumption_kwh_100km:
      value: 15.0
      source_ref: key_name
```

## Sample Vehicles
| ID | Make | Model | Type | Notes |
|----|------|-------|------|-------|
| hyundai_ioniq_28 | Hyundai | Ioniq 28 kWh | EV | Efficient compact |
| tesla_model3_rwd | Tesla | Model 3 RWD | EV | Efficient sedan |
| vw_id3_pro | VW | ID.3 Pro 58 kWh | EV | Compact, higher CdA |
| vw_id_buzz | VW | ID. Buzz Pro 77 kWh | EV | Van/bus shape |
| vw_golf_20_tdi | VW | Golf 2.0 TDI | ICE | Diesel reference |
| vw_crafter_35 | VW | Crafter 35 L2H2 | Van | Delivery van |

## Test Coverage
9 tests in `app/tests/test_repository.py`:
- Vehicle loading
- Get by ID / missing ID
- Get by IDs
- Filter by type (EV/ICE)
- CdA property calculation
- Source refs presence
- Fuel constants loading

## Entry Points for Other Modules
- `main.py` creates `VehicleRepository()` and `load_fuel_constants()` at module level
- Models are imported by both `main.py` and `repository.py`
