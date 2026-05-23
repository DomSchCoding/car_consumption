# 06 - UI/UX v2

## Designziel

Die App soll optisch ruhig, technisch glaubwuerdig und intuitiv sein. Komplexe Physik soll nicht versteckt, sondern progressiv aufklappbar erklaert werden.

## UI-Prinzipien

1. Erst Ergebnis, dann Details.
2. Jede Zahl hat Einheit.
3. Jede Annahme ist sichtbar.
4. Jede Komponente kann aufgeschluesselt werden.
5. Demo-/unsichere Daten sind sichtbar markiert.
6. Charts sollen Vergleich und Ursache zeigen.
7. Keine UI, die Core-Logik dupliziert.

## Seitenstruktur

### 1. Dashboard / Fahrzeugvergleich

Zweck:

- schneller Vergleich mehrerer Fahrzeuge
- Verbrauchskurven nach Geschwindigkeit
- Aufschluesselung Aero/Roll/Aux/Verluste
- Ranking

Elemente:

- Fahrzeugauswahl
- Speed Range
- Physics Params
- Verbrauchskurve
- Tabelle 50/80/100/130 km/h
- Ranking bei ausgewaehlter Geschwindigkeit

### 2. Route / Pendeln

Zweck:

- konkrete Strecke berechnen
- Hinweg vs Hin-und-Rueckweg
- Hoehenprofil und Stop-and-go sichtbar machen

MVP-Elemente:

- Route Name
- Distanz einfach
- Durchschnittsgeschwindigkeit
- Hoehenmeter Start->Ziel
- optional Hoehenmeter bergauf/bergab
- Stopps pro km
- Standzeit
- Temperatur
- Wind
- Checkbox: Hin und Retour
- Checkbox: Rueckweg separat
- Ergebnis-Karten
- Breakdown-Bar-Chart
- Tabelle pro Fahrzeug

Spaeter:

- Segmenteditor
- GPX Upload
- Hoehenprofil
- SOC-Verlauf
- Monats-/Jahreskosten

### 3. Fahrzeugdatenbank

Zweck:

- Fahrzeuge durchsuchen und Daten bewerten
- Quellen ansehen
- fehlende Daten erkennen

Elemente:

- Suchfeld
- Filter: Marke, Typ, Batterie, Baujahr, CdA, Masse
- Tabelle
- Detailseite
- Quellen-Badges
- Confidence-Level
- fehlende Felder

### 4. Preise & TCO

Zweck:

- Effizienz mit Kaufpreis und Betriebskosten verbinden

Elemente:

- Neupreis
- Gebrauchtpreisverteilung
- Kilometerstand-/Baujahrfilter
- TCO-Szenario
- Reichweite pro 1.000 EUR
- Kosten pro 100 km
- Break-even EV vs ICE

### 5. Datenqualitaet

Zweck:

- Agenten und Nutzer sehen, wo Daten schlecht sind

Elemente:

- Fahrzeuge ohne Quelle
- Demo-Werte
- unplausible Werte
- fehlende Preise
- fehlende CdA-Komponenten
- Import-Status

## Chart-Ideen

### Verbrauchskurve

x: Geschwindigkeit  
y: kWh/100 km  
Linien: Fahrzeuge  
Hover: Aero, Roll, Aux, Total, CdA

### Komponenten-Stack

Für eine gewaehlte Geschwindigkeit oder Route:

- Aero
- Roll
- Aux
- Hoehe
- Stop-and-go
- Drivetrain losses
- Reku als negative Komponente oder separater Rueckgewinnungsbalken

### Route-Breakdown

x: Fahrzeuge  
y: kWh/Fahrt  
Stack: Komponenten

### Hinweg/Rueckweg Vergleich

Gruppierte Balken:

- Hinweg
- Rueckweg
- Hin+Retour

### Preisverteilung

Nicht nur Glockenkurve.

Besser:

- Histogramm
- Boxplot
- Violin Plot
- Medianlinie
- Sample Count
- aufklappbare Detailtabelle

Die Normal-/Glockenkurve kann optional als Overlay angezeigt werden, aber nicht als Standardannahme.

### Reichweite pro Euro

x: Gebrauchtpreis Median  
y: Autobahn-/Routenreichweite  
Bubble: Batterie oder CdA  
Farbe: Fahrzeugtyp

### Sensitivitaet

Wie aendert sich Verbrauch bei:

- Geschwindigkeit
- Temperatur
- Gegenwind
- Zuladung
- c_rr
- Aux-Leistung
- Rekuperationsgrad

## UX fuer Komplexitaet

### Progressive Disclosure

Default:

- einfache Eingaben
- gute Presets

Details aufklappbar:

- Luftdichte
- Reifen
- Wirkungsgrade
- Rekuperation
- Temperaturmodell
- Quellen

### Presets

- Sommer 20 C
- Winter 0 C
- Winter -10 C mit Heizung
- Regen/nasse Fahrbahn
- Autobahn 130
- Stadt Stop-and-go
- Pendler Mix
- Lieferdienst

### Warnhinweise

Beispiele:

- "Dieser Wert ist ein Demo-Wert."
- "Nur Netto-Hoehendifferenz eingegeben; echte Bergauf-/Bergabanteile unbekannt."
- "Preisverteilung basiert auf nur 3 Samples."
- "EV Database Wert nicht automatisch importiert; bitte Lizenz beachten."
- "EPA-Werte koennen Ladeverluste enthalten; nicht direkt mit Batterie-Radmodell gleichsetzen."

## NiceGUI-Hinweise

Der bestehende Code hat bereits wichtige NiceGUI-Erfahrung:

- native Komponenten bevorzugen
- keine fragilen JS/Python-Bridges
- bei interaktiven Elementen vorsichtig mit `.clear()` und Rebuild
- Chart- und Tabellenlogik aus `main.py` auslagern

Empfehlung:

- Chart-Container duerfen neu gerendert werden.
- Interaktive Listen besser stabil halten und Optionen aktualisieren.
- State zentralisieren.
- UI-Tests spaeter ergaenzen.
