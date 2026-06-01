#!/usr/bin/env python3
"""Populate new filter fields for all vehicles missing them.

Run from repo root: python scripts/populate_vehicle_fields.py
"""
import yaml
from pathlib import Path

VEHICLES_DIR = Path(__file__).resolve().parent.parent / "app" / "assets" / "vehicles"

# New fields data per vehicle ID
# Format: {id: {field: value, ...}}
VEHICLE_DATA: dict[str, dict] = {
    # === TESLA ===
    "tesla_model3_rwd": {
        "length_mm": 4694, "ground_clearance_mm": 140, "drivetrain": "rwd",
        "new_price_eur": 42990, "trunk_volume_l": 561,
    },
    "tesla_model3_lr": {
        "length_mm": 4694, "ground_clearance_mm": 140, "drivetrain": "awd",
        "new_price_eur": 51990, "trunk_volume_l": 561,
    },
    "tesla_model3_highland_rwd": {
        "length_mm": 4720, "ground_clearance_mm": 138, "drivetrain": "rwd",
        "new_price_eur": 42990, "trunk_volume_l": 561,
    },
    "tesla_model3_highland_lr": {
        "length_mm": 4720, "ground_clearance_mm": 138, "drivetrain": "awd",
        "new_price_eur": 51990, "trunk_volume_l": 561,
    },
    "tesla_model_y_rwd": {
        "length_mm": 4751, "ground_clearance_mm": 167, "drivetrain": "rwd",
        "new_price_eur": 44890, "trunk_volume_l": 854,
    },
    "tesla_model_y_lr": {
        "length_mm": 4751, "ground_clearance_mm": 167, "drivetrain": "awd",
        "new_price_eur": 54990, "trunk_volume_l": 854,
    },
    "tesla_model_s_lr": {
        "length_mm": 4970, "ground_clearance_mm": 117, "drivetrain": "awd",
        "new_price_eur": 94990, "trunk_volume_l": 793,
    },
    # === MERCEDES ===
    "mercedes_eqe_350": {
        "length_mm": 4946, "ground_clearance_mm": 130, "drivetrain": "rwd",
        "new_price_eur": 70600, "trunk_volume_l": 430,
    },
    "mercedes_eqs_450": {
        "length_mm": 5216, "ground_clearance_mm": 120, "drivetrain": "rwd",
        "new_price_eur": 107300, "trunk_volume_l": 610,
    },
    "mercedes_eqa_250": {
        "length_mm": 4463, "ground_clearance_mm": 142, "drivetrain": "fwd",
        "new_price_eur": 47900, "trunk_volume_l": 340,
    },
    "mercedes_eqb_300": {
        "length_mm": 4684, "ground_clearance_mm": 142, "drivetrain": "awd",
        "new_price_eur": 55300, "trunk_volume_l": 495,
    },
    "mercedes_eqv_300": {
        "length_mm": 5140, "ground_clearance_mm": 145, "drivetrain": "fwd",
        "new_price_eur": 72600, "trunk_volume_l": 1030,
    },
    "mercedes_c220d": {
        "length_mm": 4751, "ground_clearance_mm": 115, "drivetrain": "rwd",
        "new_price_eur": 53100, "trunk_volume_l": 455,
    },
    # === MAZDA / HONDA / GENESIS / JEEP ===
    "mazda_mx30": {
        "length_mm": 4395, "ground_clearance_mm": 140, "drivetrain": "fwd",
        "new_price_eur": 34490, "trunk_volume_l": 366,
    },
    "honda_e": {
        "length_mm": 3894, "ground_clearance_mm": 145, "drivetrain": "rwd",
        "new_price_eur": 38900, "trunk_volume_l": 171,
    },
    "honda_e_ns1": {
        "length_mm": 4386, "ground_clearance_mm": 150, "drivetrain": "fwd",
        "new_price_eur": 41900, "trunk_volume_l": 345,
    },
    "genesis_gv60_adv": {
        "length_mm": 4515, "ground_clearance_mm": 160, "drivetrain": "awd",
        "new_price_eur": 58600, "trunk_volume_l": 432,
    },
    "jeep_avenger": {
        "length_mm": 4084, "ground_clearance_mm": 180, "drivetrain": "fwd",
        "new_price_eur": 39900, "trunk_volume_l": 355,
    },
    # === MG / BYD ===
    "mg4_excite_51": {
        "length_mm": 4287, "ground_clearance_mm": 150, "drivetrain": "rwd",
        "new_price_eur": 28990, "trunk_volume_l": 363,
    },
    "mg4_trophy_64": {
        "length_mm": 4287, "ground_clearance_mm": 150, "drivetrain": "rwd",
        "new_price_eur": 34990, "trunk_volume_l": 363,
    },
    "byd_seal_design": {
        "length_mm": 4800, "ground_clearance_mm": 125, "drivetrain": "rwd",
        "new_price_eur": 44990, "trunk_volume_l": 400,
    },
    "byd_atto3": {
        "length_mm": 4455, "ground_clearance_mm": 155, "drivetrain": "fwd",
        "new_price_eur": 37990, "trunk_volume_l": 440,
    },
    "byd_dolphin": {
        "length_mm": 4150, "ground_clearance_mm": 145, "drivetrain": "fwd",
        "new_price_eur": 29990, "trunk_volume_l": 345,
    },
    # === OPEL ===
    "opel_corsa_e_50": {
        "length_mm": 4060, "ground_clearance_mm": 130, "drivetrain": "fwd",
        "new_price_eur": 33340, "trunk_volume_l": 267,
    },
    "opel_astra_e_54": {
        "length_mm": 4374, "ground_clearance_mm": 130, "drivetrain": "fwd",
        "new_price_eur": 39990, "trunk_volume_l": 352,
    },
    "opel_mokka_e_50": {
        "length_mm": 4151, "ground_clearance_mm": 150, "drivetrain": "fwd",
        "new_price_eur": 36840, "trunk_volume_l": 310,
    },
    # === PEUGEOT ===
    "peugeot_e208_50": {
        "length_mm": 4055, "ground_clearance_mm": 130, "drivetrain": "fwd",
        "new_price_eur": 35060, "trunk_volume_l": 309,
    },
    "peugeot_e308_54": {
        "length_mm": 4367, "ground_clearance_mm": 130, "drivetrain": "fwd",
        "new_price_eur": 39600, "trunk_volume_l": 412,
    },
    "peugeot_e3008_98": {
        "length_mm": 4542, "ground_clearance_mm": 160, "drivetrain": "fwd",
        "new_price_eur": 46900, "trunk_volume_l": 520,
    },
    # === POLESTAR ===
    "polestar_2_std": {
        "length_mm": 4606, "ground_clearance_mm": 141, "drivetrain": "fwd",
        "new_price_eur": 48400, "trunk_volume_l": 405,
    },
    "polestar_2_lr": {
        "length_mm": 4606, "ground_clearance_mm": 141, "drivetrain": "awd",
        "new_price_eur": 53400, "trunk_volume_l": 405,
    },
    "polestar_3_lr": {
        "length_mm": 4900, "ground_clearance_mm": 165, "drivetrain": "awd",
        "new_price_eur": 85000, "trunk_volume_l": 484,
    },
    "polestar_4_sr": {
        "length_mm": 4840, "ground_clearance_mm": 165, "drivetrain": "rwd",
        "new_price_eur": 57500, "trunk_volume_l": 526,
    },
    # === PORSCHE ===
    "porsche_taycan_4s": {
        "length_mm": 4963, "ground_clearance_mm": 127, "drivetrain": "awd",
        "new_price_eur": 109600, "trunk_volume_l": 407,
    },
    "porsche_macan_ev_4": {
        "length_mm": 4784, "ground_clearance_mm": 176, "drivetrain": "awd",
        "new_price_eur": 84000, "trunk_volume_l": 540,
    },
    # === RENAULT ===
    "renault_zoe_52": {
        "length_mm": 4087, "ground_clearance_mm": 130, "drivetrain": "fwd",
        "new_price_eur": 33490, "trunk_volume_l": 338,
    },
    "renault_megane_e_tech_60": {
        "length_mm": 4200, "ground_clearance_mm": 145, "drivetrain": "fwd",
        "new_price_eur": 39990, "trunk_volume_l": 440,
    },
    "renault_5_e_tech_52": {
        "length_mm": 3920, "ground_clearance_mm": 135, "drivetrain": "fwd",
        "new_price_eur": 33490, "trunk_volume_l": 326,
    },
    # === SKODA ===
    "skoda_enyaq_60": {
        "length_mm": 4649, "ground_clearance_mm": 186, "drivetrain": "rwd",
        "new_price_eur": 41990, "trunk_volume_l": 585,
    },
    "skoda_enyaq_80": {
        "length_mm": 4649, "ground_clearance_mm": 186, "drivetrain": "rwd",
        "new_price_eur": 47490, "trunk_volume_l": 585,
    },
    "skoda_elroq_60": {
        "length_mm": 4488, "ground_clearance_mm": 178, "drivetrain": "rwd",
        "new_price_eur": 33990, "trunk_volume_l": 470,
    },
    # === TOYOTA / NISSAN ===
    "toyota_bz4x_fwd": {
        "length_mm": 4690, "ground_clearance_mm": 175, "drivetrain": "fwd",
        "new_price_eur": 47490, "trunk_volume_l": 452,
    },
    "toyota_bz4x_awd": {
        "length_mm": 4690, "ground_clearance_mm": 175, "drivetrain": "awd",
        "new_price_eur": 51490, "trunk_volume_l": 452,
    },
    "nissan_ariya_63": {
        "length_mm": 4595, "ground_clearance_mm": 170, "drivetrain": "fwd",
        "new_price_eur": 46500, "trunk_volume_l": 466,
    },
    "nissan_ariya_87": {
        "length_mm": 4595, "ground_clearance_mm": 170, "drivetrain": "awd",
        "new_price_eur": 57900, "trunk_volume_l": 466,
    },
    "nissan_leaf_40": {
        "length_mm": 4490, "ground_clearance_mm": 155, "drivetrain": "fwd",
        "new_price_eur": 36800, "trunk_volume_l": 435,
    },
    "nissan_leaf_62": {
        "length_mm": 4490, "ground_clearance_mm": 155, "drivetrain": "fwd",
        "new_price_eur": 42300, "trunk_volume_l": 435,
    },
    # === VOLKSWAGEN ===
    "vw_id3_pro": {
        "length_mm": 4261, "ground_clearance_mm": 150, "drivetrain": "rwd",
        "new_price_eur": 39990, "trunk_volume_l": 385,
    },
    "vw_id3_pro_s": {
        "length_mm": 4261, "ground_clearance_mm": 150, "drivetrain": "rwd",
        "new_price_eur": 46490, "trunk_volume_l": 385,
    },
    "vw_id4_pro": {
        "length_mm": 4584, "ground_clearance_mm": 174, "drivetrain": "rwd",
        "new_price_eur": 44490, "trunk_volume_l": 543,
    },
    "vw_id4_sr": {
        "length_mm": 4584, "ground_clearance_mm": 174, "drivetrain": "rwd",
        "new_price_eur": 39990, "trunk_volume_l": 543,
    },
    "vw_id5_pro": {
        "length_mm": 4599, "ground_clearance_mm": 174, "drivetrain": "rwd",
        "new_price_eur": 46490, "trunk_volume_l": 549,
    },
    "vw_id7_pro": {
        "length_mm": 4961, "ground_clearance_mm": 145, "drivetrain": "rwd",
        "new_price_eur": 53490, "trunk_volume_l": 532,
    },
    "vw_id_buzz": {
        "length_mm": 4712, "ground_clearance_mm": 164, "drivetrain": "rwd",
        "new_price_eur": 57990, "trunk_volume_l": 1121,
    },
    "vw_golf_20_tdi": {
        "length_mm": 4284, "ground_clearance_mm": 142, "drivetrain": "fwd",
        "new_price_eur": 35440, "trunk_volume_l": 381,
    },
    "vw_golf_20_tsi": {
        "length_mm": 4284, "ground_clearance_mm": 142, "drivetrain": "fwd",
        "new_price_eur": 33730, "trunk_volume_l": 381,
    },
    "vw_crafter_35": {
        "length_mm": 5986, "ground_clearance_mm": 180, "drivetrain": "fwd",
        "new_price_eur": 46800, "trunk_volume_l": 9300,
    },
    # === VOLVO ===
    "volvo_ex30_single": {
        "length_mm": 4233, "ground_clearance_mm": 165, "drivetrain": "rwd",
        "new_price_eur": 36590, "trunk_volume_l": 318,
    },
    "volvo_ex40_single": {
        "length_mm": 4440, "ground_clearance_mm": 175, "drivetrain": "fwd",
        "new_price_eur": 48900, "trunk_volume_l": 419,
    },
    "volvo_ex90_twin": {
        "length_mm": 5037, "ground_clearance_mm": 185, "drivetrain": "awd",
        "new_price_eur": 89900, "trunk_volume_l": 643,
    },
}


def update_yaml_file(path: Path) -> int:
    """Add missing fields to a YAML file. Returns count of updated vehicles."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "vehicles" not in data:
        return 0

    updated = 0
    for v in data["vehicles"]:
        vid = v.get("id", "")
        if vid not in VEHICLE_DATA:
            continue

        new_fields = VEHICLE_DATA[vid]
        # Insert new fields after image_attribution or before source_refs
        # We rebuild the dict in the right order
        existing_keys = list(v.keys())
        new_v = {}
        for key in existing_keys:
            new_v[key] = v[key]
            # After image_attribution, insert the new fields
            if key == "image_attribution":
                for nk, nv in new_fields.items():
                    if nk not in new_v:
                        new_v[nk] = nv
                        updated += 1

        # If image_attribution wasn't present, check for notes or source_refs
        if "image_attribution" not in existing_keys:
            # Insert before source_refs
            if "source_refs" in existing_keys:
                before = {}
                after = {}
                past_insert = False
                for key in existing_keys:
                    if key == "source_refs" and not past_insert:
                        for nk, nv in new_fields.items():
                            if nk not in v:
                                before[nk] = nv
                                updated += 1
                        past_insert = True
                    if past_insert:
                        after[key] = v[key]
                    else:
                        before[key] = v[key]
                new_v = {**before, **after}
            else:
                # Just append
                for nk, nv in new_fields.items():
                    if nk not in v:
                        new_v[nk] = nv
                        updated += 1

        v.update(new_v)

    # Write back
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    return updated


def main():
    total = 0
    for yaml_path in sorted(VEHICLES_DIR.glob("*.yaml")):
        count = update_yaml_file(yaml_path)
        if count > 0:
            print(f"  {yaml_path.name}: {count} fields added")
            total += count
        else:
            print(f"  {yaml_path.name}: no changes needed")
    print(f"\nTotal: {total} fields added")


if __name__ == "__main__":
    main()
