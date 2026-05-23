# 10 - Agent skills and workflow v3

## Skills the coding agent needs now

### GIS/routing basics

The agent must understand:

- latitude/longitude order vs longitude/latitude order differs by API
- route polyline decoding
- route geometry vs route steps vs route legs
- cumulative distance along a polyline
- elevation gain/loss smoothing
- map tile attribution

### API integration basics

The agent must implement:

- env-based API key usage
- provider timeouts
- response parsing with Pydantic or explicit validation
- cache hit/miss logic
- graceful fallback
- no network in unit tests

### NiceGUI map UI

The agent should use:

- `ui.leaflet` for map rendering
- components for reusable map helpers
- Plotly for elevation/speed/energy charts
- visible warnings and provider status

### Scientific humility

The agent must not overstate accuracy. It should label:

- speed from provider duration as estimated
- elevation from DEM as sampled
- stop count as estimated
- consumption as model estimate

## Recommended coding workflow

1. Read current files:
   - `app/core/route_energy.py`
   - `app/data/models.py`
   - `app/ui/pages/route_planner.py`
   - `app/main.py`
   - this knowledge base
2. Run tests.
3. Add service/provider models and tests.
4. Add demo route fixtures and provider.
5. Add segmentizer and tests.
6. Add map page using demo provider.
7. Wire page into `app/main.py` without breaking manual page.
8. Add ORS provider behind env key.
9. Add README/knowledge updates.
10. Run tests, lint, format.

## Anti-patterns

- Big-bang rewrite of route_energy.
- UI calls `httpx.get` directly.
- Tests that require ORS_API_KEY.
- Hard-coded personal routes.
- Silent fallback to wrong units or flat elevation.
- Manual route page deletion before map route is stable.
