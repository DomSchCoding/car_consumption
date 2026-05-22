# AGENTS.md - Arbeitsweise fuer opencode

## Projektziel
Entwickle eine NiceGUI-Webapp zur physikalisch fundierten Analyse und zum Vergleich von Fahrzeugverbraeuchen, mit Schwerpunkt Elektroautos, Aerodynamik, Rollwiderstand, Nebenverbraucher und Vergleich zu Verbrenner-Energieaequivalenten.

Die App soll nicht nur WLTP/EPA-Werte anzeigen, sondern den theoretisch minimalen Energiebedarf aus Fahrzeugparametern und Fahrprofilen transparent berechnen und gegen reale Verbrauchsdaten stellen.

## Kernprinzipien
- Physik zuerst, reale Daten danach plausibilisieren.
- Jede Fahrzeugangabe bekommt Quelle, Datum, Einheit, Vertrauenslevel und Notiz.
- Keine stillen Annahmen: Default-Werte muessen sichtbar und editierbar sein.
- Reproduzierbarkeit: Berechnungen, Datenimport und UI-Zustand sollen testbar sein.
- Lokale Entwicklung ohne externe Pflichtdienste; Datenquellen koennen als CSV/JSON gecacht werden.

## Technologiestack
- Python 3.12+
- NiceGUI fuer Web-UI
- pandas oder polars fuer Datenaufbereitung
- pydantic fuer Datenmodelle und Validierung
- plotly fuer interaktive Diagramme in NiceGUI
- pytest fuer Unit- und Integrationstests
- ruff fuer Linting/Formatierung
- pyright oder mypy fuer statische Typpruefung

## Projektstruktur (aktuell implementiert)

```text
app/
  main.py              # NiceGUI entry point
  core/
    physics.py         # Pure calculation functions
  data/
    models.py          # Pydantic data models
    repository.py      # YAML data loading
  vehicles/              # Per-make YAML files (hyundai.yaml, tesla.yaml, ...)
    fuel_constants.yaml   # Fuel energy densities
  tests/
    test_physics.py    # 35 physics tests
    test_repository.py # 10 repository tests
knowledge/
  project_overview.md  # Architecture, status, task list
  physics_module.md    # Core physics function reference
  data_module.md       # Models, repository, YAML structure
  ui_module.md         # NiceGUI frontend architecture
  testing_strategy.md  # Test organization and coverage
pyproject.toml
README.md
AGENTS.md
```

## Knowledge-Referenzen (Entry Points)
- [Projektuebersicht & Architektur](knowledge/project_overview.md) - Gesamtstruktur, Modulabhaengigkeiten, Zwischenstand, Aufgaben
- [Physics Module](knowledge/physics_module.md) - Alle Formeln, Funktionen, Konstanten, Tests
- [Data Module](knowledge/data_module.md) - Pydantic-Modelle, YAML-Struktur, Repository-API
- [UI Module](knowledge/ui_module.md) - NiceGUI-Komponenten, Layout, Reactive-Pattern, API-Notes
- [Testing Strategy](knowledge/testing_strategy.md) - Testorganisation, Coverage, DoD

### Quick Entry Points
| Bereich | Datei | Wichtige Funktionen |
|---------|-------|---------------------|
| Berechnungen | `app/core/physics.py` | `total_consumption()`, `consumption_curve()` |
| Datenmodelle | `app/data/models.py` | `Vehicle`, `PhysicsParams`, `FuelConstants` |
| Datenladen | `app/data/repository.py` | `VehicleRepository`, `load_fuel_constants()` |
| Web-UI | `app/main.py` | `index()`, `build_chart()`, `build_table()` |
| Tests | `app/tests/` | `pytest app/tests/ -v` |
| Start | - | `python -m app.main` (Port 8080) |

## Physikalisches Mindestmodell
Implementiere zuerst eine saubere Berechnungsebene ohne UI.

### Luftwiderstand
- Kraft: F_aero = 0.5 * rho_air * Cd * A * v^2
- Leistung: P_aero = F_aero * v
- Energie pro Strecke: E_aero_per_m = F_aero
- kWh/100 km: F_aero * 100000 / 3_600_000

Parameter:
- rho_air: Default 1.225 kg/m^3 bei 15 C auf Meeresspiegel; editierbar
- Cd: cw-Wert
- A: Stirnflaeche in m^2
- CdA = Cd * A
- v: m/s, UI zeigt km/h

### Rollwiderstand
- F_roll = c_rr * mass_kg * g
- kWh/100 km analog ueber F_roll * 100000 / 3_600_000
- c_rr Default je Reifentyp editierbar, z.B. 0.006 bis 0.012 fuer PKW-Reifen als Startbereich

### Nebenverbraucher / Elektronik / Klima
- P_aux konstant oder als Profil: W oder kW
- kWh/100 km = P_aux_kW / speed_kmh * 100
- Bei Stop-and-go Profilen Zeitanteil korrekt beruecksichtigen

### Antriebswirkungsgrad
- Initial: idealer Radenergiebedarf sowie optional Batteriebedarf mit eta_drivetrain
- eta_drivetrain editierbar, Default klar kennzeichnen
- Rekuperation fuer Beschleunigungsprofile erst in Phase 2

### Fahrprofile
Phase 1:
- Konstantgeschwindigkeit 30-160 km/h
- Mehrpunkt-Profil mit Segmenten: Geschwindigkeit, Dauer oder Distanz, optional Stopps

Phase 2:
- Beschleunigung, Hoehenprofil, Temperatur, Wind, Regen/Nässe, Beladung, Reifenmodell

## Verbrennervergleich
- Zeige chemischen Energieinhalt des Kraftstoffs und Nutzenergie am Rad getrennt.
- Diesel und Benzin als kWh/l editierbar in `fuel_constants.yaml`.
- App soll darstellen:
  - EV kWh/100 km am Rad und aus Batterie
  - Verbrenner l/100 km -> chemische kWh/100 km
  - angenommener thermischer Wirkungsgrad -> mechanische kWh/100 km am Rad
- Keine falsche Gleichsetzung: 1 l/100 km ist nicht direkt mit Batterie-kWh/100 km vergleichbar, weil Wirkungsgrade unterschiedlich sind.

## Datenmodell Vehicle
Pflichtfelder:
- id
- make
- model
- variant
- year_from/year_to optional
- vehicle_type: ev, ice, phev, van, bus, truck
- mass_kg
- frontal_area_m2
- drag_coefficient_cd
- cda_m2 optional berechnet
- battery_usable_kwh optional
- wltp_consumption_kwh_100km optional
- epa_consumption_kwh_100km optional
- real_consumption_kwh_100km optional: Liste mit Quelle und Kontext
- fuel_type optional: gasoline, diesel
- real_consumption_l_100km optional
- source_refs: Liste

SourceRef:
- name
- url
- accessed_at
- field_names
- confidence: high, medium, low
- license_note
- comment

## Datenquellenstrategie
Priorisierung:
1. Offizielle Herstellerdaten fuer cw, Dimensionen, Masse, Batterie.
2. EPA/fueleconomy.gov fuer EV-Verbrauch, MPGe, kWh/100 mi und Verbrennerdaten.
3. EV Database fuer real-world EV-Verbrauch und Reichweite, sofern Nutzung rechtlich/technisch akzeptabel ist.
4. Wikipedia/Automobil-Guru/weitere Tabellen fuer cw und Stirnflaeche als ergaenzende Quelle mit niedrigerem Vertrauenslevel.
5. Community-/Testdaten, z.B. dokumentierte Tests, nur mit Kontext: Geschwindigkeit, Temperatur, Reifen, Strecke.

Wichtig:
- Nicht blind scrapen. Erst robots.txt, Nutzungsbedingungen und Lizenz pruefen.
- Wo Daten nicht maschinell nutzbar sind, manuelle YAML/CSV-Kuration vorziehen.
- Importer muessen Rohdaten und normalisierte Daten trennen.

## UI-Anforderungen
Ziel: optisch ruhige, wissenschaftlich nachvollziehbare Webapp.

Seiten:
1. Dashboard / Vergleich
   - Fahrzeugauswahl Mehrfachauswahl
   - Geschwindigkeitsbereich Slider
   - Fahrprofilauswahl
   - Diagramm kWh/100 km vs km/h
   - gestapelte Kurven/Anteile: Aero, Roll, Aux, Verluste
   - Tabelle mit Kennwerten bei 50/80/100/130 km/h

2. Fahrzeugdatenbank
   - Such- und Filterfunktion
   - Detailansicht eines Fahrzeugs
   - Quellen und Vertrauenslevel sichtbar
   - fehlende Daten markiert, editierbar

3. Szenario-Editor
   - Luftdichte, Temperatur, Wind, c_rr, Zuladung, Nebenverbraucher
   - Fahrprofil-Segmente bearbeiten

4. Verbrennervergleich
   - l/100 km in chemische kWh/100 km
   - angenommener Motorwirkungsgrad
   - Vergleich Radenergie vs Tank/Batterieenergie

5. Datenqualitaet
   - fehlende Felder
   - widerspruechliche Quellen
   - Plausibilitaetschecks

Design:
- klare Karten, breite Diagramme, wenige dominante Farben
- Tooltips zu jeder Formel
- Einheiten immer anzeigen
- Warnhinweise bei theoretischen vs realen Werten

## Teststrategie
Vor jeder UI-Erweiterung muessen Kernberechnungen getestet werden.

Mindesttests:
- Luftwiderstand skaliert mit v^2 bei Energie pro Strecke und v^3 bei Leistung.
- Verdopplung von CdA verdoppelt Aero-Verbrauch.
- Rollwiderstand skaliert linear mit Masse und c_rr.
- Nebenverbrauch pro 100 km sinkt mit Geschwindigkeit bei konstanter Leistung.
- Einheitenumrechnung km/h <-> m/s, Wh/km <-> kWh/100 km, kWh/100 mi <-> kWh/100 km.
- Verbrennerumrechnung l/100 km -> kWh/100 km.
- Repository validiert fehlende Quellen und unplausible Werte.

Definition of Done pro Task:
- Tests hinzugefuegt oder begruendet nicht noetig
- `pytest` gruen
- `ruff check` gruen
- Typpruefung gruen oder erklaerte Ausnahmen
- README/Kommentare aktualisiert, wenn Verhalten geaendert wurde

## Arbeitsweise fuer opencode
Arbeite iterativ und autonom:
1. Lege minimal lauffaehiges Projekt an.
2. Implementiere erst `core/physics.py` mit Tests.
3. Implementiere Datenmodelle und Beispieldaten.
4. Baue einfache NiceGUI UI mit einem Vergleichsdiagramm.
5. Erweitere danach Datenimport, Szenarien, Verbrennervergleich und UI-Feinschliff.

Bei Unsicherheit:
- Triff eine konservative Annahme.
- Dokumentiere sie in Code und README.
- Mache sie in der UI editierbar.

Nicht tun:
- Keine unzitierten Daten hart codieren, ausser physikalische Konstanten und klar markierte Demo-Werte.
- Keine komplexe Scraping-Pipeline bauen, bevor Datenmodell, Tests und UI funktionieren.
- Keine Einheiten mischen.
- Keine WLTP/EPA/reale Werte ohne Kontext direkt gleichsetzen.
