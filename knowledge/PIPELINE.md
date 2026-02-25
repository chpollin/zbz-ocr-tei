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

**Ergebnis Pilot (Phase 1-3, 10 Docs, Variante C):**

| Phase | Mistral CER | LLM CER | Verbesserung |
|-------|-------------|---------|--------------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| **Gesamt** | **5.87%** | **5.55%** | **-0.32 (5.5% relativ)** |

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
| Alignment | Intelligente Phrasen-Suche fuer Teil-Texte |
| Output | JSON (`output/evaluation/evaluation_results.json`) + HTML-Report |

Vergleicht OCR-Output zeichenweise mit manuell erstelltem Referenz-TEI. Nutzt `rapidfuzz` fuer Levenshtein-Distanz.

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
