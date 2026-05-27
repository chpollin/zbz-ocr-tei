---
type: moc
created: 2026-01-29
updated: 2026-05-25
tags: [zbz-ocr-tei, index, navigation]
status: active
---

# Knowledge Base — zbz-ocr-tei

Dokumentation der LLM-gestuetzten OCR- und TEI-Pipeline der Jeanne-Hersch-Edition (Zentralbibliothek Zuerich).

Diese Knowledge-Base wurde am 2026-04-27 konsolidiert: 25 Dokumente auf 10 reduziert,
SSoT pro Domaene, eine Datei pro Thema.

---

## Dokumente

| Dokument | Beantwortet |
|---|---|
| [projekt.md](projekt.md) | Was ist das Projekt? Auftrag, Korpus-Trichter (325→289→286→285, ~7.186 biblio. Seiten), ZBZ-Workflow, Status, Kosten |
| [pipeline.md](pipeline.md) | Wie ist die Pipeline aufgebaut? Stufen PDF → TEI, Engines (Mistral, DeepSeek, Docling, Gemini), TEI-Mapping (DTA + ZBZ), Round-Trip-Sektion |
| [workflow.md](workflow.md) | Wie laeuft der End-to-End-Datenfluss? Datenfluss-Diagramm, Datenformate pro Stufe, Save-Mechanismus im Viewer, Round-Trip vom Edit zur regenerierten TEI, Provenance-Konzept, geplante `_complete.xml`-Variante, Roadmap |
| [entities.md](entities.md) | Wie funktioniert Entity Linking? NER + GND + Wikidata, Dual-Attribut-Strategie (E50), 4.504 Entitaeten / 47% verlinkt, Wikidata-Workflow |
| [quality.md](quality.md) | Wie gut ist die Pipeline? CER-Benchmark (Median 1.83%), CER-Methodik (BCa-Bootstrap), TEI-Schema-Validierung, Quality-Proxy, Agent-Based Quality Screening |
| [viewer.md](viewer.md) | Wie funktioniert der Pipeline-Viewer? Single-Page-App mit Doc-Liste, Faksimile + Layout-Overlay (OpenSeadragon E58), OCR/TEI-Editor, Edit-Toggle pro Panel (E60), Export-Modul (E61), Datei-Download |
| [infrastruktur.md](infrastruktur.md) | Wie wird deployed? Azure, Mistral Document AI, Podman, GitLab Uni Zuerich, CI/CD |
| [methodik.md](methodik.md) | Wie arbeiten wir? Epistemische Infrastruktur, Verifikationskaskade, Critical Expert in the Loop, Dreischichtung, operative CLI |
| [decisions.md](decisions.md) | Was ist entschieden? E1-E61, offene Punkte (O8, O13, O18, O22), Risiken |
| [journal.md](journal.md) | Was wurde wann gemacht? kompakter Sitzungs-Ueberblick (Jan-Mai 2026), wiederkehrende Muster |

Konstitution + Commands: [CLAUDE.md](../CLAUDE.md) (Top-Level, projekt-weite Regeln).

---

## Abhaengigkeiten

```
projekt (Vision, Korpus, ZBZ-Kontext)
   │
   ├── pipeline (Stufen: PDF → TEI)
   │      ├── entities (NER + Wikidata + GND)
   │      └── infrastruktur (Azure, Podman, CI/CD)
   │
   ├── workflow (End-to-End-Datenfluss + Save + Round-Trip + Provenance)
   │
   ├── quality (CER + TEI-Validierung + Screening)
   │
   ├── viewer (Pipeline-Viewer + Layout-/Transkriptions-Editor)
   │
   └── methodik (Promptotyping + Verifikationskaskade)

decisions       — cross-cutting, Entscheidungsregister
journal         — chronologisch, kompakter Ueberblick
```

---

## Schluesselkonzepte

| Begriff | Definition | Quelle |
|---|---|---|
| 7-Stage Pipeline | Bilder → OCR → Layout → PAGE-XML → NER/GND → TEI-XML → Evaluation | [pipeline.md](pipeline.md) |
| Dokumenttypen A-D | einspaltig / zweispaltig / Monografie / Spezial | [projekt.md](projekt.md) |
| DTA-Basisformat | TEI-Basisschema mit ZBZ-Anpassungen | [pipeline.md §TEI-Mapping](pipeline.md) |
| `zbz_hersch.rng` (E48/E49) | projektspezifisches RelaxNG-Schema, ref-Pattern fuer GND + #zbz | [pipeline.md](pipeline.md) |
| Dual-Attribut-Strategie (E50) | `ref="GND:..."` (primaer) + `corresp="#zbz-{typ}.{N}"` (intern) | [entities.md](entities.md) |
| Hybrid Pipeline | Docling Layout + LLM-OCR Text | [pipeline.md](pipeline.md) |
| Unified TEI Pipeline (E32) | Scaffold + Gemini Refinement + Assembly + Validation | [pipeline.md](pipeline.md) |
| Agent-Based Quality Screening (E41, deprecated E66) | 7-Schichten-Pre-Curation, Review-JSON pro Doc — als Qualitaetssignal abgeschafft, weil kein Mensch beteiligt war; Legacy als `_screening_legacy.json` erhalten | [quality.md](quality.md) |
| Workflow-Status pro Strom (E66/E67) | unverifiziert \| in_arbeit \| bearbeitet \| fertig je OCR/Layout/TEI, im Manifest mit Provenienz-History, projizierbar in `<revisionDesc>`. Ampel: gelb=unverifiziert/in_arbeit/bearbeitet, gruen=fertig, rot reserviert | [quality.md](quality.md), [viewer.md](viewer.md) |
| Ampel-Reframing (E67) | "Pipeline-Output EXISTIERT, ist nur unverifiziert" -- daher Status `offen` umbenannt zu `unverifiziert`, rote Default-Lesart aufgegeben | [decisions.md §E67](decisions.md) |
| CER-Benchmark (E51) | End-to-End TEI-vs-TEI, Median 1.83% (n=19) | [quality.md](quality.md) |
| CER-Statistik (E54) | BCa-Bootstrap-CIs, paired E2E vs OCR-only, HCPR | [quality.md](quality.md) |
| Quality Proxy | Dictionary Hit Rate fuer 285 Docs ohne Ground Truth | [quality.md](quality.md) |
| revisionDesc (E42) | Pipeline + Screening-Status im TEI-Header, reist mit dem Dokument | [pipeline.md](pipeline.md) |
| `output/tei_final/` (E43) | Single Source of Truth fuer die Edition | [pipeline.md](pipeline.md) |
| Verifikationskaskade | 4 Stufen: automatisch / kontextuell / visuell / fachlich | [methodik.md](methodik.md) |
| Dreischichtung | Command (Regel) / Artifact (Werkzeug) / Tool (Aufruf) | [methodik.md](methodik.md) |
| Pipeline-Viewer (E56) | Single-Page-App mit Faksimile + OCR + TEI + Layout-/Transkriptions-Editor, Datei-Download | [viewer.md](viewer.md) |
| Hersch Design-System | Anthrazit + Ziegelrot + EB Garamond + Jost, `--h-*` Tokens | [viewer.md](viewer.md) |
| OpenSeadragon-Faksimile (E58) | Faksimile-Renderer im View-Modus mit Pan/Zoom/Rotate, CDN-Bezug | [viewer.md](viewer.md) |
| Mode-Edit-Toggle pro Panel (E60) | Faksimile-Panel "Layout", Text-Panel "Text" (E64), aktiv = anthrazit; keine globale Mode-Leiste | [viewer.md](viewer.md) |
| Viewer = Mistral-Edition (E64) | Kein OCR-Quellen-Umschalter im Viewer; Alt-Engines (Gemini/LLM/DeepSeek) sind Benchmark-only; Doc-Subbar + Toolbar fusioniert | [viewer.md](viewer.md) |
| Export-Modul (E61) | JSZip-basierter Per-Doc-Drawer + Bulk-Export aus Korpus-Uebersicht | [viewer.md](viewer.md) |
| Methode-Seite (E62) | `docs/methode.html` mit Headline-CER, stratifizierten Werten, Limitations, Literatur-Vergleich (statisch) | [viewer.md](viewer.md) |
| End-to-End-Workflow | Datenfluss + Save-Mechanismus + Round-Trip + Provenance-Konzept + geplante `_complete.xml`-Variante | [workflow.md](workflow.md) |
| Manueller Round-Trip | User-Edit -> Download -> manuelles Ablegen -> `tei_unified --reassemble` -> regenerierte TEI | [workflow.md §3.3](workflow.md), [pipeline.md §Round-Trip](pipeline.md) |
| Provenance pro Objekt (geplant) | `{doc}_provenance.json` mit voller Edit-History (AI + human), Anzeige im Viewer als Drawer | [workflow.md §4.2](workflow.md) |
| `_complete.xml` (geplant) | Selbst-enthaltenes TEI mit `<facsimile>` + `<zone>` + `@facs` + erweitertes `<revisionDesc>` | [workflow.md §5](workflow.md) |

---

## Quick Start

1. **Projekt verstehen:** [projekt.md](projekt.md) — Auftrag, Korpus, Beteiligte
2. **Pipeline verstehen:** [pipeline.md](pipeline.md) — 7 Stufen + Engines + TEI-Mapping
3. **Qualitaet:** [quality.md](quality.md) — CER-Benchmark, Screening, Proxy
4. **Dashboard:** `docs/index.html` — Metriken + Katalog
5. **Status:** [decisions.md](decisions.md) — was ist entschieden, was blockiert
6. **Letzte Sitzung:** [journal.md](journal.md) — kompakter Sitzungs-Ueberblick

---

## Wartung

- **neuer Fakt?** in genau ein Dokument einfuegen, von anderen referenzieren
- **neue Entscheidung?** in [decisions.md](decisions.md) eintragen
- **Sitzungsende?** eine Zeile in [journal.md](journal.md) ergaenzen
- **Duplikation gefunden?** sofort beseitigen, Cross-Reference einfuegen
- **Inhalte nur in einem Dokument** — bei Ueberschneidung: ein Dokument behaelt die Definition, das andere verlinkt

---

*Konsolidiert: 2026-04-27 (von 25 Dokumenten auf 10 reduziert)*
