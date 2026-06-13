---
title: Ökosystem-Synthese — Hersch / SZD / teiCrafter
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-06-07
updated: 2026-06-10
tags: [oekosystem, synthese, zbz-ocr-tei, szd-htr, teicrafter]
---

# Ökosystem-Synthese — Hersch / SZD / teiCrafter

**Was ist das?** Ein verdichtetes Gesamtbild über die drei Editions-Projekte,
erstellt nach vollständiger Lektüre aller Knowledge-Dokumente der drei Repos
(~34 Dateien) + Frontend-Live-Analyse. **Single Source of Truth bleibt jeweils das Heimat-Repo**
(siehe §10); dieses Dokument synthetisiert, dupliziert nicht. Zeitpunktbezogen (2026-06-07);
`datei:zeile`- und Zahl-Angaben vor Nutzung gegen den Code prüfen.

---

## 1. Setup

Drei Repos, eine Methode (Promptotyping). Ziel: zwei unabhängige
HTR/OCR-Pipelines in **einem** verlustfreien Editor (teiCrafter) zusammenführen.

| Repo | Rolle / Gate |
|---|---|
| `ResearchTools/teiCrafter` | Editor/Engine/Annotation (G2), Tests (G1.2/G4), Konverter-Referenz (G1.4b-Vorleistung) |
| `szd-htr` | SZD-Batch-Konverter Page-JSON→TEI (G1.4b) |
| `DHCraft/zbz-ocr-tei` | Frontend-Gap-Analyse ZBZ→teiCrafter, Hersch zuerst |

**Gemeinsame Haltung:** „maschinell erzeugt = unverifiziert bis ein Mensch prüft" → in teiCrafter
als violette `--color-ai`-Markierung sichtbar; in zbz/szd als Workflow-/Review-Status.

**Kritischer Pfad (alle Deliverables auf Platte noch OFFEN, Stand 2026-06-07):**
```
ZBZ-Bild-URL-Schema ─┐
                     ├─> teiCrafter: converter-reference.md + <graphic>-Support
mapping-unabh. Gerüst ┘        └─> szd: pipeline/export_tei.py fertig
```
teiCrafter ist der Engpass.

---

## 2. zbz-ocr-tei — Jeanne-Hersch-Pipeline

- **Auftrag:** Zentralbibliothek Zürich, Auftragnehmer DHCraft, bestätigt 14.02.2026.
  Nachlass der Philosophin Jeanne Hersch.
- **Korpus:** 325 katalogisiert → 289 digitalisiert → **286 PDF** (~4.120 Seiten) → **285 finales TEI**
  (doc 10 unvollständig). 71% FR / 25% DE, 1931–1998, v.a. Journal-Artikel + Sammelbandbeiträge.
- **Lieferziel:** hochwertiger, schema-valider **Datensatz + Kurationswerkzeug**;
  die Edition baut ZBZ stromabwärts (Oxygen/Alma/Swisscovery). Pipeline fertig und geliefert; die fachliche
  Verifikation ist ZBZ-Aufgabe, getrackt über den Workflow-Status (alle Ströme `unverifiziert` als
  Übergabe-Default). ZBZ behält Transkribus als Parallelquelle.
- **6-Stufen-Pipeline:** PDF→PNG (300 dpi) + Gemini-Klassifikation → **Mistral Document AI 2512**
  (Azure) OCR → **Docling 2.75** Layout + Gemini-QA → PAGE-XML/METS (paralleler Export) → **Unified
  TEI** (Scaffold→Gemini-Refinement→Assembly) → Evaluation.
  - **Schlüssel-Klarstellung (E22):** TEI wird DIREKT aus Layout-JSON + OCR-Markdown erzeugt;
    PAGE-XML ist KEIN Zwischenschritt, sondern paralleler Export (für Transkribus/coOCR).
- **TEI:** `type="naegeli"`, RelaxNG `zbz_hersch.rng` (aus ODD). Enthält bereits `<facsimile>`/`<zone>`
  (absolute Pixel-Koordinaten). SoT = `output/tei_final/{doc}_final.xml` (E43); `docs/data/pages/`
  ist generierter Mirror (nie direkt editieren). Pro-Objekt-Manifest trägt Workflow-Status + History.
  **Wichtig: `{id}_final.xml` IST teiCrafters natives Format** → öffnet direkt, Text-Edit ohne Konvertierung.
- **Qualität (E70/E73/E85, SoT):** **Fidelity-CER Median 1,40% / Mean 2,71%** (n=25, BCa-Bootstrap Seed 42).
  Volltext-CER (Mean 18,94%) ist Diagnose, kein Qualitätsmaß (ZBZ-Referenzen sind Teiltranskriptionen).
  Pipeline-Mehrwert vs. reine OCR −9,45 pp (p=0,013, signifikant; E85) — frühere Headline „−14,83 pp" zurückgezogen
  (Trimming-Artefakt). **285/285 schema-valide** (E68). Dictionary Hit Rate Median 97,7% = Schätzung
  (GT nur für 25 Docs; Proxy generalisiert nachweislich nicht, LOOCV-R²<0).
- **Workflow-Status (E66/E67/E77):** je Strom (OCR/Layout/TEI) drei Stufen `unverifiziert | in_arbeit |
    verifiziert`, Ampel grau/gelb/grün, rot reserviert. Stand: **alle 285 in allen Strömen unverifiziert**.

---

## 3. szd-htr — Stefan-Zweig-Nachlass HTR

- **Projekt:** Teilprojekt von *Stefan Zweig Digital*; VLM-HTR aus Faksimiles (Literaturarchiv Salzburg),
  Bild-Hosting GAMS (Uni Graz). Komplett von Claude Code generiert, DHCraft-Projektleitung = Fachentscheider. CC-BY 4.0.
- **Korpus:** **2.107 Objekte, 18.719 Scans, ~23,6 GB.** 4 Sammlungen: lebensdokumente 127 / werke 169
  / aufsatzablage 625 / korrespondenzen 1.186. DE 95,6%. 9 Dokument-Prompt-Gruppen A–I.
- **Pipeline:** TEI-Kontext-Auflösung (Gruppe A–I) → 4-Schicht-Prompt → **Gemini 3.1 Flash Lite** VLM
  (t=0,1, Chunking >20 Bilder) → Quality-Signals/`needs_review` → Modellkonsensus (`verify.py`) →
  Layout-Ensemble (Docling+Surya+Gemini) → **Page-JSON v0.2** → PAGE-XML 2019 + METS/MODS →
  Viewer-Daten. CLI: `python pipeline/export_*.py <obj> -c <collection> [--all|--force|--dry-run]`.
- **Page-JSON v0.2** = JSON-Serialisierung des PAGE-XML-Modells (Dokument→Seiten→Regionen→Text),
  Koordinaten optional (progressive Anreicherung). Schema `schemas/page-json-v0.2.json`.
  Einschränkung: **nur ~25 von ~2.103 Objekten haben Layout-Regionen** → Rest text-only (`<lb>` + Bild).
- **Verifikation — 4 Tiers:** 0 `gt_verified` (Mensch auf 3-Modell-GT) · 1 `approved` (Mensch im Viewer) ·
  2 `agent_verified` (Claude-Vision-Sub-Agent) · 3 needs_review/unreviewed (nur Pipeline). **Stand:
  0 echte `gt_verified`** (Workflow bereit, 15 Objekte definiert) → alle CER-Zahlen sind Schätzungen.
  VLM-`confidence` ist wertlos (immer „high"); Gemini setzt fast nie `[?]`-Marker → marker_density entwertet.
  needs_review-Quote kalibriert 63%→**19,4%**.
- **Evaluation (geschätzt, n=58):** Druck/Korrekturfahne 99,6–99,9%, Typoskript 92–99,9%, Fraktur/Zeitung
  97–99,8%, Handschrift 95–99,4%, Tabellarisch 75–99% (schwächste). Fehlertypen: Fraktur ſ→f, Kurrent-
  Verwechslungen, Halluzination statt `[?]`, Tabellen-Strukturfehler. **Keine echte CER gegen GT.**
- **Architektur-Kniff:** derselbe statische Viewer ist öffentlich read-only UND lokal Editorial Workspace —
  nur ein laufender Server (`/api/status`) schaltet Edit/Approve/Rebuild frei.
- **Besonderheiten:** liefert Daten an DIA-XAI/EQUALIS (PLUS-Grant 2026/27, UC3 Expert-Korrektur);
  Security-Threat-Model abgearbeitet; Stats-Dashboard bewusst ohne CER-Dashboard (nur ~4,5% mit CER).
- **Status:** Transkription ~99% (~2.080/2.107), METS-Export ~2.074, teiCrafter-TEI-Batch 2.030 (0 Fehler);
  Layout nur ~25 Objekte (Voll-Batch ~7 Tage); echte GT fehlt.

---

## 4. teiCrafter — verlustfreier TEI-Editor

- **Zweck:** browserbasierter, **verlustfreier** Editor für beliebiges TEI. Öffnen → Folio-für-Folio
  lesen → im gerenderten Text korrigieren → **byte-identisch** zurückspeichern (außer Editiertem).
  „One workbench, two ways in": deterministischer Editor-Pfad + optionale „New from text (LLM)"-On-Ramp.
- **Werkzeug-Abgrenzung (verbindlich, 2026-06-07):** teiCrafter *bearbeitet* beliebiges TEI (Werkzeug).
  **EditionCrafter** ist eine eigene, unabhängige Linie und *baut ganze Editionen* (Anzeige/Apparat/Publikation);
  der **Editopia-Hersch-Demonstrator ist EditionCrafter v0, NICHT teiCrafter**. Die statischen ZBZ-/SZD-Viewer
  gehören zu den jeweiligen Pipelines, nicht zu teiCrafter. Merksatz: teiCrafter erzeugt/bearbeitet TEI,
  EditionCrafter erzeugt die Edition.
- **Kernmechanik:** Rohstring ist kanonisch, jede Änderung ist ein Offset-Splice darauf, `serialize()`
  byte-identisch (DOM-frei, kein DOMParser/XMLSerializer beim Serialisieren). **Granularität emergiert
  aus dem Dokument:** Wort-Ebene bei `<w xml:id>` (Wenzelsbibel), sonst Zeilen-Ebene (Hersch). Kein
  Projekt-Profil, kein Branching.
- **TEI-Kontrakt (generisch, per local-name):** `<pb>`=Folio, `<lb>`/`<l>`=Zeile, Lesetext→editierbare
  Zellen, `<facsimile>/<surface>/<zone ulx uly lrx lry>`→OpenSeadragon-Overlays, `@facs`=Zeile↔Zone
  bidirektional, `<standOff>/<note target>`=Entitäten/Apparat. Nicht-Interpretiertes bleibt verbatim.
- **Tech:** Client-only SPA, native ES6-Module, kein Build, GitHub Pages aus `/docs`; 9 JS-Dateien;
  OpenSeadragon 5.0.1 (CDN); 6 LLM-Provider (Keys nur im Speicher). 3 Schichten: `tei-document.js`
  (Offset-Kern) → `edition.js` (Folios/Zeilen/Zellen) → `editor-app.js` (UI). Reife: **Research Preview**.
- **Validierung hybrid:** live Well-Formedness + Struktur-Integrität vs. Lade-Baseline; offline RelaxNG
  (TEI All) + Schematron (Python/lxml). MVP-Gate = wohlgeformt ∧ L1-Textfidelity ∧ L3-Counts erhalten;
  L2-Schema zählt nur NEUE Fehler ggü. Input (nicht-gating).
- **Tests:** byte-identischer Round-Trip **294/294** reale Dateien (285 Hersch + 4 SZD + 5 synthetisch);
  Browser-Click-Through bestätigt 2026-06-04 (synthetische Wenzelsbibel). Reale Dateien nur gitignored
  (Lizenz); committet nur synthetisches Material.
- **Design:** Forschungswerkzeug, kein Konsumprodukt — Cream-Flächen, Serif Lesetext / Sans UI / Mono IDs,
  Navy-Header + Gold-Akzent, **Violett `--color-ai` (#6D4AB6) NUR für LLM-Output**. Tokens = einzige
  Quelle, kein Hex in Komponenten. Status dreifach kodiert (Farbe+Icon+Position).

---

## 5. User Stories (alle drei Projekte)

### teiCrafter — EXPLIZIT (`knowledge/user-stories.md`, „As a … I want … so that …")
Status: *Built* / *Browser-check* / *Future*.
- **Editing:** E.1 lokal öffnen ohne Server · E.2 in Folios blättern · E.3 Zell-Rendering wort-/zeilenweise
  (emergent) · E.4 Wort/Zeile in-place korrigieren · E.5 Save ändert nichts Unberührtes (byte-faithful) ·
  E.6 Save-in-place oder Download *(Browser-check)*.
- **Facsimile:** F.1 Zonen + Text↔Zone-Highlight · F.2 echte Bilder mit Deep-Zoom (OpenSeadragon).
- **Validation:** V.1 live Well-Formedness/Integrität · V.2 volle Schema-Validierung *(offline)*.
- **LLM On-Ramp:** L.1 Plaintext→Entwurf-TEI im Editor · L.2 generiertes klar als „unreviewed" (violett) ·
  L.3 API-Key nur im Speicher · L.4 Provider-Wahl.
- **Index/StandOff:** I.1 Person/Org/Event anlegen/umbenennen/löschen · I.2 Mention→Index verlinken
  (`<name ref="#id">`).
- **Future:** FU.1 Apparat-/Kommentar-Note authoring · FU.2 Normdaten-IDs in UI · FU.3 projekt-spezifische
  Formularansichten · FU.4 SZD-Page-JSON→TEI-Konverter · FU.5 sehr große Editionen segmentiert laden.

### zbz-ocr-tei — EXPLIZIT 3 (Viewer, aus frontend-gaps.md), Rest abgeleitet
- US1 *(explizit)* **Projektteam**: OCR/Layout/TEI QA-prüfen, viele Seiten schnell sichten.
- US2 *(explizit)* **ZBZ-Kurator:in**: Layout/Text/TEI editieren + verlässlich speichern (Human-in-the-Loop).
- US3 *(explizit)* **Projektleitung**: Ergebnisse vertrauenswürdig gegenüber ZBZ demonstrieren.
- *(abgeleitet)* DH-Entwickler:in konfiguriert Pipeline/erzeugt Qualitätssignale · Editionswissenschaftler:in
  prüft fachlich + gibt frei (Rollentrennung gegen zirkuläre Validierung) · ZBZ-Bibliothekar:in liefert
  Header-Metadaten aus Alma (O8) · Kurator:in schreibt Korrekturen per „Speichern" zurück → `--reassemble`.

### szd-htr — KEINE explizit; aus Workflow/Personas abgeleitet
- **Experte**: Transkription Seite-für-Seite gegen Faksimile korrigieren; Tier-Status setzen (approved/
  agent_verified/gt_verified); Edits direkt in Pipeline-JSON + commit; Fortschritt am Progress-Balken steuern.
- **Triagierende:r**: nach `needs_review` filtern + Gründe sehen (Aufwand priorisieren).
- **Annotator:in**: reproduzierbares diplomatisches Transkriptionsprotokoll (Inter-Annotator-CER).
- **DH-Forscher:in/Archivar:in**: aggregierte Qualitätsmetriken; METS/MODS+PAGE-XML für GAMS/DH-Stack.
- **Operator**: CLI-Batch (Einzel/Sammlung/`--all`, skip-if-exists, `--dry-run`).
- **Paper-Reviewer**: Vault/Journal/Exports im Public Site verlinkt (Claims ohne Repo-Klon prüfen).

---

## 6. Integration & gemeinsame Konzepte

```
ZBZ:  PDF → Mistral-OCR → Docling-Layout → Unified-TEI → {id}_final.xml ──┐
                                                                          ├─> teiCrafter (Open)
SZD:  Bilder → Gemini-VLM → [Layout] → Page-JSON v0.2 → (export_tei) ─────┘
                                       └─> PAGE-XML / METS (Archiv, nicht Editor)
```
- **ZBZ→Editor: funktioniert HEUTE für Text** (kein Konverter nötig; teiCrafter-Bundle ist doc 100s
  `_final.xml` + standOff-Demo).
- **SZD→Editor: braucht `export_tei.py`** (blockiert auf der Konverter-Referenz).
- **Gemeinsame Bildlücke:** Editor zeigt Faksimile nur mit BEIDEM (imageUrl ∧ surface); imageUrl kommt
  nur aus hartcodiertem Demopfad (kein `<graphic>`-Support). **Fix:** `<graphic url>` pipeline-seitig ins
  `<surface>` schreiben + `facsimile.js` liest `surface.graphic`. Lossless, generalisiert.
- **Status-Mapping:** zbz Workflow-Status ↔ szd 4-Tier-Review ↔ teiCrafter violette AI-Markierung.

---

## 7. Methodik (alle drei)

**Promptotyping** auf **epistemischer Infrastruktur**: Agent-Zuverlässigkeit skaliert mit der Qualität des
Repos als Agent-Interface (Lesbarkeit, Konsistenz, Zustandstransparenz), nicht mit Modellfähigkeit allein.
Kern ist die **Verifikationskaskade** (automatisch → kontextuell → visuell → fachlich): jede Stufe verkleinert
die Fallmenge für die nächste, teure Fachexpertise nur auf Mehrdeutigkeiten. **Critical Expert in the Loop**
trennt Rollen (wer erzeugt ≠ wer prüft) → motivierte zbz E66 (selbstzertifizierendes Agent-Screening
abgeschafft) und teiCrafters „der Mensch entscheidet". **Epistemische Asymmetrie:** LLMs erzeugen Plausibles,
können es aber nicht selbst beurteilen → deterministischer Kern macht keine probabilistischen Aussagen.

---

## 8. Befunde: Frontend-Gaps (Detail → frontend-gaps.md)

Sechs Frontends analysiert; **szd-htr = Referenzimplementierung** (Empty/Error-States, `aria-sort`,
URL-State, lokale Deps, Capability-Detection). Hersch-Top-Risiken: **H1** TEI-XML-Edit kann ganzes
`_final.xml` überschreiben (aus Code abgeleitet, NICHT reproduziert) · **H2** „Gespeichert" lügt bei
Download-Fallback · **H3** Layout-Editor nur mausbedienbar · **H4** keine QA-Seitennavigation (~4.100 Seiten)
· **H5** Modal ohne Fokus-Trap. Stärke: Token-Disziplin nahezu perfekt. **Ökosystem-Muster:** ungehärtete
fetch/Relativpfade → stille 404 auf GitHub Pages (editionCrafter, agentic-pipeline, SZD); A11y interaktiver
Visualisierungen durchgängig schwach; visuelle Inkonsistenz Hersch-Viewer (= EditionCrafter v0)↔teiCrafter.
**Hinweis:** ZBZ-Dateien in teiCrafter testen plus Bild-URL-Schema stehen noch aus.

---

## 9. Offene Punkte / Blocker / Widersprüche

**Blocker / kritischer Pfad:** converter-reference.md + `<graphic>`-Support in teiCrafter fehlen → SZD-Export
wartet; ZBZ-Bild-URL-Schema steht aus (`docs/images/<id>/<id>_p00N.png` + ggf. IIIF-Pendant).

**zbz offen:** M5 fachliche Kuration (855/855 Ströme unverifiziert) · O8 Header-Metadaten aus Alma →
**195/285 Header mit leerem Container-/Journaltitel** (Spec-Konflikt mit Editionsrichtlinien, bewusst E76) ·
O13 redaktionelle Details · O18 multimodale OCR-Korrektur ungetestet · Containerisierung/CI-CD nur Entwurf ·
Faksimiles online nur 4 Demo-Docs · LLM-Varianz ungemessen (`stability: open`).

**szd offen:** 0 echte GT · Layout nur ~25/2.000 · einige API-Fehler bei Werke-Batch.

**teiCrafter offen (Future):** echte IIIF-Tiles · Apparat-/Note-Authoring · Normdaten-IDs · Page-JSON→TEI ·
Raw-XML-Source-View · In-Browser-Full-Validate · segmentiertes Laden großer Editionen.

**Doku-Widersprüche/Veraltetes (nachgeprüft 2026-06-10):**
- zbz: Status-Stufen (E77) und E-Zähler sind in allen Docs nachgezogen (behoben 2026-06-10).
  Weiterhin offen: JSZip-ZIP-Bundle (E61) nicht eingebunden (Einzel-Export vorhanden).
  `data/curated_tei/` ist seit 2026-06-10 korrekt deklariert (vorgesehen fuer von Hand
  verifizierte TEI, derzeit leer; vorher irrefuehrend als Gold-Standard bezeichnet).
- szd: Objektzahlen schwanken dokumentübergreifend (1319…2107; maßgeblich 2.107); Modell-IDs
  („Gemini 3.1 Flash Lite", „Claude Opus 4.6") und Session-Daten in projizierter 2026-Zeitlinie;
  `teicrafter-integration.md` (06/2026) reaktiviert den in Session 21 gelöschten TEI-Konverter-Kontrakt
  (jüngeres Dokument = gültig); README „METS geplant" veraltet (seit Session 25 implementiert).
- teiCrafter: Token-Präfix-Drift in Doku (`--tc-*` veraltet, Code nutzt `--color-*`); 2026-06-04-Audit
  reparierte u.a. die nie definierten `--color-ai`/`--radius-sm` (AI-Violett war still ausgefallen).

---

## 10. Quellen & SSoT-Zuordnung

| Domäne | SSoT |
|---|---|
| Kontrakte, Gates | `teiCrafter/knowledge/integration.md` (kanonisch) |
| zbz Pipeline/Workflow/Qualität/Entscheidungen | `zbz-ocr-tei/knowledge/{pipeline,workflow,quality,decisions,methodik,projekt}.md` |
| zbz Viewer-Funktion / Frontend-Gaps | `zbz-ocr-tei/knowledge/{viewer,frontend-gaps}.md` |
| szd Pipeline/Verifikation/Daten | `szd-htr/knowledge/{data-overview,verification-concept,htr-interchange-format,page-xml-mets-architecture,evaluation-results,annotation-protocol}.md` |
| teiCrafter Spec/Architektur/Stories/Tests | `teiCrafter/knowledge/{specification,architecture,user-stories,testing,design,data}.md` |

Dieses Dokument = Synthese (zeitpunktbezogen). Bei Konflikt gilt der jeweilige Domänen-SSoT.
