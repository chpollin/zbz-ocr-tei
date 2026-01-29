# Arbeitsjournal ZBZ-OCR-TEI

**Projekt:** LLM-gestützte OCR + TEI für Jeanne Hersch Edition (ZBZ)
**Status:** Phase 1 Tests abgeschlossen, Spalten-Problem identifiziert

---

## 2026-01-29 | Materialanalyse & Erste Tests

### Entscheidungen

| Entscheidung | Begründung |
|--------------|------------|
| DeepSeek-OCR-2 als primäres OCR-Tool | 3B VLM, 95%+ Genauigkeit bei einspaltigen Docs |
| Docling als Backup für zweispaltige Layouts | Bessere Layout-Segmentierung |
| 4 Dokumenttypen (A-D) klassifiziert | Unterschiedliche OCR-Strategien nötig |
| CER/WER als Qualitätsmetriken | Industriestandard, vergleichbar |
| Text-Alignment vor Evaluation | OCR erfasst oft nur Teilseiten |

### Ergebnisse

**Phase 1 (einspaltig):** Durchschnitt 94.4% Genauigkeit - siehe [Testplan-OCR.md](Testplan-OCR.md)

**Kritisches Problem:** Zweispaltige Layouts (Typ B) haben falsche Lesereihenfolge

### Durchgeführte Arbeiten

1. **Materialanalyse:** 15 PDFs, 19 TEI-Referenzen analysiert
2. **Wissensstruktur:** 7 Detaildokumente erstellt (siehe [README.md](README.md))
3. **OCR-Pipeline:** DeepSeek-OCR-2 installiert und getestet
4. **Evaluation:** CER/WER-Skript mit HTML-Report erstellt
5. **Post-Processing:** Normalisierung, Dehyphenation implementiert
6. **GND-Extraktion:** 75 Entitäten aus 18 Referenz-TEIs extrahiert (41 Personen, 10 Orgs, 24 Werke)
7. **TEI-Templates:** 5 Templates erstellt (base, essay, review, interview, lexicon)

### Offene Punkte

- [ ] Spalten-Problem lösen (Prompt-Varianten oder Docling)
- [ ] Phase 2-4 Tests durchführen (GPU erforderlich)
- [ ] TEI-Transformations-Pipeline implementieren
- [ ] GND-Lookup API-Integration (lobid.org)

### Technische Hindernisse (29.01.2026)

| Problem | Status | Workaround |
|---------|--------|------------|
| Docling: Windows Symlink-Fehler | Blockiert | Developer Mode aktivieren oder Cloud |
| DeepSeek: Hohe GPU-Last | PC friert ein | Tests einzeln oder Cloud |

**Empfehlung:** GPU-intensive Tests auf Cloud-VM oder wenn PC nicht gebraucht wird.

---

*Aktualisiert: 29.01.2026*
