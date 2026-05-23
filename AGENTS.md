# AGENTS.md - Arbeitsweise fuer opencode

Stand: 2026-05-23

## Projektziel

Entwickle `car_consumption` zu einer physikbasierten NiceGUI-Webapp zur Analyse, Erklaerung und Kaufunterstuetzung von Fahrzeugverbraeuchen.

Schwerpunkt:

- Elektroautos, aber mit sauberem Verbrennervergleich
- Aerodynamik, Rollwiderstand, Nebenverbraucher, Antriebseffizienz
- Fahrprofile und konkrete Routen inklusive Pendelstrecken
- Hoehenprofil, Wind, Temperatur, Stop-and-go und Rekuperation
- reale Verbrauchsdaten, Preise, Gebrauchtmarkt und TCO
- transparente Datenqualitaet und nachvollziehbare Quellen

Die App soll nicht nur WLTP/EPA/Realwerte anzeigen, sondern erklaeren, welcher Teil des Verbrauchs aus welcher physikalischen Ursache entsteht.

## Kernprinzipien

1. Physik zuerst, reale Daten danach zur Plausibilisierung.
2. Keine stillen Annahmen: Jeder Default ist sichtbar, editierbar und dokumentiert.
3. Jede Fahrzeug-, Verbrauchs-, Preis- und Routendatenquelle braucht Quelle, Datum, Einheit, Kontext und Confidence-Level.
4. Core-Logik bleibt frei von UI-Code.
5. Jede neue Formel bekommt Unit-Tests.
6. Jede neue UI-Funktion bekommt mindestens eine robuste Daten-/Core-Schicht darunter.
7. Nicht blind scrapen. Nutzungsbedingungen, robots.txt, Lizenz und Caching-Konzept pruefen.
8. Wenn eine Annahme unsicher ist: konservativ waehlen, dokumentieren, in UI editierbar machen.
9. Zwischen Radenergie, Batterieenergie und chemischer Energie immer klar unterscheiden.
10. Bei Routen nie nur Netto-Hoehendifferenz verrechnen: Hinweg/Rueckweg und Rekuperationsverluste getrennt modellieren.

## Knowledge-Entry-Points

Vor groesseren Arbeiten lesen:

- `knowledge/00_project_overview.md`
- `knowledge/01_architecture_v2.md`
- `knowledge/02_physics_model_v2.md`
- `knowledge/03_route_and_commute_model.md`
- `knowledge/10_roadmap_backlog.md`

Bei Datenarbeiten:

- `knowledge/04_data_model_v2.md`
- `knowledge/05_data_sources_and_quality.md`

Bei UI-Arbeiten:

- `knowledge/06_ui_ux_v2.md`

Bei Preisen/TCO:

- `knowledge/07_economics_price_tco.md`

Bei Tests/Qualitaet:

- `knowledge/08_testing_strategy_v2.md`

## Zielarchitektur

```text
app/
  main.py                         # nur Startpunkt, Routing, globale App-Konfiguration
  core/
    physics.py                    # bestehende Grundformeln
    route_energy.py               # Routen-/Segmentberechnung
    drive_profiles.py             # Stadt/Land/Autobahn/Pendelprofile
    regeneration.py               # Stop-and-go, Rekuperationsmodell
    environment.py                # Luftdichte, Temperatur, Wind, Wetter
    economics.py                  # Preise, TCO, Kostenmetriken
    units.py                      # Einheitenumrechnung
  data/
    models.py                     # Pydantic-Domainmodelle
    repository.py                 # Laden, Validieren, Query
    importers/
      epa.py
      ev_database_manual.py
      price_csv.py
      gpx.py
  ui/
    pages/
      dashboard.py
      vehicles.py
      route_planner.py
      economics.py
      data_quality.py
    components/
      vehicle_selector.py
      chart_cards.py
      parameter_panels.py
      source_badges.py
    charts.py
    state.py
  assets/
    vehicles/
      hyundai.yaml
      volkswagen.yaml
      ...
    route_profiles.yaml
    tire_profiles.yaml
    fuel_constants.yaml
    price_samples_demo.yaml
  tests/
    test_physics.py
    test_route_energy.py
    test_regeneration.py
    test_economics.py
    test_repository.py
    test_importers.py
```

## Definition of Done

Ein Task ist erst fertig, wenn:

- relevante Knowledge-Datei aktualisiert ist
- Tests fuer neue Core-Logik existieren
- `pytest` erfolgreich ist
- `ruff check` erfolgreich ist
- `ruff format` angewandt oder geprueft wurde
- Typpruefung fuer Core/Data gruene Ergebnisse liefert oder eine Ausnahme dokumentiert ist
- keine unklaren Einheiten in UI oder Code bleiben
- Quellen, Confidence und Datenkontext bei neuen Daten gepflegt sind
- die App lokal mit `python -m app.main` startet

## Arbeitsmodus fuer opencode

Arbeite in kleinen, lauffaehigen Schritten:

1. Relevante Knowledge-Dateien lesen.
2. Minimalen Implementierungsplan in 5-10 Punkten schreiben.
3. Bestehende Tests ausfuehren.
4. Erst Core/Data aendern, dann UI.
5. Neue Tests hinzufuegen.
6. UI integrieren.
7. README/Knowledge aktualisieren.
8. Kurzen Abschlussbericht mit Aenderungen, Tests und bekannten Grenzen schreiben.

## Nicht tun

- Keine komplexe Scraping-Pipeline bauen, bevor Datenmodell und manuelle Imports stabil sind.
- Keine Werte aus Webseiten ohne Quelle/Datum/Confidence hart codieren.
- Keine WLTP-, EPA-, Real- und Modellwerte ohne Kontext direkt gleichsetzen.
- Keine Magic Numbers in UI-Code verstecken.
- Kein UI-State-Chaos durch vermischte globale Listen, Chartlogik und Datenmodelllogik.
- Keine Route mit Hoehenprofil als blossen Durchschnittsverbrauch behandeln.
