# Recherche- und Modellnotizen

## Kernformeln

### Aerodynamik
F_aero = 0.5 * rho_air * Cd * A * v^2
P_aero = F_aero * v
kWh/100km = F_aero * 100000 / 3600000

### Rollwiderstand
F_roll = c_rr * mass_kg * g
kWh/100km = F_roll * 100000 / 3600000

### Nebenverbraucher
kWh/100km = P_aux_kW / speed_kmh * 100

### Kraftstoffenergie
fuel_energy_kWh_per_100km = liters_per_100km * kWh_per_liter
wheel_energy_estimate = fuel_energy_kWh_per_100km * thermal_efficiency

## Wichtige Einheiten
- km/h -> m/s: / 3.6
- Wh/km -> kWh/100 km: /10
- kWh/100 mi -> kWh/100 km: /1.609344
- 1 US gallon gasoline equivalent nach EPA: 33.7 kWh

## Datenquellenideen
- Herstellerdaten: bevorzugt für cw, Abmessungen, Masse, Batterie
- EPA/fueleconomy.gov: Download-CSV und API für offizielle US-Verbrauchsdaten
- EV Database: real-world EV-Verbrauch, Reichweite, Batterie; Nutzungsbedingungen beachten
- Automobil-Guru: cw und Stirnfläche, Vertrauenslevel mittel/niedrig je nach Eintrag
- Wikipedia-Liste cw-Werte: ergänzend, quellenkritisch prüfen
- Fachtests: nur mit Fahrbedingungen speichern

## Plausibilitätschecks
- Cd: grob 0.18 bis 0.45 für PKW, Vans höher möglich
- A: grob 1.8 bis 3.5 m2 für PKW/Van
- CdA: sehr effiziente PKW etwa 0.45 bis 0.60 m2; Vans/Lieferwagen oft deutlich höher
- c_rr: Pkw-Reifen grob 0.006 bis 0.012 als editierbarer Startbereich
- EV-Verbrauch: Kontextabhängig, reale Werte nie ohne Geschwindigkeit/Temperatur/Reifen vergleichen
