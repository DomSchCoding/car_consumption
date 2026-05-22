"""Download vehicle images from Wikipedia.

Uses the Wikipedia API to find and download thumbnail images for each vehicle.
Images are stored as app/assets/images/{vehicle_id}.jpg with a max width of 400px.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
VEHICLES_DIR = ASSETS_DIR / "vehicles"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.models import Vehicle
from app.data.repository import VehicleRepository

WIKI_API = "https://en.wikipedia.org/w/api.php"
DE_WIKI_API = "https://de.wikipedia.org/w/api.php"
USER_AGENT = "CarConsumptionApp/1.0 (https://github.com/example; educational use)"
THUMB_SIZE = 400
RATE_LIMIT = 0.5

SEARCH_TERMS = {
    "hyundai_ioniq_28": "Hyundai Ioniq Electric",
    "hyundai_ioniq_38": "Hyundai Ioniq Electric",
    "hyundai_ioniq5_rwd": "Hyundai Ioniq 5",
    "hyundai_ioniq5_awd": "Hyundai Ioniq 5",
    "hyundai_ioniq6_rwd": "Hyundai Ioniq 6",
    "hyundai_kona_ev_39": "Hyundai Kona Electric",
    "hyundai_kona_ev_64": "Hyundai Kona Electric",
    "hyundai_kona_ev_fl_48": "Hyundai Kona Electric",
    "hyundai_kona_ev_fl_65": "Hyundai Kona Electric",
    "hyundai_kona_ev_48_n": "Hyundai Kona Electric (2024)",
    "hyundai_kona_ev_65_n": "Hyundai Kona Electric (2024)",
    "kia_ev6_sr": "Kia EV6",
    "kia_ev6_rwd": "Kia EV6",
    "kia_ev9_awd": "Kia EV9",
    "kia_niro_ev_39": "Kia Niro EV",
    "kia_niro_ev_64": "Kia Niro EV",
    "tesla_model3_rwd": "Tesla Model 3",
    "tesla_model3_lr": "Tesla Model 3",
    "tesla_model3_highland_rwd": "Tesla Model 3",
    "tesla_model3_highland_lr": "Tesla Model 3",
    "tesla_model_y_rwd": "Tesla Model Y",
    "tesla_model_y_lr": "Tesla Model Y",
    "tesla_model_s_lr": "Tesla Model S",
    "vw_id3_pro": "Volkswagen ID.3",
    "vw_id3_pro_s": "Volkswagen ID.3",
    "vw_id4_pro": "Volkswagen ID.4",
    "vw_id4_sr": "Volkswagen ID.4",
    "vw_id5_pro": "Volkswagen ID.5",
    "vw_id7_pro": "Volkswagen ID.7",
    "vw_id_buzz": "Volkswagen ID. Buzz",
    "vw_golf_20_tdi": "Volkswagen Golf",
    "vw_golf_20_tsi": "Volkswagen Golf",
    "vw_crafter_35": "Volkswagen Crafter",
    "bmw_i4_edrive40": "BMW i4",
    "bmw_i4_m50": "BMW i4 M50",
    "bmw_i5_edrive40": "BMW i5",
    "bmw_ix_xdrive40": "BMW iX",
    "bmw_i7_xdrive60": "BMW i7",
    "bmw_320d": "BMW 3 Series (G20)",
    "mercedes_eqe_350": "Mercedes-Benz EQE",
    "mercedes_eqs_450": "Mercedes-Benz EQS",
    "mercedes_eqa_250": "Mercedes-Benz EQA",
    "mercedes_eqb_300": "Mercedes-Benz EQB",
    "mercedes_eqv_300": "Mercedes-Benz EQV",
    "mercedes_c220d": "Mercedes-Benz C-Class (W206)",
    "audi_q4_etron_40": "Audi Q4 e-tron",
    "audi_q4_etron_45": "Audi Q4 e-tron",
    "audi_q8_etron_50": "Audi Q8 e-tron",
    "audi_etron_gt": "Audi e-tron GT",
    "porsche_taycan_4s": "Porsche Taycan",
    "porsche_macan_ev_4": "Porsche Macan Electric",
    "peugeot_e208_50": "Peugeot e-208",
    "peugeot_e308_54": "Peugeot e-308",
    "peugeot_e3008_98": "Peugeot e-3008",
    "renault_zoe_52": "Renault Zoe",
    "renault_megane_e_tech_60": "Renault Megane E-Tech Electric",
    "renault_5_e_tech_52": "Renault 5 E-Tech",
    "fiat_500e_42": "Fiat 500e",
    "fiat_500e_24": "Fiat 500e",
    "ford_mustang_mach_e_sr": "Ford Mustang Mach-E",
    "ford_mustang_mach_e_lr": "Ford Mustang Mach-E",
    "ford_explorer_ev": "Ford Explorer EV",
    "ford_focus_10_ecoboost": "Ford Focus",
    "skoda_enyaq_60": "Skoda Enyaq",
    "skoda_enyaq_80": "Skoda Enyaq",
    "skoda_elroq_60": "Skoda Elroq",
    "volvo_ex30_single": "Volvo EX30",
    "volvo_ex40_single": "Volvo EX40",
    "volvo_ex90_twin": "Volvo EX90",
    "toyota_bz4x_fwd": "Toyota bZ4X",
    "toyota_bz4x_awd": "Toyota bZ4X",
    "nissan_ariya_63": "Nissan Ariya",
    "nissan_ariya_87": "Nissan Ariya",
    "nissan_leaf_40": "Nissan Leaf",
    "nissan_leaf_62": "Nissan Leaf",
    "opel_corsa_e_50": "Opel Corsa-e",
    "opel_astra_e_54": "Opel Astra Electric",
    "opel_mokka_e_50": "Opel Mokka-e",
    "polestar_2_std": "Polestar 2",
    "polestar_2_lr": "Polestar 2",
    "polestar_3_lr": "Polestar 3",
    "polestar_4_sr": "Polestar 4",
    "cupra_tavascan_vz": "Cupra Tavascan",
    "seat_mii_electric": "SEAT Mii Electric",
    "citroen_ec4_50": "Citroen e-C4",
    "mazda_mx30": "Mazda MX-30",
    "honda_e": "Honda e",
    "honda_e_ns1": "Honda e:NS1",
    "genesis_gv60_adv": "Genesis GV60",
    "jeep_avenger": "Jeep Avenger",
    "mg4_excite_51": "MG4 (electric car)",
    "mg4_trophy_64": "MG4 (electric car)",
    "byd_seal_design": "BYD Seal",
    "byd_atto3": "BYD Atto 3",
    "byd_dolphin": "BYD Dolphin",
}


def wiki_request(params: dict, api_url: str = WIKI_API) -> dict | None:
    headers = {"User-Agent": USER_AGENT}
    qs = urllib.parse.urlencode(params)
    url = f"{api_url}?{qs}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def get_wiki_image(title: str, api_url: str = WIKI_API) -> tuple[str | None, str | None]:
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages|revisions",
        "format": "json",
        "pithumbsize": THUMB_SIZE,
        "piprop": "thumbnail",
        "rvprop": "ids",
    }
    data = wiki_request(params, api_url)
    if not data:
        return None, None

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        thumb = page.get("thumbnail", {})
        url = thumb.get("source")
        if url:
            attribution = f"Wikipedia ({'de' if 'de.wikipedia' in api_url else 'en'})"
            return url, attribution
    return None, None


def search_wiki_title(query: str, api_url: str = WIKI_API) -> str | None:
    params = {
        "action": "opensearch",
        "search": query,
        "format": "json",
        "limit": 3,
    }
    data = wiki_request(params, api_url)
    if not data:
        return None
    titles = data[1] if len(data) > 1 else []
    return titles[0] if titles else None


def download_image(url: str, dest: Path) -> bool:
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            dest.write_bytes(content)
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    repo = VehicleRepository()
    vehicles = repo.get_all()

    results: dict[str, dict] = {}
    already_downloaded_ids: set[str] = set()
    for img_path in IMAGES_DIR.glob("*.jpg"):
        already_downloaded_ids.add(img_path.stem)

    for v in vehicles:
        if v.id in already_downloaded_ids:
            print(f"  SKIP (exists): {v.id}")
            continue

        search_term = SEARCH_TERMS.get(v.id, f"{v.make} {v.model}")
        print(f"  {v.id}: searching for '{search_term}'...")

        image_url = None
        attribution = None

        for api_url in [WIKI_API, DE_WIKI_API]:
            title = search_wiki_title(search_term, api_url)
            if title:
                image_url, attribution = get_wiki_image(title, api_url)
                if image_url:
                    break
            time.sleep(RATE_LIMIT)

        if image_url:
            dest = IMAGES_DIR / f"{v.id}.jpg"
            if download_image(image_url, dest):
                results[v.id] = {
                    "status": "ok",
                    "attribution": attribution,
                    "file": str(dest.name),
                }
                print(f"    -> downloaded")
            else:
                results[v.id] = {"status": "download_failed", "attribution": None}
                print(f"    -> download FAILED")
        else:
            results[v.id] = {"status": "no_image_found", "attribution": None}
            print(f"    -> no image found")

        time.sleep(RATE_LIMIT)

    ok = sum(1 for r in results.values() if r["status"] == "ok")
    fail = sum(1 for r in results.values() if r["status"] != "ok")
    print(f"\nDone: {ok} downloaded, {fail} failed/missing out of {len(results)} attempted")

    meta_path = IMAGES_DIR / "image_attribution.json"
    existing = {}
    if meta_path.exists():
        with open(meta_path) as f:
            existing = json.load(f)
    existing.update(results)
    with open(meta_path, "w") as f:
        json.dump(existing, f, indent=2)


if __name__ == "__main__":
    main()