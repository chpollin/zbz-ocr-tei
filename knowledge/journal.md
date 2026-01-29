# Arbeitsjournal ZBZ-OCR-TEI

**Projekt:** LLM-gestützte OCR + TEI für Jeanne Hersch Edition (ZBZ)
**Status:** Phase 1 Tests abgeschlossen, Spalten-Problem identifiziert

---

## 2026-01-29 | Materialanalyse & Erste Tests

### Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| Docling + DeepSeek-OCR-2 kombiniert | Layout-Analyse + beste OCR-Qualität |
| Deterministisch → LLM nur für Komplexes | Reproduzierbar, kostengünstig, debugbar |
| 4 Dokumenttypen (A-D) klassifiziert | Unterschiedliche Pipeline-Strategien |
| CER/WER als Qualitätsmetriken | Industriestandard, vergleichbar |
| TEI-Transformation regelbasiert | Markdown → TEI ohne LLM für Grundstruktur |

### Ergebnisse

| Bereich | Ergebnis | Erkenntnis |
|---------|----------|------------|
| OCR Phase 1 | 94.4% Genauigkeit | DeepSeek funktioniert gut für einspaltige Texte |
| Spalten-Problem | Lösung: Docling | Docling + DeepSeek kombiniert für Typ B |
| GND-Extraktion | 75 Entitäten | Karl Jaspers dominiert (90 Nennungen) |
| TEI-Templates | 5 erstellt | Dokumenttyp bestimmt Template-Wahl |
| TEI-Transformation | Prototyp fertig | Regelbasiert Markdown → TEI |
| Bildextraktion | 383 Seiten | Basis für QS-Viewer und digitale Edition |

### Gelernt

1. **OCR-Qualität ist dokumenttyp-abhängig** - Einspaltig funktioniert, zweispaltig nicht
2. **Windows-Limitierung** - Docling benötigt Symlinks (Developer Mode oder Cloud)
3. **GPU-Last** - DeepSeek friert PC ein, Tests nur isoliert möglich
4. **Single Source of Truth** - Offene Punkte nur an einem Ort führen

### Offene Punkte

- [x] ~~Bilder extrahieren~~ → 383 Seiten aus 15 PDFs
- [x] ~~TEI-Transformation Prototyp~~ → `scripts/transform_to_tei.py`
- [x] ~~OCR-Pipeline vereinheitlicht~~ → `scripts/ocr_pipeline.py`
- [ ] Docling auf Windows testen (Developer Mode aktivieren)
- [ ] Phase 2-4 OCR-Tests durchführen (GPU erforderlich)
- [ ] GND-Lookup API-Integration (lobid.org)

### Technische Hindernisse (29.01.2026)

| Problem | Status | Workaround |
|---------|--------|------------|
| Docling: Windows Symlink-Fehler | Blockiert | Developer Mode aktivieren oder Cloud |
| DeepSeek: Hohe GPU-Last | PC friert ein | Tests einzeln oder Cloud |

**Empfehlung:** GPU-intensive Tests auf Cloud-VM oder wenn PC nicht gebraucht wird.

---

*Aktualisiert: 29.01.2026*
