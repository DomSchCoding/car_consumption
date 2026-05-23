# Task List - Vehicle Consumption Analyzer

## Completed
- [x] Bug fix: `VehicleType.diesel` -> `FuelType.diesel`
- [x] Bug fix: Pydantic model field accepts YAML integers
- [x] Vehicle database expanded to 60 vehicles (22 brands)
- [x] Chart redesign: total curves only, hover shows breakdown with icons
- [x] Settings-Menü: Parameters, Speed Range, ICE Comparison in ausklappbarem Settings-Bereich
- [x] Vehicle-Auswahl: scrollbare Liste ausgewählter Fahrzeuge mit 🗑️ Remove-Button
- [x] Defekte Fahrzeugliste unten entfernt
- [x] Marken-Dropdown: Nur eine Marke anzeigen, dann deren Modelle
- [x] EV/ICE Filter-Checkboxen: Marken ohne passende Modelle verschwinden aus Dropdown
- [x] Verbrauchs-Charts-Liste: Speed-Dropdown, sortierte Balken-Liste
- [x] Search/filter bar in vehicle model list
- [x] Dark/light theme toggle
- [x] Vehicle detail page with all specs and sources
- [x] Data quality indicators: source confidence badges, missing field tags
- [x] Vehicle comparison limit (max 8)
- [x] Export chart as PNG (kaleido)
- [x] Physics formula explanation in Settings
- [x] Verified EPA data for 12 US-market vehicles
- [x] Model/selected lists as HTML (fixed clear/rebuild race condition)
- [x] All 44 tests passing, ruff clean

## Active Sprint: Phase 2 Physics

### Tire Model (in progress)
- [ ] Add per-vehicle default c_rr based on tire dimensions and class
- [ ] Add tire data fields to Vehicle model (width, aspect, rim)
- [ ] Classify tires: eco-LRR, standard, sport, SUV, van/truck
- [ ] Per-vehicle c_rr shown in detail page and table
- [ ] Global c_rr slider overrides individual values

### Remaining Phase 2
- [ ] Acceleration profiles and regenerative braking
- [ ] Temperature effects on battery and air density
- [ ] Wind and elevation profiles
- [ ] Payload effects
- [ ] Aux power per vehicle (heat pump vs resistive)

### UI Enhancements
- [ ] Responsive layout for mobile
- [ ] Export chart as interactive HTML
- [ ] Scenario presets (city, highway, winter)

### New Pages
- [ ] Data quality dashboard
- [ ] Scenario editor page

### Data Import
- [ ] EPA/fueleconomy.gov CSV importer
- [ ] EV Database scraper (check ToS first)
- [ ] Manufacturer data importer

## Progress Notes
- 2026-05-22: MVP complete, 6 demo vehicles
- 2026-05-22: Bug fixes, 60 vehicles, modern UI, chart redesign
- 2026-05-22: Sprint 2 - Settings menu, brand dropdown, EV/ICE filter, ranking list
- 2026-05-22: Sprint 3 - Search bar, dark theme, vehicle detail page, data quality
- 2026-05-22: Sprint 4 - EPA data, PNG export, vehicle limit, physics formulas
- 2026-05-22: Sprint 5 - HTML lists fix clear/rebuild bugs, URL-based add/remove
- Next: per-vehicle tire c_rr, acceleration profiles, scenario editor
