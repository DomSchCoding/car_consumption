"""Pydantic data models for vehicles, sources, and configuration."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class VehicleType(str, Enum):
    ev = "ev"
    ice = "ice"
    phev = "phev"
    van = "van"
    bus = "bus"
    truck = "truck"


class FuelType(str, Enum):
    gasoline = "gasoline"
    diesel = "diesel"


class TireClass(str, Enum):
    eco_lrr = "eco_lrr"
    standard = "standard"
    sport = "sport"
    suv = "suv"
    van_truck = "van_truck"


C_RR_LOOKUP: dict[TireClass, float] = {
    TireClass.eco_lrr: 0.007,
    TireClass.standard: 0.009,
    TireClass.sport: 0.011,
    TireClass.suv: 0.010,
    TireClass.van_truck: 0.012,
}


class SourceRef(BaseModel):
    name: str
    url: str | None = None
    accessed_at: date | None = None
    field_names: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.medium
    license_note: str | None = None
    comment: str | None = None


class ConsumptionValue(BaseModel):
    value: float
    source_ref: str | None = None
    comment: str | None = None


class ChargingCurvePoint(BaseModel):
    soc_percent: float
    power_kw: float


class Vehicle(BaseModel):
    id: str
    make: str
    model: str
    variant: str = ""
    year_from: int | None = None
    year_to: int | None = None
    vehicle_type: VehicleType = VehicleType.ev

    mass_kg: float
    frontal_area_m2: float
    drag_coefficient_cd: float
    tire_class: TireClass | None = None

    battery_usable_kwh: float | None = None
    wltp_consumption_kwh_100km: ConsumptionValue | None = None
    epa_consumption_kwh_100km: ConsumptionValue | None = None
    real_consumption_kwh_100km: list[ConsumptionValue] = Field(default_factory=list)

    ac_charging_kw: float | None = None
    dc_charging_kw: float | None = None
    dc_charging_curve: list[ChargingCurvePoint] | None = None

    has_heat_pump: bool | None = None
    hvac_cop_heat: float | None = None

    fuel_type: FuelType | None = None
    real_consumption_l_100km: ConsumptionValue | None = None

    image: str | None = None
    image_attribution: str | None = None

    source_refs: dict[str, SourceRef] = Field(default_factory=dict)
    notes: str | None = None

    @field_validator("model", "variant", mode="before")
    @classmethod
    def to_str(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @property
    def cda_m2(self) -> float:
        return self.drag_coefficient_cd * self.frontal_area_m2

    @property
    def default_c_rr(self) -> float:
        if self.tire_class is not None:
            return C_RR_LOOKUP.get(self.tire_class, 0.009)
        return 0.009

    @property
    def has_dc_charging_data(self) -> bool:
        return self.dc_charging_kw is not None and self.battery_usable_kwh is not None

    @property
    def charge_time_20_80_min(self) -> float | None:
        if not self.has_dc_charging_data or self.battery_usable_kwh is None:
            return None
        from app.core.physics import charge_time_minutes

        curve_tuples: list[tuple[float, float]] | None = None
        if self.dc_charging_curve:
            curve_tuples = [(p.soc_percent, p.power_kw) for p in self.dc_charging_curve]

        return charge_time_minutes(
            battery_kwh=self.battery_usable_kwh,
            charging_curve=curve_tuples,
            peak_dc_kw=self.dc_charging_kw,
            soc_from=20.0,
            soc_to=80.0,
        )

    @model_validator(mode="after")
    def validate_plausible(self) -> Vehicle:
        if not (0.1 <= self.drag_coefficient_cd <= 0.6):
            raise ValueError(f"Cd={self.drag_coefficient_cd} outside plausible range 0.1-0.6")
        if not (1.0 <= self.frontal_area_m2 <= 5.0):
            raise ValueError(f"Frontal area={self.frontal_area_m2} m2 outside plausible range 1.0-5.0")
        if self.mass_kg <= 0:
            raise ValueError(f"Mass must be positive, got {self.mass_kg}")
        return self


class PhysicsParams(BaseModel):
    rho_air: float = 1.225
    c_rr: float = 0.009
    p_aux_kw: float = 1.5
    eta_drivetrain: float = 0.92
    eta_regen: float = 0.65
    eta_charging: float = 0.90
    temperature_c: float = 20.0
    cabin_target_temp_c: float = 21.0


class FuelConstants(BaseModel):
    gasoline_kwh_per_liter: float = 8.9
    diesel_kwh_per_liter: float = 9.7
