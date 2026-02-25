---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, pipeline, datenfluss, ocr]
status: active
---

# Pipeline

Datenfluss von PDF zu TEI-XML: Stufen, Scripts, Formate. Seit Scope-Erweiterung (25.02.2026) deckt zbz-ocr-tei die gesamte Pipeline ab (OCR + Layout + PAGE-XML + NER/GND + TEI-XML). Implementierungsplan: [PLAN.md](../PLAN.md).

**Abhängigkeiten:** [PROJEKT](PROJEKT.md)

---

## Pipeline-Übersicht

```
PDF ──→ Seitenbilder ──→ OCR ──→ Layout ──→ PAGE-XML ──→ NER/GND ──→ TEI-XML
         extract_pages    ocr_pipeline  layout/    page_xml_gen    ner/       tei/
         docs/images/     output/       output/    output/         output/    output/
                          mistral_res/  layout/    page_xml/       entities/  tei_xml/
                                                       │
                              ┌─────────────────────────┘
                              ▼
                    Evaluation + Dashboard
                    evaluate_ocr + generate_dashboard_data
```

### Stufen (7-Stufen-Pipeline)

| Stufe | Aufgabe | Script | Output | Status |
|-------|---------|--------|--------|--------|
| 1 | PDF → Seitenbilder | `scripts/extract_pages.py` | PNG (`docs/images/`) | Produktiv |
| 2 | OCR | `scripts/ocr_pipeline.py` | Seitenweises Markdown (`output/mistral_results/`) | Produktiv |
| 2a | LLM-Nachkorrektur (optional) | `scripts/llm_postprocess.py` | Korrigiertes Markdown (`output/llm_corrected_c/`) | Produktiv, E17: optional |
| 3 | Layout-Analyse | `scripts/run_layout_analysis.py` | Regionen + BBox (JSON, `output/layout/`) + Overlay-PNGs | Produktiv (7/15 Docs) |
| 4 | Layout + OCR → PAGE-XML | `scripts/layout/page_xml_generator.py` | PAGE-XML + METS (`output/page_xml/`) | **Phase 1** |
| 5 | NER + GND | `scripts/ner/ner_pipeline.py` + `gnd_linker.py` | Entitaeten-JSON (`output/entities/`) | **Phase 2** |
| 6 | PAGE-XML + Entitaeten → TEI-XML | `scripts/tei/tei_generator.py` | TEI-XML (`output/tei_xml/`) | **Phase 3** |
| 7 | Evaluation + Dashboard | `scripts/evaluate_ocr.py` + `generate_dashboard_data.py` | Reports + `docs/data/dashboard.json` | Produktiv (Erweiterung in Phase 4) |

**Hilfsskripte:** `extract_pages.py` (Seitenbilder), `extract_gnd.py` (GND-IDs), `postprocess/` (Normalisierung).

**Layout-Engine (E19):** Docling 2.75 (RT-DETR V2 Heron, 17 Blocktypen, CPU). Phase 0 Evaluation bestanden: alle 4 Dokumenttypen korrekt erkannt, Spalten-Trennung Type B funktioniert. Details: [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md).

---

## Stufe 1: OCR

**Skript:** `scripts/ocr_pipeline.py`

### Engine-Auswahl (Auto-Modus in `ocr_pipeline.py`)

1. Dokument in `TWO_COLUMN_DOCS`? → Docling (Layout) + DeepSeek
2. `MISTRAL_DOC_AI_KEY` gesetzt? → Mistral Document AI (API)
3. Sonst → DeepSeek (lokal, GPU)

Dokumenttypen: Siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Dokumenttypen.
Engine-Details: Siehe [OCR-ENGINES](OCR-ENGINES.md).

### Layout-Analyse (nur Typ B)

Fuer zweispaltige Dokumente nutzt `ocr_pipeline.py` intern Docling (IBM) mit `do_ocr=False` zur Spaltenerkennung. Doclings eigene OCR wird nicht verwendet (RapidOCR hat Encoding-Probleme). Details: [OCR-ENGINES](OCR-ENGINES.md) §Docling.

### Prompts

**Mistral Document AI:** Kein Prompt — die API bekommt nur das PDF als Base64, kein Instruktionstext. Output ist seitenweises Markdown.

**DeepSeek-OCR-2:** Fester Prompt in `config.py:31`:
```
<image>\n<|grounding|>Convert the document to markdown.
```

### OCR-Qualitaet

Vollstaendige Ergebnisse: Siehe [TESTPLAN](TESTPLAN.md) §Ergebnisse.

---

## Stufe 2: LLM-Nachkorrektur

**Skript:** `scripts/llm_postprocess.py`

| Aspekt | Details |
|--------|---------|
| Modell | Claude Haiku 4.5 (Anthropic) |
| Input | OCR-Markdown aus Stufe 2 |
| Output | Korrigiertes Markdown |
| Rolle | Korrektur, NICHT Transkription — das LLM sieht nie das Bild |
| Kosten | ~$0.33 fuer 50 Seiten, ~$48 fuer 7.200 Seiten |

**Wichtig:** Das LLM macht keine OCR. Es korrigiert nur den von Mistral/DeepSeek erzeugten Text. Es erhaelt Dokumentkontext (Typ, Sprache, Genre) und identifiziert Zeichenfehler, fehlende Akzente, OCR-Artefakte.

### Prompts (3 Varianten)

Alle Prompts in `llm_postprocess.py`. Variante C ist Default (E17).

**Variante A (Analysis)** — System-Prompt mit `<analysis>` + `<corrected>` Bloecken:
```
Du bist ein Experte fuer OCR-Nachkorrektur akademischer Texte des 20. Jahrhunderts
von Jeanne Hersch (Philosophin, 1910-2000). Du erhaeltst OCR-Output aus gescannten
Dokumenten und korrigierst Zeichenfehler.

Regeln:
- Korrigiere NUR OCR-Fehler (falsche Buchstaben, fehlende Akzente, zusammengeklebte Woerter)
- Formuliere NICHTS um, erfinde NICHTS
- Markdown beibehalten
- Maschinenerzeugte Artefakte (JSTOR-Header, Copyright-Zeilen) entfernen
- Im Zweifel: unveraendert lassen

{Sprach-Hint}

Antwortformat: 1. <analysis>-Block mit Fehlerliste, 2. <corrected>-Block mit Text
```

**Variante B (Lean)** — Nur korrigierter Text, kein Analysis-Block:
```
Korrigiere OCR-Fehler im folgenden Text. [Gleiche Regeln wie A, ohne Antwortformat]
Gib NUR den korrigierten Text aus, ohne Erklaerungen.
```

**Variante C (Few-Shot, Default)** — Wie B, plus typische Mistral-OCR-Fehler als Beispiele:
```
...
Typische OCR-Fehler dieser Engine (Mistral Document AI):
- 'inconnaisable' -> 'inconnaissable' (fehlender Buchstabe)
- 'etrente' -> 'etreinte' (falsche Zeichenfolge)
- 'seule tu le courant' -> 'sens-tu le courant' (Wortgrenze falsch)
- 'rereferme' -> 'se referme' (zusammengeklebte Woerter)
- 'lisse, comme' -> 'hisse, comme' (aehnliche Buchstaben)
- 'This content downloaded from...' -> entfernen (JSTOR-Artefakt)
Gib NUR den korrigierten Text aus, ohne Erklaerungen.
```

**Sprach-Hints** (dynamisch eingefuegt, `_lang_hint()` in `llm_postprocess.py:62`):

| Sprache | Hint |
|---------|------|
| FR | Achte auf Akzente, Guillemets, Apostrophe (l', d', qu') |
| DE | Achte auf Umlaute, Eszett, Komposita |
| DE/FR | Achte auf Umlaute UND Akzente |

**User-Message-Template** (pro Seite, `build_user_message()` in `llm_postprocess.py:136`):
```
Dokument: {doc_id}
Typ: {doc_type} ({Einspaltig|Zweispaltig|Monografie|Spezialformat})
Sprache: {language}
Genre: {genre}
OCR-Engine: Mistral Document AI
Seite: {page_num} von {total_pages}

<ocr_text>
{ocr_text}
</ocr_text>
```

### Varianten-Vergleich (Phase 1-3, 10 Docs)

| Variante | Avg CER | Bemerkung |
|----------|---------|-----------|
| A (Analysis) | 5.47% | Bester CER, aber teurer (laengerer Output) |
| B (Lean) | 5.59% | Guenstigster |
| C (Few-Shot) | 5.55% | Bester CER/Kosten-Tradeoff → Default |

**Ergebnis Pilot (alle 15 Docs, Variante C Few-Shot):**

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| Phase 4 (C) | 2.65% | 2.70% | +0.05 |
| **Gesamt (15 Docs)** | **6.42%** | **6.52%** | **+0.10** |

**Erkenntnis:** LLM-Korrektur verbessert Docs mit CER >10%, verschlechtert leicht bei gutem OCR (<5%). Empfehlung: Optional einsetzen, nicht als Default.

### Optimierungspotenzial (Recherche 25.02.2026)

| Idee | Erwarteter Effekt | Aufwand | Quelle |
|------|-------------------|---------|--------|
| **Multimodale Korrektur** (Scan-Bild + OCR-Text) | <1% CER laut Forschung | Mittel (Sonnet/Opus noetig, hoehere Kosten) | [arXiv:2504.00414](https://arxiv.org/abs/2504.00414) |
| Groesseres Modell (Sonnet statt Haiku) | Besser bei FR (Trainingsdaten) | Gering (nur Config-Aenderung) | [ACL 2025](https://arxiv.org/abs/2502.01205) |
| Segmentlaenge 200-300 Woerter | Optimal laut Studie; wir senden ganze Seiten — bereits gut | Keiner | [ACL 2025](https://arxiv.org/abs/2502.01205) |

**Risiko:** 66% unseres Korpus ist Franzoesisch. Studie zeigt, dass LLM-Korrektur bei nicht-englischen Texten oft negativ wirkt — bestaetigt unsere Beobachtung (Phase 2/4: leichte Verschlechterung).

---

## Post-Processing (Hilfsmodul)

**Implementiert in:** `scripts/postprocess/` — wird nicht automatisch in der Pipeline ausgefuehrt, sondern bei Bedarf manuell.

| Funktion | Zweck | Beispiel |
|----------|-------|----------|
| `normalize_text()` | Typografische Varianten vereinheitlichen | `\u201e` -> `"` |
| `dehyphenate()` | Silbentrennung aufloesen | `Wis- senschaft` -> `Wissenschaft` |
| `clean_markdown()` | Markdown-Syntax entfernen | `## Titel` -> `Titel` |

**Wichtig (R6):** Markdown-Formatierung (`**bold**`, `*italic*`) muss fuer den Export ERHALTEN bleiben. PAGE-XML speichert Text as-is in `<TextEquiv><Unicode>`, TEI-Transformation konvertiert zu `<hi rendition>`. Deshalb wird `clean_markdown()` im Produktionspfad **nicht** aufgerufen — nur `normalize_text()` und `dehyphenate()` sind sicher.

---

## Stufe 3: Evaluation

**Skript:** `scripts/evaluate_ocr.py`

| Aspekt | Details |
|--------|---------|
| Input | OCR-Markdown + Referenz-TEI (`data/referenz-tei/*.xml`) |
| Metriken | CER (Character Error Rate), WER (Word Error Rate) |
| Alignment | Global (kurze Docs) oder seitenweise (Monografien) |
| Output | JSON (`output/evaluation/evaluation_results.json`) + HTML-Report |

Vergleicht OCR-Output zeichenweise mit manuell erstelltem Referenz-TEI. Nutzt `rapidfuzz` fuer Levenshtein-Distanz.

### Zwei Vergleichsmodi

| Modus | Bedingung | Verfahren |
|-------|-----------|-----------|
| Global | ≤10 TEI-Seiten | Gesamttext-Alignment (Phrasen-Suche) |
| Seitenweise | >10 TEI-Seiten | Pro-Seite-Vergleich via `<pb facs>` Tags |

**Auto-Erkennung:** Das Skript waehlt den Modus automatisch anhand der TEI-Seitenanzahl. CLI-Flags `--pagewise` / `--no-pagewise` ueberschreiben.

**Seitenweiser Vergleich (fuer Monografien):**
1. TEI wird anhand `<pb facs="#facs_N">` Tags in Einzelseiten zerlegt
2. Content-basiertes Matching ordnet jede TEI-Seite der passenden OCR-Datei zu (Wort-Ueberlappung mit Sliding Window)
3. CER/WER wird pro Seite berechnet, dann zeichengewichtet gemittelt

**Warum kein fixer Offset:** Bibliotheks-PDFs enthalten Deckblaetter, Leerseiten und Illustrationen, die nicht in der TEI vorkommen. Der Versatz zwischen TEI-Seitennummern und OCR-Dateinummern ist nicht konstant (z.B. Doc 1520: Offset +8, driftet auf +9). Content-Matching loest das automatisch.

---

## Stufe 4: Dashboard

**Skript:** `scripts/generate_dashboard_data.py`

Aggregiert alle Pipeline-Outputs (Seitenbilder, Evaluationsergebnisse, LLM-Manifest) zu `docs/data/dashboard.json`. Prueft pro Dokument die Existenz jeder Pipeline-Stufe und berechnet Durchschnittswerte pro Phase.

---

## PAGE-XML-Export (Phase 1)

**Skripte:** `scripts/layout/page_xml_generator.py`, `scripts/layout/mets_generator.py`

PAGE-XML ist das Zwischenformat fuer die Layout-Regionen + OCR-Text. Es dient als Input fuer die TEI-Transformation (Phase 3) und als optionaler Export fuer Transkribus-kompatible Tools.

| Aspekt | Details |
|--------|---------|
| Schema | PAGE-XML 2019-07-15 |
| Namespace | `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15` |
| Layout-Engine | Docling 2.75 (E19/E20) |

### Exportstruktur pro Dokument

```
output/page_xml/{doc_id}/
  mets.xml                    # METS-Manifest
  images/{doc_id}_p001.png    # Seitenbilder
  page/{doc_id}_p001.xml      # PAGE-XML pro Seite
```

Details: Siehe [PLAN.md](../PLAN.md) Phase 1.

---

## CLI-Befehle

```bash
# Seitenbilder extrahieren (fuer Viewer)
python scripts/extract_pages.py                              # alle PDFs, 150 DPI
python scripts/extract_pages.py --pdf 2310.pdf --dpi 300     # einzelnes PDF

# OCR (Stufe 1)
python scripts/ocr_pipeline.py -i data/scans/2310.pdf -e mistral
python scripts/ocr_pipeline.py --all --engine auto

# LLM-Nachkorrektur (Stufe 2, braucht ANTHROPIC_API_KEY)
python -m scripts.llm_postprocess --phase phase1 --variant C
python -m scripts.llm_postprocess --all

# Evaluation (Stufe 3)
python scripts/evaluate_ocr.py --all
python scripts/evaluate_ocr.py --phase phase1 --engine mistral

# Layout-Analyse (Stufe 3, braucht GPU fuer Docling)
python -m scripts.run_layout_analysis                      # alle Dokumente
python -m scripts.run_layout_analysis --doc 2310           # einzelnes Dokument
python -m scripts.run_layout_analysis --overlay            # Overlay-PNGs erzeugen (ohne GPU)
python -m scripts.run_layout_analysis --overlay --doc 2310 # Overlay fuer ein Dokument

# Dashboard-Daten (Stufe 4)
python -m scripts.generate_dashboard_data

# Post-Processing (manuell, bei Bedarf)
python -m scripts.postprocess.pipeline
```

---

## Dashboard & QA-UI

**Verzeichnis:** `docs/`

| Datei | Zweck |
|-------|-------|
| `docs/index.html` | Dashboard: Metriken, Dokumentkatalog, Qualitaetsvergleich |
| `docs/viewer.html` | Dokumentansicht: Faksimile + OCR-Text, Source-Toggle |
| `docs/shared.css` | Unified Design System (CSS Custom Properties) |
| `docs/shared.js` | Shared Utilities (Data Loading, Formatting, DOM Helpers) |
| `docs/data/dashboard.json` | Generierte Datenbasis (aus `scripts/generate_dashboard_data.py`) |

Das Dashboard zeigt Pipeline-Status, CER-Vergleich (Mistral/LLM/DeepSeek), Engine-Verfuegbarkeit und filterbaren Dokumentkatalog. Daten werden statisch aus Pipeline-Outputs generiert.

---

## Referenzen

- [PROJEKT](PROJEKT.md) fuer Oekosystem und Meilensteine
- [OCR-ENGINES](OCR-ENGINES.md) fuer Engine-Details
- [TESTPLAN](TESTPLAN.md) fuer Testergebnisse
- [INFRASTRUKTUR](INFRASTRUKTUR.md) fuer Deployment

---

*Erstellt: 2026-01-29 | Umbenannt von ARCHITEKTUR.md: 2026-02-25*
