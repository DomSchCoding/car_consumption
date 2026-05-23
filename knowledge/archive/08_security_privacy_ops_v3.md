# 08 - Security, privacy and operations v3

## API keys

Never commit API keys. Read keys from environment variables:

```text
ORS_API_KEY
GRAPHHOPPER_API_KEY
VALHALLA_API_KEY
ROUTING_PROVIDER
OSRM_BASE_URL
```

Show status in UI:

```text
OpenRouteService: configured
OSRM: configured at local URL
Elevation: unavailable, using flat fallback
```

## Location privacy

Routes can contain personal information such as home and workplace. Therefore:

- do not commit user route cache files
- add `.cache/` to `.gitignore`
- allow clearing local cache
- avoid sending addresses to multiple providers unnecessarily
- show provider name before external route calculation

## Caching

Caching is required because:

- route APIs have quotas
- elevation APIs have quotas
- debugging should be reproducible
- UI changes should not re-fetch the same route repeatedly

Cache normalized provider results, not just raw responses. Include schema version.

## Attribution

Map tiles and data providers require attribution. The UI must preserve map tile attribution and docs must list provider requirements.

## Offline/demo mode

The app must always work in demo mode without API key. Demo mode is not a toy; it is the foundation for tests and screenshots.

## Provider failure behavior

If provider fails:

1. use cached result if available
2. otherwise show a clear error and offer demo route/manual route
3. never crash the page
4. never silently switch to flat route without warning
