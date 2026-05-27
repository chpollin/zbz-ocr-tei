---
title: "Methodik: Epistemische Infrastruktur und Promptotyping"
type: knowledge
created: 2026-03-15
updated: 2026-05-25
dependencies: [pipeline, viewer]
source: "papers/Paper.md (Workshop-Beitrag DHd/DH, Pollin & Kreyenbuehl)"
---

# Methodik

Epistemische Infrastruktur, Verifikationskaskade, Critical Expert in the Loop und der operative
Promptotyping-Zyklus. Vereinigt die fruehere `METHODIK.md` und `PROMPTOTYPING.md`.

---

## Epistemische Infrastruktur

Agent-Zuverlaessigkeit skaliert nicht mit Modellfaehigkeit allein, sondern mit der Qualitaet der
epistemischen Infrastruktur, in der das Modell operiert (belegt durch SWE-bench vs. SWE-bench Pro:
~60 Prozentpunkte Differenz bei identischen Modellen).

Das Repository ist fuer Agents kein Ablageort, sondern ihr primaeres Interface. Drei
Eigenschaften muessen gegeben sein:

- **Lesbarkeit:** Jedes Artifact hat einen dokumentierten Zweck ([CLAUDE.md](../CLAUDE.md), Knowledge-Docs). Wartungspflicht: neue Artifacts muessen reflektiert werden.
- **Konsistenz:** Pfade, Benennungen, Datenformate folgen durchgaengigen Konventionen. Was an einem Dokument gelernt wurde, gilt fuer alle.
- **Zustandstransparenz:** Verarbeitungsstand jedes Objekts ist maschinell abfragbar (JSON-Reports, `<revisionDesc>` im TEI-Header).

---

## Verifikationskaskade

Vier Stufen, oekonomisch geordnet (guenstig zuerst, teuer zuletzt):

1. **Automatisch** — Schema-Validierung, Python-Tests. Binaer, schnell, filtert offensichtliche Fehler.
2. **Kontextuell** — LLM prueft inhaltliche Plausibilitaet gegen Projektkontext. Graduelles Ergebnis (plausibel/fraglich/unplausibel).
3. **Visuell** — Faksimile-Abgleich durch Vision-faehigen Agent oder LLM-as-Judge. Andere Modalitaet = epistemische Diversitaet.
4. **Fachlich** — Domaenenexpertise, nicht delegierbar. Editionswissenschaftlerin entscheidet bei Mehrdeutigkeiten.

Operative Wirkung: Jede Stufe reduziert die Fallmenge fuer die naechste. Fachexpertise wird auf
ihren hoechstwertigen Einsatzbereich fokussiert (asymmetrische Amplifikation).

---

## Operativer Zyklus (Promptotyping)

Fuenf Schritte, iterativ (aligned mit ReAct: Thought-Action-Observation):

1. **Diagnose** — Agent ermittelt Zustand via Diagnose-Artifacts (Validierungsreport lesen). Handeln auf Befund, nicht auf Vermutung.
2. **Exploration** — Priorisierung der Korrekturmassnahme nach groesstem Qualitaetsgewinn. Strukturfehler vor Referenzfehlern vor Formatierung.
3. **Ausfuehrung** — Agent ruft Artifact auf. Bei API-Kosten: `--dry-run` + Ruecksprache.
4. **Re-Validierung** — Diagnose erneut ausfuehren. Vorher-Nachher-Vergleich. Jede unverifizierte Aenderung ist eine Hypothese, keine Verbesserung.
5. **Eskalation** — Nach definierter Iterationszahl oder bei Stagnation: Problem an den richtigen Expert in the Loop weiterleiten.

**Abbruchbedingungen:** max. 2-3 Zyklen pro Dokument, Stagnationsindikator, Fehlermuster-Erkennung.

---

## Critical Expert in the Loop

Mehrere Rollen mit getrennten Kompetenzen verhindern zirkulaere Validierung (Anchoring-Effekt,
belegt durch Schroeder et al. 2025):

- **DH-Entwickler:in** — Prozesskonfiguration (Prompts, Skripte, Schwellenwerte). Interagiert nicht mit fachlichen Inhalten.
- **Editionswissenschaftler:in** — fachliche Bewertung der Ergebnisse. Hat den Prozess nicht konfiguriert.
- **Projektleitung** — Priorisierung und Abnahme.

**Kernprinzip:** Die Person, die ein Ergebnis erzeugt (oder deren Agent es erzeugt hat), ist nicht
dieselbe, die es fachlich prueft.

---

## Dreischichtung: Command / Artifact / Tool

| Schicht | Was | Beispiel |
|---|---|---|
| **Command** | Entscheidungsregel (wann, unter welchen Bedingungen) | "Nach jeder TEI-Korrektur validieren" |
| **Artifact** | materielles Werkzeug (versioniert, wartbar) | `tei_validator.py`, Entity Index, [CLAUDE.md](../CLAUDE.md) |
| **Tool** | konkreter Aufruf durch den Agent | `python -m scripts.tei.tei_validator --doc 290` |

Commands ohne Artifacts bleiben abstrakt. Artifacts ohne Commands liegen ungenutzt. Tools ohne
Commands sind Ad-hoc-Aktionen. Erst das Zusammenspiel aller drei Schichten erzeugt den zyklischen,
qualitaetsgesicherten Arbeitsprozess.

Artifacts sind rueckgekoppelter Output: gleichzeitig Ergebnis des Prozesses und Input fuer den
naechsten Zyklus. Die epistemische Infrastruktur waechst reaktiv auf Qualitaetssignale.

---

## Qualitaetssicherung: vom Agent-Screening zum Workflow-Status (E66)

Urspruenglich war hier ein agentenbasiertes 7-Schichten-Screening angesiedelt (285 Docs:
242 APPROVED / 43 WITH_NOTES). Es ist mit **E66 abgeschafft** — kein Mensch hatte die „APPROVED"
vergeben, der Agent zertifizierte sich selbst mit eingebauter Ignorier-Liste; das Etikett war
gegenueber ZBZ irrefuehrend.

Ersatz: **menschgesetzter Workflow-Status pro Strom** (`unverifiziert | in_arbeit | bearbeitet | fertig`
je OCR/Layout/TEI), gesetzt im Viewer, mit Provenienz-History im Pro-Objekt-Manifest und Projektion
in den `<revisionDesc>`. Die Verifikationskaskade bleibt das Prinzip; nur die *fachliche* Stufe ist
jetzt explizit menschlich statt agentisch. Details: [quality.md §Workflow-Status](quality.md).

---

## Operative Werkzeuge (CLI)

CLI-Operationen entlang der Pipeline-Stufen. Jede Operation produziert oder transformiert ein
Wissensartefakt und erzeugt maschinenlesbare Qualitaetssignale.

Die vollstaendige CLI-Referenz steht in der projekt-internen [CLAUDE.md](../CLAUDE.md) §Commands.
Die untenstehende Liste ist die methodisch geordnete Auswahl (Diagnose → Korrektur → Re-Validierung).

### 1. Diagnose — Zustand ermitteln

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}            # TEI-Validierung
python -m scripts.tei.tei_validator --all --html-report        # Korpus-Report
python -m scripts.tei.tei_validator --compare-ref              # Referenz-Vergleich (11 Docs)
python -m scripts.ner.ner_evaluate --doc {DOC_ID}              # NER-Abdeckung
python -m scripts.eval.evaluate_ocr --all                           # OCR-Metriken
python -m scripts.eval.quality_proxy --all --html                   # Quality Proxy (Hit Rate)
python -m scripts.eval.completeness_check --html                    # Vollstaendigkeits-Check (Seiten)
python -m scripts.eval.benchmark_cer --all --html                   # CER-Benchmark (25 GT-Docs)
python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000  # wiss. CER-Statistik
python -m pytest tests/test_cer_statistics.py -q               # 55 Tests fuer Statistik-Library
```

Output: `docs/data/cer_statistics.json` (deterministisch, das frueher daneben existierende
HTML-Dashboard wurde mit E56 abgeschafft — Daten weiterhin als JSON verfuegbar).

### 2. Textschicht verbessern

```bash
python scripts/ocr/ocr_pipeline.py -i data/scans/{DOC_ID}.pdf -e mistral   # Basis-OCR
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --variant B         # Gemini multimodal
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --dry-run           # Vorschau
```

### 3. Layout

```bash
python -m scripts.layout.run_layout_analysis --doc {DOC_ID}                    # Docling
python -m scripts.layout.layout_qa_gemini --doc {DOC_ID}                       # Gemini QA
python -m scripts.layout.layout_qa_gemini --mode detect --doc {DOC_ID}         # Neudetektion
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare     # Overlay
```

### 4. TEI erzeugen

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                        # Standard (3 Stufen)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1               # nur Scaffold (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble           # Re-Assembly (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                # alles neu (inkl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run              # Prompt-Vorschau
python -m scripts.tei.tei_unified --all --reassemble --ner              # Korpus Re-Assembly
```

### 5. Entitaeten

```bash
python -m scripts.ner.ner_extract --doc {DOC_ID}                        # Extraktion
python -m scripts.ner.wikidata_linker --doc {DOC_ID}                    # Wikidata
python -m scripts.ner.ner_inject_tei --doc {DOC_ID} --validate          # Injektion
python -m scripts.ner.entity_index --merge-all                          # Index zusammenfuehren
python -m scripts.ner.entity_index --stats                              # Statistiken
```

### 6. Validierung (Qualitaetsgate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # Einzeldokument
python -m scripts.tei.tei_validator --all --report                      # JSON-Report
python -m scripts.tei.tei_validator --all --html-report                 # HTML-Report
```

### 7. Workflow-Status (ersetzt Agent-Screening, E66)

Das Agent-Screening ist abgeschafft. Status wird von Menschen im Viewer gesetzt;
die CLI deckt Validierung und Status-Projektion ab:

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # RelaxNG + Projektregeln
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}        # gegen ZBZ-Referenz
python -m scripts.tei.tei_add_revision --all                            # revisionDesc schreiben
python -m scripts.tei.tei_status_marker                                 # Workflow-History -> revisionDesc (ZBZ-Uebergabe)
```

Output: `output/tei_final/{DOC_ID}_final.xml` + `{DOC_ID}_manifest.json` (Workflow-Status + History).

### 8. Visuelle Artefakte

```bash
python scripts/edition/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300            # Seitenbilder
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare     # Layout-Overlay
```

---

## Konventionen

- Dokument-IDs folgen dem Muster `{DOC_ID}` (z.B. 2310, 2530, 1440).
- Outputs landen in `output/`-Unterverzeichnissen (gitignored, ausser `data/tei_curated/`).
- `--dry-run` steht bei allen API-nutzenden Tools zur Verfuegung. Vor kostenpflichtigen Batch-Operationen verwenden.
- `--force` ueberschreibt gecachte Ergebnisse. Nur sinnvoll bei tatsaechlichen Upstream-Aenderungen.
- `--reassemble` wendet alle Fixes an ohne Gemini-Calls (Step 2 aus Cache).

---

## Literatur

- Yang et al. (2024). *SWE-agent: Agent-Computer Interfaces.* NeurIPS 2024. — Scaffolding > Modellfaehigkeit
- Kamoi et al. (2024). *When Can LLMs Actually Correct Their Own Mistakes?* TACL. — Selbstkorrektur braucht externen Feedback
- Schroeder, Roy, Kabbara (2025). *Just Put a Human in the Loop?* Findings of ACL. — Anchoring-Effekt bei LLM-Vorschlaegen
- Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting.* ICLR 2023. — Thought-Action-Observation-Loop
- He et al. (2026). *Speed at the Cost of Quality.* MSR 2026. — Geschwindigkeit ohne Infrastruktur erzeugt technische Schulden
- Zhang et al. (2025/2026). *Agentic Context Engineering (ACE).* arXiv. — akkumuliertes Kontextwissen kompensiert Modellfaehigkeit

---

## Verweise

- [pipeline.md](pipeline.md) — technische Pipeline-Architektur
- [viewer.md](viewer.md) — Viewer als Verifikationsumgebung
- [quality.md](quality.md) — Qualitaetsmetriken und Screening
- [CLAUDE.md](../CLAUDE.md) — Projekt-Regeln, vollstaendige CLI-Referenz
