# 11 - Migration Plan from Current Repository

## Ziel

Die neue Knowledge Base und Architektur sollen den vorhandenen funktionalen Stand nicht zerstoeren.

## Schritt 1 - Knowledge einchecken

- Bestehende `knowledge/` sichern
- Neue v2-Dateien hinzufuegen
- `AGENTS.md` mergen
- README nur minimal aktualisieren

Keine Codeaenderung.

## Schritt 2 - Tests baseline

Ausfuehren:

```bash
pytest
ruff check app/
ruff format --check app/
pyright app/
```

Ergebnis dokumentieren.

## Schritt 3 - main.py Verantwortlichkeiten listen

In `main.py` identifizieren:

- Chart-Funktionen
- Tabellen-Funktionen
- Fahrzeugauswahl
- Ranking
- Settings
- globaler State
- Eventhandler

Keine Aenderung.

## Schritt 4 - Chart/Table extrahieren

Neue Dateien:

```text
app/ui/charts.py
app/ui/tables.py
```

Nur Funktionen verschieben, Verhalten beibehalten.

Tests:

- Import-Test
- falls moeglich Snapshot/Smoke fuer Figure-Daten

## Schritt 5 - State kapseln

Neue Datei:

```text
app/ui/state.py
```

Ziel:

- selected vehicles
- filters
- physics params
- ranking options

Nicht sofort ueber-engineeren.

## Schritt 6 - Route Models

In `data/models.py` oder neuer Datei `data/route_models.py`:

- RouteSegment
- Route
- CommuteScenario
- RouteEnergyBreakdown

Tests nur Validation.

## Schritt 7 - Route Core

Neue Datei:

```text
app/core/route_energy.py
```

Funktionen:

- `calculate_segment_energy`
- `calculate_route_energy`
- `reverse_route`
- `calculate_commute_energy`

Tests umfassend.

## Schritt 8 - Route UI MVP

Neue Seite oder Tab:

- einfache Route
- Hin-und-Rueckweg
- Ergebnis je Fahrzeug

Erst nach Core-Tests.

## Schritt 9 - Preis/TCO getrennt

Nicht mit Route vermischen, sondern als eigene Phase.

## Schritt 10 - Datenqualitaet

Erst wenn Datenmodell stabil ist.

## Rueckfallstrategie

Jeder Schritt soll isoliert revertierbar sein.

Keine parallelen grossen Umbauten:

- nicht gleichzeitig Route, Preise und Importer
- nicht gleichzeitig UI-Redesign und Core-Formeln
- nicht gleichzeitig Datenmodell und Scraping

## Risikoarme Reihenfolge

1. Knowledge
2. Tests baseline
3. Refactor charts/tables
4. Route models
5. Route core
6. Route UI
7. Preise
8. Importer
9. Advanced physics
