# Arbeitsjournal ZBZ-OCR-TEI

**Projekt:** LLM-gestützte OCR + TEI für Jeanne Hersch Edition (ZBZ)
**Status:** Hybrid-Pipeline validiert (Docling Layout + DeepSeek OCR)

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
- [ ] Hybrid-Workflow komplettieren (Layout → Crop → DeepSeek)
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

*Aktualisiert: 29.01.2026*
