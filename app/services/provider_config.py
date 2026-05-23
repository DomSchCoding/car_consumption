"""Provider configuration from environment variables.

All live providers are disabled by default. Set environment variables to enable.
"""

from __future__ import annotations

import os

_DEFAULT_USER_AGENT = "car_consumption_private_dev/0.1"


def is_live_routing_enabled() -> bool:
    return os.environ.get("CAR_CONSUMPTION_ENABLE_LIVE_ROUTING", "false").lower() in ("true", "1", "yes")


def is_nominatim_enabled() -> bool:
    return os.environ.get("CAR_CONSUMPTION_ENABLE_NOMINATIM", "false").lower() in ("true", "1", "yes")


def is_osrm_enabled() -> bool:
    return os.environ.get("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM", "false").lower() in ("true", "1", "yes")


def is_open_meteo_elevation_enabled() -> bool:
    return os.environ.get("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION", "false").lower() in ("true", "1", "yes")


def get_user_agent() -> str:
    return os.environ.get("CAR_CONSUMPTION_USER_AGENT", _DEFAULT_USER_AGENT)


def get_osrm_base_url() -> str:
    return os.environ.get("CAR_CONSUMPTION_OSRM_BASE_URL", "https://router.project-osrm.org")


def get_open_meteo_elevation_url() -> str:
    return os.environ.get("CAR_CONSUMPTION_OPEN_METEO_ELEVATION_URL", "https://api.open-meteo.com/v1/elevation")


def live_provider_status() -> dict[str, bool]:
    return {
        "live_routing": is_live_routing_enabled(),
        "nominatim": is_nominatim_enabled(),
        "osrm": is_osrm_enabled(),
        "open_meteo_elevation": is_open_meteo_elevation_enabled(),
    }
