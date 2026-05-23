# 09 - Agent Workflow, Skills and Prompts

## Ziel

Die agentische Weiterentwicklung soll autonom, aber kontrolliert laufen.

## Benoetigte Agenten-Skills / Rollen

### 1. Software Architect

Aufgaben:

- Module schneiden
- Abhaengigkeiten sauber halten
- Refactoring planen
- Komplexitaet reduzieren

Aktuell wichtig wegen wachsendem `main.py`.

### 2. Physics Modeler

Aufgaben:

- Formeln implementieren
- Einheiten pruefen
- Grenzfaelle testen
- physikalische Plausibilitaet sicherstellen

Wichtig fuer Route, Hoehe, Wind, Rekuperation.

### 3. Data Engineer / Data Curator

Aufgaben:

- Datenmodelle erweitern
- Importer bauen
- Quellen/Confidence pflegen
- Plausibilitaetschecks

Wichtig fuer Fahrzeuge, Realverbraeuche, Preise.

### 4. UX Engineer

Aufgaben:

- Komplexe Modelle einfach bedienbar machen
- Progressive Disclosure
- gute Charts
- Warnungen/Tooltips
- mobile/responsive Layout

Wichtig fuer NiceGUI.

### 5. Test Engineer

Aufgaben:

- Testmatrix
- Golden Scenarios
- Regressionstests
- Edge Cases
- CI-Stabilitaet

### 6. Product Analyst

Aufgaben:

- Features priorisieren
- Nutzerfragen formulieren
- Metriken definieren
- Roadmap fokussieren

## Agentenregeln

Bei jedem Task:

1. Relevante Knowledge-Dateien lesen.
2. Bestehenden Code inspizieren.
3. Tests laufen lassen.
4. Kleinen Plan schreiben.
5. Minimal implementieren.
6. Tests erweitern.
7. UI nur nach Core/Data.
8. Knowledge aktualisieren.
9. Abschlussbericht.

## Gute Task-Groessen

Gut:

- "Extrahiere Chart-Erzeugung aus main.py"
- "Fuehre RouteSegment und RouteEnergyBreakdown ein"
- "Implementiere flat route calculation mit Tests"
- "Baue Route-MVP-Seite mit SimpleRoute"
- "Fuehre PriceSample und Quantile ein"

Zu gross:

- "Baue alle Routenfeatures, GPX, Preise und Datenimport"
- "Scrape alle Autodaten aus dem Internet"
- "Mach UI perfekt"

## Standard-Prompt fuer opencode

```text
Lies zuerst AGENTS.md und die Knowledge-Dateien:
- knowledge/00_project_overview.md
- knowledge/01_architecture_v2.md
- knowledge/02_physics_model_v2.md
- knowledge/03_route_and_commute_model.md
- knowledge/08_testing_strategy_v2.md
- knowledge/10_roadmap_backlog.md

Arbeite autonom, aber in kleinen lauffaehigen Schritten.
Fuehre zuerst die bestehenden Tests aus.
Implementiere keine UI-Logik, bevor die Core-Logik getestet ist.
Bei unklaren Annahmen waehle konservative Defaults, dokumentiere sie und mache sie in der UI editierbar.
Aktualisiere Knowledge/README, wenn du Verhalten oder Architektur aenderst.
```

## Naechster sinnvoller Agentenauftrag

Wenn zuerst stabilisieren:

```text
Refactore app/main.py so, dass Chart-Erzeugung, UI-State und Fahrzeugauswahl in separate Module unter app/ui/ wandern. Aendere dabei moeglichst kein Verhalten. Fuege Smoke-Tests oder zumindest Import-Tests hinzu. Danach alle Tests laufen lassen und Knowledge aktualisieren.
```

Wenn direkt Route bauen:

```text
Implementiere das Route-MVP aus knowledge/03_route_and_commute_model.md:
- Pydantic-Modelle RouteSegment, Route, CommuteScenario, RouteEnergyBreakdown
- core/route_energy.py mit Segment- und Routenberechnung
- Tests fuer flache Route, Hoehenprofil, Hin-und-Rueckweg, Stopps und Aux-Zeit
- einfache NiceGUI-Seite Route/Pendeln mit Distanz, Speed, Hoehe, Stopps, Hin+Retour Checkbox
- Chart/Tabelle fuer ausgewaehlte Fahrzeuge
```

## Umgang mit Unsicherheit

Nie blockieren, wenn sinnvolle Defaults moeglich sind.

Statt fragen:

- Default waehlen
- im Code kommentieren
- in UI editierbar machen
- in Knowledge dokumentieren

Fragen nur, wenn eine Entscheidung das Produktziel grundlegend aendert.

## Abschlussbericht-Template

```text
Geaendert:
- ...

Tests:
- pytest: ...
- ruff: ...
- pyright: ...

Annahmen:
- ...

Bekannte Grenzen:
- ...

Naechste sinnvolle Schritte:
- ...
```
