# Projektwissen: ZBZ-OCR-TEI

Kompaktes Wissensdokument, synthetisiert aus allen 12 Knowledge-Docs. Stand: 20.02.2026.

---

## 1. Was ist das Projekt?

LLM-gestuetzte OCR-Pipeline fuer 289 Jeanne-Hersch-Texte (7.200 Seiten) der Zentralbibliothek Zuerich. Auftrag bestaetigt (14.02.2026), Team: Christopher (DHCraft), Elias + Anouschka (ZBZ).

### Oekosystem — Drei Tools

```
zbz-ocr-tei (Batch-OCR)  -->  coOCR/HTR (Experte korrigiert)  -->  teiCrafter (TEI + GND)
   Python, CLI                  Browser-App                         Browser-App
   289 PDFs automatisch         Einzeldokument, Editor-in-Loop      LLM-Annotation + Review
   Output: PAGE-XML + PNG       Output: Basis-TEI (<ab>, <lb/>)     Output: Produktions-TEI
```

**Dieses Repo (zbz-ocr-tei):** Nur OCR — PDF zu korrigiertem Markdown, dann Export als PAGE-XML fuer coOCR. Keine TEI-Transformation hier (E12).

---

## 2. Pipeline (5 Stufen)

```
PDF --> Docling (Layout) --> Mistral OCR --> LLM-Korrektur --> Post-Processing --> Export (PAGE-XML)
        Stufe 1               Stufe 2        Stufe 2.5         Stufe 3            Stufe 4
```

| Stufe | Tool | Output | Status |
|-------|------|--------|--------|
| 1 | Docling (do_ocr=False) | JSON BBox-Koordinaten | Implementiert |
| 2 | Mistral Document AI 2512 (Azure) | Seitenweises Markdown | Implementiert |
| 2.5 | Claude Haiku 4.5 (Anthropic) | Korrigiertes Markdown | Implementiert |
| 3 | `scripts/postprocess/` | Bereinigtes Markdown | Implementiert |
| 4 | `scripts/export_page_xml.py` | PAGE-XML + PNG + METS | **Geplant** |

---

## 3. Quellmaterial

| Aspekt | Wert |
|--------|------|
| Korpus | 289 Texte, 7.200 Seiten, 1931-2010 |
| Sprachen | 66% FR, 30% DE, 2% EN, 1% IT |
| Median | 6 Seiten/Text |
| Maximum | 588 Seiten |
| Gattungen | 49% Zeitschriftenartikel, 39% Sammelband, 12% Monografien |

### 4 Dokumenttypen

| Typ | Layout | Pipeline | Anzahl |
|-----|--------|----------|--------|
| A | Einspaltig | OCR direkt | Mehrheit |
| B | Zweispaltig | Layout + OCR pro Region / Gemini Agentic Vision | ~10 |
| C | Monografie | OCR + Chunking | 38 |
| D | Spezial | Fallweise | ~20 |

---

## 4. OCR-Engines

| Engine | Zugang | Einsatz | CER | Status |
|--------|--------|---------|-----|--------|
| **Mistral Doc AI 2512** | Azure AI Foundry | Produktion (alle Typen) | 5.87% (Phase 1-3) | Implementiert |
| DeepSeek-OCR-2 | Lokal (GPU 8GB+) | Entwicklung | 94-97% (Phase 1) | Implementiert |
| Gemini 3 Flash | Google API | Typ B/D (Agentic Vision) | Ungetestet | Geplant |
| Claude Haiku 4.5 | Anthropic API | LLM-Nachkorrektur | 5.55% (nach Korrektur) | Implementiert |
| Docling | Lokal (CPU) | Nur Layout-Analyse | - | Implementiert |

**Wichtig:** Docling OCR nicht nutzen (RapidOCR hat Encoding-Fehler bei frz. Text).

---

## 5. OCR-Qualitaet (gemessen)

### Mistral Document AI — Phase 1-3 (10 Docs)

| Phase | Typ | Avg CER | Genauigkeit |
|-------|-----|---------|-------------|
| Phase 1 | A (einspaltig) | 9.40% | 90.60% |
| Phase 2 | B (zweispaltig) | 6.31% | 93.69% |
| Phase 3 | D (Spezial) | 2.88% | 97.12% |
| **Gesamt** | **10 Docs** | **5.87%** | **94.14%** |

### Nach LLM-Korrektur (Haiku 4.5, Variante C)

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| **Gesamt** | **5.87%** | **5.55%** | **-0.32** |

Drei Prompt-Varianten getestet: A (5.47%), B (5.59%), **C (5.55%, Default)**.

### Einzelergebnisse

| Doc | Typ | Mistral CER | LLM CER | Anmerkung |
|-----|-----|-------------|---------|-----------|
| 2310 | A | 7.00% | 3.93% | Staerkste Verbesserung |
| 1180 | A | 3.12% | 3.17% | Bereits sehr gut |
| **290** | **A** | **18.07%** | **18.20%** | **Problematisch (Scan?)** |
| 2530 | B | 3.96% | 3.98% | Zweispaltig, gut |
| 890 | B | 5.96% | 6.05% | Lehrerzeitung |
| 3040 | B | 9.02% | 8.97% | Lexikon |
| 90 | D | 1.21% | 1.10% | Exzellent (hist. 1944) |
| 1440 | D | 3.71% | 3.71% | Interview |
| 830 | D | 4.00% | 3.29% | Bildband |
| 1330 | D | 2.60% | 2.78% | Sammelband |

---

## 6. Schnittstelle zu coOCR (E13, geloest)

coOCR/HTR erwartet **PAGE-XML (Schema 2019-07-15) + PNG + METS-XML**.

### Exportformat

```
output/export/{doc_id}/
  mets.xml                    # Multi-Page-Manifest
  images/{doc_id}_p001.png    # Seitenbilder (zero-padded)
  page/{doc_id}_p001.xml      # PAGE-XML pro Seite
```

### PAGE-XML

```xml
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15">
  <Page imageFilename="../images/{doc_id}_p001.png" imageWidth="..." imageHeight="...">
    <TextRegion id="r1">
      <TextLine id="r1_l1">
        <TextEquiv conf="0.95">
          <Unicode>OCR-Text</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
```

**Confidence:** Mistral-roh=0.85, LLM-korrigiert=0.95.
**Markdown-Formatierung bleibt erhalten** (E14/R6) — coOCR speichert Text as-is.

---

## 7. Infrastruktur

| Aspekt | Details |
|--------|---------|
| OCR-API | Azure AI Foundry (Mistral), Anthropic (Haiku 4.5) |
| Versionskontrolle | GitHub (DHCraft), Fork auf GitLab Uni Zuerich |
| Container | Podman (OCI-kompatibel, kein Docker) |
| CI/CD | GitLab CI (noch nicht eingerichtet) |
| Lokale Entwicklung | Python 3.11+, optional CUDA 12.4+ fuer DeepSeek |

---

## 8. Kosten

| Posten | Betrag |
|--------|--------|
| Mistral OCR (Azure, 289 Docs) | 6-15 USD |
| LLM-Korrektur (Haiku 4.5, 289 Docs) | ~48 USD |
| GPU-Cloud (optional) | ~10-20 USD |
| **Gesamt** | **~65-85 USD** |

---

## 9. Meilensteine

| # | Meilenstein | Status |
|---|-------------|--------|
| M0 | Bildextraktion + QS-Viewer | **Erledigt** |
| M1 | OCR validiert (>=95% Genauigkeit) | **Phase 1-3: 94.14% + LLM 94.45%** |
| M2 | Produktions-OCR alle 289 Docs | Ausstehend |
| M3 | Integration mit coOCR/HTR (Export) | Format definiert, Code ausstehend |
| M4 | Pilotbetrieb | Ausstehend |

---

## 10. Entscheidungen (E1-E14)

| # | Entscheidung | Datum |
|---|-------------|-------|
| E1 | Hybrid-Pipeline: Docling (Layout) + LLM-OCR (Text) | 29.01. |
| E2 | Docling nur fuer Layout, nicht fuer OCR | 29.01. |
| E3 | Deterministisch first, LLM nur fuer Komplexes | 29.01. |
| E4 | 4 Dokumenttypen (A-D) klassifiziert | 29.01. |
| E5 | Nachgelagerte GND-Verknuepfung | 29.01. |
| E6 | Mistral OCR 3 als Produktions-Engine | 14.02. |
| E7 | Offerte bleibt unveraendert | 14.02. |
| E8 | Konfigurierbare API-Endpoints | 14.02. |
| E9 | Containerisierung mit Podman | 14.02. |
| E10 | Fork auf GitLab Uni Zuerich | 14.02. |
| E11 | Dreistufiges Oekosystem | 18.02. |
| E12 | zbz-ocr-tei nur OCR, keine TEI | 19.02. |
| E13 | Export als PAGE-XML + METS fuer coOCR | 20.02. |
| E14 | Markdown-Formatierung erhalten (R6) | 20.02. |

---

## 11. Offene Fragen

### Hoch (blockierend)

| # | Frage | Klaerung |
|---|-------|----------|
| O2 | Alignment-Call Termin? | ZBZ |
| O3 | Fork-Modell und Merge-Strategie? | ZBZ (Meeting) |
| O5 | Schnittstelle coOCR -> teiCrafter: `<ab>` vs. `<p>`? | Eigene Entscheidung |

### Mittel

| # | Frage |
|---|-------|
| O10 | Spalten-Problem Typ B: Docling+Crop, Gemini Agentic Vision, oder Prompt-Tuning? |

### Erledigt

O1 (Azure-Key), O4 (coOCR-Format=PAGE-XML), O6-O9, O11-O14 (nach coOCR/teiCrafter verschoben, E12)

---

## 12. Risiken

| # | Risiko | Status |
|---|--------|--------|
| R1 | Spalten-Problem unloesbar | Offen (O10) |
| R4 | Azure-API-Kompatibilitaet | **Geloest** |
| R5 | Fork-Divergenz DHCraft/ZBZ | Wartet auf Meeting (O3) |
| R6 | Post-Processing entfernt Formatierung | **Geloest** (E14) |

---

## 13. TEI-Regeln (Referenz, in coOCR/teiCrafter)

- DTA-Basisformat mit ZBZ-Anpassungen
- Jede Entitaet wird mit GND verlinkt (auch bei Wiederholung)
- Vorlagengetreue Transkription
- Spezialtypen: Rezension, Interview, Lexikonartikel, Sammelband
- GND-Seed: 75 Entitaeten aus Referenz-TEI extrahiert (Top: Karl Jaspers 90x)

---

## 14. ZBZ-Workflow

Bestehend (manuell): Digitalisat -> Transkribus -> GitLab -> Oxygen -> Korrekturschleife.
Automatisiert (DHCraft): zbz-ocr-tei ersetzt Transkribus-OCR, coOCR ersetzt Oxygen-Korrektur, teiCrafter ersetzt manuelle GND.

---

## 15. Scripts (implementiert)

| Script | Zweck |
|--------|-------|
| `scripts/ocr_pipeline.py` | OCR mit Mistral/DeepSeek |
| `scripts/llm_postprocess.py` | LLM-Nachkorrektur (Haiku 4.5) |
| `scripts/evaluate_ocr.py` | CER/WER-Evaluation |
| `scripts/extract_layout.py` | Docling Layout-Analyse |
| `scripts/extract_pages.py` | PDF zu PNG |
| `scripts/extract_gnd.py` | GND-Seed aus Referenz-TEI |
| `scripts/config.py` | Zentrale Konfiguration |
| `scripts/utils.py` | Shared Utilities |
| `scripts/postprocess/` | Deterministisches Post-Processing |

---

## 16. Naechste Schritte

1. **M2 Produktion**: Batch-Orchestrierung (`scripts/run_pipeline.py`) fuer 289 Docs
2. **M3 Export**: PAGE-XML-Konverter (`scripts/export_page_xml.py`) fuer coOCR
3. **Post-Processing Fix**: Markdown-Markup erhalten (R6/E14)
4. **Doc 290 analysieren**: CER 18% — Scan- oder OCR-Problem?
5. **Gemini Typ B testen**: Agentic Vision fuer Spalten (O10)
6. **Alignment-Call ZBZ**: Fork-Modell, Merge-Strategie (O2, O3)

---

*Synthetisiert aus 12 Knowledge-Docs am 20.02.2026. Fuer Details: siehe [knowledge/INDEX.md](knowledge/INDEX.md)*
