# 08 - UI Redesign Plan

*Stand: 2026-05-26 | Branch: `hermes/ui-redesign-2026`*

## Ziel

Komplettes UI-Redesign mit konsistentem Layout, zentralem Theme, NiceGUI-nativen Komponenten und responsivem Design. Physics, Data und Services bleiben unverändert.

## Probleme im aktuellen UI

| Problem | Beschreibung |
|---------|-------------|
| Kein Shared Layout | Jede Seite hat eigenes Header, CSS, Navigation |
| CSS-Duplizierung | LIGHT_CSS, DARK_CSS in main.py UND route_pages |
| Dashboard = Single-Page Wall | Alles vertikal gestapelt, keine Tabs/Sektionen |
| HTML-Tables | Raw HTML mit Inline-Styles, kein Dark-Mode, keine Accessibility |
| Route Planner Pages | 756+ Zeilen, geocoding in UI, keine Loading-States |
| State Management | Module-level SESSION dict, keine Session-Isolation |
| Kein Responsive Design | Alles Desktop-first, mobil unbrauchbar |

## Phasen-Übersicht

### Phase 1: Foundation — Shared Layout & Theme ✅ DONE
- `app/ui/layout.py` — Shared page layout mit Top-Nav, Breadcrumb, Dark-Mode Toggle
- `app/ui/theme.py` — Zentrale CSS (light/dark), Color-Palette, Card-Styles
- `app/ui/components/nav.py` — Navigation-Komponente
- Alle Pages wrappen Inhalt in Shared Layout
- CSS wird einmal via `ui.add_css()` injiziert

### Phase 2: Dashboard Redesign (`/`) ✅ DONE
- **Tabs statt vertikaler Stapel:**
  - **Compare** (default): Vehicle Selector (links) + Chart (rechts)
  - **Table**: Consumption Table
  - **Ranking**: Full fleet ranking mit Filtern
  - **Settings**: Physics Params, Environment
- Duplicate `nav_bar()` Calls entfernt (wird von `page_layout()` gehandhabt)

### Phase 3: NiceGUI Tables statt HTML
- `build_table()` → `ui.aggrid` oder `ui.table`
- `build_ranking_list()` → `ui.list` mit `ui.linear_progress`
- `build_vehicle_detail_html()` → Native NiceGUI Cards/Grid
- Auto Dark-Mode, responsive, sortable

### Phase 4: Route Planner Improvements
- **Map Route (`/route`):**
  - Loading Spinner während Geocoding/Routing
  - Error Cards statt scattered labels
  - Energy Results als Tabs: Overview | Elevation | Speed | Breakdown
- **Manual Route (`/route/manual`):**
  - Gleiche Behandlung — Cards, NiceGUI Components
  - Results Table konvertiert

### Phase 5: Vehicle Detail Page
- HTML → NiceGUI Cards
- Grid-Layout (2 col desktop, 1 col mobile)
- Sources als expandable List Items

### Phase 6: Responsive Design
- Mobile: columns vertikal stapeln
- Tablet: 2-column wo möglich
- Desktop: aktuelle Layouts erhalten
- `ui.query()` für Media Queries

## Nicht ändern
- `app/core/` — Physics, Route Energy, Geometry, Segmentizer
- `app/data/` — Models, Repository
- `app/services/` — Routing, Geocoding, Elevation, Cache
- Test-Dateien (außer UI smoke tests anpassen)
- `app/assets/` — YAML Daten

## Qualitätskriterien pro Phase
- Alle bestehenden Tests müssen weiterpassen (226 core tests)
- App startet ohne Errors: `python -m app.main`
- Keine Secrets/Keys im Code
- Ruff lint/format clean
- Pyright type checking clean

## Fortschritt

- [x] Phase 1: Layout + Theme (2026-05-26)
- [x] Phase 2: Dashboard Redesign (2026-05-26)
- [ ] Phase 3: NiceGUI Tables
- [ ] Phase 4: Route Planner
- [ ] Phase 5: Vehicle Detail
- [ ] Phase 6: Responsive
