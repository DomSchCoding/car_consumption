# 06 - Testing Strategy

## Core principle

No unit test may depend on an external routing/elevation/geocoding API. All network behavior must be mocked or fixture-based.

## Test layers

### 1. Provider model tests

```text
test_geopoint_validation
test_provider_route_minimum_fields
test_route_request_hash_stability
```

### 2. Cache tests

```text
test_route_cache_key_is_stable
test_cache_write_and_read
test_cache_miss_returns_none
test_cache_does_not_store_api_key
```

### 3. Geometry tests

```text
test_haversine_distance_known_values
test_cumulative_distance_monotonic
test_resample_preserves_start_end
test_elevation_gain_loss_with_noise_threshold
```

### 4. Segmentizer tests

```text
test_flat_route_becomes_expected_segment_count
test_speed_from_step_duration
test_fallback_average_speed_when_no_steps
test_slope_change_splits_segment
test_route_segments_have_positive_distance_and_speed
```

### 5. Physics integration tests

```text
test_provider_route_to_energy_flat_route_matches_manual_route
test_hilly_return_trip_has_energy_loss_despite_net_zero_height
test_downhill_recovery_is_less_than_climb_energy
test_outward_return_breakdown_is_reported_separately
test_headwind_changes_aero_energy
```

### 6. Route energy regression tests (existing, must keep)

```text
test_flat_route_no_stops_matches_constant_speed
test_double_distance_doubles_energy
test_elevation_gain_increases_consumption
test_return_trip_swaps_gain_loss
test_round_trip_has_net_zero_height_but_positive_losses
test_zero_regen_no_recovery
test_full_regen_maximum_theoretical_recovery
test_stops_increase_consumption
test_aux_increases_with_duration
test_headwind_increases_aero
test_tailwind_reduces_aero_but_not_negative
```

### 7. UI smoke tests

```text
test_map_route_page_imports
test_manual_route_page_still_imports
test_route_controls_construct_without_provider
```

## Fixtures

Create fixture files:

```text
app/tests/fixtures/routes/demo_city_commute.json
app/tests/fixtures/routes/demo_hilly_commute.json
app/tests/fixtures/routes/demo_highway_route.json
```

Each fixture includes:

```text
ProviderRoute JSON (normalized)
expected distance range
expected elevation gain/loss range
expected duration range
expected segment count range
```

## Network integration tests

Optional, disabled by default:

```text
pytest -m integration
```

Only run if an API key is present. Never in normal CI until quota and stability are solved.

## Security tests

```text
test_no_api_key_in_cache_files
test_cache_directory_ignored_by_git
test_demo_provider_works_without_keys
```

## Regression

Keep existing route_energy tests. Add one test ensuring the manual route path still builds a Route and produces consumption results.

## Definition of Done

Every change must pass:

```bash
pytest
ruff check app/
ruff format app/
```

Type checking with `pyright app/` is recommended. Core/data modules must be clean; UI may have documented exceptions for NiceGUI types.