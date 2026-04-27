---
title: "Methodik: Epistemische Infrastruktur und Promptotyping"
type: knowledge
dependencies: [PROMPTOTYPING, PIPELINE, EDITION]
source: "papers/Paper.md (Workshop-Beitrag DHd/DH, Pollin & Kreyenbuehl)"
---

# Methodik

## Epistemische Infrastruktur

Agent-Zuverlaessigkeit skaliert nicht mit Modellfaehigkeit allein, sondern mit der
Qualitaet der epistemischen Infrastruktur, in der das Modell operiert (belegt durch
SWE-bench vs. SWE-bench Pro: ~60 Prozentpunkte Differenz bei identischen Modellen).

Das Repository ist fuer Agents kein Ablageort, sondern ihr primaeres Interface.
Drei Eigenschaften muessen gegeben sein:

- **Lesbarkeit**: Jedes Artifact hat einen dokumentierten Zweck (CLAUDE.md, Knowledge-Docs). Wartungspflicht: neue Artifacts muessen reflektiert werden.
- **Konsistenz**: Pfade, Benennungen, Datenformate folgen durchgaengigen Konventionen. Was an einem Dokument gelernt wurde, gilt fuer alle.
- **Zustandstransparenz**: Verarbeitungsstand jedes Objekts ist maschinell abfragbar (JSON-Reports, Review-Status im TEI-Header).

## Verifikationskaskade

Vier Stufen, oekonomisch geordnet (guenstig zuerst, teuer zuletzt):

1. **Automatisch** -- Schema-Validierung, Python-Tests. Binaer, schnell, filtert offensichtliche Fehler.
2. **Kontextuell** -- LLM prueft inhaltliche Plausibilitaet gegen Projektkontext. Graduelles Ergebnis (plausibel/fraglich/unplausibel).
3. **Visuell** -- Facsimile-Abgleich durch Vision-faehigen Agent oder LLM-as-Judge. Andere Modalitaet = epistemische Diversitaet.
4. **Fachlich** -- Domaenenexpertise, nicht delegierbar. Editionswissenschaftlerin entscheidet bei Mehrdeutigkeiten.

Operative Wirkung: Jede Stufe reduziert die Fallmenge fuer die naechste. Fachexpertise wird auf ihren hoechstwertigen Einsatzbereich fokussiert (asymmetrische Amplifikation).

## Operativer Zyklus

Fuenf Schritte, iterativ (aligned mit ReAct: Thought-Action-Observation):

1. **Diagnose** -- Agent ermittelt Zustand via Diagnose-Artifacts (Validierungsreport lesen). Handeln auf Befund, nicht auf Vermutung.
2. **Exploration** -- Priorisierung der Korrekturmassnahme nach groesstem Qualitaetsgewinn. Strukturfehler vor Referenzfehlern vor Formatierung.
3. **Ausfuehrung** -- Agent ruft Artifact auf. Bei API-Kosten: --dry-run + Ruecksprache.
4. **Re-Validierung** -- Diagnose erneut ausfuehren. Vorher-Nachher-Vergleich. Jede unverificierte Aenderung ist eine Hypothese, keine Verbesserung.
5. **Eskalation** -- Nach definierter Iterationszahl oder bei Stagnation: Problem an den richtigen Expert in the Loop weiterleiten.

Abbruchbedingungen: Max. 2-3 Zyklen pro Dokument, Stagnationsindikator, Fehlermuster-Erkennung.

## Critical Expert in the Loop

Mehrere Rollen mit getrennten Kompetenzen verhindern zirkulaere Validierung (Anchoring-Effekt, belegt durch Schroeder et al. 2025):

- **DH-Entwickler:in** -- Prozesskonfiguration (Prompts, Scripts, Schwellenwerte). Interagiert nicht mit fachlichen Inhalten.
- **Editionswissenschaftler:in** -- Fachliche Bewertung der Ergebnisse. Hat den Prozess nicht konfiguriert.
- **Projektleitung** -- Priorisierung und Abnahme.

Kernprinzip: Die Person, die ein Ergebnis erzeugt (oder deren Agent es erzeugt hat), ist nicht dieselbe, die es fachlich prueft.

## Agent-Based Quality Screening

Praktische Implementation der Verifikationskaskade auf Korpusebene (285 Dokumente):

- 7 Pruefschichten: Scan-Qualitaet, OCR-Treue, Layout, TEI-Struktur, Referenz-Vergleich, Entity-Plausibilitaet, Gesamtkohaerenz
- Output: Review-JSON pro Dokument mit Layer-Scores und konkreten Findings
- Ergebnis: 85% publikationsreif (242 APPROVED), 15% mit Hinweisen (43 WITH_NOTES)
- Hauptprobleme: Entity-False-Positives bei Gattungsbegriffen (15), OCR-Halluzinationen bei Zeitungslayouts (8), Strukturprobleme (9)

## Dreischichtung: Command / Artifact / Tool

| Schicht | Was | Beispiel |
|---------|-----|----------|
| **Command** | Entscheidungsregel (wann, unter welchen Bedingungen) | "Nach jeder TEI-Korrektur validieren" |
| **Artifact** | Materielles Werkzeug (versioniert, wartbar) | `tei_validator.py`, Entity Index, CLAUDE-COMMANDS.md |
| **Tool** | Konkreter Aufruf durch Agent | `python -m scripts.tei.tei_validator --doc 290` |

Commands ohne Artifacts bleiben abstrakt. Artifacts ohne Commands liegen ungenutzt. Tools ohne Commands sind Ad-hoc-Aktionen. Erst das Zusammenspiel aller drei Schichten erzeugt den zyklischen, qualitaetsgesicherten Arbeitsprozess.

Artifacts sind rueckgekoppelter Output: gleichzeitig Ergebnis des Prozesses und Input fuer den naechsten Zyklus. Die epistemische Infrastruktur waechst reaktiv auf Qualitaetssignale.

## Literatur

- Yang et al. (2024). SWE-agent: Agent-Computer Interfaces. *NeurIPS 2024*. -- Scaffolding > Modellfaehigkeit
- Kamoi et al. (2024). When Can LLMs Actually Correct Their Own Mistakes? *TACL*. -- Selbstkorrektur braucht externen Feedback
- Schroeder, Roy, Kabbara (2025). Just Put a Human in the Loop? *Findings of ACL*. -- Anchoring-Effekt bei LLM-Vorschlaegen
- Yao et al. (2023). ReAct: Synergizing Reasoning and Acting. *ICLR 2023*. -- Thought-Action-Observation-Loop
- He et al. (2026). Speed at the Cost of Quality. *MSR 2026*. -- Geschwindigkeit ohne Infrastruktur erzeugt technische Schulden
- Zhang et al. (2025/2026). Agentic Context Engineering (ACE). arXiv. -- Akkumuliertes Kontextwissen kompensiert Modellfaehigkeit

## Siehe auch

- [PROMPTOTYPING](PROMPTOTYPING.md) -- Operative Werkzeuge und CLI-Referenz
- [PIPELINE](PIPELINE.md) -- Technische Pipeline-Architektur
- [EDITION](EDITION.md) -- Digitale Edition als Verifikationsumgebung
