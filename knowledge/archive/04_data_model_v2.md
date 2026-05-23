# 04 - Data Model v2

## Ziel

Die Datenmodelle sollen nachvollziehbare, versionierbare und quellenbasierte Daten ermoeglichen.

## Grundprinzipien

- Jede Zahl braucht Einheit.
- Jede nicht-physikalische Konstante braucht Quelle oder Demo-Markierung.
- Unterschiedliche Datenarten nicht vermischen.
- Realverbrauch ist eine Beobachtung, kein fixes Fahrzeugattribut.
- Preis ist eine Stichprobe oder Verteilung, kein einzelner wahrer Wert.
- Route ist ein Szenario, kein Fahrzeugattribut.

## Enums

```python
class ConfidenceLevel(StrEnum):
    verified = "verified"
    high = "high"
    medium = "medium"
    low = "low"
    demo = "demo"
    unknown = "unknown"
```

```python
class VehicleType(StrEnum):
    ev = "ev"
    ice = "ice"
    phev = "phev"
    hev = "hev"
    van = "van"
    bus = "bus"
    truck = "truck"
```

```python
class RoadType(StrEnum):
    city = "city"
    suburban = "suburban"
    rural = "rural"
    highway = "highway"
    mountain = "mountain"
    mixed = "mixed"
```

```python
class DirectionMode(StrEnum):
    one_way = "one_way"
    return_trip = "return_trip"
```

## SourceRef

```python
class SourceRef(BaseModel):
    id: str
    name: str
    url: str | None = None
    accessed_at: date | None = None
    published_at: date | None = None
    field_names: list[str] = []
    confidence: ConfidenceLevel = ConfidenceLevel.unknown
    license_note: str | None = None
    comment: str | None = None
```

## Vehicle

```python
class Vehicle(BaseModel):
    id: str
    make: str
    model: str
    variant: str
    year_from: int | None = None
    year_to: int | None = None

    vehicle_type: VehicleType
    body_style: str | None = None

    mass_kg: float
    payload_kg_default: float = 0.0
    frontal_area_m2: float
    drag_coefficient_cd: float

    battery_usable_kwh: float | None = None
    battery_gross_kwh: float | None = None

    fuel_type: FuelType | None = None
    tank_liters: float | None = None

    tire_profile_id: str | None = None
    drivetrain_efficiency_default: float | None = None
    regen_efficiency_default: float | None = None
    has_heat_pump: bool | None = None

    wltp_consumption_kwh_100km: ConsumptionValue | None = None
    epa_consumption_kwh_100km: ConsumptionValue | None = None
    real_consumption_kwh_100km: list[ConsumptionObservation] = []

    real_consumption_l_100km: ConsumptionValue | None = None

    source_refs: dict[str, SourceRef] = {}
    notes: str | None = None

    @property
    def cda_m2(self) -> float:
        return self.drag_coefficient_cd * self.frontal_area_m2
```

## ConsumptionObservation

Realverbrauch braucht Kontext:

```python
class ConsumptionObservation(BaseModel):
    value: float
    unit: str = "kWh/100km"
    source_ref: str | None = None
    speed_kmh: float | None = None
    avg_speed_kmh: float | None = None
    temperature_c: float | None = None
    route_type: RoadType | None = None
    tire: str | None = None
    payload_kg: float | None = None
    hvac: str | None = None
    includes_charging_losses: bool | None = None
    comment: str | None = None
```

## TireProfile

```python
class TireProfile(BaseModel):
    id: str
    name: str
    c_rr: float
    description: str | None = None
    source_ref: str | None = None
```

Beispiele:

- eco_summer
- standard_summer
- winter
- all_season
- van_tire

## EnvironmentProfile

```python
class EnvironmentProfile(BaseModel):
    name: str
    ambient_temp_c: float = 15.0
    air_density_kg_m3: float | None = None
    pressure_hpa: float | None = None
    altitude_m: float | None = None
    headwind_kmh: float = 0.0
    road_wetness_factor: float = 1.0
```

## DriveProfile

```python
class DriveProfile(BaseModel):
    id: str
    name: str
    description: str | None = None
    segments: list[DriveProfileSegment]
```

## Route und Commute

Siehe `03_route_and_commute_model.md`.

## PriceSample

```python
class PriceSample(BaseModel):
    vehicle_id: str
    observed_at: date
    source_ref: str | None = None
    country: str | None = None
    price_eur: float
    mileage_km: float | None = None
    first_registration_year: int | None = None
    age_months: int | None = None
    seller_type: str | None = None  # dealer/private
    battery_soh_percent: float | None = None
    trim: str | None = None
    has_accident_history: bool | None = None
    comment: str | None = None
```

## PriceDistribution

Wird aus Samples berechnet, nicht manuell gepflegt:

```python
class PriceDistribution(BaseModel):
    vehicle_id: str
    sample_count: int
    median_eur: float
    mean_eur: float
    p10_eur: float
    p25_eur: float
    p75_eur: float
    p90_eur: float
    min_eur: float
    max_eur: float
    filters: dict[str, str | float | int]
```

## YAML-Organisation

Statt einer grossen Datei:

```text
assets/
  vehicles/
    hyundai.yaml
    volkswagen.yaml
    tesla.yaml
    bmw.yaml
  routes/
    demo_commutes.yaml
  economics/
    price_samples_demo.yaml
  profiles/
    tire_profiles.yaml
    environment_profiles.yaml
    drive_profiles.yaml
```

## Validierungsregeln

### Vehicle

- `0.1 <= Cd <= 0.7`, Warnung ab 0.45 fuer PKW
- `1.0 <= frontal_area_m2 <= 8.0`
- `mass_kg > 0`
- EV braucht `battery_usable_kwh` oder klare Demo-Markierung
- ICE braucht `fuel_type`
- `source_refs` muessen referenzierte keys enthalten

### Route

- Distanz > 0
- Geschwindigkeit > 0
- Hoehenmeter >= 0
- Stops >= 0
- Rueckweg darf aus Hinweg generiert werden

### PriceSample

- Preis > 0
- Beobachtungsdatum darf nicht in Zukunft liegen
- Kilometerstand >= 0
- Vehicle ID muss existieren
