#!/usr/bin/env python3
"""Add new European-market vehicles to the car_consumption YAML data.

Run from repo root: python scripts/add_new_vehicles.py
"""
import yaml
from pathlib import Path

VEHICLES_DIR = Path(__file__).resolve().parent.parent / "app" / "assets" / "vehicles"

# New vehicles to add to EXISTING YAML files
EXISTING_ADDITIONS: dict[str, list[dict]] = {
    "bmw.yaml": [
        {
            "id": "bmw_ix1_xdrive30",
            "make": "BMW", "model": "iX1", "variant": "xDrive30",
            "year_from": 2022, "vehicle_type": "ev",
            "mass_kg": 2085, "frontal_area_m2": 2.48, "drag_coefficient_cd": 0.26,
            "tire_class": "suv", "battery_usable_kwh": 64.7,
            "ac_charging_kw": 11, "dc_charging_kw": 130,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 130}, {"soc_percent": 10, "power_kw": 130},
                {"soc_percent": 30, "power_kw": 125}, {"soc_percent": 50, "power_kw": 100},
                {"soc_percent": 70, "power_kw": 70}, {"soc_percent": 80, "power_kw": 50},
                {"soc_percent": 90, "power_kw": 30}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 17.3, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 18.5, "source_ref": "evdb"}],
            "length_mm": 4500, "ground_clearance_mm": 175, "drivetrain": "awd",
            "new_price_eur": 47500, "trunk_volume_l": 490,
        },
        {
            "id": "bmw_ix3",
            "make": "BMW", "model": "iX3", "variant": "xDrive30",
            "year_from": 2021, "year_to": 2024, "vehicle_type": "ev",
            "mass_kg": 2205, "frontal_area_m2": 2.54, "drag_coefficient_cd": 0.29,
            "tire_class": "suv", "battery_usable_kwh": 74.0,
            "ac_charging_kw": 11, "dc_charging_kw": 150,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                {"soc_percent": 70, "power_kw": 75}, {"soc_percent": 80, "power_kw": 50},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 18.5, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 19.5, "source_ref": "evdb"}],
            "length_mm": 4734, "ground_clearance_mm": 180, "drivetrain": "rwd",
            "new_price_eur": 67300, "trunk_volume_l": 510,
        },
        {
            "id": "bmw_i4_edrive35",
            "make": "BMW", "model": "i4", "variant": "eDrive35",
            "year_from": 2023, "vehicle_type": "ev",
            "mass_kg": 2125, "frontal_area_m2": 2.28, "drag_coefficient_cd": 0.24,
            "tire_class": "standard", "battery_usable_kwh": 67.0,
            "ac_charging_kw": 11, "dc_charging_kw": 180,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 180}, {"soc_percent": 10, "power_kw": 180},
                {"soc_percent": 30, "power_kw": 170}, {"soc_percent": 50, "power_kw": 130},
                {"soc_percent": 70, "power_kw": 90}, {"soc_percent": 80, "power_kw": 60},
                {"soc_percent": 90, "power_kw": 30}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 15.8, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 16.5, "source_ref": "evdb"}],
            "length_mm": 4783, "ground_clearance_mm": 125, "drivetrain": "rwd",
            "new_price_eur": 51000, "trunk_volume_l": 470,
        },
    ],
    "mercedes.yaml": [
        {
            "id": "mercedes_eqs_suv_450",
            "make": "Mercedes-Benz", "model": "EQS SUV", "variant": "450+",
            "year_from": 2022, "vehicle_type": "ev",
            "mass_kg": 2810, "frontal_area_m2": 2.78, "drag_coefficient_cd": 0.26,
            "tire_class": "suv", "battery_usable_kwh": 108.4,
            "ac_charging_kw": 11, "dc_charging_kw": 200,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 200}, {"soc_percent": 10, "power_kw": 200},
                {"soc_percent": 30, "power_kw": 190}, {"soc_percent": 50, "power_kw": 150},
                {"soc_percent": 70, "power_kw": 100}, {"soc_percent": 80, "power_kw": 65},
                {"soc_percent": 90, "power_kw": 35}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.5,
            "wltp_consumption_kwh_100km": {"value": 21.1, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 23.0, "source_ref": "evdb"}],
            "length_mm": 5125, "ground_clearance_mm": 170, "drivetrain": "rwd",
            "new_price_eur": 135000, "trunk_volume_l": 645,
        },
        {
            "id": "mercedes_eqe_suv_300",
            "make": "Mercedes-Benz", "model": "EQE SUV", "variant": "300",
            "year_from": 2023, "vehicle_type": "ev",
            "mass_kg": 2430, "frontal_area_m2": 2.60, "drag_coefficient_cd": 0.26,
            "tire_class": "suv", "battery_usable_kwh": 90.6,
            "ac_charging_kw": 11, "dc_charging_kw": 170,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 170}, {"soc_percent": 10, "power_kw": 170},
                {"soc_percent": 30, "power_kw": 160}, {"soc_percent": 50, "power_kw": 130},
                {"soc_percent": 70, "power_kw": 90}, {"soc_percent": 80, "power_kw": 60},
                {"soc_percent": 90, "power_kw": 30}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.5,
            "wltp_consumption_kwh_100km": {"value": 19.4, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 21.0, "source_ref": "evdb"}],
            "length_mm": 4863, "ground_clearance_mm": 160, "drivetrain": "rwd",
            "new_price_eur": 77000, "trunk_volume_l": 520,
        },
        {
            "id": "mercedes_eqa_300",
            "make": "Mercedes-Benz", "model": "EQA", "variant": "300 4MATIC",
            "year_from": 2023, "vehicle_type": "ev",
            "mass_kg": 2115, "frontal_area_m2": 2.48, "drag_coefficient_cd": 0.28,
            "tire_class": "suv", "battery_usable_kwh": 66.5,
            "ac_charging_kw": 11, "dc_charging_kw": 130,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 130}, {"soc_percent": 10, "power_kw": 130},
                {"soc_percent": 30, "power_kw": 125}, {"soc_percent": 50, "power_kw": 100},
                {"soc_percent": 70, "power_kw": 70}, {"soc_percent": 80, "power_kw": 50},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.5,
            "wltp_consumption_kwh_100km": {"value": 17.4, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 18.5, "source_ref": "evdb"}],
            "length_mm": 4463, "ground_clearance_mm": 142, "drivetrain": "awd",
            "new_price_eur": 53000, "trunk_volume_l": 340,
        },
    ],
    "volvo.yaml": [
        {
            "id": "volvo_c40_single",
            "make": "Volvo", "model": "C40 Recharge", "variant": "Single Motor",
            "year_from": 2022, "vehicle_type": "ev",
            "mass_kg": 2040, "frontal_area_m2": 2.42, "drag_coefficient_cd": 0.27,
            "tire_class": "suv", "battery_usable_kwh": 69.0,
            "ac_charging_kw": 11, "dc_charging_kw": 150,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                {"soc_percent": 70, "power_kw": 80}, {"soc_percent": 80, "power_kw": 50},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 17.8, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 18.5, "source_ref": "evdb"}],
            "length_mm": 4440, "ground_clearance_mm": 175, "drivetrain": "fwd",
            "new_price_eur": 48900, "trunk_volume_l": 413,
        },
        {
            "id": "volvo_xc40_recharge_twin",
            "make": "Volvo", "model": "XC40 Recharge", "variant": "Twin Motor",
            "year_from": 2021, "vehicle_type": "ev",
            "mass_kg": 2185, "frontal_area_m2": 2.52, "drag_coefficient_cd": 0.29,
            "tire_class": "suv", "battery_usable_kwh": 78.0,
            "ac_charging_kw": 11, "dc_charging_kw": 150,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                {"soc_percent": 70, "power_kw": 80}, {"soc_percent": 80, "power_kw": 50},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 19.8, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 21.0, "source_ref": "evdb"}],
            "length_mm": 4425, "ground_clearance_mm": 175, "drivetrain": "awd",
            "new_price_eur": 52900, "trunk_volume_l": 419,
        },
    ],
    "peugeot.yaml": [
        {
            "id": "peugeot_e2008_50",
            "make": "Peugeot", "model": "e-2008", "variant": "50 kWh",
            "year_from": 2023, "vehicle_type": "ev",
            "mass_kg": 1610, "frontal_area_m2": 2.40, "drag_coefficient_cd": 0.30,
            "tire_class": "suv", "battery_usable_kwh": 50.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 95}, {"soc_percent": 50, "power_kw": 75},
                {"soc_percent": 70, "power_kw": 55}, {"soc_percent": 80, "power_kw": 40},
                {"soc_percent": 90, "power_kw": 20}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 17.8, "source_ref": "wltp"},
            "length_mm": 4300, "ground_clearance_mm": 170, "drivetrain": "fwd",
            "new_price_eur": 38060, "trunk_volume_l": 434,
        },
    ],
    "opel.yaml": [
        {
            "id": "opel_combo_e_life",
            "make": "Opel", "model": "Combo-e Life", "variant": "50 kWh",
            "year_from": 2021, "vehicle_type": "ev",
            "mass_kg": 1756, "frontal_area_m2": 2.65, "drag_coefficient_cd": 0.32,
            "tire_class": "standard", "battery_usable_kwh": 50.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 90}, {"soc_percent": 50, "power_kw": 70},
                {"soc_percent": 70, "power_kw": 50}, {"soc_percent": 80, "power_kw": 35},
                {"soc_percent": 90, "power_kw": 18}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 19.3, "source_ref": "wltp"},
            "length_mm": 4403, "ground_clearance_mm": 155, "drivetrain": "fwd",
            "new_price_eur": 36490, "trunk_volume_l": 775,
        },
    ],
    "citroen.yaml": [
        {
            "id": "citroen_ec3_44",
            "make": "Citroën", "model": "ë-C3", "variant": "44 kWh",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 1416, "frontal_area_m2": 2.30, "drag_coefficient_cd": 0.30,
            "tire_class": "eco_lrr", "battery_usable_kwh": 44.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 90}, {"soc_percent": 50, "power_kw": 70},
                {"soc_percent": 70, "power_kw": 50}, {"soc_percent": 80, "power_kw": 35},
                {"soc_percent": 90, "power_kw": 18}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 14.3, "source_ref": "wltp"},
            "length_mm": 3997, "ground_clearance_mm": 145, "drivetrain": "fwd",
            "new_price_eur": 23300, "trunk_volume_l": 310,
        },
        {
            "id": "citroen_eberlingo_50",
            "make": "Citroën", "model": "ë-Berlingo", "variant": "50 kWh",
            "year_from": 2021, "vehicle_type": "ev",
            "mass_kg": 1728, "frontal_area_m2": 2.68, "drag_coefficient_cd": 0.32,
            "tire_class": "standard", "battery_usable_kwh": 50.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 90}, {"soc_percent": 50, "power_kw": 70},
                {"soc_percent": 70, "power_kw": 50}, {"soc_percent": 80, "power_kw": 35},
                {"soc_percent": 90, "power_kw": 18}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 18.9, "source_ref": "wltp"},
            "length_mm": 4403, "ground_clearance_mm": 155, "drivetrain": "fwd",
            "new_price_eur": 35490, "trunk_volume_l": 775,
        },
    ],
    "fiat.yaml": [
        {
            "id": "fiat_600e",
            "make": "Fiat", "model": "600e", "variant": "54 kWh",
            "year_from": 2023, "vehicle_type": "ev",
            "mass_kg": 1536, "frontal_area_m2": 2.32, "drag_coefficient_cd": 0.29,
            "tire_class": "eco_lrr", "battery_usable_kwh": 54.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 90}, {"soc_percent": 50, "power_kw": 70},
                {"soc_percent": 70, "power_kw": 50}, {"soc_percent": 80, "power_kw": 35},
                {"soc_percent": 90, "power_kw": 18}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 15.3, "source_ref": "wltp"},
            "length_mm": 4178, "ground_clearance_mm": 155, "drivetrain": "fwd",
            "new_price_eur": 31900, "trunk_volume_l": 360,
        },
    ],
    "renault.yaml": [
        {
            "id": "renault_scenic_etech_87",
            "make": "Renault", "model": "Scenic E-Tech", "variant": "87 kWh",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 2040, "frontal_area_m2": 2.48, "drag_coefficient_cd": 0.26,
            "tire_class": "suv", "battery_usable_kwh": 87.0,
            "ac_charging_kw": 22, "dc_charging_kw": 150,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                {"soc_percent": 70, "power_kw": 80}, {"soc_percent": 80, "power_kw": 55},
                {"soc_percent": 90, "power_kw": 28}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 16.2, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 17.0, "source_ref": "evdb"}],
            "length_mm": 4551, "ground_clearance_mm": 165, "drivetrain": "rwd",
            "new_price_eur": 47500, "trunk_volume_l": 545,
        },
    ],
    "volkswagen.yaml": [
        {
            "id": "vw_e_up",
            "make": "Volkswagen", "model": "e-Up!", "variant": "36.8 kWh",
            "year_from": 2019, "year_to": 2023, "vehicle_type": "ev",
            "mass_kg": 1235, "frontal_area_m2": 2.10, "drag_coefficient_cd": 0.28,
            "tire_class": "eco_lrr", "battery_usable_kwh": 32.3,
            "ac_charging_kw": 7.2, "dc_charging_kw": 40,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 40}, {"soc_percent": 10, "power_kw": 40},
                {"soc_percent": 30, "power_kw": 38}, {"soc_percent": 50, "power_kw": 32},
                {"soc_percent": 70, "power_kw": 25}, {"soc_percent": 80, "power_kw": 18},
                {"soc_percent": 90, "power_kw": 10}, {"soc_percent": 100, "power_kw": 5},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 12.7, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 14.0, "source_ref": "evdb"}],
            "length_mm": 3600, "ground_clearance_mm": 135, "drivetrain": "fwd",
            "new_price_eur": 21990, "trunk_volume_l": 251,
        },
        {
            "id": "vw_id7_pro_s",
            "make": "Volkswagen", "model": "ID.7", "variant": "Pro S",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 2230, "frontal_area_m2": 2.46, "drag_coefficient_cd": 0.23,
            "tire_class": "eco_lrr", "battery_usable_kwh": 86.0,
            "ac_charging_kw": 11, "dc_charging_kw": 200,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 200}, {"soc_percent": 10, "power_kw": 200},
                {"soc_percent": 30, "power_kw": 185}, {"soc_percent": 50, "power_kw": 140},
                {"soc_percent": 70, "power_kw": 100}, {"soc_percent": 80, "power_kw": 65},
                {"soc_percent": 90, "power_kw": 35}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 14.1, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 15.0, "source_ref": "evdb"}],
            "length_mm": 4961, "ground_clearance_mm": 145, "drivetrain": "rwd",
            "new_price_eur": 57990, "trunk_volume_l": 532,
        },
        {
            "id": "vw_id_buzz_lwb",
            "make": "Volkswagen", "model": "ID. Buzz", "variant": "LWB Pro S",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 2380, "frontal_area_m2": 2.72, "drag_coefficient_cd": 0.27,
            "tire_class": "suv", "battery_usable_kwh": 86.0,
            "ac_charging_kw": 11, "dc_charging_kw": 200,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 200}, {"soc_percent": 10, "power_kw": 200},
                {"soc_percent": 30, "power_kw": 185}, {"soc_percent": 50, "power_kw": 140},
                {"soc_percent": 70, "power_kw": 100}, {"soc_percent": 80, "power_kw": 65},
                {"soc_percent": 90, "power_kw": 35}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 19.0, "source_ref": "wltp"},
            "length_mm": 4962, "ground_clearance_mm": 164, "drivetrain": "rwd",
            "new_price_eur": 61990, "trunk_volume_l": 1340,
        },
    ],
    "toyota_nissan.yaml": [
        {
            "id": "toyota_prius_phev",
            "make": "Toyota", "model": "Prius PHEV", "variant": "2.0 PHEV",
            "year_from": 2023, "vehicle_type": "phev",
            "mass_kg": 1560, "frontal_area_m2": 2.18, "drag_coefficient_cd": 0.22,
            "tire_class": "eco_lrr",
            "battery_usable_kwh": 8.8,
            "ac_charging_kw": 3.7,
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 12.8, "source_ref": "wltp"},
            "fuel_type": "gasoline",
            "real_consumption_l_100km": {"value": 4.2, "source_ref": "wltp"},
            "length_mm": 4600, "ground_clearance_mm": 130, "drivetrain": "fwd",
            "new_price_eur": 42900, "trunk_volume_l": 284,
        },
        {
            "id": "toyota_rav4_phev",
            "make": "Toyota", "model": "RAV4 PHEV", "variant": "2.5 PHEV AWD",
            "year_from": 2021, "vehicle_type": "phev",
            "mass_kg": 1930, "frontal_area_m2": 2.55, "drag_coefficient_cd": 0.32,
            "tire_class": "suv",
            "battery_usable_kwh": 18.1,
            "ac_charging_kw": 6.6,
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 15.6, "source_ref": "wltp"},
            "fuel_type": "gasoline",
            "real_consumption_l_100km": {"value": 5.6, "source_ref": "wltp"},
            "length_mm": 4600, "ground_clearance_mm": 190, "drivetrain": "awd",
            "new_price_eur": 51490, "trunk_volume_l": 520,
        },
    ],
    "porsche.yaml": [
        {
            "id": "porsche_taycan_turbo_s",
            "make": "Porsche", "model": "Taycan", "variant": "Turbo S",
            "year_from": 2020, "vehicle_type": "ev",
            "mass_kg": 2295, "frontal_area_m2": 2.34, "drag_coefficient_cd": 0.25,
            "tire_class": "sport", "battery_usable_kwh": 83.7,
            "ac_charging_kw": 11, "dc_charging_kw": 270,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 270}, {"soc_percent": 10, "power_kw": 270},
                {"soc_percent": 30, "power_kw": 250}, {"soc_percent": 50, "power_kw": 180},
                {"soc_percent": 70, "power_kw": 120}, {"soc_percent": 80, "power_kw": 80},
                {"soc_percent": 90, "power_kw": 40}, {"soc_percent": 100, "power_kw": 12},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 20.5, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 22.0, "source_ref": "evdb"}],
            "length_mm": 4963, "ground_clearance_mm": 127, "drivetrain": "awd",
            "new_price_eur": 188800, "trunk_volume_l": 407,
        },
        {
            "id": "porsche_taycan_gts",
            "make": "Porsche", "model": "Taycan", "variant": "GTS",
            "year_from": 2022, "vehicle_type": "ev",
            "mass_kg": 2295, "frontal_area_m2": 2.34, "drag_coefficient_cd": 0.25,
            "tire_class": "sport", "battery_usable_kwh": 83.7,
            "ac_charging_kw": 11, "dc_charging_kw": 270,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 270}, {"soc_percent": 10, "power_kw": 270},
                {"soc_percent": 30, "power_kw": 250}, {"soc_percent": 50, "power_kw": 180},
                {"soc_percent": 70, "power_kw": 120}, {"soc_percent": 80, "power_kw": 80},
                {"soc_percent": 90, "power_kw": 40}, {"soc_percent": 100, "power_kw": 12},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 20.3, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 21.5, "source_ref": "evdb"}],
            "length_mm": 4963, "ground_clearance_mm": 127, "drivetrain": "awd",
            "new_price_eur": 141700, "trunk_volume_l": 407,
        },
    ],
    "kia.yaml": [
        {
            "id": "kia_ev3_58",
            "make": "Kia", "model": "EV3", "variant": "Standard 58 kWh",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 1765, "frontal_area_m2": 2.42, "drag_coefficient_cd": 0.26,
            "tire_class": "eco_lrr", "battery_usable_kwh": 58.3,
            "ac_charging_kw": 11, "dc_charging_kw": 128,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 128}, {"soc_percent": 10, "power_kw": 128},
                {"soc_percent": 30, "power_kw": 120}, {"soc_percent": 50, "power_kw": 95},
                {"soc_percent": 70, "power_kw": 65}, {"soc_percent": 80, "power_kw": 45},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 15.0, "source_ref": "wltp"},
            "length_mm": 4300, "ground_clearance_mm": 160, "drivetrain": "fwd",
            "new_price_eur": 35990, "trunk_volume_l": 460,
        },
        {
            "id": "kia_ev3_81",
            "make": "Kia", "model": "EV3", "variant": "Long Range 81 kWh",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 1865, "frontal_area_m2": 2.42, "drag_coefficient_cd": 0.26,
            "tire_class": "eco_lrr", "battery_usable_kwh": 81.4,
            "ac_charging_kw": 11, "dc_charging_kw": 128,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 128}, {"soc_percent": 10, "power_kw": 128},
                {"soc_percent": 30, "power_kw": 120}, {"soc_percent": 50, "power_kw": 95},
                {"soc_percent": 70, "power_kw": 65}, {"soc_percent": 80, "power_kw": 45},
                {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.0,
            "wltp_consumption_kwh_100km": {"value": 15.2, "source_ref": "wltp"},
            "length_mm": 4300, "ground_clearance_mm": 160, "drivetrain": "fwd",
            "new_price_eur": 40490, "trunk_volume_l": 460,
        },
    ],
    "hyundai.yaml": [
        {
            "id": "hyundai_ioniq5_n",
            "make": "Hyundai", "model": "Ioniq 5 N", "variant": "Performance AWD",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 2235, "frontal_area_m2": 2.57, "drag_coefficient_cd": 0.29,
            "tire_class": "sport", "battery_usable_kwh": 84.0,
            "ac_charging_kw": 11, "dc_charging_kw": 350,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 350}, {"soc_percent": 10, "power_kw": 350},
                {"soc_percent": 30, "power_kw": 300}, {"soc_percent": 50, "power_kw": 200},
                {"soc_percent": 70, "power_kw": 130}, {"soc_percent": 80, "power_kw": 85},
                {"soc_percent": 90, "power_kw": 40}, {"soc_percent": 100, "power_kw": 12},
            ],
            "has_heat_pump": True, "hvac_cop_heat": 3.5,
            "wltp_consumption_kwh_100km": {"value": 21.2, "source_ref": "wltp"},
            "real_consumption_kwh_100km": [{"value": 23.0, "source_ref": "evdb"}],
            "length_mm": 4715, "ground_clearance_mm": 155, "drivetrain": "awd",
            "new_price_eur": 74900, "trunk_volume_l": 527,
        },
    ],
    "alfa_romeo.yaml": [
        {
            "id": "alfa_junior_elettrica",
            "make": "Alfa Romeo", "model": "Junior", "variant": "Elettrica 54 kWh",
            "year_from": 2024, "vehicle_type": "ev",
            "mass_kg": 1530, "frontal_area_m2": 2.28, "drag_coefficient_cd": 0.29,
            "tire_class": "eco_lrr", "battery_usable_kwh": 54.0,
            "ac_charging_kw": 7.4, "dc_charging_kw": 100,
            "dc_charging_curve": [
                {"soc_percent": 0, "power_kw": 100}, {"soc_percent": 10, "power_kw": 100},
                {"soc_percent": 30, "power_kw": 90}, {"soc_percent": 50, "power_kw": 70},
                {"soc_percent": 70, "power_kw": 50}, {"soc_percent": 80, "power_kw": 35},
                {"soc_percent": 90, "power_kw": 18}, {"soc_percent": 100, "power_kw": 8},
            ],
            "has_heat_pump": False,
            "wltp_consumption_kwh_100km": {"value": 15.6, "source_ref": "wltp"},
            "length_mm": 4170, "ground_clearance_mm": 155, "drivetrain": "fwd",
            "new_price_eur": 30900, "trunk_volume_l": 400,
        },
    ],
}


# New YAML files for NEW brands
NEW_FILES: dict[str, dict] = {
    "dacia.yaml": {
        "vehicles": [
            {
                "id": "dacia_spring",
                "make": "Dacia", "model": "Spring", "variant": "Electric 26.8 kWh",
                "year_from": 2021, "vehicle_type": "ev",
                "mass_kg": 970, "frontal_area_m2": 2.17, "drag_coefficient_cd": 0.30,
                "tire_class": "eco_lrr", "battery_usable_kwh": 26.8,
                "ac_charging_kw": 7.4, "dc_charging_kw": 30,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 30}, {"soc_percent": 10, "power_kw": 30},
                    {"soc_percent": 30, "power_kw": 28}, {"soc_percent": 50, "power_kw": 24},
                    {"soc_percent": 70, "power_kw": 18}, {"soc_percent": 80, "power_kw": 12},
                    {"soc_percent": 90, "power_kw": 6}, {"soc_percent": 100, "power_kw": 3},
                ],
                "has_heat_pump": False,
                "wltp_consumption_kwh_100km": {"value": 13.7, "source_ref": "wltp"},
                "real_consumption_kwh_100km": [{"value": 15.0, "source_ref": "evdb"}],
                "length_mm": 3734, "ground_clearance_mm": 150, "drivetrain": "fwd",
                "new_price_eur": 16900, "trunk_volume_l": 290,
            },
        ],
    },
    "smart.yaml": {
        "vehicles": [
            {
                "id": "smart_1_pro_plus",
                "make": "Smart", "model": "#1", "variant": "Pro+",
                "year_from": 2023, "vehicle_type": "ev",
                "mass_kg": 1820, "frontal_area_m2": 2.44, "drag_coefficient_cd": 0.29,
                "tire_class": "suv", "battery_usable_kwh": 62.0,
                "ac_charging_kw": 22, "dc_charging_kw": 150,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                    {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                    {"soc_percent": 70, "power_kw": 75}, {"soc_percent": 80, "power_kw": 50},
                    {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.0,
                "wltp_consumption_kwh_100km": {"value": 16.8, "source_ref": "wltp"},
                "real_consumption_kwh_100km": [{"value": 18.0, "source_ref": "evdb"}],
                "length_mm": 4270, "ground_clearance_mm": 160, "drivetrain": "rwd",
                "new_price_eur": 41490, "trunk_volume_l": 323,
            },
            {
                "id": "smart_3_premium",
                "make": "Smart", "model": "#3", "variant": "Premium",
                "year_from": 2024, "vehicle_type": "ev",
                "mass_kg": 1910, "frontal_area_m2": 2.50, "drag_coefficient_cd": 0.27,
                "tire_class": "suv", "battery_usable_kwh": 62.0,
                "ac_charging_kw": 22, "dc_charging_kw": 150,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                    {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                    {"soc_percent": 70, "power_kw": 75}, {"soc_percent": 80, "power_kw": 50},
                    {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.0,
                "wltp_consumption_kwh_100km": {"value": 17.1, "source_ref": "wltp"},
                "length_mm": 4400, "ground_clearance_mm": 165, "drivetrain": "rwd",
                "new_price_eur": 44990, "trunk_volume_l": 370,
            },
        ],
    },
    "mini.yaml": {
        "vehicles": [
            {
                "id": "mini_cooper_se_24",
                "make": "Mini", "model": "Cooper SE", "variant": "Electric",
                "year_from": 2024, "vehicle_type": "ev",
                "mass_kg": 1600, "frontal_area_m2": 2.14, "drag_coefficient_cd": 0.28,
                "tire_class": "standard", "battery_usable_kwh": 40.7,
                "ac_charging_kw": 11, "dc_charging_kw": 95,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 95}, {"soc_percent": 10, "power_kw": 95},
                    {"soc_percent": 30, "power_kw": 85}, {"soc_percent": 50, "power_kw": 65},
                    {"soc_percent": 70, "power_kw": 45}, {"soc_percent": 80, "power_kw": 30},
                    {"soc_percent": 90, "power_kw": 15}, {"soc_percent": 100, "power_kw": 5},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.0,
                "wltp_consumption_kwh_100km": {"value": 14.2, "source_ref": "wltp"},
                "real_consumption_kwh_100km": [{"value": 15.0, "source_ref": "evdb"}],
                "length_mm": 3858, "ground_clearance_mm": 130, "drivetrain": "fwd",
                "new_price_eur": 31900, "trunk_volume_l": 211,
            },
            {
                "id": "mini_countryman_se",
                "make": "Mini", "model": "Countryman", "variant": "SE ALL4",
                "year_from": 2024, "vehicle_type": "ev",
                "mass_kg": 2105, "frontal_area_m2": 2.52, "drag_coefficient_cd": 0.28,
                "tire_class": "suv", "battery_usable_kwh": 64.7,
                "ac_charging_kw": 11, "dc_charging_kw": 130,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 130}, {"soc_percent": 10, "power_kw": 130},
                    {"soc_percent": 30, "power_kw": 120}, {"soc_percent": 50, "power_kw": 95},
                    {"soc_percent": 70, "power_kw": 65}, {"soc_percent": 80, "power_kw": 45},
                    {"soc_percent": 90, "power_kw": 25}, {"soc_percent": 100, "power_kw": 10},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.0,
                "wltp_consumption_kwh_100km": {"value": 17.3, "source_ref": "wltp"},
                "length_mm": 4433, "ground_clearance_mm": 165, "drivetrain": "awd",
                "new_price_eur": 46500, "trunk_volume_l": 460,
            },
        ],
    },
    "lexus.yaml": {
        "vehicles": [
            {
                "id": "lexus_ux300e",
                "make": "Lexus", "model": "UX 300e", "variant": "Electric",
                "year_from": 2020, "vehicle_type": "ev",
                "mass_kg": 1900, "frontal_area_m2": 2.38, "drag_coefficient_cd": 0.29,
                "tire_class": "suv", "battery_usable_kwh": 54.3,
                "ac_charging_kw": 6.6, "dc_charging_kw": 50,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 50}, {"soc_percent": 10, "power_kw": 50},
                    {"soc_percent": 30, "power_kw": 48}, {"soc_percent": 50, "power_kw": 40},
                    {"soc_percent": 70, "power_kw": 30}, {"soc_percent": 80, "power_kw": 22},
                    {"soc_percent": 90, "power_kw": 12}, {"soc_percent": 100, "power_kw": 5},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.0,
                "wltp_consumption_kwh_100km": {"value": 16.8, "source_ref": "wltp"},
                "real_consumption_kwh_100km": [{"value": 18.0, "source_ref": "evdb"}],
                "length_mm": 4495, "ground_clearance_mm": 160, "drivetrain": "fwd",
                "new_price_eur": 47900, "trunk_volume_l": 367,
            },
            {
                "id": "lexus_rz450e",
                "make": "Lexus", "model": "RZ 450e", "variant": "Direct4 AWD",
                "year_from": 2023, "vehicle_type": "ev",
                "mass_kg": 2110, "frontal_area_m2": 2.58, "drag_coefficient_cd": 0.27,
                "tire_class": "suv", "battery_usable_kwh": 71.4,
                "ac_charging_kw": 11, "dc_charging_kw": 150,
                "dc_charging_curve": [
                    {"soc_percent": 0, "power_kw": 150}, {"soc_percent": 10, "power_kw": 150},
                    {"soc_percent": 30, "power_kw": 140}, {"soc_percent": 50, "power_kw": 110},
                    {"soc_percent": 70, "power_kw": 80}, {"soc_percent": 80, "power_kw": 55},
                    {"soc_percent": 90, "power_kw": 28}, {"soc_percent": 100, "power_kw": 10},
                ],
                "has_heat_pump": True, "hvac_cop_heat": 3.5,
                "wltp_consumption_kwh_100km": {"value": 18.3, "source_ref": "wltp"},
                "real_consumption_kwh_100km": [{"value": 20.0, "source_ref": "evdb"}],
                "length_mm": 4805, "ground_clearance_mm": 175, "drivetrain": "awd",
                "new_price_eur": 67000, "trunk_volume_l": 522,
            },
        ],
    },
}


def add_to_existing_file(yaml_path: Path, vehicles: list[dict]) -> int:
    """Add new vehicle entries to an existing YAML file."""
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "vehicles" not in data:
        return 0

    existing_ids = {v.get("id") for v in data["vehicles"]}
    added = 0
    for vdata in vehicles:
        if vdata["id"] not in existing_ids:
            data["vehicles"].append(vdata)
            added += 1

    if added:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    return added


def create_new_file(yaml_path: Path, data: dict) -> int:
    """Create a new YAML file with vehicle data."""
    count = len(data.get("vehicles", []))
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
    return count


def main():
    total = 0

    # Add to existing files
    for filename, vehicles in EXISTING_ADDITIONS.items():
        path = VEHICLES_DIR / filename
        if path.exists():
            count = add_to_existing_file(path, vehicles)
            if count:
                print(f"  {filename}: +{count} vehicles")
                total += count
            else:
                print(f"  {filename}: all already present")
        else:
            print(f"  {filename}: file not found, skipping")

    # Create new files
    for filename, data in NEW_FILES.items():
        path = VEHICLES_DIR / filename
        if path.exists():
            # Merge with existing
            count = add_to_existing_file(path, data.get("vehicles", []))
            if count:
                print(f"  {filename}: +{count} vehicles (merged)")
                total += count
            else:
                print(f"  {filename}: all already present")
        else:
            count = create_new_file(path, data)
            print(f"  {filename}: created with {count} vehicles")
            total += count

    print(f"\nTotal: {total} new vehicles added")


if __name__ == "__main__":
    main()
