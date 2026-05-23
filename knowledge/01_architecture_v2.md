# 01 - Architecture v2

## Architekturziel

Der aktuelle Stand hat eine sinnvolle Grundstruktur, aber die weitere Entwicklung wird schnell komplex. Daher soll die Zielarchitektur frueh modularisiert werden.

Hauptregel:

> UI fragt orchestrierte Services ab. UI berechnet keine Physik.

## Ist-Risiko

`app/main.py` kann zu gross werden, weil dort aktuell UI, Plotly, Filterlogik, State und Berechnungsaufrufe zusammenlaufen. Das ist fuer den MVP okay, aber fuer Route, Preise, TCO und Fahrprofile zu fehleranfaellig.

## Zielmodule

```text
app/
  main.py
  core/
    physics.py
    route_energy.py
    drive_profiles.py
    regeneration.py
    environment.py
    economics.py
    units.py
  data/
    models.py
    repository.py
    importers/
  ui/
    pages/
    components/
    charts.py
    state.py
```

## Core-Schicht

### `core/physics.py`

Bleibt fuer elementare, reine Formeln:

- Luftwiderstand
- Rollwiderstand
- Nebenverbrauch
- Antriebswirkungsgrad
- Kraftstoffenergie
- Einheitenumrechnung, falls nicht nach `units.py` ausgelagert

### `core/route_energy.py`

Neue Route-/Segmentlogik:

- Segmentverbrauch
- Routenverbrauch
- Pendelstrecke: Hinweg/Rueckweg
- Hoehenenergie
- Routen-Breakdown

### `core/drive_profiles.py`

Standardisierte Fahrprofile:

- Stadt
- Landstrasse
- Autobahn
- Pendlerprofil
- Lieferdienst
- Kurzstrecke Winter
- konstante Geschwindigkeit
- frei definierte Segmentliste

### `core/regeneration.py`

Rekuperationsmodell:

- kinetische Energie pro Stop
- netto Verlust aus Beschleunigen/Bremsen
- Rekuperationswirkungsgrad
- Begrenzungen durch Batterie, SoC, Temperatur, Rekuperationsleistung
- erster MVP: einfache ETA, spaeter Constraints

### `core/environment.py`

Umweltparameter:

- Luftdichte aus Temperatur, Hoehe, Luftdruck
- Windkomponente
- Temperaturwirkung auf Nebenverbrauch
- nasse Strasse/Reifen optional
- Winter/Sommer-Presets

### `core/economics.py`

Kosten und Preise:

- Energiepreis
- Kraftstoffpreis
- Wartungspauschale
- Kaufpreis
- Restwert
- TCO pro Monat / Jahr / 100 km
- Reichweite pro 1.000 EUR
- Verbrauchsvorteil pro Euro

### `core/units.py`

Alle Einheitenumrechnungen zentralisieren:

- km/h, m/s
- Wh/km, kWh/100 km
- kWh/100 mi
- Liter/100 km
- Joule, kWh
- Hoehenmeter in kWh

## Data-Schicht

### `data/models.py`

Soll Domainmodelle bereitstellen, aber keine komplexe Logik enthalten. Pydantic fuer Validierung, berechnete Properties nur fuer einfache Ableitungen wie CdA.

### `data/repository.py`

Repository soll:

- Fahrzeuge laden
- Routenprofile laden
- Preissamples laden
- Quellen validieren
- Abfragen kapseln

### `data/importers/`

Importer trennen Rohdaten und normalisierte Daten:

```text
raw -> parsed -> normalized -> validated -> cached
```

Keine direkte UI-Abhaengigkeit.

## UI-Schicht

### `ui/pages/`

- `dashboard.py` - Vergleichskurven
- `vehicles.py` - Fahrzeugdatenbank
- `route_planner.py` - Pendler-/Routenanalyse
- `economics.py` - Preis/TCO
- `data_quality.py` - Quellen/Fehler/Confidence

### `ui/components/`

Wiederverwendbare UI-Bausteine:

- Fahrzeugauswahl
- Parameterpanel
- Routen-Segmenteditor
- Preisverteilungs-Panel
- Quellen-Badges
- Verbrauchs-Breakdown-Karten

### `ui/charts.py`

Alle Plotly-Erzeugung hier bündeln:

- Verbrauchskurve
- gestapelter Verbrauchs-Breakdown
- Routenenergie pro Segment
- Preisverteilung
- Reichweite-pro-Euro
- Sensitivitaetsdiagramme

### `ui/state.py`

Zentraler UI-State:

- ausgewaehlte Fahrzeuge
- PhysicsParams
- EnvironmentProfile
- RouteScenario
- sichtbare Chartoptionen
- Filter

## Service-Layer optional

Wenn UI und Core weiter wachsen, kann ein Service-Layer helfen:

```text
services/
  comparison_service.py
  route_service.py
  economics_service.py
```

Diese Services kombinieren Domainobjekte und liefern ViewModels an die UI.

## Refactoring-Prioritaet

1. Chart-Erzeugung aus `main.py` nach `ui/charts.py`
2. UI-State in `ui/state.py`
3. Fahrzeugauswahl in Komponente auslagern
4. Core-Route-Modelle ohne UI einfuehren
5. Route-Planner-Seite aufbauen
6. Economics-Modul einfuehren
7. Datenqualitaetsseite

## Abhaengigkeitsregel

Erlaubt:

```text
ui -> services -> core
ui -> data
services -> core
services -> data
data -> models
core -> models optional, besser einfache DTOs/Dataclasses
```

Verboten:

```text
core -> ui
data -> ui
importers -> ui
physics.py -> repository.py
```
