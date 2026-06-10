---
type: journal
created: 2026-01-29
updated: 2026-06-10
tags: [zbz-ocr-tei, journal]
status: active
---

# Arbeitsjournal

Kompakter chronologischer Ueberblick aller Arbeitssitzungen. Eine Zeile pro Sitzung;
Entscheidungen und Begruendungen in [decisions.md](decisions.md), Code-Aenderungen im Git-Log.

---

## Juni 2026 — Abnahme-Vorbereitung

| # | Datum | Thema |
|---|---|---|
| 69 | 2026-06-10 | Repository-Audit mit Umsetzungswelle (E86). Im Viewer das Datenverlust-Risiko des XML-Modus behoben: er laedt jetzt das Gesamtdokument, ein Save-Guard weist unvollstaendige TEI-Inhalte ab; dazu die uebrigen Befunde der Frontend-Gap-Analyse (Seitennavigation, Katalog-Statusaktualisierung, Fehlermeldungen, Tastaturbedienung, Barrierefreiheit). Ein GitHub-Actions-Test-Gate prueft seither jeden Push; `requirements.txt` fuer frische Umgebungen lauffaehig gemacht. CER-Kennzahlen site-weit auf den kanonischen Stand (Mean 2,71 %/Median 1,40 %) vereinheitlicht; Wissensbasis konsolidiert (Entscheidungsregister fuehrt E64 ff. mit Begruendung als Unterkapitel, Roadmap auf den Ist-Stand gebracht, `data/curated_tei/` als vorgesehen fuer kuenftig verifizierte TEI und derzeit leer praezisiert). Suite 563 gruen. |
| 68 | 2026-06-08 | Doc-30-Bereinigung und Tail-Analyse (E82): ein dupliziertes OCR-Blockpaar entfernt (Fidelity-CER 18,25 -> 11,59 %). Die Analyse der verbliebenen Ausreisser zeigt strukturelle Ursachen (Fussnoten-Ueberdetektion, Scope-Differenzen, Doppelseiten), keine Schwaechen der Zeichenerkennung. Korpus-Mean 4,26 -> 3,99 % konsistent publiziert. |
| 67 | 2026-06-08 | Transkribus-Export/Upload (E81): Pipeline-PAGE-XML rueckspielbar nach Transkribus (`edition.transkribus_export` baut Bundles, `edition.transkribus_upload` laedt via REST in eine Collection). Stichprobe 18 Docs gebaut, Doc 1500 in der Plattform verifiziert; Auth nur via Env-Vars. |
| 66 | 2026-06-08 | CER-Einordnung print-kalibriert (E80): da der Korpus aus Druckseiten besteht, ist der Vergleich mit Handschriften-Benchmarks unangemessen; die Bewertung wurde am Print-Literaturvergleich ausgerichtet und wertende Zuschreibungen entfernt. Geaendert: quality.md, methode.html, Arbeitsbericht. |
| 65 | 2026-06-07 | M2.4 Bild-URL-Schema + ZBZ-Testplan fuer die teiCrafter-Integration: Bildregel pro `<surface xml:id="facs_K">` ist `{id}_p{KKK}.png` mit K = Scan-Position (nicht `@n`; Edge Case 2310 beachten), Deployment live verifiziert (GitHub Pages, kein IIIF), Demo-Objekt 1540 gewaehlt. Erstellt: `reports/bericht-m2-2026-06-07.md` + Testplan T1-T9. |
| 64 | 2026-06-07 | Frontend-Gap-Analyse ueber 6 Frontends (live + statisch): Hersch-HOCH-Befunde H1 (TEI-XML-Edit kann `_final.xml` ueberschreiben) bis H5 (Modal ohne Fokus-Trap), Token-Disziplin bestaetigt. Neues Knowledge-Doc [frontend-gaps.md](frontend-gaps.md) als SSoT + datierter Bericht in `reports/`. |
| 63 | 2026-06-07 | Viewer-Kuration: ein Speichern-Knopf (E78) + Mirror-Write-Fix (E79). Gespeicherte Korrekturen verschwanden nach dem Seiten-Reload, weil der Viewer nur aus `docs/data/` liest, E72 aber nur nach `output/` schrieb; seitdem spiegelt jeder Speichervorgang die identische Nutzlast in beide Ablagen, der Viewer liest kuratierte Daten zuerst. Einzel-Downloads im Export-Dropdown. |
| 62 | 2026-06-07 | Workflow-Status von vier auf drei Stufen kollabiert (E77): `unverifiziert\|in_arbeit\|verifiziert`, eine Farbe je Stufe (grau/gelb/gruen), rot reserviert. Backend + Frontend + CSS umgestellt, neues Gate `test_workflow_status.py`, Suite 525 gruen; keine Mirror-Regeneration noetig (alle 285 Docs standen auf `unverifiziert`). |
| 61 | 2026-06-03 | Abnahme-Tiefenanalyse + Repo-Hygiene + MMSID-Entfernung (E76): Korpus-Invarianten am realen Datenbestand verifiziert (524 Tests gruen, 285/285 schema-valide, 0 Drift), Abnahme-Befunde dokumentiert (855 Stroeme `unverifiziert`, 195 leere Container-Titel, Doc 10 unvollstaendig). Die Projektion der Alma-Katalognummer (MMSID) in den TEI-Header wurde nach Vorlage des Spezifikations-Konflikts entfernt, da Katalog-Metadaten in der ZBZ-Domaene liegen (O8); Root-README abnahmetauglich neu gefasst. |

---

## Mai 2026 — Viewer-Datenversorgung + Deploy-Vorbereitung + Edition-Uplift

| # | Datum | Thema |
|---|---|---|
| 60 | 2026-05-27 | Frontend-UI-Review aller 5 `docs/`-Seiten + Quick-Wins: blockierendes `window.prompt()` fuers Bearbeiter-Kuerzel durch Inline-Feld ersetzt, Statuswechsel erst bei echter Aenderung statt beim Oeffnen, Dirty-Marker pro Strom, Mobile-/Filter-/Sortier-Fixes, JS-Cache-Versionierung (`?v=`). Bewusst offen gelassen: toter Panel-Divider, TEI-gerendert-Edit ohne Speicherpfad, Umlaut-Transliteration der UI-Chrome, fragmentierte Sprachfilter. |
| 59 | 2026-05-27 | Repository-Aufraeum-Welle W1-W5 (10 Commits): Doku-Drift + tote NER-Reste + Hex-zu-Token bereinigt, OCR-Quellen auf `loaders.OCR_SOURCES` vereinheitlicht, inkohaerente CER-Scope-Ausschlussliste entfernt (alle Metriken n=25, Fidelity 4,26/1,83 bleibt exakt, E73), Schematron dokumentiert statt gebaut (E74), `ocr_dedup` + DoclingOCR-Engine entfernt (E75). Suite 524 gruen. |
| 58 | 2026-05-27 | Direkt-Schreiben-Loop fuer die Viewer-Kuration (E72): `ZBZ.FsAccess` schreibt per File System Access API in den freigegebenen Repo-Ordner (Chromium, Download-Fallback), und `loaders.py` konsumiert kuratierte Layout-/OCR-Dateien real in `--reassemble`. Gate `test_curated_loaders.py`. |
| 57 | 2026-05-27 | Doku-Korrektheits-Welle: alle Markdown-Docs gegen den realen Repo-Stand auditiert (Entscheidungs-Zaehler, Agent-Screening-Reste in workflow.md, fehlende Artefakte, Test-Inventar) und parallel zu E70/E71 nachgezogen. Kein Commit (gemischter Tree). |
| 56 | 2026-05-27 | NER/Entity-Linking vollstaendig entfernt (E71): nur ~2,6 % der ~30.500 Erwaehnungen trugen echte GND-IDs, die Verlinkung war nie lieferfaehig. Code, Daten und Frontend-Anteile entfernt, deterministischer Tag-Strip ueber alle 285 TEI, 285/285 schema-valide. |
| 55 | 2026-05-27 | CER-Methodik tief geprueft + korrigiert (E70): ZBZ-Referenzen sind selektive Teiltranskriptionen, das alte Alignment-Trimming verbarg das. Neue Fidelity/Scope-Zerlegung, Headline Fidelity Mean 4,26 %/Median 1,83 % ueber alle 25 Docs, drei CER-Pfade vereinheitlicht, Paired-Test korrigiert. 18 goldene Tests, Suite 507 gruen. |
| 54 | 2026-05-27 | Hygiene + Korrektheits-Welle (E69): stiller Validator-CER-Importfehler behoben, `<pb>`-Splitter-Duplikat zu `pb_split.py` zusammengefuehrt (byte-identisch ueber alle 285 Finals verifiziert), `build_tei_header` auf den Liefer-Vertrag gehoben (idno + biblStruct + langUsage). Suite 503 gruen. |
| 53 | 2026-05-27 | Schema-Regression entdeckt + behoben (E68): die ausgelieferte Schicht `tei_final` wurde nie batch-validiert und stand bei 0/285 valide (teiHeader-Elemente fehlten im ODD-Subset). Schema ergaenzt, 285/285 valide, neues Gate `test_tei_schema.py`. |
| 52 | 2026-05-26 | E66-Abschluss: `tei_status_marker` ueber alle 285 Docs (285 irrefuehrende Agent-Screening-Eintraege raus, 855 ehrliche Workflow-Eintraege rein), 4 Commits gepusht, Frontend-Audit mit 15 priorisierten Befunden, tote Screening-Badges entfernt. |
| 51 | 2026-05-26 | Catalog-UI-Refactor + Ampel-Reframing (E67): Status `offen` umbenannt in `unverifiziert` (Pipeline-Output existiert, ist nur ungeprueft), rot reserviert; Filter, Spalten-Sortierung und Workflow-Spalte ueberarbeitet, Footer + Impressum site-weit konsistent. |
| 50 | 2026-05-26 | Agent-Screening abgeschafft, Workflow-Status pro Strom eingefuehrt (E66): menschengesetzte Statuswerte je Datenstrom mit Provenienz-History im Pro-Objekt-Manifest; Catalog + Viewer umgestellt, `tei_status_marker` projiziert die History in den `<revisionDesc>`. |
| 49 | 2026-05-26 | Leerseiten-Manifest + TEI-Marker (E63 Phase 2; E65): `page_manifest.py` detektiert deterministisch 79 Leerseiten in 15 Docs (OCR-Regel + Docling=0, cross-validiert, 0 Konflikte), `tei_blank_marker.py` projiziert `<pb type="blank"/>` und leert Junk-Bodies. 0 Schema-Regression. |
| 48 | 2026-05-26 | Viewer-UI verdichtet (E64): totes OCR-Engine-Dropdown entfernt (Viewer = ausgelieferte Edition = Mistral), Doc-Subbar + Toolbar fusioniert, Edit-Toggles heissen "Layout"/"Text". |
| 47 | 2026-05-26 | Viewer-Live-Review + Leerseiten-Welle (E63): Leerseiten zeigten OCR-Muell + Phantom-Regionen; Blank-Handling im Viewer gebaut und Architektur entschieden: Pro-Objekt-Manifest als SSoT fuer Seiten-Fakten, TEI-Marker als Projektion daraus. |
| 46 | 2026-05-26 | Methode-Seite `docs/methode.html` als schlanke Nachfolgerin des abgeschafften CER-Dashboards (E62): Headline-CER, Stratifizierung, Literaturvergleich, Limitations, Werkzeug-Doku. |
| 45 | 2026-05-25 | Edition-Uplift-Welle gestartet (E58-E61): OpenSeadragon 5.0.1 als Faksimile-Renderer, Polygone explizit ausgeschlossen (Druck-Korpus), Edit-Toggle pro Panel statt globaler Mode-Leiste, Export-Modul mit JSZip geplant. |
| 44 | 2026-05-25 | Befund-Fixes + Konsistenz-Refactoring: TEI-Doppelkodierung `&amp;amp;` behoben, Knowledge-Drift nach E56/E57 bereinigt, `<pb>`-Splitter balanciert jetzt `<div>`-Grenzen. Alle 4970 ausgelieferten XML wohlgeformt (vorher 327 nicht). |
| 43 | 2026-05-25 | Viewer auf vollen Korpus erweitert (E57): Mirror-Generator fuer alle 285 Docs (8083 Layout-, 4117 OCR-, 4115 TEI-Seiten via `<pb>`-Splitting), dreistufiger Pfad-Resolver, GitHub-Pages-tauglich. Bildlieferung bleibt lokal. |

---

## April 2026 — Frontend-Radikalkur + Wissenschaftliche CER-Re-Evaluation

| # | Datum | Thema |
|---|---|---|
| 42 | 2026-04-27 | Knowledge-Konsolidierung (25 auf 10 Docs) + Frontend-Radikalreduktion: Edition, Diagnostik, CER-Dashboard und Curation Editor abgeschafft, neue Single-Page-App `docs/viewer.html` (Faksimile + OCR/TEI + Layout-/Transkriptions-Editor). 9 auf 1 HTML, 23 auf 6 JS, CSS minus 84 %. E56. |
| 41 | 2026-04-27 | CER wissenschaftlich fundiert: BCa-Bootstrap-CIs (B=10000, Seed=42), Paired-Test E2E vs OCR-only, Selektionsbias ehrlich geflaggt, Pagewise-vs-Global-Artefakt diagnostiziert und in [quality.md](quality.md) dokumentiert. E54/E55. |

---

## Maerz 2026 — Pipeline-Konsolidierung + Edition

| # | Datum | Thema |
|---|---|---|
| 40 | 2026-03-27 | Frontend-Refactoring Phase 1+2: CSS-Token-Konsolidierung, HTML-Semantik (Skip-Nav, ARIA), JS-Foundation-Layer (`zbz-core.js`), Unified TEI Renderer. |
| 39 | 2026-03-26 | OCR-Diagnostik Abschluss: 6 Scope-Mismatches identifiziert; bereinigte Statistik n=19 Mean 4.18% / Median 1.83%. |
| 38 | 2026-03-26 | Diagnostik-UI Rewrite: 4 Tabs, ZBZ.Diagnostik-Namespace, Search-Index 279→285 (XML-Parsing-Fix). |
| 37 | 2026-03-26 | Diagnostik-Datenproduktion: W10-Tiefenanalyse, Corpus-Statistik (285 Docs / 4.108 Seiten), Validierungs-Timeline. |
| 36 | 2026-03-26 | Edition-Sync Fortsetzung: Log-Tab, Seitenzaehlung 383→4.117. |
| 35 | 2026-03-26 | Edition-Synchronisation: Katalog 15→285 Docs, Wikidata-Resume-Flag, revisionDesc im Reader. |
| 34 | 2026-03-26 | TEI-Qualitaet: ref-Pattern in `zbz_hersch.rng` erweitert (GND + #zbz), 285/285 schema-valide. Heuristische lb-Injection (10.635 lb in 46 Docs), Post-Assembly-Fixes W3/W4/W7. |
| 33 | 2026-03-26 | OCR-Diagnostik + Eval-Optimierung: Symmetrische Normalisierung, Hyphen, CI-Alignment. Mean CER 9.33%→5.97%, Median 5.52%→2.42%. |
| 32 | 2026-03-26 | End-to-End CER Benchmark (E51): TEI-vs-TEI Eval, `benchmark_cer.py`, Median 5.5%. Sub-Projekt CER-Verbesserung definiert. |
| 31 | 2026-03-26 | Neues Schema `zbz_hersch.rng` + verbindliche Editionsrichtlinien ZBZ eingearbeitet (18 Dateien). E48/E49/E50 (Dual-Attribut). |
| 30 | 2026-03-15 | Hersch Design-System: Migration auf Anthrazit+Ziegelrot+EB Garamond+Jost. Zweistufige CSS-Tokens (`--h-*` / `--ed-*`). Hersch-Komponenten (Seuil, Etonnement, Polyphonie). |
| 29 | 2026-03-15 | NEEDS_REVIEW 32→0: 20 neue Entity-Stopwoerter (E45), Strukturfixes, OCR-Dedup `ocr_dedup.py` (E46). Finalstand 242 APPROVED / 43 WITH_NOTES / 0 NEEDS_REVIEW. |
| 28 | 2026-03-15 | Edition Frontend Refactoring: Discovery Hub, Volltextsuche, Galerie, Screening + Curation Workflow getrennt, 5 Curation-States. |
| 27 | 2026-03-15 | Agent-Based Quality Screening Rollout 285/285 (58 Batches, 4 Tiers): 210 APPROVED, 43 WITH_NOTES, 32 NEEDS_REVIEW. revisionDesc-Standard etabliert (E42), `output/tei_final/` als Single Source of Truth (E43). |
| 26 | 2026-03-15 | TEI Validation Quality Gate refactored: 2-Ebenen (Errors/Warnings), W1-W11, HTML-Report. Entity-Tagging typkorrekt mit internen IDs. div-Merge. `--reassemble` Flag. 284/285 VALID. |
| 25 | 2026-03-14 | Frontend-Konsolidierung: Edition nach `docs/`, Pipeline-UI nach `docs/infrastruktur/`. ES5→ES6+ in 13 JS-Dateien. |
| 24 | 2026-03-12 | Viewer-Erweiterung: WD/zbz-ID Support, GND-0%-Bug behoben (`entity_index.py` schrieb GND nie ins TEI-XML — Fix + Cache-Backfill, 0%→21.7%). |
| 23 | 2026-03-09 | NER Completion + TEI Entity Injection: 285 Docs, 11.685 Entities, 26.197 Mentions. Wikidata-Linking gestartet. |
| 22 | 2026-03-09 | Knowledge-Refactoring: EDITION + CURATION getrennt. NER Production Run 285 Docs, 4.100 Index-Eintraege. |
| 19-21 | 2026-03-08–09 | Curation Editor Phasen 2-5: Block-Toolbar, Entity-Kuration mit Autocomplete, Review-Workflow (3 Status), TEI-Validierung. `data/tei_curated/` als git-tracked Gold-Standard. |
| 17-18 | 2026-03-08 | tei_unified Refactoring (Orchestrator ~1100→~70 Z.). NER-Robustheit (Diakritik, Retry, Surname-Matching). NER Production Phase 1 (7 Qualitaetsverbesserungen, E35). |
| 14-16 | 2026-03-06–07 | Unified TEI Pipeline (E32): 4 Stufen (Scaffold + Gemini + Assembly + Validation). NER Pipeline (E34): Gemini Flash Lite, 6 Entity-Typen, Wikidata-Reconciliation. |
| 12-13 | 2026-03-06 | Gemini Vision TEI (E30, superseded). Dokumenttyp-spezifische Prompts (4-Ebenen). Layout-QA Full Run E31 (14.708 Korrekturen). |
| 11 | 2026-03-05 | Gemini-Dokumentklassifikation (E27, Stage 1a). Online-Demo (E28). Gemini OCR-Korrektur Stage 2b (E29). |
| 9-10 | 2026-03-03–04 | docling-serve API (E24), Gemini Layout QA + Detect (E25/E26): 3 Modi (qa/detect/auto). |

---

## Februar 2026 — Pipeline-Aufbau

| # | Datum | Thema |
|---|---|---|
| 7-8 | 2026-02-25–27 | Scope-Expansion (E21): Full Pipeline (OCR + Layout + PAGE-XML + NER/GND + TEI). Pilot 15 Docs, page-by-page Comparison (E16/E18). Data Delivery E23 (286 PDFs, 25 TEI-XMLs). |
| 4-6 | 2026-02-14–20 | Mistral OCR 3 als Production Engine (E6). Azure-Integration. PAGE-XML + METS Export (E13, Schema 2013-07-15). Dashboard-Redesign (E15). |
| 1-3 | 2026-01-29–02-14 | Initiale Quellenanalyse: 286 PDFs, 4 Dokumenttypen (A-D), Sprachverteilung FR 66% / DE 30%. Hybrid Pipeline-Entscheidung (E1): Docling Layout + LLM-OCR Text. |

Aeltere Detail-Eintraege im Git-Verlauf erhalten.

---

## Wiederkehrende Muster

Aus den Sessions destillierte Beobachtungen, die fuer kuenftige Arbeit relevant bleiben:

- **L1** Validierung muss actionable sein. False-Positive-Quote >50% macht Reports nutzlos. Jede Warning braucht eine konkrete Aktion.
- **L2** Entity-Typ darf nicht verloren gehen. `annotate_entities()` braucht `(tag, id)` aus dem Index, nicht nur Namen.
- **L3** Stopwort-Filter ist essenziell. Gattungsbegriffe (Mensch, Gott, Wahl) erzeugen ohne Filter ~30% False Positives.
- **L4** Seiten-Fragmente zu Dokument-Struktur mergen. ZBZ-Referenz hat 1 top-level div. Post-Assembly-Merge ist deterministisch und kostenlos.
- **L5** Step-2-Cache invalidieren bei Prompt-Aenderungen. `--force` regeneriert nicht den Step-2-Cache.
- **L6** LLM-NER hat ~5-10% False Positives. Inhaerent. Loesung: Curation Editor, nicht Code-Fix.
- **L7** Page-Numbering-Drift macht Pagewise-CER unbrauchbar. Content-aligned Eval (`evaluate_tei_vs_tei`) ist immun.
- **L8** Mehrsprachige Codes korrekt parsen. "fra/deu" zerfaellt sonst zu "und". Betrifft ~40 Docs.
- **L9** facsimile/pb synchron halten. Leere surfaces fuer Seiten ohne Layout-Zones.
- **L10** Interne IDs (zbz-p/o/l/w.N) als primaere Referenz. GND in `ref`, intern in `corresp` (Dual-Attribut, E50).
- **L11** Eine server-lose Persistenz hat zwei Wahrheiten: den kanonischen Konsum-Ort (`output/`, Pipeline) und den Lese-Ort des Frontends (`docs/data/`-Mirror). Wer nur in den ersten schreibt, speichert real, aber unsichtbar fuer den Kuratierenden.
- **L12** Bei parallelen Instanzen im selben Tree sind `git status` + Verifikation gegen den realen Dateistand Pflicht; ein "file modified since read"-Konflikt ist das Signal zum Zuruecktreten, nicht zum Erzwingen.
- **L13** Eine Prosa-Zahl ("285/285 valide") ist kein Beleg. Die ausgelieferte SSoT braucht ein automatisiertes Gate, keine Behauptung.
- **P7** Gattungsbegriffe im Entity-Index erzeugen False Positives in ~30% der Docs.
- **P8** Zeitungslayouts versagen systematisch (>40 Zones, OCR-Halluzinationen). ~3% des Korpus.
- **P10** Tier-2-Docs (4-8 Seiten) haben 85%+ APPROVED-Rate, Tier-1 (1-3 Seiten) nur 40%.
