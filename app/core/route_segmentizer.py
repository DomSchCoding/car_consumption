"""Converts ProviderRoute geometry into internal RouteSegment list.

This module bridges the gap between provider data and the physics core.
It does not duplicate route_energy formulas; it produces RouteSegment
objects that the existing engine can consume.
"""

from __future__ import annotations

from app.core.route_geometry import (
    compute_elevation_gain_loss,
    cumulative_distances_km,
    resample_route_points,
)
from app.data.models import (
    CommuteScenario,
    DirectionMode,
    RoadType,
    Route,
    RouteSegment,
)
from app.services.provider_models import ProviderRoute

DEFAULT_CITY_STOP_PER_KM = 2.0
DEFAULT_RURAL_STOP_PER_KM = 0.2
DEFAULT_HIGHWAY_STOP_PER_KM = 0.0


class SegmentizationSettings:
    def __init__(
        self,
        target_segment_length_km: float = 1.0,
        max_segment_length_km: float = 5.0,
        min_segment_length_km: float = 0.1,
        slope_change_threshold: float = 0.03,
        speed_change_threshold_kmh: float = 15.0,
        default_stops_per_km: dict[str, float] | None = None,
        noise_threshold_m: float = 1.0,
    ) -> None:
        self.target_segment_length_km = target_segment_length_km
        self.max_segment_length_km = max_segment_length_km
        self.min_segment_length_km = min_segment_length_km
        self.slope_change_threshold = slope_change_threshold
        self.speed_change_threshold_kmh = speed_change_threshold_kmh
        self.noise_threshold_m = noise_threshold_m
        self.default_stops_per_km = default_stops_per_km or {
            "city": DEFAULT_CITY_STOP_PER_KM,
            "suburban": 1.0,
            "rural": DEFAULT_RURAL_STOP_PER_KM,
            "highway": DEFAULT_HIGHWAY_STOP_PER_KM,
            "mixed": 0.5,
        }


def _speed_to_road_type(speed_kmh: float) -> RoadType:
    if speed_kmh < 50:
        return RoadType.city
    elif speed_kmh < 80:
        return RoadType.rural
    elif speed_kmh < 110:
        return RoadType.suburban
    else:
        return RoadType.highway


def _stops_per_km_for_road_type(road_type: RoadType, settings: SegmentizationSettings) -> float:
    key = road_type.value
    return settings.default_stops_per_km.get(key, 0.5)


def provider_route_to_segments(
    provider_route: ProviderRoute,
    settings: SegmentizationSettings | None = None,
) -> list[RouteSegment]:
    if settings is None:
        settings = SegmentizationSettings()

    steps = provider_route.steps
    if steps:
        segments: list[RouteSegment] = []
        for i, step in enumerate(steps):
            speed = step.speed_kmh
            if speed is None:
                total_d = step.distance_km
                total_t = step.duration_s
                if total_d > 0 and total_t is not None and total_t > 0:
                    speed = total_d / (total_t / 3600.0)
                else:
                    speed = (
                        provider_route.summary_distance_km / (provider_route.summary_duration_s / 3600.0)
                        if provider_route.summary_duration_s and provider_route.summary_duration_s > 0
                        else 60.0
                    )

            road_type_str = step.road_type or "mixed"
            try:
                road_type = RoadType(road_type_str)
            except ValueError:
                road_type = _speed_to_road_type(speed)

            geom = step.geometry if step.geometry else provider_route.geometry
            gain, loss = 0.0, 0.0
            if geom and len(geom) > 1:
                computed_gain, computed_loss = compute_elevation_gain_loss(geom, settings.noise_threshold_m)
                if computed_gain > 0 or computed_loss > 0:
                    gain, loss = computed_gain, computed_loss
                elif provider_route.elevation_gain_m is not None or provider_route.elevation_loss_m is not None:
                    n_steps = len(steps) if steps else 1
                    gain = (provider_route.elevation_gain_m or 0.0) / n_steps if n_steps > 0 else 0.0
                    loss = (provider_route.elevation_loss_m or 0.0) / n_steps if n_steps > 0 else 0.0

            stops_per_km = _stops_per_km_for_road_type(road_type, settings)

            segments.append(
                RouteSegment(
                    name=step.name or f"Segment {i + 1}",
                    distance_km=round(step.distance_km, 3),
                    avg_speed_kmh=round(speed, 1),
                    road_type=road_type,
                    elevation_gain_m=round(gain, 1),
                    elevation_loss_m=round(loss, 1),
                    stops=round(stops_per_km, 2),
                    dwell_time_min=0.0,
                    headwind_kmh=0.0,
                )
            )
        return segments

    geometry = provider_route.geometry
    if not geometry or len(geometry) < 2:
        return []

    resampled = resample_route_points(geometry, settings.target_segment_length_km)
    dists = cumulative_distances_km(resampled)
    total_dist = dists[-1] if dists else 0.0
    if total_dist <= 0:
        return []

    avg_speed = (
        provider_route.summary_distance_km / (provider_route.summary_duration_s / 3600.0)
        if provider_route.summary_duration_s and provider_route.summary_duration_s > 0
        else 60.0
    )

    road_type = _speed_to_road_type(avg_speed)
    stops_per_km = _stops_per_km_for_road_type(road_type, settings)

    gain, loss = compute_elevation_gain_loss(resampled, settings.noise_threshold_m)

    segment = RouteSegment(
        name="Full route",
        distance_km=round(total_dist, 3),
        avg_speed_kmh=round(avg_speed, 1),
        road_type=road_type,
        elevation_gain_m=round(gain, 1),
        elevation_loss_m=round(loss, 1),
        stops=round(stops_per_km, 2),
        dwell_time_min=0.0,
        headwind_kmh=0.0,
    )
    return [segment]


def provider_route_to_route(
    provider_route: ProviderRoute,
    settings: SegmentizationSettings | None = None,
) -> Route:
    segments = provider_route_to_segments(provider_route, settings)
    name = f"{provider_route.start_label or 'Start'} → {provider_route.destination_label or 'Destination'}"
    return Route(
        id=f"route_{provider_route.provider}_{provider_route.cache_key or 'unknown'}",
        name=name,
        description=f"From {provider_route.provider} provider",
        segments=segments,
        notes="; ".join(provider_route.warnings) if provider_route.warnings else None,
    )


def provider_route_to_commute_scenario(
    provider_route: ProviderRoute,
    direction_mode: DirectionMode = DirectionMode.one_way,
    invert_wind_on_return: bool = True,
    settings: SegmentizationSettings | None = None,
) -> CommuteScenario:
    route = provider_route_to_route(provider_route, settings)
    return CommuteScenario(
        route=route,
        direction_mode=direction_mode,
        invert_wind_on_return=invert_wind_on_return,
    )
