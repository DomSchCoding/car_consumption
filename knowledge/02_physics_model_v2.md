# 02 - Physics Model v2

## Ziel

Das Physikmodell soll erklaeren, nicht nur schaetzen. Es soll die wichtigsten Verbrauchskomponenten getrennt ausgeben und alle Annahmen sichtbar machen.

## Energieebenen

Immer unterscheiden:

1. Radenergie / mechanische Arbeit
2. Batterieenergie beim EV
3. Netzenergie inklusive Ladeverluste optional
4. Chemische Energie im Kraftstoff beim ICE
5. Nutzenergie am Rad beim ICE

## Basismodell

### Luftwiderstand

```text
F_aero = 0.5 * rho_air * Cd * A * v_air^2
P_aero = F_aero * v_vehicle
E_aero = F_aero * distance
```

Pro Strecke skaliert der Luftwiderstandsverbrauch mit `v^2`; Leistung mit `v^3`.

Wichtig fuer Wind:

- Aerodynamische Kraft haengt von Luftgeschwindigkeit ab.
- Strecke/Zeit haengt von Fahrzeuggeschwindigkeit ueber Grund ab.
- Gegenwind erhoeht `v_air`, Rueckenwind reduziert `v_air`.

MVP:

```text
v_air = max(0, v_vehicle + headwind_component)
F_aero = 0.5 * rho * CdA * v_air^2
E_aero = F_aero * distance
```

### Rollwiderstand

```text
F_roll = c_rr * mass * g
E_roll = F_roll * distance
```

MVP: konstant.

Spaeter:

- Reifenklasse
- Reifendruck
- Temperatur
- nasse Fahrbahn
- Geschwindigkeitseffekt
- Lastabhaengigkeit

### Nebenverbrauch

Bei konstantem Nebenverbrauch:

```text
E_aux_kWh = P_aux_kW * time_h
time_h = distance_km / speed_kmh
```

Das ist fuer Routen besser als die Kurzform `P_aux / speed * 100`, weil Stopps und Segmentzeiten wichtig werden.

Nebenverbrauch-Komponenten:

- Grundelektronik
- Infotainment
- Licht
- Klima/Kuehlung
- Heizung
- Batterieheizung
- Scheibenheizung
- Sitzheizung
- Standzeit

### Antriebswirkungsgrad EV

```text
E_battery_drive = E_wheel_positive / eta_drivetrain
```

MVP: ein konstanter Wirkungsgrad.

Spaeter:

- Geschwindigkeits-/Lastabhaengigkeit
- Motorwirkungsgrad-Karte
- Inverterverluste
- Getriebe
- Akku-Innenwiderstand

## Hoehenenergie

```text
E_potential = mass * g * height
```

Bergauf:

```text
E_climb = mass * g * elevation_gain
```

Bergab:

```text
E_descent_available = mass * g * elevation_loss
E_regen_recovered = E_descent_available * eta_regen
```

Aber:

- Rekuperation ist begrenzt durch Batterie-SoC.
- Rekuperation ist begrenzt durch Temperatur.
- Rekuperation ist begrenzt durch Leistung.
- Bergab kann auch mechanisch gebremst werden.
- Bei ICE ohne Hybrid ist Rueckgewinnung meist null.

Wichtige Modellregel:

> Bei Hin-und-Rueckweg ist die Netto-Hoehendifferenz null, aber der Energieverlust nicht null, weil bergab nur ein Teil der bergauf investierten Lageenergie zurueckgewonnen wird.

## Stop-and-go / Rekuperation

Kinetische Energie bei Beschleunigung auf Geschwindigkeit `v`:

```text
E_kin = 0.5 * mass * v^2
```

Ein Stop-and-go-Ereignis:

```text
E_accel_from_battery = E_kin / eta_drive
E_recovered_to_battery = E_kin * eta_regen
E_stop_net = E_accel_from_battery - E_recovered_to_battery
```

Vereinfachter MVP:

```text
E_stop_loss = E_kin * (1 - eta_regen_effective)
```

Besserer MVP fuer Batterieenergie:

```text
E_stop_net_battery = E_kin / eta_drive - E_kin * eta_regen_to_battery
```

Parameter:

- `stops_per_km`
- `stop_speed_kmh`
- `eta_regen`
- `regen_available`
- `traffic_smoothness`

Stadtprofil:

- niedrige Aero-Verluste
- Aux wird wichtiger wegen Zeit
- Masse wird wichtiger durch Stop-and-go
- Rekuperation reduziert, aber eliminiert nicht die Verluste

## Temperaturmodell

MVP:

- Temperatur beeinflusst HVAC-Leistung.
- Temperatur beeinflusst nutzbare Batteriekapazitaet.
- Optional: Temperatur beeinflusst Rekuperationsverfuegbarkeit.

Parameter:

```text
ambient_temp_c
cabin_temp_target_c
has_heat_pump
heat_pump_cop
battery_temp_factor
regen_temp_factor
```

Wichtig:

- Kurzstrecke im Winter kann stark durch Aufheizen dominiert werden.
- Langstrecke im Winter eher durch Dauerleistung und dichtere Luft.
- Kalte Luft erhoeht Luftdichte und damit Luftwiderstand.

## Luftdichte

Default bleibt `1.225 kg/m3`.

Spaeter berechnen aus:

- Temperatur
- Luftdruck
- Hoehe
- Feuchte optional

MVP-Form:

```text
rho = rho0 * (T0 / T)
```

Nur als Naeherung, sauber dokumentieren.

## Nutzlast

Masse:

```text
mass_total = vehicle_mass_kg + payload_kg + occupants_kg
```

Wirkt auf:

- Rollwiderstand
- Hoehenenergie
- Stop-and-go
- kaum auf Luftwiderstand

Sehr wichtig fuer:

- Lieferwagen
- Busse
- Familienautos
- Urlaubsfahrten
- Pendler mit wenig Zuladung vs Handwerkerfahrzeug

## Grenzen des Modells

Nicht im MVP exakt modellieren:

- Reifen-Walkverluste abhaengig von Geschwindigkeit/Temperatur
- Antriebswirkungsgrad-Kennfelder
- Batteriewirkungsgrad nach C-Rate
- Windboeen/Seitenwind
- Fahrerverhalten
- Verkehrsstau mit langen Standzeiten
- Regen, Schnee, Matsch
- Klima-Aufheiztransient im Innenraum
- Ladeverluste, wenn nicht explizit aktiviert

Stattdessen:

- einfache Parameter
- sichtbare Annahmen
- Sensitivitaetsanalyse
- klare Confidence
