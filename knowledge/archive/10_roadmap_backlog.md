# 10 - Roadmap and Backlog v2

## Phase 0 - Stabilisierung und Knowledge-Migration

Ziel: Agenten koennen sicher weiterarbeiten.

Tasks:

- [x] Knowledge Base v2 einchecken
- [x] AGENTS.md mergen/ersetzen
- [x] bestehende Tests laufen lassen
- [x] `main.py` grob vermessen: Laenge, Funktionen, Verantwortlichkeiten
- [x] Refactoring-Plan mit kleinen PRs erstellen

## Phase 1 - UI/Core-Refactoring ohne Funktionsaenderung

Ziel: Wachstum vorbereiten.

Tasks:

- [x] `ui/charts.py` anlegen
- [x] `build_chart()` aus `main.py` extrahieren
- [x] `build_table()` aus `main.py` extrahieren
- [x] `ui/state.py` einfuehren
- [x] Vehicle Selector Komponente extrahieren
- [x] Import-/Smoke-Tests
- [x] Knowledge aktualisieren

## Phase 2 - Route MVP / Pendelstrecke

Ziel: Route als Kernfeature.

Tasks:

- [x] `RouteSegment`, `Route`, `CommuteScenario`, `RouteEnergyBreakdown` Modelle
- [x] `core/route_energy.py`
- [x] flache Segmentberechnung
- [x] Hoehenenergie
- [x] Hinweg/Rueckweg-Generator
- [x] Stop-and-go vereinfachtes Modell
- [x] Aux-Zeitmodell
- [x] Tests (23 Tests in test_route_energy.py)
- [x] NiceGUI-Seite "Route / Pendeln"
- [x] Checkbox "Hin und Retour"
- [x] Tabelle mit Breakdown-Komponenten

MVP-Eingaben:

- Distanz einfach
- Durchschnittsgeschwindigkeit
- Netto-Hoehendifferenz
- optional Gain/Loss
- Stopps pro km
- Standzeit
- Temperatur
- Wind
- Hinweg / Hin und Retour

## Phase 3 - Segmenteditor und GPX/CSV

Ziel: realistischere Routen.

Tasks:

- [ ] Segmenteditor UI
- [ ] Segmentliste add/remove
- [ ] Route YAML speichern/laden
- [ ] CSV Import fuer Segmente
- [ ] GPX Parser
- [ ] GPX Hoehendaten glätten/resamplen
- [ ] Hoehenprofil-Chart
- [ ] Route exportieren

## Phase 4 - Rekuperation und Fahrprofile

Ziel: Stadt/Stop-and-go plausibel modellieren.

Tasks:

- [ ] `core/regeneration.py`
- [ ] RoadType Defaults fuer Stops/Speed
- [ ] Stadtprofil
- [ ] Lieferdienstprofil
- [ ] Autobahnprofil
- [ ] Pendlerprofil
- [ ] Temperaturfaktor fuer Rekuperation
- [ ] SOC-/Batterietemperatur-Begrenzung spaeter

## Phase 5 - Preise, Gebrauchtmarkt, TCO

Ziel: Effizienz mit Wirtschaftlichkeit verbinden.

Tasks:

- [ ] `PriceSample`
- [ ] CSV Import fuer Preise
- [ ] Quantile/Median/Histogramm
- [ ] Preisverteilung in UI
- [ ] Reichweite pro 1.000 EUR
- [ ] Kosten pro Fahrt/Monat/Jahr
- [ ] TCO-MVP
- [ ] Break-even EV vs ICE

## Phase 6 - Umweltmodell

Ziel: Winter, Wind, Temperatur besser abbilden.

Tasks:

- [ ] Luftdichte aus Temperatur
- [ ] Windmodell
- [ ] Heatpump/HVAC Presets
- [ ] Batteriekapazitaetsfaktor
- [ ] Winter-/Sommerpresets
- [ ] Regen/Nässe-Faktor optional

## Phase 7 - Datenqualitaet und Importe

Ziel: Datenbasis robust erweitern.

Tasks:

- [ ] SourceRef-Validierung
- [ ] Data Quality Dashboard
- [ ] EPA Importer
- [ ] Manuelle EV-Database Importstruktur
- [ ] Price CSV Import
- [ ] Realverbrauch CSV Import
- [ ] Plausibilitaetswarnungen

## Phase 8 - UX Polishing

Ziel: Die App fuehlt sich rund an.

Tasks:

- [ ] responsive Layout
- [ ] Tooltips fuer Formeln
- [ ] Preset-Karten
- [ ] Export als CSV/JSON
- [ ] Vergleichslinks/Szenario-Speichern
- [ ] bessere Farben und Legenden
- [ ] Accessibility

## Ideen fuer spaeter

- Jahresprofil mit Sommer/Winter-Anteil
- Akku-Degradation und SoH
- Ladeverluste AC/DC
- Ladezeit und Ladeplanung
- Wohnwagen/Anhaenger-Modell
- Dachbox/Fahrradtraeger CdA-Aufschlag
- Reifen-/Felgengroesse
- Monte-Carlo Unsicherheitsanalyse
- CO2-Betrachtung nach Strommix/Kraftstoff
- Nutzer-Messdatenimport aus Tronity/ABRP/CSV
- ABRP/OpenStreetMap/OSRM Integration, falls rechtlich/technisch passend
