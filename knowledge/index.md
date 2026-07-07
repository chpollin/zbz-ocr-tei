---
title: Knowledge Base — zbz-ocr-tei
type: moc
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-01-29
updated: 2026-06-21
tags: [zbz-ocr-tei, index, navigation]
---

# Knowledge Base — zbz-ocr-tei

Dokumentation der LLM-gestuetzten OCR- und TEI-Pipeline der Jeanne-Hersch-Edition (Zentralbibliothek Zuerich).

Diese Knowledge-Base wurde am 2026-04-27 konsolidiert (25 Dokumente auf 10 reduziert) und
seither auf 12 erweitert (frontend-gaps.md, oekosystem-synthese.md, je 2026-06-07):
SSoT pro Domaene, eine Datei pro Thema.

---

## Dokumente

| Dokument | Beantwortet |
|---|---|
| [projekt.md](projekt.md) | Was ist das Projekt? Auftrag, Korpus-Trichter + Seitenbilanz (generiert via corpus_audit), ZBZ-Workflow, Status |
| [pipeline.md](pipeline.md) | Wie ist die Pipeline aufgebaut? Stufen PDF → TEI, Engines (Mistral, Docling, Gemini), TEI-Mapping (DTA + ZBZ), Round-Trip-Sektion |
| [workflow.md](workflow.md) | Wie laeuft der End-to-End-Datenfluss? Datenfluss-Diagramm, Datenformate pro Stufe, Save-Mechanismus im Viewer, Round-Trip vom Edit zur regenerierten TEI, Provenance-Konzept, geplante `_complete.xml`-Variante, Roadmap |
| [quality.md](quality.md) | Wie gut ist die Pipeline? CER-Benchmark (Fidelity-CER als Headline, Werte in quality.md), CER-Methodik (BCa-Bootstrap), TEI-Schema-Validierung, Quality-Proxy, Workflow-Status pro Strom (E66, ersetzt Agent-Screening) |
| [viewer.md](viewer.md) | Wie funktioniert der Pipeline-Viewer? Single-Page-App mit Doc-Liste, Faksimile + Layout-Overlay (OpenSeadragon E58), OCR/TEI-Editor, Edit-Toggle pro Panel (E60), ein "Speichern" -> direkt ins Repo + Mirror (E78/E79), Export ▾ pro Strom |
| [frontend-gaps.md](frontend-gaps.md) | Wie gut erfuellt das Frontend seine User-Stories? Befunde (Bugs/UX/A11y/Performance) je Schweregrad mit `datei:zeile`, Top-10 Hersch, Oekosystem-Vergleich (6 Frontends), Querschnitts-Muster, Methodik-Notizen (2026-06-07) |
| [oekosystem-synthese.md](oekosystem-synthese.md) | Gesamtbild der drei Projekte (zbz / szd-htr / teiCrafter): Setup + Gates + kritischer Pfad, je Projekt Pipeline/Status, ALLE User-Stories, Integration + Bildluecke, Methodik, offene Punkte + Doku-Widersprueche, SSoT-Zuordnung (2026-06-07) |
| [infrastruktur.md](infrastruktur.md) | Wie wird deployed? Azure, Mistral Document AI, Podman, GitLab Uni Zuerich, CI/CD |
| [methodik.md](methodik.md) | Wie arbeiten wir? Epistemische Infrastruktur, Verifikationskaskade, Critical Expert in the Loop, Dreischichtung, operative CLI |
| [decisions.md](decisions.md) | Was ist entschieden? Entscheidungsregister (E-Eintraege bis E90), offene Punkte (O8/O13/O27 an ZBZ, O18 DHCraft; O25/O26 geschlossen), Risiken |
| [journal.md](journal.md) | Was wurde wann gemacht? kompakter Sitzungs-Ueberblick (seit Jan 2026), wiederkehrende Muster |

Konstitution + Commands: [CLAUDE.md](../CLAUDE.md) (Top-Level, projekt-weite Regeln).

---

## Abhaengigkeiten

```
projekt (Vision, Korpus, ZBZ-Kontext)
   │
   ├── pipeline (Stufen: PDF → TEI)
   │      └── infrastruktur (Azure, Podman, CI/CD)
   │
   ├── workflow (End-to-End-Datenfluss + Save + Round-Trip + Provenance)
   │
   ├── quality (CER + TEI-Validierung + Screening)
   │
   ├── viewer (Pipeline-Viewer + Layout-/Transkriptions-Editor)
   │      └── frontend-gaps (Befunde/UX/A11y/Performance, Oekosystem-Vergleich)
   │
   └── methodik (Promptotyping + Verifikationskaskade)

decisions       — cross-cutting, Entscheidungsregister
journal         — chronologisch, kompakter Ueberblick
```

---

## Schluesselkonzepte

| Begriff | Definition | Quelle |
|---|---|---|
| 6-Stage Pipeline | Bilder → OCR → Layout → PAGE-XML → TEI-XML → Evaluation | [pipeline.md](pipeline.md) |
| Dokumenttypen A-D | einspaltig / zweispaltig / Monografie / Spezial | [projekt.md](projekt.md) |
| DTA-Basisformat | TEI-Basisschema mit ZBZ-Anpassungen | [pipeline.md §TEI-Mapping](pipeline.md) |
| `zbz_hersch.rng` (E48/E49, erweitert E68) | projektspezifisches RelaxNG-Schema fuer das ausgelieferte TEI; aktiver Stand = ZBZ-Pruefvorlage (`data/source/zbz-lieferung-2026-06-21/`) + E68-Header-Elemente. Auszeichnungsmodell Inline-GND (E88): `persName`/`orgName`/`bibl` mit `ref="GND:..."` am Erwaehnungsort, kein standOff-Register | [pipeline.md](pipeline.md), [decisions.md §E88](decisions.md) |
| Hybrid Pipeline | Docling Layout + LLM-OCR Text | [pipeline.md](pipeline.md) |
| Unified TEI Pipeline (E32) | Scaffold + Gemini Refinement + Assembly + Validation | [pipeline.md](pipeline.md) |
| Agent-Based Quality Screening (E41, deprecated E66) | 7-Schichten-Pre-Curation, Review-JSON pro Doc — als Qualitaetssignal abgeschafft, weil kein Mensch beteiligt war; Legacy als `_screening_legacy.json` erhalten | [quality.md](quality.md) |
| Workflow-Status pro Strom (E66/E67/E77) | unverifiziert \| in_arbeit \| verifiziert je OCR/Layout/TEI (drei Stufen seit E77), im Manifest mit Provenienz-History, projizierbar in `<revisionDesc>`. Ampel: grau=unverifiziert, gelb=in_arbeit, gruen=verifiziert, rot reserviert | [quality.md](quality.md), [viewer.md](viewer.md) |
| Ampel-Reframing (E67) + 3-Stufen-Kollaps (E77) | "Pipeline-Output EXISTIERT, ist nur unverifiziert" -- daher Status `offen` umbenannt zu `unverifiziert`, rote Default-Lesart aufgegeben (E67); E77 fuehrt `bearbeitet`+`fertig` zu `verifiziert` zusammen, eine Farbe je Stufe | [decisions.md §E77](decisions.md) |
| CER-Benchmark (E51/E70/E85) | End-to-End TEI-vs-TEI, Fidelity-CER als Headline ueber die 25 Referenz-Docs (Werte in quality.md) | [quality.md](quality.md) |
| CER-Statistik (E54) | BCa-Bootstrap-CIs, paired E2E vs OCR-only, HCPR | [quality.md](quality.md) |
| Quality Proxy | Dictionary Hit Rate fuer 285 Docs ohne Ground Truth | [quality.md](quality.md) |
| revisionDesc (E42) | Pipeline + Screening-Status im TEI-Header, reist mit dem Dokument | [pipeline.md](pipeline.md) |
| `output/tei_final/` (E43) | Single Source of Truth der ausgelieferten TEI-Daten | [pipeline.md](pipeline.md) |
| Verifikationskaskade | 4 Stufen: automatisch / kontextuell / visuell / fachlich | [methodik.md](methodik.md) |
| Dreischichtung | Command (Regel) / Artifact (Werkzeug) / Tool (Aufruf) | [methodik.md](methodik.md) |
| Pipeline-Viewer (E56) | Single-Page-App mit Faksimile + OCR + TEI + Layout-/Transkriptions-Editor; ein "Speichern" -> direkt ins Repo + Mirror (E78/E79) | [viewer.md](viewer.md) |
| Hersch Design-System | Anthrazit + Ziegelrot + EB Garamond + Jost, `--h-*` Tokens | [viewer.md](viewer.md) |
| OpenSeadragon-Faksimile (E58) | Faksimile-Renderer im View-Modus mit Pan/Zoom/Rotate, CDN-Bezug | [viewer.md](viewer.md) |
| Mode-Edit-Toggle pro Panel (E60) | Faksimile-Panel "Layout bearbeiten", Text-Panel "Text bearbeiten" (E78), aktiv = anthrazit; keine globale Mode-Leiste; Seitennav im Faksimile-Header | [viewer.md](viewer.md) |
| Viewer = Mistral-Datenstand (E64) | Kein OCR-Quellen-Umschalter im Viewer; Alt-Engines (Gemini/LLM) sind Benchmark-only; Doc-Subbar + Toolbar fusioniert | [viewer.md](viewer.md) |
| Export ▾ (E78) | Einzel-Download pro Strom (Layout/Text/TEI/Manifest) als Dropdown umgesetzt; JSZip-Komplett-/Bulk-Export (E61) weiter geplant, im Code noch nicht eingebunden | [viewer.md](viewer.md) |
| Methode-Seite (E62) | `docs/methode.html` mit Headline-CER, stratifizierten Werten, Limitations, Literatur-Vergleich (statisch) | [viewer.md](viewer.md) |
| End-to-End-Workflow | Datenfluss + Save-Mechanismus + Round-Trip + Provenance-Konzept + geplante `_complete.xml`-Variante | [workflow.md](workflow.md) |
| Round-Trip | User-Edit -> "Speichern" (direkt ins Repo + Mirror, E78/E79) -> `tei_unified --reassemble` -> regenerierte TEI | [workflow.md §3.3](workflow.md), [pipeline.md §Round-Trip](pipeline.md) |
| Transkribus-Export (E81) | Pipeline-PAGE-XML -> Bundle (`transkribus_export`) -> REST-Upload in Collection (`transkribus_upload`); Gegenrichtung zum Round-Trip, Auth via Env-Vars | [pipeline.md §Transkribus-Export](pipeline.md) |
| Provenance pro Objekt (geplant) | `{doc}_provenance.json` mit voller Edit-History (AI + human), Anzeige im Viewer als Drawer | [workflow.md §4.2](workflow.md) |
| `_complete.xml` (geplant) | Selbst-enthaltenes TEI mit `<facsimile>` + `<zone>` + `@facs` + erweitertes `<revisionDesc>` | [workflow.md §5](workflow.md) |

---

## Quick Start

1. **Projekt verstehen:** [projekt.md](projekt.md) — Auftrag, Korpus, Beteiligte
2. **Pipeline verstehen:** [pipeline.md](pipeline.md) — 6 Stufen + Engines + TEI-Mapping
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

*Konsolidiert: 2026-04-27 (25 auf 10 Dokumente); erweitert auf 12: 2026-06-07*
