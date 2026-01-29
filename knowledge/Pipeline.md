# Pipeline

Technische Architektur für die LLM-gestützte OCR und TEI-Auszeichnung.

---

## Übersicht

Die Pipeline folgt einem zweistufigen Ansatz:

```
PDF → OCR (Markdown) → LLM (TEI-Transformation) → Validierung → [GND-Verknüpfung]
```

### Designentscheidungen

| Entscheidung | Gewählt | Begründung |
|--------------|---------|------------|
| OCR-Output | Markdown | Strukturerhalt, LLM-freundlich |
| Architektur | Zweistufig | Separation of Concerns, bessere Fehleranalyse |
| GND-Verknüpfung | Nachgelagert | Reduktion von Halluzinationen |

---

## Stufe 1: OCR

### Primäre Option: DeepSeek-OCR-2

| Aspekt | Details |
|--------|---------|
| Modell | deepseek-ai/DeepSeek-OCR-2 |
| Repository | https://github.com/deepseek-ai/DeepSeek-OCR-2 |
| Lizenz | Apache-2.0 |
| Hugging Face | deepseek-ai/DeepSeek-OCR-2 |
| Release | Januar 2026 |

**Prompts:**

```
# Mit Layout-Erhaltung
<image>\n<|grounding|>Convert the document to markdown.

# Ohne Layout (reiner Text)
<image>\nFree OCR.
```

**Technische Details:**
- Auflösung: Dynamisch, bis zu 6×768×768 + 1×1024×1024
- Inference: vLLM (Batch/Concurrency) oder Transformers

**Offene Fragen:**
- Qualität bei französischer Typografie (Guillemets, Akzente)?
- Umgang mit historischen Drucktypen (1930er–1950er)?
- Batch-Verarbeitung für große PDFs?

### Alternative: Docling

| Aspekt | Details |
|--------|---------|
| Repository | https://github.com/DS4SD/docling |
| Maintainer | IBM |
| Lizenz | MIT |
| GitHub Stars | 37.000+ |
| Status | Linux Foundation |

**Architektur:**
- Modulare Pipeline (nicht monolithisches VLM)
- Layout-Analyse: DocLayNet
- Tabellenstruktur: TableFormer
- OCR-Engines: Tesseract, EasyOCR, RapidOCR (wählbar)

**Output-Formate:**
- Markdown
- HTML
- JSON
- DocTags (strukturerhaltend)

### Vergleich

| Aspekt | DeepSeek-OCR-2 | Docling |
|--------|----------------|---------|
| Architektur | Monolithisches VLM | Modulare Pipeline |
| Strukturerhalt | Gut bei Fließtext | Stark bei Tabellen, Layout, Formeln |
| OCR-Engine | Integriert | Wählbar |
| Community | Neu (Jan 2026) | Etabliert (37k Stars) |
| Geschwindigkeit | ? | Bis zu 30x schneller als VLM |

**Empfehlung für PoC:** Beide Optionen testen, Qualität vergleichen.

---

## Stufe 2: TEI-Transformation

### Aufgaben

1. **Strukturerkennung**: Dokumenttyp identifizieren (Essay, Rezension, Interview, Lexikon)
2. **Element-Mapping**: Markdown → TEI-Elemente (siehe [TEI-Mapping.md](TEI-Mapping.md))
3. **Normalisierung**: Zeichenkonvertierung gemäß Regeln
4. **Metadaten**: Seiten-/Zeilennummern aus OCR-Output extrahieren

### Modellauswahl

| Modell | Anbieter | Input | Output | Stärken |
|--------|----------|-------|--------|---------|
| Claude Haiku 4.5 | Anthropic | 0,80 USD/1M | 4,00 USD/1M | Strukturierte Ausgaben, XML |
| Gemini 3 Flash | Google | 0,50 USD/1M | 3,00 USD/1M | Dokumentenanalyse, Geschwindigkeit |

**Empfehlung für PoC:** Beide Modelle an denselben Testdokumenten vergleichen.

### Prompt-Strategie

**System-Prompt (Konzept):**

```
Du bist ein TEI-XML-Experte für die Edition von Texten nach dem DTA-Basisformat.

Aufgabe: Transformiere den Markdown-Text in TEI-XML.

Regeln:
1. Dokumentstruktur: <TEI><teiHeader/><text><body>...</body></text></TEI>
2. Normalisierung: [Regeln aus TEI-Mapping.md]
3. Struktur: [Regeln für div, p, head, etc.]
4. Hervorhebungen: [Regeln für hi rendition]
5. Sprache: Der Text ist überwiegend Französisch.

Gib nur das XML aus, keine Erklärungen.
```

**Sprachspezifische Anpassung:**
- 66% der Texte sind Französisch → Prompt und Beispiele primär französisch
- Bei deutschen Texten: Prompt-Variante oder Spracherkennung vorschalten

---

## Validierung

### Schema-Validierung

- TEI P5 Schema
- Projektspezifische Einschränkungen (RelaxNG/Schematron)

### Strukturelle Prüfungen

| Prüfung | Beschreibung |
|---------|--------------|
| Wohlgeformtheit | Valides XML |
| Element-Hierarchie | div-Verschachtelung korrekt |
| Attribut-Vollständigkeit | pb/@facs, pb/@n vorhanden |
| ID-Eindeutigkeit | xml:id nicht doppelt |

### Inhaltliche Prüfungen

| Prüfung | Beschreibung |
|---------|--------------|
| Seitenzählung | Konsekutive Seitennummern |
| Fußnoten-Verkettung | @next/@prev-Paare vollständig |
| GND-Format | ref="GND:..." wohlgeformt |

---

## Architekturoptionen

### Option A: Sequentiell

```
PDF₁ → OCR → TEI → Validierung
PDF₂ → OCR → TEI → Validierung
...
```

**Vorteile:** Einfach, gut debuggbar
**Nachteile:** Langsam bei großen Korpora

### Option B: Parallel (Batch)

```
[PDF₁, PDF₂, PDF₃, ...] → OCR (Batch) → TEI (Batch) → Validierung (Batch)
```

**Vorteile:** Schneller, kosteneffizienter (API-Batching)
**Nachteile:** Komplexere Fehlerbehandlung

### Option C: Streaming

```
PDF → OCR (Seite für Seite) → TEI (Seite für Seite) → Aggregation
```

**Vorteile:** Für sehr große Dokumente (588 Seiten)
**Nachteile:** Kontextverlust über Seitengrenzen (Fußnoten!)

**Empfehlung für PoC:** Option A (sequentiell), später Option B für Produktion.

---

## Kostenabschätzung

### Annahmen

- Durchschnitt: 6 Seiten/Dokument
- ca. 500 Tokens/Seite (Markdown) → 3.000 Tokens Input
- ca. 1.000 Tokens/Seite (TEI) → 6.000 Tokens Output

### Kosten pro Dokument (Stufe 2)

| Modell | Input (3k) | Output (6k) | Gesamt |
|--------|------------|-------------|--------|
| Claude Haiku 4.5 | 0,0024 USD | 0,024 USD | ~0,03 USD |
| Gemini 3 Flash | 0,0015 USD | 0,018 USD | ~0,02 USD |

### Hochrechnung Gesamtkorpus (289 Dokumente)

| Modell | Geschätzte Kosten |
|--------|-------------------|
| Claude Haiku 4.5 | ~8,70 USD |
| Gemini 3 Flash | ~5,80 USD |

**Hinweis:** OCR-Kosten (Stufe 1) kommen hinzu – abhängig von Hosting (lokal vs. Cloud).

---

## Technologie-Stack

### Empfohlen für PoC

| Komponente | Technologie |
|------------|-------------|
| Sprache | Python 3.11+ |
| OCR | DeepSeek-OCR-2 (via Transformers/vLLM) oder Docling |
| LLM-API | Anthropic SDK / Google AI SDK |
| XML-Validierung | lxml + RelaxNG |
| Orchestrierung | Einfaches Python-Script |

### Für Produktion (später)

| Komponente | Technologie |
|------------|-------------|
| Orchestrierung | Apache Airflow / Prefect |
| Speicher | S3-kompatibel für PDFs/XMLs |
| Monitoring | Logging, Metriken |
| UI | Streamlit / Gradio (optional) |

---

## Risikoanalyse

### Hohe Risiken

| Risiko | Beschreibung | Mitigation |
|--------|--------------|------------|
| GND-Verknüpfung | Externe Lookups, Disambiguierung | Nachgelagert, nicht im LLM |
| Mehrseitige Fußnoten | @next/@prev-Verkettung über Seitengrenzen | Speziallogik, manuelle QS |
| Komplexe Layouts | Lexikon, Interview, Tabellen | Dokumenttyp-Erkennung vorschalten |

### Mittlere Risiken

| Risiko | Beschreibung | Mitigation |
|--------|--------------|------------|
| Druckfehlererkennung | Sprachverständnis erforderlich | LLM mit Sprachkenntnis |
| Strukturhierarchie | div n="1/2/3" korrekt verschachteln | Validierung, Beispiele im Prompt |
| Semantische Hervorhebungen | Nur relevante auszeichnen | Klare Regeln im Prompt |
| OCR-Qualität historischer Drucke | 1930er–1950er Typografie | Beide OCR-Engines testen |

### Niedrige Risiken

| Risiko | Beschreibung | Mitigation |
|--------|--------------|------------|
| Zeichennormalisierung | Regelbasiert automatisierbar | Post-Processing-Script |
| Grundstruktur (pb, lb, p) | Standardaufgabe | Gute Prompt-Beispiele |

---

## Mehrwert des LLM-Ansatzes

- **Schnellere Ersttranskription** als manueller Transkribus-Workflow
- **Konsistente Normalisierung** durch regelbasierte Post-Processing
- **Skalierbarkeit** für 289 Texte (parallel verarbeitbar)
- **Dokumenttyp-Erkennung** (Review, Interview, etc.) durch LLM

### Grenzen

- GND-Verknüpfung erfordert externes System (lobid.org / GND-API)
- Komplexe Fußnoten-Verkettung braucht Speziallogik
- Finale QS bleibt manuell notwendig

---

## Herausforderungen

| Bereich | Komplexität | Anmerkung |
|---------|-------------|-----------|
| OCR aus PDF | Mittel | Qualität bei historischen Drucken unklar |
| Zeichennormalisierung | Niedrig | Regelbasiert |
| Strukturerkennung | Mittel | Dokumenttyp-Erkennung |
| Silbentrennung | Mittel | Französisch/Deutsch unterschiedlich |
| Fußnotenverarbeitung | Mittel | Seitenübergreifend komplex |
| NER/GND | Hoch | Disambiguierung, externe API |

---

## Offene Fragen

- DeepSeek-OCR-2 vs. Docling: Welches performt besser auf französischen Texten?
- Chunking-Strategie für große Dokumente (>100 Seiten)?
- Wie mit OCR-Fehlern umgehen, die die TEI-Struktur beeinflussen?
- Lokales Hosting der OCR oder Cloud-API?

---

## Nächste Schritte

1. [ ] DeepSeek-OCR-2 auf Pilot-PDFs testen
2. [ ] Docling als Alternative evaluieren
3. [ ] Claude Haiku 4.5 vs. Gemini 3 Flash vergleichen
4. [ ] Prompt-Engineering für TEI-Transformation
5. [ ] Validierungs-Pipeline aufsetzen

---

## PoC-Priorisierung

| Phase | Dokumente | Fokus |
|-------|-----------|-------|
| 1 | 2310, 2530, 1180 | OCR-Qualität, Grundstruktur |
| 2 | 130, 290, 90 | Fußnoten, Sprachwechsel |
| 3 | 3040, 890 | Lexikon, Interview, GND |

---

*Erstellt: 29.01.2026*
