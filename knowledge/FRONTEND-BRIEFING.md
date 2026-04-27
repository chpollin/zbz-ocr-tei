---
type: knowledge
created: 2026-03-27
tags: [zbz-ocr-tei, frontend, diagnostik, briefing]
status: active
---

# Frontend-Briefing: CER-Ergebnisdarstellung

## Ausgangslage

Die OCR-Pipeline erreicht einen **Median-CER von 1.83%** (Mean 4.10%) auf 19 scope-bereinigten Dokumenten — besser als Transkribus allein (3.67%) und Gemini 2.5 Pro zero-shot (3.36%). 68% der Dokumente liegen unter 3%, die besten bei 0.3-0.8% (State of the Art). Nur 2 von 19 Docs ueberschreiten 15% CER. 93% der im Benchmark gemessenen Differenzen sind Scope-Mismatches, keine echten OCR-Fehler.

Die Web-Darstellung dieser Ergebnisse (`docs/infrastruktur/diagnostik.html`) ist **funktional vorhanden**, aber visuell und narrativ unzureichend fuer ein Fachpublikum.

## Was "sehr gut" hier bedeutet

Fuer eine digitale Edition mit epistemischem Anspruch heisst "sehr gut" nicht huebsche Charts, sondern:

- **Nachvollziehbarkeit**: Fachpublikum (DH, Editionswissenschaft) muss den Weg von Scan zu TEI verstehen — nicht nur Endzahlen, sondern Methodik, Ausschlusskriterien, Schwaechen
- **Vergleichbarkeit**: Eigene CER-Werte neben publizierten Referenzwerten (Crosilla 2025, Nosova 2025)
- **Transparenz**: Scope-Mismatches und Problemdokumente sichtbar, nicht versteckt
- **Drill-Down**: Von der Verteilung zum einzelnen Dokument zum Fehler

## Ist-Zustand

| Komponente | Datei | Status |
|------------|-------|--------|
| 4-Tab-Diagnostik (Uebersicht, OCR, TEI, Aktivitaet) | `diagnostik.html` | Vorhanden |
| Rendering-Logik (483 Zeilen Vanilla JS) | `diagnostik.js` | Funktional |
| Datenquellen (OCR, TEI, Log) | `diagnostik_ocr.json` etc. | Gut strukturiert |
| Styles | `infra.css` | Grundlegend |
| Chart-Library | — | Keine (alles HTML-Tabellen + CSS-Balken) |

Die Daten enthalten bereits `baseline_comparison` (25 Docs mit CER, WER, Sprache, Layout-Typ, Scope-Status), `confusion_matrix`, `by_language`, `by_layout`. Die Datengrundlage ist solide — es fehlt die visuelle Schicht.

## Arbeitspaket (5 Aufgaben)

### 1. CER-Verteilungschart (Kernaufgabe)

**Ist:** Sortierbare Tabelle (`diagnostik.js` Z.240-273)
**Soll:** Sortiertes Balkendiagramm — alle Docs auf X-Achse nach CER sortiert, Schwellenwertlinien bei 3% und 15%, Farbkodierung nach Sprache oder Layout-Typ. Auf einen Blick: wo liegen die Dokumente, wo die Ausreisser?

### 2. Literaturvergleich inline

**Ist:** Fehlt komplett (Referenzwerte nur in `knowledge/CER-BENCHMARK.md`)
**Soll:** Horizontaler Dot Plot oder annotierte Achse neben den eigenen Werten: "Hersch-Edition 1.83% | Transkribus 3.67% | Gemini 2.5 Pro 3.36% | GPT-4o 6.31%". Neues JSON-Feld `literature_benchmarks` in `diagnostik_ocr.json`.

### 3. Scope-Transparenz

**Ist:** Scope-Mismatches nur als Spalte in der Doc-Tabelle
**Soll:** Eigener Abschnitt *vor* den Hauptmetriken: "6 Docs ausgeschlossen" mit Begruendung (Seitenverhaeltnis Ref/Pipeline, Ursache). Methodische Entscheidung wird sichtbar.

### 4. Doc-Tabelle mit Drill-Down

**Ist:** Klick sortiert nur, kein Link
**Soll:** Klick auf Doc-ID oeffnet `viewer.html?id=X` — Faksimile neben erkanntem Text.

### 5. Konfusionsmatrix visuell

**Ist:** Flache 3-Spalten-Tabelle (Ref, Hyp, Anzahl)
**Soll:** Heatmap-Grid oder proportionale Balken pro Substitution.

## Betroffene Dateien

```
docs/infrastruktur/diagnostik.html   — HTML-Struktur (neue Sektionen)
docs/js/diagnostik.js                — Rendering-Logik (Hauptarbeit)
docs/css/infra.css                   — Styles fuer Charts/Heatmap
docs/data/diagnostik_ocr.json        — Feld literature_benchmarks ergaenzen
```

Empfehlung: **Observable Plot** via CDN als Chart-Library — leichtgewichtig, passt zur bestehenden Vanilla-JS-Architektur.

## Ideales Team

| Rolle | Aufgabe |
|-------|---------|
| **Information Designer** | Visuelle Sprache: CER-Verteilung erzaehlbar machen, Schwellenwerte, Farbkodierung |
| **DH-Editionswissenschaftler/in** | Inhaltliche Priorisierung: welche Metriken sind fuer kritische Editionen relevant vs. nice-to-have? Literaturvergleich kuratieren |
| **Frontend-Entwickler/in** | Observable Plot / D3 integrieren, Drill-Down bauen, bestehende JS-Architektur erweitern |

Optional: UX-Kurztest (1-2 Tage) mit 3-5 Personen aus der Zielgruppe.

## Priorisierung

**Aufgabe 1** (CER-Verteilungschart) und **3** (Scope-Transparenz) bringen den groessten Erklaerungswert bei geringstem Aufwand. **Aufgabe 2** (Literaturvergleich) ist wissenschaftlich am wichtigsten. **4** und **5** sind Kuer.
