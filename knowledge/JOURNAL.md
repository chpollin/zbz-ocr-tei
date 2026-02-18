---
type: journal
created: 2026-01-29
updated: 2026-02-18
tags: [zbz-ocr-tei, journal, log]
status: active
---

# Arbeitsjournal

Chronologisches Arbeitslog. Entscheidungen sind in [DECISIONS](DECISIONS.md) konsolidiert, Projektstatus in [PROJEKT](PROJEKT.md).

**Abhängigkeiten:** Keine (eigenständiges Log)

---

## 2026-02-18 | M1: OCR-Validierung alle Dokumenttypen

### Durchgefuehrt

- `evaluate_ocr.py` erweitert: `--ocr-dir`, `--engine`, `--phase` Parameter
- Fuzzy TEI-Lookup (findet `1520 - in Arbeit.xml`)
- rapidfuzz fuer CER-Berechnung (loest MemoryError bei langen Texten)
- Verbessertes Alignment (Markdown-Stripping, abgestufte Phrase-Suche)
- Mistral OCR fuer alle 12 Testdokumente (Phase 1-4) ausgefuehrt
- CER/WER-Evaluation gegen Referenz-TEI abgeschlossen

### Ergebnisse Mistral Document AI

| Phase | Typ | Docs | Avg CER | Avg WER | Genauigkeit |
|-------|-----|------|---------|---------|-------------|
| Phase 1 | A (einspaltig) | 3 | 9.40% | 20.22% | 90.60% |
| Phase 2 | B (zweispaltig) | 3 | 6.31% | 17.53% | 93.69% |
| Phase 3 | D (Spezial) | 4 | 2.88% | 12.62% | 97.12% |
| Phase 4 | C (Monografie) | 2 | n/a | n/a | Alignment-Problem |

**Phase 1-3 Durchschnitt: CER 5.87%, Genauigkeit 94.14%**

Phase 4 (Monografien) nicht aussagekraeftig: Alignment bei 156/142-seitigen Buechern funktioniert
nicht zuverlaessig (gesamter Referenz-Text vs. gesamte OCR verglichen).

### Einzelergebnisse

| Doc | Typ | CER | WER |
|-----|-----|-----|-----|
| 2310 | A | 7.00% | 22.04% |
| 1180 | A | 3.12% | 10.45% |
| 290 | A | 18.07% | 28.17% |
| 2530 | B | 3.96% | 17.06% |
| 890 | B | 5.96% | 12.80% |
| 3040 | B | 9.02% | 22.73% |
| 90 | D | 1.21% | 8.92% |
| 1440 | D | 3.71% | 12.69% |
| 830 | D | 4.00% | 17.46% |
| 1330 | D | 2.60% | 11.42% |

### Erkenntnisse

- Mistral Document AI zeigt beste Ergebnisse bei Typ D (Spezialformate): 97% Genauigkeit
- Doc 290 (Comptes Rendus FR) hat schlechteste CER in Phase 1-3 (18%) - vermutlich Scan-Qualitaet
- Zweispaltige Docs (Typ B) werden ueberraschend gut erkannt (CER 6.3%)
- Fuer Monografien braucht die Evaluation einen seitenweisen Vergleichsansatz

---

## 2026-02-18 | Code-Refactoring: Zentrale Module

### Durchgefuehrt

- `scripts/config.py` erstellt: Alle Pfade, Modellnamen, Konstanten, Testplan an einem Ort
- `scripts/utils.py` erstellt: `pdf_to_images()`, `check_gpu()`, `load_env()`, `load_deepseek_model()`
- 12 Scripts refactored: Duplizierte Funktionen durch shared imports ersetzt
- Eliminiert: 4x `pdf_to_images()`, 4x `check_gpu()`, 4x `load_model()`, 2x `load_env()`, 2x `TESTPLAN`
- Alle Imports verifiziert (16 Module laden korrekt)

### Betroffene Dateien

| Datei | Aenderung |
|-------|-----------|
| `scripts/config.py` | **NEU** - Zentrale Konfiguration |
| `scripts/utils.py` | **NEU** - Gemeinsame Hilfsfunktionen |
| `scripts/ocr_pipeline.py` | Nutzt config/utils, lokale Duplikate entfernt |
| `scripts/test_mistral_ocr.py` | Nutzt config/utils statt eigener load_env/PHASE1_TESTS |
| `scripts/test_all_pdfs.py` | Nutzt config/utils statt eigenem TESTPLAN/check_gpu/load_model |
| `scripts/test_deepseek_ocr.py` | Nutzt config/utils statt eigener pdf_to_images/check_gpu/load_model |
| `scripts/test_column_prompt.py` | Nutzt config/utils statt eigener check_gpu/load_model |
| `scripts/evaluate_ocr.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/transform_to_tei.py` | Nutzt config statt lokaler DOC_TYPES/KNOWN_ENTITIES |
| `scripts/extract_pages.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/extract_layout.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/extract_gnd.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/test_docling.py` | Nutzt config statt PROJECT_ROOT-Pfade |

---

## 2026-02-18 | Mistral Document AI Integration & Benchmark

### Durchgefuehrt

- Mistral Document AI 2512 als OCR-Engine in Pipeline integriert (MistralOCR-Klasse)
- Azure AI Foundry Endpoint konfiguriert (.env, .claudeignore, .gitignore)
- Phase-1-Benchmark: alle 3 Typ-A-Dokumente erfolgreich verarbeitet
- Benchmark-Ergebnis: Mistral erkennt 142% mehr Zeichen als DeepSeek (alle Seiten vs 2 Seiten)
- Interaktives Benchmark Web-UI erstellt (docs/benchmark.html)
- Knowledge-Vault aktualisiert (OCR-ENGINES.md, INFRASTRUKTUR.md)

### Benchmark-Ergebnisse Phase 1

| Dokument | Seiten | Mistral Zeichen | DeepSeek Zeichen | Mistral Zeit |
|----------|--------|-----------------|------------------|--------------|
| 2310.pdf | 3 | 8.041 | 6.597 | 5.6s (1.9s/S) |
| 1180.pdf | 8 | 20.121 | 6.070 | 6.4s (0.8s/S) |
| 290.pdf | 5 | 15.148 | 5.213 | 6.3s (1.3s/S) |

Hinweis: DeepSeek hatte in frueheren Tests nur 2 Seiten pro Dokument verarbeitet (lokale GPU), Mistral verarbeitet alle Seiten serverseitig.

### Neue Dateien

- `scripts/test_mistral_ocr.py` - Benchmark-Skript
- `docs/benchmark.html` - Interaktives Benchmark-UI
- `.env` / `.env.example` / `.claudeignore` - Konfiguration & Sicherheit
- `output/mistral_results/` - OCR-Ergebnisse + Manifest

### Technische Erkenntnisse

- Azure AI Foundry Endpoint hat eigenes URL-Format (nicht Standard Mistral-API)
- PyMuPDF >= 1.24 hat `fitz` zu `pymupdf` umbenannt
- Mistral erkennt Kursivschrift (*italics*), Fussnoten und Akzente zuverlaessig
- Kein GPU noetig (Cloud-API), ~1.3s/Seite Durchschnitt

---

## 2026-02-18 | Knowledge-Vault Refactoring

### Durchgeführt

- Vollständige Repository-Analyse (Struktur, Code, Dokumentation)
- Knowledge-Ordner nach coOCR/teiCrafter-Muster refactored
- Neue Kerndokumente: INDEX.md, PROJEKT.md, DECISIONS.md, INFRASTRUKTUR.md
- Duplikation eliminiert, Single Source of Truth eingeführt
- Ökosystem-Kontext dokumentiert (zbz-ocr-tei → coOCR → teiCrafter)

### Erkenntnisse

- Post-Processing entfernt Markdown-Formatierung *vor* TEI-Transformation — Informationsverlust (→ R6 in [DECISIONS](DECISIONS.md))
- TEI-Transformation nur als Einzelseiten-Prototyp, nicht als Dokument-Assembly
- Kein Code für Azure/Mistral/Gemini — nur DeepSeek + Docling implementiert
- Schnittstellen zwischen den drei Tools noch undefiniert

---

## 2026-02-14 | Auftrag beidseitig bestätigt, Projektstart

### Zusammenfassung

Auftrag beidseitig bestätigt. ZBZ hat erteilt (Mail Elias, nach 07.02.), DHCraft hat angenommen (Mail Christopher, 14.02.). Projekt wechselt von Akquisephase in Umsetzung.

### Neue Rahmenbedingungen

- Mistral OCR 3 über Azure verfügbar, API-Key wird bereitgestellt
- Claude Max Subscription empfohlen (Coding, Promptotyping)
- Gemini API empfohlen (OCR/HTR, multimodale Stärke)
- CI/CD: Fork auf GitLab Uni Zürich, Podman
- Team ZBZ: Anouschka (Editions- und Informatik-Background, seit Januar)
- coOCR/HTR als Community-Projekt positioniert (Klugseder-Fork als Referenz)

### Alignment-Call

Terminvorschläge gesendet, Rückmeldung ausstehend. Agenda: Fork-Modell, Merge-Strategie, GitLab-Setup, Podman-Details, Vor-Ort-Termin Zürich.

### Dokumentation aktualisiert

- Vault-Dokument, Projektplan, Pipeline, OCR-Tools

---

## 2026-02-02 | Gemini 3 Agentic Vision Analyse

### Zusammenfassung

Google hat am 27.01.2026 Agentic Vision für Gemini 3 Flash veröffentlicht. Think-Act-Observe Loop ermöglicht Auto-Crop von Spalten — potenzielle Lösung für Typ-B-Problem.

Details: Siehe [OCR-ENGINES](OCR-ENGINES.md) §Gemini.

### Quellen

- [Agentic Vision Announcement](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/)
- [IIIF Annotation Example](https://gist.github.com/charlesLoder/5341c539ab8330cfebc2d807e6b9c765)

---

## 2026-01-29 | Materialanalyse & Pipeline-Entwicklung

### Zusammenfassung

Intensive Arbeitssession: Korpusanalyse, Hybrid-Pipeline validiert, OCR Phase 1 durchgeführt, TEI-Prototyp erstellt, GND-Seed extrahiert, Bildextraktion abgeschlossen.

### Ergebnisse

| Bereich | Ergebnis |
|---------|----------|
| OCR Phase 1 | 94.4% Genauigkeit — Details in [TESTPLAN](TESTPLAN.md) |
| Docling Layout | Funktioniert auf Windows, Spalten erkannt |
| Docling OCR | Nicht nutzbar (Encoding-Fehler) — Details in [OCR-ENGINES](OCR-ENGINES.md) |
| GND-Extraktion | 75 Entitäten — Details in [GND-STRATEGIE](GND-STRATEGIE.md) |
| TEI-Templates | 5 erstellt in `templates/` |
| Bildextraktion | 383 Seiten aus 15 PDFs |

### Gelernt

1. Docling nur für Layout — OCR-Komponente hat Encoding-Probleme
2. Hybrid-Ansatz validiert — Docling Koordinaten + DeepSeek Text funktioniert
3. Windows funktioniert — Docling läuft (mit Symlink-Warnung)
4. OCR-Qualität ist dokumenttyp-abhängig
5. Single Source of Truth für offene Punkte

### Technische Hindernisse

| Problem | Status | Workaround |
|---------|--------|------------|
| Docling OCR: Encoding-Fehler | Gelöst | Docling nur für Layout |
| Docling: Symlink-Warnung | Ignorierbar | Funktioniert trotzdem |
| DeepSeek: Hohe GPU-Last | Bekannt | Tests einzeln oder Cloud |

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-18*
