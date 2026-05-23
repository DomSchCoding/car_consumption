# 00 - Project Overview v2

Stand: 2026-05-23

## Ausgangspunkt

Das Repository `DomSchCoding/car_consumption` ist bereits ein funktionaler Prototyp einer NiceGUI-Webapp zur physikbasierten Verbrauchsanalyse.

Der oeffentlich sichtbare Stand enthaelt:

- NiceGUI-Webapp als Einstiegspunkt `app/main.py`
- Core-Physik in `app/core/physics.py`
- Pydantic-Datenmodelle in `app/data/models.py`
- YAML-basierte Fahrzeugdaten
- Verbrauchskurven nach Geschwindigkeit
- EV/ICE-Vergleich
- Datenquellenstrategie
- Tests fuer Physik und Repository

Der bestehende README beschreibt das Ziel als physics-based web application fuer Fahrzeugenergieverbrauch mit Fokus auf EVs, Aerodynamik, Rollwiderstand, Nebenverbraucher und ICE-Vergleich.

## Neue Produktvision

Das Projekt soll zu einem interaktiven Erklaer-, Analyse- und Kaufentscheidungswerkzeug werden.

Nicht nur:

> Welches Auto verbraucht bei 100 km/h wie viel?

Sondern:

> Warum verbraucht dieses Auto auf meiner Pendlerstrecke im Winter so viel, waehrend ein anderes Auto trotz aehnlicher WLTP-Angabe deutlich besser ist?

Kernfragen:

1. Was ist der theoretisch minimale Verbrauch aus CdA, Masse, Reifen und Geschwindigkeit?
2. Welche Differenz entsteht durch Nebenverbrauch, Temperatur, Wind, Hoehenprofil und Fahrprofil?
3. Wie verhalten sich konkrete Pendlerstrecken: nur Hinweg, nur Rueckweg, Hin und Retour?
4. Wie viel Reichweite bekomme ich pro Euro Kaufpreis oder pro Euro Gesamtkosten?
5. Welche Fahrzeugform ist fuer welches Einsatzprofil physikalisch sinnvoll?
6. Wo liegen harte physikalische Grenzen fuer Lieferwagen, Busse, SUVs und Transporter?
7. Wie unterscheiden sich Radenergie, Batterieenergie und chemische Energie bei Verbrennern?

## Zielnutzer

### 1. Technisch interessierte EV-Fahrer

Wollen verstehen, warum Verbraeuche stark schwanken.

### 2. Kaufinteressenten

Wollen nicht nur WLTP sehen, sondern reale Reichweite bei Autobahn, Pendelstrecke, Winter, Preis und TCO.

### 3. Didaktische Nutzer

Wollen Zusammenhaenge zwischen Aerodynamik, Geschwindigkeit, Masse, Temperatur und Rekuperation verstehen.

### 4. Daten-/Tech-Nutzer

Wollen eigene Fahrzeuge, Routen, CSVs, GPX-Dateien und Quellen einpflegen.

## Produktprinzipien

- Physikalisch nachvollziehbar statt Blackbox.
- Schieberegler und Eingaben muessen sofort visuelle Wirkung zeigen.
- Default-Werte muessen sichtbar sein.
- Quellen muessen sichtbar sein.
- Unsicherheit muss sichtbar sein.
- Demo-Daten duerfen existieren, muessen aber klar als Demo markiert werden.
- Diagramme sollen erklaeren, nicht nur beeindrucken.

## Kernobjekte

- Vehicle
- VehicleVariant
- SourceRef
- ConsumptionObservation
- PhysicsParams
- EnvironmentProfile
- DriveProfile
- Route
- RouteSegment
- CommuteScenario
- PriceSample
- PriceDistribution
- TcoScenario
- ComparisonResult

## Wichtigste neue Funktion: Route / Pendelstrecke

Eine Route ist kein Sonderfall, sondern soll zum zentralen Analyseobjekt werden.

Mindestfunktion:

- Eingabe von Distanz, Durchschnittsgeschwindigkeit, Hoehenmeter bergauf/bergab
- Option: nur Hinweg
- Option: Hin und Retour
- Energieaufschluesselung: Aero, Roll, Aux, Hoehe, Stop-and-go, Rekuperation, Verluste
- Vergleich mehrerer Fahrzeuge auf derselben Route
- Reichweite in Fahrten pro Ladung: z.B. "wie oft komme ich hin und zurueck?"
- Kosten pro Fahrt und Monat

Spaeter:

- Segmenteditor
- GPX/CSV-Import
- Routenservice-Integration
- Tages-/Jahresprofil fuer Pendler
- Winter/Sommer-Szenarien
