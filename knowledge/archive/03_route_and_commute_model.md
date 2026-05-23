# 03 - Route and Commute Model

## Warum Route ein Kernfeature ist

Eine konkrete Route macht das Projekt praktisch relevant. Viele Nutzer interessieren sich nicht nur fuer Verbrauch bei 100 km/h, sondern fuer:

- meine Pendelstrecke
- mein Arbeitsweg im Winter
- ein Wochenendtrip ueber Huegel/Berge
- Lieferdienst mit vielen Stopps
- Autobahnetappe mit Gegenwind
- Hinweg bergauf, Rueckweg bergab
- wie oft schaffe ich Hin-und-Rueckweg pro Ladung?

## Produktanforderung

Die App soll eine Route eingeben und fuer ausgewaehlte Fahrzeuge berechnen:

- Energie pro Fahrt
- kWh/100 km bezogen auf Route
- Reichweite in Anzahl Fahrten
- Restakku nach Hinweg
- Restakku nach Hin-und-Rueckweg
- Kosten pro Fahrt, Monat, Jahr
- Breakdown nach Aero, Roll, Aux, Hoehe, Stop-and-go, Rekuperation, Verluste

## Modi

### Modus A: Einfache Pendelstrecke

Eingaben:

```text
Name
Distanz einfach [km]
Durchschnittsgeschwindigkeit [km/h]
Hoehendifferenz Start->Ziel [m]
Hoehenmeter bergauf [m] optional
Hoehenmeter bergab [m] optional
Stopps pro km
Standzeit pro Fahrt [min]
Temperatur [C]
Windkomponente [km/h]
nur Hinweg / Hin und Retour
Arbeitstage pro Woche
Wochen pro Jahr
```

Wenn nur Netto-Hoehendifferenz vorhanden ist:

- Hinweg bergauf, wenn Ziel hoeher liegt.
- Rueckweg bergab.
- Modell mit Warnhinweis: "Nur Netto-Hoehendifferenz, kein echtes Hoehenprofil."

Wenn `elevation_gain_m` und `elevation_loss_m` vorhanden sind:

- realistischere Berechnung je Richtung.
- Rueckweg vertauscht Gain/Loss.

### Modus B: Segmentroute

Route besteht aus Segmenten:

```text
RouteSegment:
  name
  distance_km
  avg_speed_kmh
  road_type
  elevation_gain_m
  elevation_loss_m
  stops
  stop_speed_kmh
  aux_power_kw_override
  headwind_kmh
  payload_kg
```

Beispiele:

- Wohngebiet 2 km, 30 km/h, 4 Stopps
- Landstrasse 18 km, 80 km/h, 120 m bergauf
- Autobahn 35 km, 120 km/h, Gegenwind 10 km/h
- Stadtzentrum 3 km, 25 km/h, 12 Stopps

### Modus C: GPX/CSV Import

Spaeter:

- GPX-Datei mit Trackpunkten und Hoehe
- CSV mit Distanz, Geschwindigkeit, Hoehe
- Vereinfachung/Resampling in Segmente
- optional Routenservice

MVP muss ohne externe Dienste funktionieren.

## Datenmodelle

### `Route`

```python
class Route(BaseModel):
    id: str
    name: str
    description: str | None = None
    segments: list[RouteSegment]
    source_refs: dict[str, SourceRef] = {}
    notes: str | None = None
```

### `RouteSegment`

```python
class RouteSegment(BaseModel):
    name: str
    distance_km: float
    avg_speed_kmh: float
    road_type: RoadType = RoadType.mixed
    elevation_gain_m: float = 0.0
    elevation_loss_m: float = 0.0
    stops: float = 0.0
    stop_speed_kmh: float | None = None
    dwell_time_min: float = 0.0
    headwind_kmh: float = 0.0
    payload_kg: float = 0.0
    aux_power_kw: float | None = None
```

### `CommuteScenario`

```python
class CommuteScenario(BaseModel):
    route: Route
    direction_mode: DirectionMode  # one_way, return_trip
    days_per_week: float = 5
    weeks_per_year: float = 46
    energy_price_eur_per_kwh: float | None = None
    fuel_price_eur_per_liter: float | None = None
```

### `RouteEnergyBreakdown`

```python
class RouteEnergyBreakdown(BaseModel):
    distance_km: float
    duration_h: float
    aero_kwh: float
    roll_kwh: float
    aux_kwh: float
    climb_kwh: float
    descent_recovered_kwh: float
    stop_go_kwh: float
    drivetrain_loss_kwh: float
    total_wheel_kwh: float
    total_battery_kwh: float
    kwh_per_100km: float
```

## Berechnung pro Segment

### Zeit

```text
time_h = distance_km / avg_speed_kmh
```

Plus Standzeit:

```text
time_total_h = time_h + dwell_time_min / 60
```

### Aerodynamik

```text
v_vehicle = avg_speed_kmh / 3.6
v_air = max(0, (avg_speed_kmh + headwind_kmh) / 3.6)
F_aero = 0.5 * rho_air * CdA * v_air^2
E_aero = F_aero * distance_m
```

### Rollwiderstand

```text
F_roll = c_rr * mass_total * g
E_roll = F_roll * distance_m
```

### Nebenverbrauch

```text
E_aux = aux_power_kw * time_total_h
```

### Hoehe

Bergauf:

```text
E_climb = mass_total * g * elevation_gain_m
```

Bergab Rueckgewinnung:

```text
E_descent_available = mass_total * g * elevation_loss_m
E_descent_recovered = E_descent_available * eta_regen_downhill
```

MVP:

- `eta_regen_downhill` editierbar
- Default konservativ, z.B. 0.50 bis 0.70
- fuer ICE ohne Hybrid 0.0

### Stop-and-go

Wenn `stop_speed_kmh` leer ist:

- Default je RoadType:
  - city: 35 km/h
  - suburban: 50 km/h
  - rural: 70 km/h
  - highway: 90 km/h, aber stops meist 0

```text
E_kin_per_stop = 0.5 * mass_total * v_stop^2
E_stop_net = E_kin_per_stop / eta_drive - E_kin_per_stop * eta_regen_stop
E_stop_go = stops * max(0, E_stop_net)
```

## Hinweg / Rueckweg

### Einweg

Berechne Segmente in definierter Reihenfolge.

### Hin und Retour

Rueckweg ist nicht einfach `2 * Hinweg`, wenn Hoehe, Wind, Stopps oder Geschwindigkeit asymmetrisch sind.

MVP Rueckweg:

- Segmentreihenfolge umdrehen
- `elevation_gain_m` und `elevation_loss_m` tauschen
- Windkomponente optional invertieren oder separat abfragen
- Geschwindigkeit und Stopps gleich lassen, falls keine Rueckweg-Overrides gesetzt sind

```text
return_segment.distance = segment.distance
return_segment.avg_speed = segment.avg_speed
return_segment.elevation_gain = segment.elevation_loss
return_segment.elevation_loss = segment.elevation_gain
return_segment.headwind = -segment.headwind  # optional, aber in UI erklaeren
```

UI-Schalter:

```text
[ ] Nur Hinweg
[x] Hin und Retour
[ ] Rueckweg separat bearbeiten
[ ] Windrichtung fuer Rueckweg invertieren
```

## Wichtige Darstellung

Bei Route unbedingt getrennt anzeigen:

- kWh pro Fahrt
- kWh/100 km normiert
- Fahrtdauer
- Kosten pro Fahrt
- Reichweite in Fahrten
- Anteil der Komponenten in Prozent
- Hoehenenergie brutto und rekuperiert
- Netto-Hoeheneffekt

Beispiel:

```text
Hinweg:
  17.8 km, +220 m netto, 31 min
  4.2 kWh Batterie
  23.6 kWh/100 km

Rueckweg:
  17.8 km, -220 m netto, 29 min
  2.6 kWh Batterie
  14.6 kWh/100 km

Hin+Retour:
  35.6 km
  6.8 kWh
  19.1 kWh/100 km
```

## Tests fuer Route

Pflichttests:

1. Flache Route ohne Stops entspricht Konstantgeschwindigkeitsmodell.
2. Doppelte Distanz verdoppelt Energie.
3. Hoehengewinn erhoeht Verbrauch.
4. Rueckweg mit gleicher Route tauscht Gain/Loss.
5. Hin-und-Rueckweg hat Netto-Hoehendifferenz null, aber Hoehenverluste bleiben positiv.
6. Rekuperationswirkungsgrad 0 erzeugt keine Rueckgewinnung.
7. Rekuperationswirkungsgrad 1 erzeugt maximal theoretische Rueckgewinnung, aber nie negative Gesamtenergie.
8. Stopps erhoehen Verbrauch bei `eta_regen < 1`.
9. Mehr Masse erhoeht Roll-, Hoehen- und Stop-and-go-Verbrauch.
10. Aux-Verbrauch steigt mit Fahrtdauer und Standzeit.
11. Gegenwind erhoeht Aero-Verbrauch.
12. Rueckenwind kann Aero-Verbrauch reduzieren, aber nicht negativ machen.

## UI fuer Route

### Minimaler MVP

- Neue Seite "Route / Pendeln"
- Fahrzeugauswahl wiederverwenden
- Simple-Route-Formular
- Checkbox "Hin und Retour"
- Ergebnis-Karten
- gestapeltes Balkendiagramm pro Fahrzeug
- Tabelle mit kWh/Fahrt, kWh/100 km, Kosten, Reichweite

### Spaeter

- Segmenteditor mit Add/Remove
- GPX Upload
- Hoehenprofil-Chart
- Vergleich Hinweg vs Rueckweg
- Monats-/Jahreskosten
- Akku-SOC-Simulation
- "Worst case Winter" und "Best case Sommer"
