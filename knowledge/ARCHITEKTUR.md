---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, architektur, pipeline, workflow]
status: active
---

# Architektur

Technische Pipeline-Architektur: PDF zu korrigiertem Markdown. TEI-Transformation findet downstream in coOCR/teiCrafter statt.

**Abhängigkeiten:** [PROJEKT](PROJEKT.md)

---

## Pipeline-Übersicht

```
PDF --> Docling (Layout) --> OCR Engine --> LLM-Korrektur --> Post-Processing --> Export (PAGE-XML + PNG)
        output/layout/       output/ocr_results/  output/llm_corrected/  output/clean/   output/export/
                                                                                              |
                                                                                              v
                                                                                     coOCR/HTR (Korrektur)
                                                                                              |
                                                                                              v
                                                                                     teiCrafter (TEI + GND)
```

### 5 Stufen (in diesem Repo)

| Stufe | Aufgabe | Tool | Output |
|-------|---------|------|--------|
| 1 | Layout-Analyse | Docling (do_ocr=False) | JSON mit BBox-Koordinaten |
| 2 | OCR | DeepSeek / Mistral / Gemini | Seitenweises Markdown |
| 2.5 | LLM-Nachkorrektur | Claude Haiku 4.5 | Korrigiertes Markdown |
| 3 | Post-Processing | `scripts/postprocess/` | Bereinigtes Markdown |
| 4 | Export fuer coOCR | `scripts/export_page_xml.py` (geplant) | PAGE-XML + PNG + METS |

**TEI-Transformation und GND-Verknuepfung sind nicht Scope dieses Repos.** Sie finden in coOCR/HTR und teiCrafter statt.

---

## Stufe 1: Layout-Analyse (Docling)

**Integriert in:** `scripts/ocr_pipeline.py` (Layout-Erkennung als Teil der Pipeline)

| Aspekt | Details |
|--------|---------|
| Tool | Docling (IBM) |
| Modus | `do_ocr=False` |
| Output | JSON mit BBox-Koordinaten pro Region |
| Erkennt | Spalten, Header, Text, Listen, Tabellen |

Validiert: 2530.pdf — zweispaltig erkannt, 14 Regionen pro Seite.

**Wichtig:** Docling OCR nicht nutzen (RapidOCR hat Encoding-Probleme). Details: [OCR-ENGINES](OCR-ENGINES.md) §Docling.

---

## Stufe 2: OCR

**Skript:** `scripts/ocr_pipeline.py`

### Engine-Auswahl nach Dokumenttyp

Dokumenttypen: Siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Dokumenttypen.

| Typ | Pipeline | Engine |
|-----|----------|--------|
| A (einspaltig) | OCR direkt | DeepSeek / Mistral |
| B (zweispaltig) | Layout + OCR pro Region, oder Agentic Vision | Docling + DeepSeek, oder Gemini |
| C (Monografie) | OCR + Chunking | DeepSeek / Mistral |
| D (Spezial) | Fallweise | Gemini Agentic Vision |

Engine-Details: Siehe [OCR-ENGINES](OCR-ENGINES.md).

### OCR-Qualität (gemessen)

Vollständige Ergebnisse: Siehe [TESTPLAN](TESTPLAN.md) §Ergebnisse.

| Dokument | Typ | CER | Genauigkeit |
|----------|-----|-----|-------------|
| 2310 | A | 2.67% | 97.33% |
| 1180 | A | 4.89% | 95.11% |
| 290 | A | 9.21% | 90.79% |

---

## Stufe 2.5: LLM-Nachkorrektur (optional)

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

## Stufe 3: Post-Processing

**Implementiert in:** `scripts/postprocess/`

| Schritt | Funktion | Beispiel |
|---------|----------|----------|
| 1. Markdown entfernen | `clean_markdown()` | `## Titel` -> `Titel` |
| 2. Zeichen normalisieren | `normalize_text()` | typografische Varianten vereinheitlichen |
| 3. Silbentrennung | `dehyphenate()` | `Wis- senschaft` -> `Wissenschaft` |
| 4. Whitespace | (inline) | Mehrfache Leerzeilen -> eine |

**Geloest (R6):** Markdown-Formatierung (`**bold**`, `*italic*`) muss ERHALTEN bleiben. coOCR speichert Text as-is in `<TextEquiv><Unicode>` — Formatierungsinformation geht sonst verloren. Post-Processing darf Markdown-Markup nicht entfernen.

---

## Stufe 4: Export fuer coOCR/HTR (geplant)

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
# OCR Pipeline (GPU erforderlich)
python scripts/ocr_pipeline.py --input data/scans/2310.pdf
python scripts/ocr_pipeline.py --all --engine auto

# LLM-Nachkorrektur (braucht ANTHROPIC_API_KEY in .env)
python -m scripts.llm_postprocess --phase phase1
python -m scripts.llm_postprocess --all

# Post-Processing (ohne GPU)
python -m scripts.postprocess.pipeline

# Evaluation
python scripts/evaluate_ocr.py --all

# Dashboard-Daten generieren (ohne GPU)
python -m scripts.generate_dashboard_data
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

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
