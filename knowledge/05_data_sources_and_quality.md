# 05 - Data Sources and Quality

## Ziel

Die Datenbasis soll wachsen, aber nicht auf Kosten von Nachvollziehbarkeit, Lizenzproblemen oder Datenchaos.

## Quellenklassen

### Klasse A - Offiziell / hoch vertrauenswuerdig

- Herstellerdatenblaetter
- Zulassungs-/Typdaten
- EPA / fueleconomy.gov
- offizielle technische Dokumente

Verwendung:

- cw, Abmessungen, Masse, Batterie
- EPA-Verbrauch
- Fuel Economy Vergleichsdaten

### Klasse B - Kuratierte Datenbanken

- EV Database
- automobile-catalog
- andere strukturierte EV/Auto-Datenbanken

Verwendung:

- Realverbrauch
- Reichweite
- technische Vergleichsdaten

Wichtig:

- Nutzungsbedingungen pruefen
- automatisches Scraping nur wenn erlaubt
- sonst manuelle Kuration oder Import aus eigenen CSVs

### Klasse C - Community / Tests

- Bjorn Nyland Tests
- Spritmonitor
- Foren
- YouTube-Tests
- eigene Messungen

Verwendung:

- Realverbrauch mit Kontext
- Plausibilisierung
- Streuung

Bedingung:

- Kontext erfassen: Geschwindigkeit, Temperatur, Reifen, Strecke, Nutzlast
- nie als alleinige Wahrheit darstellen

### Klasse D - Fallback / niedrigere Confidence

- Wikipedia
- Tabellenblogs
- Sekundaerquellen

Verwendung:

- Startwerte fuer Cd, Stirnflaeche, Masse
- nur mit Confidence `low` oder `demo`, wenn nicht gegenvalidiert

## Datenqualitaetsfelder

Jeder Datenpunkt soll wissen:

```text
value
unit
source_ref
confidence
accessed_at
context
comment
```

## Datenstatus

- `verified`: durch offizielle/mehrere Quellen bestaetigt
- `high`: gute Quelle, plausibel
- `medium`: brauchbar, aber nicht vollstaendig bestaetigt
- `low`: Sekundaerquelle
- `demo`: fuer UI/Tests, nicht als realer Wert zu interpretieren
- `unknown`: noch nicht bewertet

## Importstrategie

### Phase 1: Manuelle YAML/CSV-Kuration

Ziel:

- stabile Datenmodelle
- nachvollziehbare Quellen
- keine Rechts-/Scrapingprobleme

### Phase 2: CSV-Importer

Importer fuer:

- EPA Download-Daten
- eigene Verbrauchslisten
- eigene Preisbeobachtungen
- eigene Routen/GPX-Konvertierungen

### Phase 3: Halbautomatische Importer

Nur wenn Lizenz/Nutzung okay:

- HTTP Download
- Cache in `data/raw/`
- Normalisierung nach `data/normalized/`
- Protokollierung

### Phase 4: Data Quality Dashboard

Anzeigen:

- fehlende Felder
- Fahrzeuge ohne Quelle
- Fahrzeuge mit nur Demo-Daten
- unplausible CdA-Werte
- widerspruechliche Verbrauchsdaten
- Preis-Samples mit zu kleiner Stichprobe

## Keine blinde Scraping-Pipeline

Nicht tun:

- Webseiten ohne Nutzungspruefung scrapen
- Daten ohne Quelle in YAML kopieren
- robots.txt ignorieren
- dynamische Webseiten aggressiv abrufen
- Datenbankinhalte als eigene Daten ausgeben

Besser:

- manuelle CSVs
- offizielle Downloads
- klare Lizenznotizen
- Quellenlink und Abrufdatum
- Cache-Datei mit Rohdaten

## Plausibilitaetschecks

### CdA

```text
CdA = Cd * A
```

Warnbereiche:

- sehr effiziente Limousine: ca. 0.45-0.60 m2
- Kompakt/SUV: ca. 0.60-0.85 m2
- Van/Bus: ca. 0.9-1.3+ m2

Nicht hart als Fehler, nur Warnung.

### Verbrauch

Vergleiche:

- Modellverbrauch bei 100 km/h
- WLTP/EPA
- Realwerte

Warnung, wenn:

- Realwert < theoretischer Radenergiebedarf bei aehnlicher Geschwindigkeit
- WLTP extrem unter physikalischem Modell liegt, ohne Kontext
- Verbrauchseinheiten unsicher sind

### Batterie

Warnung, wenn:

- realistische Reichweite > Batterie / theoretischer Verbrauch deutlich unplausibel
- usable/gross verwechselt scheint

### Preis

Warnung, wenn:

- weniger als 5 Samples
- Sample aelter als definierter Zeitraum
- Kilometerstand fehlt
- Ausreisser ausserhalb 3 IQR
- Variante/Batterie nicht eindeutig
