---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, pipeline, datenfluss, ocr]
status: active
---

# Pipeline

Datenfluss von PDF zu korrigiertem Markdown: Stufen, Scripts, Formate. TEI-Transformation findet downstream in coOCR/teiCrafter statt.

**Abhängigkeiten:** [PROJEKT](PROJEKT.md)

---

## Pipeline-Übersicht

```
PDF ──→ OCR Engine ──→ LLM-Korrektur ──→ Evaluation ──→ Dashboard
         ocr_pipeline    llm_postprocess    evaluate_ocr    generate_dashboard_data
         output/          output/             output/          docs/data/
         mistral_results/ llm_corrected_c/    evaluation/      dashboard.json
                                                    │
                              ┌──────────────────────┘
                              ▼
                    Export fuer coOCR (geplant)
                              │
                              ▼
                    coOCR/HTR (Korrektur) ──→ teiCrafter (TEI + GND)
```

### Stufen (in diesem Repo)

| Stufe | Aufgabe | Script | Output |
|-------|---------|--------|--------|
| 1 | OCR | `scripts/ocr_pipeline.py` | Seitenweises Markdown (`output/mistral_results/`) |
| 1a | Layout (nur Typ B) | Docling in `ocr_pipeline.py` | BBox-Koordinaten (intern) |
| 2 | LLM-Nachkorrektur | `scripts/llm_postprocess.py` | Korrigiertes Markdown (`output/llm_corrected_c/`) |
| 3 | Evaluation | `scripts/evaluate_ocr.py` | CER/WER-Report (`output/evaluation/`) |
| 4 | Dashboard | `scripts/generate_dashboard_data.py` | `docs/data/dashboard.json` |
| 5 | Export fuer coOCR | `scripts/export_page_xml.py` (geplant) | PAGE-XML + PNG + METS |

**Hilfsskripte:** `extract_pages.py` (Seitenbilder), `extract_gnd.py` (GND-IDs), `postprocess/` (Normalisierung).

**TEI-Transformation und GND-Verknuepfung sind nicht Scope dieses Repos.** Sie finden in coOCR/HTR und teiCrafter statt.

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

**Wichtig (R6):** Markdown-Formatierung (`**bold**`, `*italic*`) muss fuer den Export ERHALTEN bleiben. coOCR speichert Text as-is in `<TextEquiv><Unicode>`. Deshalb wird `clean_markdown()` im Produktionspfad **nicht** aufgerufen — nur `normalize_text()` und `dehyphenate()` sind sicher.

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

## Stufe 5: Export fuer coOCR/HTR (geplant)

**Skript:** `scripts/export_page_xml.py` (noch nicht implementiert)

coOCR/HTR ([DHCraft/co-ocr-htr](https://github.com/DHCraft/co-ocr-htr)) ist eine browserbasierte Korrektur-Plattform. Sie erwartet:

| Aspekt | Details |
|--------|---------|
| Bildformat | PNG / JPEG / TIFF (eine Datei pro Seite) |
| Textformat | PAGE-XML (Schema 2019-07-15) |
| Manifest | METS-XML fuer Multi-Page-Dokumente |
| Namespace | `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15` |

### Exportstruktur pro Dokument

```
output/export/{doc_id}/
  mets.xml                    # METS-Manifest (verknuepft Bilder + PAGE-XML)
  images/{doc_id}_p001.png    # Seitenbilder (zero-padded)
  page/{doc_id}_p001.xml      # PAGE-XML pro Seite
```

### PAGE-XML Struktur

```xml
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageFilename="../images/{doc_id}_p001.png" imageWidth="..." imageHeight="...">
    <TextRegion id="r1">
      <TextLine id="r1_l1">
        <TextEquiv conf="0.95">
          <Unicode>Korrigierter OCR-Text dieser Zeile</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
```

### Confidence-Mapping

| Quelle | Confidence |
|--------|-----------|
| Mistral OCR (roh) | 0.85 |
| LLM-korrigiert (Haiku 4.5) | 0.95 |

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
