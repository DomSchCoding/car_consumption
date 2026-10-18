# Design System

Stand: 2026-10-18

Zentrales UI-Design für die Web-App. Alle Tokens, Farben und CSS-Klassen
liegen in `app/ui/theme.py` (`LIGHT`, `DARK`, `THEME_CSS`, `DARK_MODE_CSS`).
**Neue UI-Elemente immer über die dortigen Klassen aufbauen, keine
ad-hoc-Farben in Komponenten.**

## Grundprinzipien

- Modern, ruhig, icon-getrieben: ein Akzentfarbton (Indigo), Slate-Neutrals
- Keine externen Fonts/CDNs — die App muss offline im LAN laufen
  (System-Font-Stack, Material-Icons von NiceGUI/Quasar)
- Weiche Oberflächen: 16px Card-Radius, 1px Borders, weiche Schattenebenen
- Eindeutige Typo-Hierarchie: 800 für Werte/Titel, 700 für Labels,
  600 für Text; `tabular-nums` in allen Zahlenkolonnen

## Farbpalette

| Rolle | Light | Dark |
|---|---|---|
| Hintergrund | `#f6f7fb → #eef1f8` (Gradient) | `#0b1020 → #10162b` |
| Karte | `#ffffff` | `#141a2e` |
| Karte-Border | `rgba(15,23,42,0.07)` | `rgba(148,163,184,0.14)` |
| Text primär / sekundär / tertiär | `#0f172a / #475569 / #94a3b8` | `#e5e7eb / #94a3b8 / #64748b` |
| Akzent / Akzent-soft | `#6366f1 / #eef2ff` | `#818cf8 / rgba(129,140,248,0.14)` |
| Semantik EV/ICE | `#16a34a / #dc2626` | `#4ade80 / #f87171` |
| Warnung / Gefahr | `#d97706 / #dc2626` | `#fbbf24 / #f87171` |

## Wichtige Klassen (Auszug)

- `.app-nav`, `.app-nav-brand`, `.app-nav-brand-icon`, `.app-nav-link`
  — Sticky-Navigation mit Blur, Brand-Chip (Gradient) + Pill-Links
- `.q-card` — globaler Karten-Look (Radius, Shadow, Border, Light/Dark)
- `.app-stat-strip`, `.app-stat`, `.app-stat-icon`, `.app-stat-value/label`
  — Dashboard-Übersichtsleiste (Fleet-Stats)
- `.section-header`, `.section-icon` — Karten-Sektionskopf mit Icon-Chip
- `.rank-row`, `.rank-medal(-1/2/3)`, `.rank-badge-ev/ice`,
  `.rank-value-ev/ice` — Fahrzeug-Ranking
- `.detail-grid`, `.detail-col`, `.detail-row/label/value/header/sub/missing`
  — Fahrzeug-Detailseite (native NiceGUI-Komponenten)
- `.app-table*` — Tabellen (sticky Header, Zebra, Hover, tabular-nums)
- Responsive: Compare stapelt <900px, Detail-Bild vollflächig <768px,
  Stat-Chips 2er-Reihe <768px

## Icons

- Navigation/Tab-Labels: Material-Icons über `.props("icon=…")`
  (space_dashboard, map, calculate, bar_chart, table_rows, emoji_events,
  settings, directions_car, electric_car, speed, payments)
- Sektions-Icons: `tune`, `speed`, `source`, `sticky_note_2`
- App-Logo (Brand + Favicon): generiertes Icon `app/static/logo.png`
  (Ideogram 4, flat vector, Indigo-Gradient) — bei Änderung: neu generieren
  und hier dokumentieren (Seed/Prompt im Commit-Hinweis halten)

## Dark Mode

- Schalter in der Navigation (`.dark-mode` auf `<body>`, Session-Flag)
- Alle Dark-Overrides stehen in `DARK_MODE_CSS` — neue Klassen, die
  farbige Inline-Styles brauchen, müssen dort einen Override bekommen
- Inline-Hex-Farben in Komponenten vermeiden, wo eine Theme-Klasse passt
