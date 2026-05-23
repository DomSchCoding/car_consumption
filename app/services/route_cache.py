"""File-based cache for route provider responses.

Stores normalized ProviderRoute JSON keyed by a stable hash derived from
provider, profile, coordinates, and schema version. Never caches API keys.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.services.provider_models import ProviderRoute

CACHE_DIR = Path(".cache/routes")
SCHEMA_VERSION = 1


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_cache_key(
    provider: str,
    profile: str,
    start_lat: float,
    start_lon: float,
    dest_lat: float,
    dest_lon: float,
    schema_version: int = SCHEMA_VERSION,
) -> str:
    raw = f"{provider}|{profile}|{start_lat:.6f},{start_lon:.6f}|{dest_lat:.6f},{dest_lon:.6f}|v{schema_version}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def write_route(route: ProviderRoute) -> Path:
    _ensure_cache_dir()
    key = route.cache_key or compute_cache_key(
        provider=route.provider,
        profile=route.profile,
        start_lat=route.start.lat,
        start_lon=route.start.lon,
        dest_lat=route.destination.lat,
        dest_lon=route.destination.lon,
    )
    path = CACHE_DIR / f"{key}.json"
    data = route.model_dump(mode="json")
    data.pop("raw_response", None)
    data.pop("cache_key", None)
    data["_schema_version"] = SCHEMA_VERSION
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_route(cache_key: str) -> ProviderRoute | None:
    path = CACHE_DIR / f"{cache_key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_schema_version", None)
        data["cache_key"] = cache_key
        return ProviderRoute.model_validate(data)
    except Exception:
        return None


def clear_cache() -> int:
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    return count
