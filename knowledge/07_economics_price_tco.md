# 07 - Economics, Price and TCO

## Motivation

Effizienz allein reicht fuer reale Entscheidungen nicht. Ein extrem effizientes Auto kann teuer sein, ein weniger effizientes Auto gebraucht sehr guenstig. Daher sollen Verbrauch, Reichweite und Preis zusammengefuehrt werden.

## Preisarten

### Neupreis

Felder:

- Listenpreis
- Jahr
- Land
- Variante
- Batterie
- Ausstattung
- Quelle

### Gebrauchtpreis

Nicht als einzelner Wert, sondern als Stichprobe.

Felder pro Sample:

- Preis
- Datum
- Land
- Kilometerstand
- Erstzulassung
- Alter
- Batterie/Variante
- Zustand
- Anbieterart
- Quelle

## Preisverteilung

Nicht standardmaessig als Glockenkurve modellieren.

Gebrauchtwagenpreise sind oft schief verteilt wegen:

- Kilometerstand
- Alter
- Ausstattung
- Akku-Zustand
- Haendler vs privat
- Region
- Unfallhistorie
- Saisonalitaet
- Foerderungen/Steuern

Standarddarstellung:

- Median
- p10/p25/p75/p90
- Histogramm
- Boxplot oder Violin
- Sample Count
- Ausreisser markiert

Optional:

- Normalverteilungs-Overlay als didaktische Referenz
- KDE/Kernel-Dichte, wenn genug Samples vorhanden sind

## Effizienz-/Preis-Metriken

### Reichweite pro Euro

```text
range_per_1000_eur = route_or_speed_range_km / price_eur * 1000
```

Varianten:

- WLTP-Reichweite pro 1.000 EUR
- Autobahn-130-Reichweite pro 1.000 EUR
- Pendelroute-Fahrten pro 1.000 EUR
- Winterroute-Fahrten pro 1.000 EUR

### Energieeffizienz pro Preis

```text
efficiency_score = 1 / (kwh_per_100km * price_eur)
```

Besser als Ranking nur mit klarer Erklaerung.

### Kosten pro 100 km

EV:

```text
cost_100km = kwh_100km * electricity_price_eur_per_kwh
```

ICE:

```text
cost_100km = liters_100km * fuel_price_eur_per_liter
```

### Monatskosten Pendelroute

```text
monthly_distance = one_way_distance * trips_per_day * workdays_per_month
monthly_energy_cost = route_energy_per_trip * trips_per_month * energy_price
```

### TCO

MVP:

```text
TCO = depreciation + energy_cost + insurance + maintenance + taxes
```

Start einfach:

- Kaufpreis
- Restwert nach X Jahren
- Jahreskilometer
- Energie-/Kraftstoffpreis
- Wartungspauschale
- Steuer/Versicherung optional

## Break-even EV vs ICE

Vergleich:

- Mehrpreis EV
- Verbrauchskosten EV
- Verbrauchskosten ICE
- Wartung
- Restwert

```text
break_even_km = price_delta / (cost_per_km_ice - cost_per_km_ev)
```

Warnung:

- Nur grobe Naeherung.
- Restwert und Reparaturen dominieren oft.
- Foerderungen/Steuern landesspezifisch.

## UI-Ideen

### Preisverteilungs-Accordion pro Fahrzeug

In Effizienzcharts kann jedes Fahrzeug eine aufklappbare Preisverteilung haben:

- Medianpreis
- Range p10-p90
- Histogramm
- Sample Count
- Filterchips: Baujahr, km, Land

### Kombinierte Charts

1. Verbrauch bei 130 km/h vs Gebrauchtpreis
2. Pendelroute-kWh/Fahrt vs Gebrauchtpreis
3. Reichweite pro 1.000 EUR
4. Monatskosten bei Pendlerprofil
5. TCO ueber 5 Jahre

## Datenquellen fuer Preise

MVP:

- manuelle CSV
- eigene Beobachtungen
- Demo-Samples

Spaeter:

- AutoScout/mobile.de nur wenn Nutzungsbedingungen es erlauben
- Kaggle/öffentliche Datensätze falls lizenzierbar
- Nutzerimport

## Tests

- Median und Quantile korrekt
- Ausreisserbehandlung
- Filter nach Kilometerstand/Baujahr
- Reichweite-pro-Euro korrekt
- TCO-Komponenten summieren korrekt
- Break-even bei negativen/gleichen Kosten robust
