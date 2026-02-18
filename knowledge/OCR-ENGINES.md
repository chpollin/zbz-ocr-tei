---
type: knowledge
created: 2026-01-29
updated: 2026-02-18
tags: [zbz-ocr-tei, ocr, deepseek, mistral, gemini, docling]
status: active
---

# OCR-Engines

Alle OCR-Tools und ihre Rollen in der Pipeline. Docling wird nur für Layout-Analyse eingesetzt.

**Abhängigkeiten:** [ARCHITEKTUR](ARCHITEKTUR.md)

---

## Übersicht

| Engine | Zugang | Parameter | Einsatz | Status |
|--------|--------|-----------|---------|--------|
| DeepSeek-OCR-2 | Lokal (GPU) | 3B VLM | Entwicklung, Typ A | Validiert |
| Mistral OCR 3 | Azure | - | Produktionsbetrieb ZBZ | API-Key ausstehend |
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

## Mistral OCR 3

| Aspekt | Details |
|--------|---------|
| Provider | Azure AI Services |
| Modell | mistral-ocr-latest |
| Einsatz | Primäre Produktions-Engine (ZBZ hat Azure-Zugang) |
| Vorteil | Kein GPU nötig, serverbasiert, skalierbar |
| Status | API verfügbar, Key wird von ZBZ bereitgestellt |

### Noch zu tun

- [ ] API-Key erhalten (-> [DECISIONS](DECISIONS.md) O1)
- [ ] Azure-Endpoint testen
- [ ] Qualitätsvergleich gegen DeepSeek auf Phase-1-Daten
- [ ] Engine-Klasse `MistralOCR` in `ocr_pipeline.py` implementieren

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
| A (einspaltig) | DeepSeek-OCR-2 / Mistral (lokal/kostenlos bzw. Azure) |
| B (zweispaltig) | Gemini 3 Agentic Vision |
| C (Monografie) | DeepSeek / Mistral + Chunking |
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
| Genauigkeit | 94-97% | Ungetestet | Ungetestet | Nur Layout |
| GPU nötig | Ja (8GB+) | Nein (API) | Nein (API) | Nein (CPU) |
| Kosten | Kostenlos | Azure-Abo | ~$27/Projekt | Kostenlos |
| Spalten | Nein | Ungetestet | Ja (Agentic) | Ja (Layout) |
| Geschwindigkeit | ~1.6s/Seite | Ungetestet | Ungetestet | ~3s/Seite |
| Offline | Ja | Nein | Nein | Ja |

---

## Referenzen

- [ARCHITEKTUR](ARCHITEKTUR.md) für Pipeline-Integration
- [TESTPLAN](TESTPLAN.md) für Qualitätsmessungen
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Azure-Konfiguration
- [DECISIONS](DECISIONS.md) O1 (Azure-Key), O10 (Spalten-Lösung)

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-18*
