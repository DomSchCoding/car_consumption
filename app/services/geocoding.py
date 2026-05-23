"""Nominatim geocoding provider with rate limiting and caching.

Uses geopy with a custom user agent. Rate-limited to 1 request/second.
Results are cached in the route cache directory.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from app.services.provider_config import get_user_agent, is_nominatim_enabled
from app.services.provider_models import GeoCandidate, GeoPoint, ProviderStatus

GEOCODE_CACHE_DIR = Path(".cache/geocode")

_logger = logging.getLogger(__name__)

_last_request_time: float = 0.0
_MIN_REQUEST_INTERVAL = 1.0


def _rate_limit() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def _cache_key(query: str) -> str:
    import hashlib

    return hashlib.sha256(f"nominatim|{query.strip().lower()}".encode()).hexdigest()[:16]


def _ensure_cache_dir() -> None:
    GEOCODE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _read_cache(key: str) -> list[dict] | None:
    path = GEOCODE_CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(key: str, data: list[dict]) -> None:
    _ensure_cache_dir()
    path = GEOCODE_CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def nominatim_status() -> ProviderStatus:
    enabled = is_nominatim_enabled()
    return ProviderStatus(
        name="nominatim",
        configured=enabled,
        available=enabled,
        message="Nominatim geocoding enabled" if enabled else "Disabled (set CAR_CONSUMPTION_ENABLE_NOMINATIM=true)",
    )


def geocode(query: str) -> tuple[list[GeoCandidate], str]:
    """Geocode an address using Nominatim.

    Returns (candidates, error_message). On success, error_message is empty.
    On failure, candidates is empty and error_message describes the problem.
    """
    if not is_nominatim_enabled():
        return [], "Nominatim geocoding is not enabled. Set CAR_CONSUMPTION_ENABLE_NOMINATIM=true"

    key = _cache_key(query)
    cached = _read_cache(key)
    if cached is not None:
        return [GeoCandidate.model_validate(c) for c in cached], ""

    _rate_limit()

    try:
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent=get_user_agent())
        results = geolocator.geocode(query, exactly_one=False, limit=5)
    except Exception as exc:
        msg = f"Geocoding request failed: {type(exc).__name__}: {exc}"
        _logger.warning(msg)
        return [], msg

    if results is None or len(results) == 0:
        return [], f"No results for '{query}'"

    candidates = []
    for r in results:
        if r.latitude is not None and r.longitude is not None:
            candidates.append(
                GeoCandidate(
                    label=r.address or query,
                    point=GeoPoint(lat=r.latitude, lon=r.longitude),
                    confidence=0.8 if r.raw.get("importance", 0) > 0.5 else 0.5,
                    provider="nominatim",
                )
            )

    _write_cache(key, [c.model_dump(mode="json") for c in candidates])
    return candidates, ""
