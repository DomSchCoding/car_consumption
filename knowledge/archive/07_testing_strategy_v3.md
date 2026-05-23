# 07 - Testing strategy v3

## Testing principle

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

### 6. UI smoke tests

MVP:

```text
test_map_route_page_imports
test_manual_route_page_still_imports
test_route_controls_construct_without_provider
```

Full browser/UI tests can come later. NiceGUI supports testing patterns, but first protect the domain and service layers.

## Fixtures

Create fixture files:

```text
app/tests/fixtures/routes/demo_city_commute.json
app/tests/fixtures/routes/demo_hilly_commute.json
app/tests/fixtures/routes/demo_highway_route.json
```

Each fixture should include:

```text
provider route response or normalized ProviderRoute JSON
expected distance range
expected elevation gain/loss range
expected duration range
expected segment count range
```

## Regression tests for old behavior

Keep existing route_energy tests. Add one test that ensures the existing manual route path can still build a `Route` and produce consumption results.

## Network integration tests

Optional, disabled by default:

```text
pytest -m integration
```

Only run if an API key is present. Never make these part of normal CI until quota and stability are solved.
