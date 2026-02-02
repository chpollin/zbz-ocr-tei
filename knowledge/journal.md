# Arbeitsjournal ZBZ-OCR-TEI

**Projekt:** LLM-gestützte OCR + TEI für Jeanne Hersch Edition (ZBZ)
**Status:** Pipeline erweitert um Gemini 3 Agentic Vision

---

## 2026-02-02 | Gemini 3 Agentic Vision Analyse

### Neue Erkenntnis

Google hat am 27.01.2026 **Agentic Vision** für Gemini 3 Flash veröffentlicht:
- **Think-Act-Observe Loop**: Modell plant, führt Python-Code aus, validiert Ergebnis
- **Auto-Crop/Zoom**: Erkennt Spalten automatisch, croppt und liest sequenziell
- **Selbstvalidierung**: 5-10% Qualitätsboost durch iterative Prüfung
- **BBox-Output**: Kann Koordinaten für TEI `<facsimile>` liefern

### Auswirkung auf Pipeline

| Dokumenttyp | Bisherige Pipeline | Neue Option |
|-------------|-------------------|-------------|
| Typ A (einspaltig) | DeepSeek-OCR-2 | Keine Änderung |
| Typ B (zweispaltig) | Docling + DeepSeek | **Gemini 3 Agentic Vision** |
| Typ C (Monografie) | DeepSeek + Chunking | Keine Änderung |
| Typ D (Spezial) | DeepSeek | **Gemini 3 Agentic Vision** |

**Vorteil:** Gemini löst Spaltenproblem ohne separate Layout-Extraktion.

### Dokumentation aktualisiert

- [x] Pipeline.md: Agentic Vision Strategie
- [x] OCR-Tools.md: Think-Act-Observe, Vergleichstabelle
- [x] Testplan-OCR.md: Gemini-Testfall für Phase 2
- [x] TEI-Mapping.md: `<facsimile>` Koordinaten-Sektion

### Kosten (aktualisiert)

| Szenario | Kosten |
|----------|--------|
| Nur NER/Korrektur | ~$20 |
| + Typ B/D via Gemini | ~$27 |

### Quellen

- [Agentic Vision Announcement](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/)
- [IIIF Annotation Example](https://gist.github.com/charlesLoder/5341c539ab8330cfebc2d807e6b9c765)

---

## 2026-01-29 | Materialanalyse & Pipeline-Entwicklung

### Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Hybrid: Docling (Layout) + DeepSeek (OCR) | Layout-Analyse ohne OCR, DeepSeek für Texterkennung |
| Docling nur für Layout | RapidOCR hat Encoding-Probleme bei französischem Text |
| Deterministisch → LLM nur für Komplexes | Reproduzierbar, kostengünstig, debugbar |
| 4 Dokumenttypen (A-D) klassifiziert | Unterschiedliche Pipeline-Strategien |
| TEI-Transformation regelbasiert | Markdown → TEI ohne LLM für Grundstruktur |

### Ergebnisse

| Bereich | Ergebnis | Erkenntnis |
|---------|----------|------------|
| OCR Phase 1 | 94.4% Genauigkeit | DeepSeek funktioniert gut für einspaltige Texte |
| Docling Layout | Funktioniert auf Windows | Spalten korrekt erkannt, Koordinaten extrahiert |
| Docling OCR | Nicht nutzbar | RapidOCR erzeugt Encoding-Fehler (é → Ø) |
| Layout-Extraktion | 2530.pdf getestet | Zweispaltig erkannt, 14 Regionen pro Seite |
| GND-Extraktion | 75 Entitäten | Karl Jaspers dominiert (90 Nennungen) |
| TEI-Templates | 5 erstellt | Dokumenttyp bestimmt Template-Wahl |
| TEI-Transformation | Prototyp fertig | Regelbasiert Markdown → TEI |
| Bildextraktion | 383 Seiten | Basis für QS-Viewer und digitale Edition |

### Gelernt

1. **Docling nur für Layout** - OCR-Komponente hat Encoding-Probleme
2. **Hybrid-Ansatz validiert** - Docling Koordinaten + DeepSeek Text funktioniert
3. **Windows funktioniert** - Docling läuft (mit Symlink-Warnung, aber ohne Fehler)
4. **OCR-Qualität ist dokumenttyp-abhängig** - Einspaltig funktioniert, zweispaltig braucht Layout-Analyse
5. **Single Source of Truth** - Offene Punkte nur an einem Ort führen

### Offene Punkte

- [x] ~~Bilder extrahieren~~ → 383 Seiten aus 15 PDFs
- [x] ~~TEI-Transformation Prototyp~~ → `scripts/transform_to_tei.py`
- [x] ~~OCR-Pipeline vereinheitlicht~~ → `scripts/ocr_pipeline.py`
- [x] ~~Docling Layout-Extraktion~~ → `scripts/extract_layout.py`
- [ ] Gemini 3 Agentic Vision für Typ B testen (2530.pdf)
- [ ] Hybrid-Workflow komplettieren (Layout -> Crop -> DeepSeek)
- [ ] Phase 2-4 OCR-Tests durchführen (GPU erforderlich)
- [ ] GND-Lookup API-Integration (lobid.org)

### Technische Hindernisse (29.01.2026)

| Problem | Status | Workaround |
|---------|--------|------------|
| Docling OCR: Encoding-Fehler | Gelöst | Docling nur für Layout, DeepSeek für OCR |
| Docling: Symlink-Warnung | Ignorierbar | Funktioniert trotzdem |
| DeepSeek: Hohe GPU-Last | PC friert ein | Tests einzeln oder Cloud |

**Empfehlung:** GPU-intensive Tests auf Cloud-VM oder wenn PC nicht gebraucht wird.

---

*Aktualisiert: 02.02.2026*
