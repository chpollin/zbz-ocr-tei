---
type: moc
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, index, navigation]
status: active
---

# Knowledge Base — ZBZ-OCR-TEI

Dokumentation für die LLM-gestützte OCR- und TEI-Pipeline der Jeanne Hersch Edition (Zentralbibliothek Zürich).

---

## Dokumentmatrix

| Dokument | Beantwortet | Zielgruppe | Abhängigkeiten |
|----------|-------------|------------|----------------|
| [PROJEKT](PROJEKT.md) | Was ist das Projekt? Wie hängt es mit coOCR und teiCrafter zusammen? | Alle | — |
| [PIPELINE](PIPELINE.md) | Wie ist die Pipeline technisch aufgebaut? | Entwicklung | PROJEKT |
| [QUELLENANALYSE](QUELLENANALYSE.md) | Was ist das Material? Welche Dokumenttypen gibt es? | Alle | — |
| [OCR-ENGINES](OCR-ENGINES.md) | Welche OCR-Tools werden eingesetzt und wie? | Entwicklung | PIPELINE |
| [TEI-MAPPING](TEI-MAPPING.md) | Welche TEI-Regeln gelten? | Entwicklung, Edition | QUELLENANALYSE |
| [GND-STRATEGIE](GND-STRATEGIE.md) | Wie funktioniert die Entitätsverknüpfung? | Entwicklung, Edition | TEI-MAPPING |
| [TESTPLAN](TESTPLAN.md) | Wie wird Qualität gemessen? Was sind die Ergebnisse? | Entwicklung, QS | QUELLENANALYSE, OCR-ENGINES |
| [INFRASTRUKTUR](INFRASTRUKTUR.md) | Wie wird deployed? Azure, Podman, CI/CD? | Entwicklung, Ops | PIPELINE |
| [DECISIONS](DECISIONS.md) | Was ist entschieden? Was ist offen? | Alle | Alle |
| [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) | Wie arbeitet die ZBZ redaktionell? | Alle | — |
| [JOURNAL](JOURNAL.md) | Was wurde wann gemacht? | Alle | — |

---

## Abhängigkeiten

```
PROJEKT (Vision, Ökosystem)
    │
    ├──▶ PIPELINE (5-Stufen-Pipeline inkl. Export)
    │        ├──▶ OCR-ENGINES (DeepSeek, Mistral, Gemini)
    │        ├──▶ INFRASTRUKTUR (Azure, Podman, CI/CD)
    │        └──▶ TESTPLAN (Phasen, Metriken)
    │
    ├──▶ QUELLENANALYSE (Korpus, Dokumenttypen, Pilotdateien)
    │        ├──▶ TEI-MAPPING (DTA-Basisformat, Regeln)
    │        │        └──▶ GND-STRATEGIE (NER, Entity Linking)
    │        └──▶ TESTPLAN (Single Source für Ergebnisse)
    │
    └──▶ ZBZ-WORKFLOW (Redaktioneller Kontext)

DECISIONS ◄── querschnittlich, sammelt aus allen Docs
JOURNAL   ◄── chronologisch, verweist auf alle Docs
```

---

## Kernbegriffe

| Begriff | Definition | Dokument |
|---------|------------|----------|
| Ökosystem | Dreistufige Toolchain: zbz-ocr-tei → coOCR/HTR → teiCrafter | [PROJEKT](PROJEKT.md) |
| 5-Stufen-Pipeline | Layout → OCR → LLM-Korrektur → Post-Processing → Export | [PIPELINE](PIPELINE.md) |
| Dokumenttypen A-D | Einspaltig, Zweispaltig, Monografie, Spezial | [QUELLENANALYSE](QUELLENANALYSE.md) |
| DTA-Basisformat | TEI-Grundschema mit ZBZ-Anpassungen | [TEI-MAPPING](TEI-MAPPING.md) |
| Agentic Vision | Gemini 3 Think-Act-Observe Loop für Spalten | [OCR-ENGINES](OCR-ENGINES.md) |
| Nachgelagerte GND | TEI-Struktur zuerst, NER + Linking separat | [GND-STRATEGIE](GND-STRATEGIE.md) |
| CER / WER | Character Error Rate / Word Error Rate | [TESTPLAN](TESTPLAN.md) |
| Hybrid-Pipeline | Docling (Layout) + LLM-OCR (Text) kombiniert | [PIPELINE](PIPELINE.md) |
| PAGE-XML | Exportformat fuer coOCR (Schema 2019-07-15) | [PIPELINE](PIPELINE.md) |
| Dashboard | QA-UI mit Metriken, Engine-Vergleich und Dokumentkatalog | [PIPELINE](PIPELINE.md) |
| METS-XML | Multi-Page-Manifest fuer coOCR-Import | [PIPELINE](PIPELINE.md) |

---

## Schnelleinstieg

1. **Ökosystem verstehen:** [PROJEKT](PROJEKT.md) — wie hängen die drei Tools zusammen?
2. **Pipeline verstehen:** [PIPELINE](PIPELINE.md) — die 5 Verarbeitungsstufen (OCR + Export)
3. **Material kennen:** [QUELLENANALYSE](QUELLENANALYSE.md) — 289 Texte, 4 Dokumenttypen
4. **Dashboard ansehen:** `docs/index.html` -- Metriken, Engine-Vergleich, Pipeline-Status
5. **Status prüfen:** [DECISIONS](DECISIONS.md) — was ist entschieden, was blockiert?
6. **Letzte Session:** [JOURNAL](JOURNAL.md) — chronologisches Arbeitslog

---

## Verzeichnisstruktur

```
knowledge/
├── INDEX.md              # Dieser Index (MOC)
├── PROJEKT.md            # Vision, Ökosystem, Meilensteine
├── PIPELINE.md           # Technische Pipeline-Dokumentation
├── QUELLENANALYSE.md     # Korpus, Dokumenttypen, Pilotdateien
├── OCR-ENGINES.md        # OCR-Tools: DeepSeek, Mistral, Gemini, Docling
├── TEI-MAPPING.md        # TEI-Transformationsregeln
├── GND-STRATEGIE.md      # NER + Entity Linking
├── TESTPLAN.md           # Testphasen, Metriken, Ergebnisse
├── INFRASTRUKTUR.md      # Azure, Podman, GitLab, CI/CD
├── DECISIONS.md          # Entschiedenes + Offenes (priorisiert)
├── ZBZ-WORKFLOW.md       # ZBZ-Redaktionsworkflow + Integrationspunkte
└── JOURNAL.md            # Chronologisches Arbeitsjournal
```

---

## Wartung

- **Neuer Fakt?** In genau ein Dokument eintragen, andere verweisen
- **Neue Entscheidung?** In [DECISIONS](DECISIONS.md) dokumentieren
- **Session beenden?** [JOURNAL](JOURNAL.md) aktualisieren
- **Duplikation entdeckt?** Sofort eliminieren, Querverweis setzen

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
