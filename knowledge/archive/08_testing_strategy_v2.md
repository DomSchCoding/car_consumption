# 08 - Testing Strategy v2

## Ziel

Das Projekt soll schnell wachsen koennen, ohne dass Physik, Einheiten oder UI-State unkontrollierbar werden.

## Testpyramide

1. Viele Unit-Tests fuer Core-Formeln
2. Model-/Validation-Tests fuer Pydantic
3. Repository-/Importer-Tests
4. Service-/Integrationstests fuer komplette Szenarien
5. Wenige UI-Tests fuer Hauptflows

## Bestehende Basis

Der aktuelle Stand dokumentiert bereits Tests fuer:

- Einheitenumrechnung
- Luftwiderstand
- Rollwiderstand
- Nebenverbrauch
- Drivetrain
- Gesamtkonsum
- Verbrauchskurven
- Fuel conversions
- Repository

Diese Tests sollen erhalten bleiben.

## Neue Testdateien

```text
app/tests/
  test_physics.py
  test_route_energy.py
  test_regeneration.py
  test_environment.py
  test_economics.py
  test_models.py
  test_repository.py
  test_importers.py
  test_ui_smoke.py
```

## Route-Tests

Pflicht:

- flache Route ohne Stops entspricht Konstantgeschwindigkeit
- doppelte Distanz -> doppelte Energie
- Gegenwind erhoeht Aero
- Rueckenwind macht Aero nie negativ
- Hoehengewinn erhoeht Energie
- Hoehenverlust kann Energie zurueckgewinnen, aber nicht unbegrenzt
- Hin-und-Rueckweg generiert Ruecksegmente korrekt
- Hin-und-Rueckweg mit Hoehe hat Netto-Hoehe null, aber positive Verluste
- Stopps erhoehen Verbrauch bei unvollstaendiger Rekuperation
- Aux beruecksichtigt Fahrzeit und Standzeit
- Massenzunahme erhoeht Roll/Hoehe/Stop-and-go

## Regeneration-Tests

- `eta_regen=0` -> keine Rueckgewinnung
- `eta_regen=1` -> theoretisches Maximum
- Rueckgewinnung nie groesser als verfuegbare Energie
- Batterieenergie nie negativ
- bei ICE ohne Hybrid Rueckgewinnung null
- Temperaturfaktor kann Rekuperation reduzieren

## Economics-Tests

- Quantile korrekt
- Preisfilter korrekt
- Reichweite pro 1.000 EUR korrekt
- Kosten pro Fahrt korrekt
- Monats-/Jahreskosten korrekt
- Break-even robust bei Division durch null
- fehlende Preisdaten erzeugen saubere Warnung

## Data Quality Tests

- SourceRefs werden aufgeloest
- fehlende Quelle wird markiert
- Demo-Werte bleiben sichtbar
- unplausible CdA-Werte erzeugen Warnung, nicht zwingend Fehler
- Vehicle IDs eindeutig
- Route IDs eindeutig
- Price Samples referenzieren existierende Fahrzeuge

## Snapshot/Golden Tests

Fuer komplexe Szenarien:

- Demo-Route flach
- Demo-Route bergauf/bergab
- Winterpendeln
- Autobahn mit Gegenwind
- Lieferdienst Stop-and-go

Golden-Values in JSON/YAML speichern, aber nur fuer stabile Core-Ergebnisse.

## Property-Based Tests optional

Mit Hypothesis spaeter sinnvoll:

- Energie nie negativ
- mehr Distanz erzeugt nicht weniger Energie bei gleichen Parametern
- mehr CdA erhoeht Aero-Verbrauch
- mehr Masse erhoeht Roll/Hoehe/Stop-and-go
- Rekuperation begrenzt Rueckgewinnung

## UI-Tests

Minimal:

- App startet
- Dashboard rendert
- Route-Seite rendert
- Fahrzeugauswahl funktioniert
- Route-Berechnung zeigt Ergebnis
- keine Exception bei leerer Auswahl

NiceGUI-spezifische Tests nur nach stabiler UI-Struktur einfuehren.

## Debugging-Funktionen

Die App sollte einen Debug-/Details-Modus haben:

- Formelparameter anzeigen
- Intermediate values anzeigen
- Segment-Breakdown exportieren
- JSON-Ergebnis exportieren
- Datenquelle pro Wert anzeigen

Das hilft sowohl Nutzer als auch Agenten.

## Definition of Done

Jede Aenderung:

```bash
pytest
ruff check app/
ruff format app/
pyright app/
```

Falls `pyright` wegen NiceGUI-Typen Probleme macht:

- Core/Data muessen sauber sein
- UI-Ausnahmen dokumentieren
