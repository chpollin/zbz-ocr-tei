---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, ocr, deepseek, mistral, gemini, docling]
status: active
---

# OCR-Engines

Alle OCR-Tools und ihre Rollen in der Pipeline. Docling wird nur für Layout-Analyse eingesetzt.

**Abhängigkeiten:** [PIPELINE](PIPELINE.md)

---

## Übersicht

| Engine | Zugang | Parameter | Einsatz | Status |
|--------|--------|-----------|---------|--------|
| DeepSeek-OCR-2 | Lokal (GPU) | 3B VLM | Entwicklung, Typ A | Validiert |
| Mistral Document AI | Azure AI Foundry | mistral-document-ai-2512 | Produktionsbetrieb ZBZ | API-Key vorhanden |
| Gemini 3 Flash | Google API | - | Typ B/D (Agentic Vision), NER | Nicht getestet |
| Claude | Anthropic/Azure | - | Komplexe Strukturen, QS | Nicht getestet |
| Docling | Lokal (CPU) | IBM Research | Nur Layout-Analyse | Validiert |

---

## DeepSeek-OCR-2

| Aspekt | Details |
|--------|---------|
| Modell | deepseek-ai/DeepSeek-OCR-2 (3B VLM) |
| Hardware | GPU mit 8+ GB VRAM, CUDA 12.4+ |
| Genauigkeit | 94-97% (validiert auf Typ A) |
| Geschwindigkeit | ~1.6 Sekunden/Seite (RTX 3070) |
| Einsatz | Entwicklung, Typ A (einspaltig), Typ C (Monografien) |

### Prompt

```
<image>\n<|grounding|>Convert the document to markdown.
```

### Bekannte Probleme

| Problem | Workaround |
|---------|------------|
| Hohe GPU-Last (PC friert ein) | Tests einzeln oder auf Cloud-VM |
| Spaltenreihenfolge bei Typ B falsch | Layout-Vorverarbeitung oder Gemini nutzen |
| safetensors erforderlich | `use_safetensors=True` beim Laden |

---

## Mistral Document AI (Azure)

| Aspekt | Details |
|--------|---------|
| Provider | Azure AI Foundry (Serverless API, Pay-as-you-go) |
| Modell | `mistral-document-ai-2512` (Preview, basiert auf mistral-ocr-2512) |
| Alte Version | `mistral-document-ai-2505` (verfuegbar, aber ueberholt) |
| Eingestellt | `mistral-ocr-2503` (seit 30.01.2026 nicht mehr deploybar) |
| Endpoint | `/v1/ocr` mit Base64-kodierten Dokumenten |
| Output | Seitenweises Markdown mit Bild-Referenzen und Dimensionen |
| Einsatz | Primaere Produktions-Engine (ZBZ hat Azure-Zugang) |
| Status | API-Key vorhanden, Engine implementiert |

### Modellversionen

| Modell | Status | Hinweis |
|--------|--------|---------|
| `mistral-document-ai-2512` | Verfuegbar (Preview) | Aktuell, +74% bei Scans/Tabellen/Handschrift |
| `mistral-document-ai-2505` | Verfuegbar | Erste Document AI Version |
| `mistral-ocr-2503` | Eingestellt (30.01.2026) | Nicht mehr deploybar |

### Limits

| Parameter | Wert |
|-----------|------|
| Max. Dateigroesse | 30 MB |
| Max. Seiten (OCR) | 30 pro Request |
| Max. Seiten (Annotations) | 8 pro Request |
| Eingabe | PDF, PNG, JPEG, TIFF, GIF, WEBP, PPTX, DOCX, TXT, EPUB |
| Ausgabe | Markdown (Tabellen optional als HTML) |
| Sprachen | 36 (de, fr, en, es, it, nl, pt, hu, pl, cs, zh, ja, ko, ar, ...) |

### Einrichtung auf Azure

1. **Azure AI Foundry Ressource** erstellen im Azure Portal (portal.azure.com)
2. **Modell deployen**: Im Foundry Portal (ai.azure.com) unter Model Catalog nach `mistral-document-ai-2512` suchen, als Serverless Endpoint deployen
3. **Credentials abrufen**: Unter Meine Ressourcen > Modelle und Endpunkte — Endpoint URL und API Key kopieren

**Konfiguration im Projekt:** Werte in `.env` eintragen (siehe `.env.example`):
```bash
MISTRAL_DOC_AI_ENDPOINT="https://<deployment>.<region>.models.ai.azure.com"
MISTRAL_DOC_AI_KEY="<api-key>"
```

**Unterstuetzte Regionen:** East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central.

### API-Details

**Endpoint:** `POST {endpoint}/v1/ocr` mit Bearer-Token-Authentifizierung.

**Eingabe:** Dokumente als Base64 im Feld `document.document_url` (Format: `data:application/pdf;base64,...`). Direkte URLs werden auf Azure nicht unterstuetzt.

**Antwortstruktur:** JSON mit `pages[]`, jede Seite hat:
- `index` — Seitennummer (0-basiert)
- `markdown` — extrahierter Text
- `images[]` — Bounding Boxes (und optional Base64 mit `include_image_base64: true`)
- `dimensions` — DPI, Hoehe, Breite

**Grosse Dokumente (>30 Seiten):** Pipeline splittet automatisch mit PyMuPDF (`MistralOCR._split_pdf()`).

### Annotations (strukturierte Extraktion)

Zusaetzlich zum OCR kann das Modell Inhalte direkt in ein JSON-Schema extrahieren:
- **`bbox_annotation`**: Beschriftet erkannte Bildbereiche (z.B. Diagramme)
- **`document_annotation`**: Extrahiert Gesamtdokument in definiertes JSON-Format

Annotations sind auf 8 Seiten begrenzt. Relevant fuer: Metadaten-Extraktion, TEI-Header-Generierung.

### Fehlerbehandlung

| Problem | Loesung |
|---------|---------|
| 404 nach Deployment | `/v1/ocr` an Endpoint-URL anhaengen |
| 413 / Datei zu gross | PDF komprimieren oder splitten (max 30 MB) |
| Timeout bei Annotations | Timeout auf min. 120s setzen |
| Base64-Fehler | Keine Zeilenumbrueche im Base64-String |

### Alternative Zugangswege

| Zugang | Modell | Vorteil |
|--------|--------|---------|
| Azure AI Foundry | `mistral-document-ai-2512` | Data Residency, Enterprise-Governance |
| Mistral API direkt (console.mistral.ai) | `mistral-ocr-latest` | Einfachstes Setup, kein Azure noetig |
| Google Vertex AI | `mistral-ocr-2512` | Google Cloud Infrastruktur |

### Benchmark- und CER/WER-Ergebnisse

Alle Evaluationsdaten (CER, WER, Einzeldokument-Ergebnisse) sind in [TESTPLAN](TESTPLAN.md) §Ergebnisse konsolidiert.

Interaktiver Engine-Vergleich im Dashboard: `docs/index.html`

### Offen

- [ ] Doc 290 analysieren (CER 18% — Scan- oder OCR-Problem?) — niedrige Prio, blockiert nichts
- [ ] Doc 1060 analysieren (CER 22.6% — Alignment-Problem bei kurzem PDF?) — niedrige Prio

---

## Gemini 3 Flash

| Aspekt | Details |
|--------|---------|
| Modell | google/gemini-3.0-flash |
| Kosten | $0.50/1M Input, $3.00/1M Output |
| Einsatz | Typ B/D (Agentic Vision), NER, OCR-Korrektur, QS |
| Geschätzte Kosten | ~$27 für 289 Dokumente |

### Agentic Vision (seit 27.01.2026)

Think-Act-Observe Loop für aktive Bildmanipulation:

1. **Think**: Analysiert Bild, plant Schritte
2. **Act**: Generiert Python-Code (Crop, Zoom, Rotate)
3. **Observe**: Validiert eigenes Ergebnis, iteriert bei Bedarf

| Fähigkeit | Nutzen |
|-----------|--------|
| Auto-Crop Spalten | Typ B ohne Docling-Vorverarbeitung |
| Selbstvalidierung | 5-10% Qualitätsboost |
| BBox-Output | `<facsimile>` Koordinaten für TEI |
| Iteratives Zoomen | Historische Drucke, kleine Schrift |

### Empfohlene Strategie nach Dokumenttyp

Dokumenttypen: Siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Dokumenttypen.

| Typ | Engine |
|-----|--------|
| A (einspaltig) | DeepSeek-OCR-2 / Mistral Document AI (lokal/kostenlos bzw. Azure) |
| B (zweispaltig) | Gemini 3 Agentic Vision |
| C (Monografie) | DeepSeek / Mistral Document AI + Chunking |
| D (Spezial) | Gemini 3 Agentic Vision |

### Noch zu tun

- [ ] API-Key für Gemini erhalten
- [ ] Agentic Vision auf 2530.pdf (Typ B) testen
- [ ] Qualität vs. DeepSeek vergleichen
- [ ] Engine-Klasse `GeminiOCR` in `ocr_pipeline.py` implementieren

---

## Docling (nur Layout)

| Aspekt | Details |
|--------|---------|
| Herkunft | IBM Research |
| Modus | `do_ocr=False` — nur Layout-Analyse |
| Erkennt | Spalten, Header, Text, Listen, Tabellen |
| Output | JSON mit BBox-Koordinaten |
| Status | Validiert (Windows, mit Symlink-Warnung) |

### Wichtig: Docling OCR nicht nutzen

Doclings eingebaute OCR (RapidOCR) hat Encoding-Probleme bei französischem Text. Beispiel: `e` wird zu `O`. Docling wird ausschließlich für Layout-Analyse verwendet.

### Troubleshooting

| Problem | Lösung |
|---------|--------|
| Symlink-Warnung auf Windows | `HF_HUB_DISABLE_SYMLINKS_WARNING=1` — ignorierbar |
| Encoding-Fehler bei OCR | `do_ocr=False` verwenden, OCR durch DeepSeek/Mistral |
| CUDA-Konflikt mit DeepSeek | Docling auf CPU laufen lassen (Standard) |

---

## Vergleichstabelle

| Kriterium | DeepSeek | Mistral | Gemini | Docling |
|-----------|----------|---------|--------|---------|
| Genauigkeit (CER) | 94-97% (Phase 1) | 94.14% (Phase 1-3) | Ungetestet | Nur Layout |
| GPU noetig | Ja (8GB+) | Nein (API) | Nein (API) | Nein (CPU) |
| Kosten | Kostenlos | Azure-Abo | ~$27/Projekt | Kostenlos |
| Spalten (Typ B) | Nein | 93.69% Genauigkeit | Ja (Agentic) | Ja (Layout) |
| Geschwindigkeit | ~1.6s/Seite | ~1.3s/Seite | Ungetestet | ~3s/Seite |
| Offline | Ja | Nein | Nein | Ja |
| Kursiv/Formatting | Nein | Ja (*italics*) | Ungetestet | - |
| Alle Seiten | Teilweise (GPU-Limit) | Ja (Cloud) | Ungetestet | - |

---

## Referenzen

- [PIPELINE](PIPELINE.md) für Pipeline-Integration
- [TESTPLAN](TESTPLAN.md) für Qualitätsmessungen
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Azure-Konfiguration
- [DECISIONS](DECISIONS.md) O1 (Azure-Key), O10 (Spalten-Lösung)

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
