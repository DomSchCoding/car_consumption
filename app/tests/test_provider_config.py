"""Tests for live provider configuration and feature flags."""

from __future__ import annotations

import os

from app.services.provider_config import (
    get_open_meteo_elevation_url,
    get_osrm_base_url,
    get_user_agent,
    is_live_routing_enabled,
    is_nominatim_enabled,
    is_open_meteo_elevation_enabled,
    is_osrm_enabled,
    live_provider_status,
)


class TestProviderConfigDefaults:
    def test_live_routing_disabled_by_default(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_LIVE_ROUTING", None)
        assert is_live_routing_enabled() is False

    def test_nominatim_disabled_by_default(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_NOMINATIM", None)
        assert is_nominatim_enabled() is False

    def test_osrm_disabled_by_default(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM", None)
        assert is_osrm_enabled() is False

    def test_open_meteo_disabled_by_default(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION", None)
        assert is_open_meteo_elevation_enabled() is False

    def test_default_user_agent(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_USER_AGENT", None)
        assert "car_consumption" in get_user_agent()

    def test_default_osrm_url(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_OSRM_BASE_URL", None)
        assert "router.project-osrm.org" in get_osrm_base_url()

    def test_default_open_meteo_url(self) -> None:
        os.environ.pop("CAR_CONSUMPTION_OPEN_METEO_ELEVATION_URL", None)
        assert "open-meteo" in get_open_meteo_elevation_url()


class TestProviderConfigEnabled:
    def test_live_routing_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_LIVE_ROUTING"] = "true"
        try:
            assert is_live_routing_enabled() is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_LIVE_ROUTING"]

    def test_nominatim_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_NOMINATIM"] = "true"
        try:
            assert is_nominatim_enabled() is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_NOMINATIM"]

    def test_osrm_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM"] = "1"
        try:
            assert is_osrm_enabled() is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM"]

    def test_open_meteo_enabled(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION"] = "yes"
        try:
            assert is_open_meteo_elevation_enabled() is True
        finally:
            del os.environ["CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION"]

    def test_custom_user_agent(self) -> None:
        os.environ["CAR_CONSUMPTION_USER_AGENT"] = "test_app/1.0"
        try:
            assert get_user_agent() == "test_app/1.0"
        finally:
            del os.environ["CAR_CONSUMPTION_USER_AGENT"]

    def test_live_provider_status(self) -> None:
        os.environ["CAR_CONSUMPTION_ENABLE_LIVE_ROUTING"] = "true"
        os.environ["CAR_CONSUMPTION_ENABLE_NOMINATIM"] = "true"
        os.environ["CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM"] = "false"
        os.environ["CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION"] = "false"
        try:
            status = live_provider_status()
            assert status["live_routing"] is True
            assert status["nominatim"] is True
            assert status["osrm"] is False
            assert status["open_meteo_elevation"] is False
        finally:
            for key in [
                "CAR_CONSUMPTION_ENABLE_LIVE_ROUTING",
                "CAR_CONSUMPTION_ENABLE_NOMINATIM",
                "CAR_CONSUMPTION_ENABLE_PUBLIC_OSRM",
                "CAR_CONSUMPTION_ENABLE_OPEN_METEO_ELEVATION",
            ]:
                os.environ.pop(key, None)
