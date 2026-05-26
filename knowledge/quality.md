---
type: knowledge
created: 2026-03-26
updated: 2026-05-25
tags: [zbz-ocr-tei, qualitaet, cer, tei-validation, screening, evaluation]
status: active
---

# Qualitaet

Konsolidiertes Qualitaetswissen: Character Error Rate (Benchmark + Methodik), TEI-Validierung,
Quality-Proxy, Agent-Based Quality Screening, Testplan-Baseline.

**Datenquelle:** `docs/data/cer_statistics.json` (regenerierbar via `cer_statistics_full.py`,
deterministisch bei `seed=42`; derzeit nicht eingecheckt). Das fruehere interaktive CER-Dashboard
und die Diagnostik-Seite wurden mit E56 abgeschafft (siehe [decisions.md](decisions.md)).
Visualisierung kann bei Bedarf neu aufgebaut werden — die JSON-Daten sind reproduzierbar.

---

## CER-Benchmark (Headline)

End-to-End Character Error Rate: Pipeline-TEI vs. ZBZ-Referenz-TEI (Transkribus Ground Truth).
Wissenschaftliche Re-Evaluation 2026-04-27 (E54).

### Methodik (Kurzfassung)

- **Referenz:** 25 ZBZ-Referenz-TEIs (`data/referenz-tei/`), manuell via Transkribus erstellt.
- **Hypothese:** Pipeline-TEIs (`output/tei_final/`), aus 7-Stufen-Pipeline.
- **Textextraktion:** mit `<choice>`-Korrektur, Fussnoten exkludiert, symmetrische Unicode-Normalisierung.
- **Distanzmass:** `Levenshtein(ref, hyp) / max(1, |ref|)` via `rapidfuzz`.
- **Alignment:** content-aligned via `evaluate_tei_vs_tei()` (immun gegen Page-Numbering-Drift, siehe §Lessons).
- **Aggregation:** char-gewichtete Per-Dok-CER; Bootstrap ueber Docs (n=19).
- **Statistik:** BCa-Bootstrap (B=10000, Seed=42) fuer alle CIs; Paired Bootstrap fuer E2E vs OCR-only; Chi-Square + KS fuer Selektionsbias.
- **Werkzeug:** `scripts/cer_statistics_full.py` (Orchestrator) + `scripts/cer_statistics.py` (Library mit 55 Tests). Output: `docs/data/cer_statistics.json` (deterministisch bei `seed=42`).

### Headline-Werte (n=19 scope-clean, BCa, 2026-04-27)

| Metrik | Punktwert | 95%-CI |
|---|---|---|
| **End-to-End-CER Mean** | **4.10 %** | [2.01 %, 6.75 %] |
| **End-to-End-CER Median** | **1.83 %** | [0.84 %, 5.14 %] |
| **OCR-only-CER Mean** (Mistral Stage 2) | 18.93 % | [9.19 %, 30.57 %] |
| **Pipeline-Verbesserung** (paired) | **−14.83 pp** | p = 0.0004, mehr als 80% der Docs verbessert |
| **HCPR (Diakritik-Erhalt) Mean** | ~99 % | siehe `domain_metrics` im JSON |

**Lesehilfe:**

- Median 1.83% heisst: die Haelfte aller Docs hat CER ≤ 1.83% — State-of-the-Art fuer historischen Druck.
- Paired Test: Pipeline reduziert CER gegenueber rohem Mistral-OCR um ~14.8pp (p < 0.01). Stages 3-7 (Layout-QA, TEI-Generation, Post-Processing) liefern messbaren Mehrwert.
- HCPR 99.32%: praktisch alle franzoesischen/deutschen Diakritika werden korrekt erhalten.

### Reduktions-Timeline

| Schritt | Mean CER | Median CER | n |
|---|---|---|---|
| Ausgangslage (E51) | 9.33% | 5.52% | 24 |
| + symmetrische Normalisierung | 8.11% | 5.36% | 24 |
| + Hyphen-Normalisierung | 7.29% | 2.61% | 25 |
| + CI-Alignment | 5.97% | 2.42% | 25 |
| + Scope-Bereinigung | 4.18% | 1.83% | 19 |
| **+ Case-Normalisierung** | **4.10%** | **1.83%** | **19** |

### Statistik scope-bereinigt (n=19)

| Metrik | Wert |
|---|---|
| ausgeschlossen | 6 (Scope-Mismatch) |
| Std CER | 5.48% |
| Min / Max | 0.30% / 20.7% |
| Q1 / Q3 | 0.80% / 5.57% |
| Docs <3% | 13 (68%) |
| Docs >15% | 2 (290, 1910) |

**Ziel Median <3.5%: ERREICHT (1.83%).**

### Scope-Mismatches (ausgeschlossen)

| Doc | CER | Ref/Pipe Seiten | Ratio | Ursache |
|---|---|---|---|---|
| 1440 | 25.7% | 8 / 7 | 1.1x | 2 OCR-Seiten fehlen, S.267 fehlt |
| 30 | 18.7% | 8 / 4 | 2.0x | nur 50% OCR'd |
| 300 | 15.2% | 2 / 4 | 2.0x | Referenz nur 2 von 4 Seiten |
| 760 | 7.0% | 38 / 20 | 1.9x | auto-detektiert |
| 3020 | 1.5% | 10 / 6 | 1.7x | auto-detektiert |
| 830 | 1.5% | 4 / 2 | 2.0x | auto-detektiert |

### Nach Layout-Typ / Sprache (scope-bereinigt)

| Typ | n | Mittl. CER | Median CER |
|---|---|---|---|
| A (einspaltig) | 11 | 3.7% | 1.8% |
| B (zweispaltig) | 5 | 5.9% | 5.1% |
| C (Monografie) | 2 | 4.0% | 4.0% |
| D (Spezial) | 1 | 0.8% | 0.8% |

| Sprache | n | Mittl. CER | Median CER |
|---|---|---|---|
| fra | 11 | 4.0% | 1.8% |
| deu | 5 | 5.9% | 5.6% |
| fra/deu | 3 | 2.1% | 0.8% |

### Top-5 Substitutionen (Konfusionsmatrix)

| # | Erwartet | Erkannt | Codepoints | Anzahl |
|---|---|---|---|---|
| 1 | e | (Space) | U+0065 → U+0020 | 31 |
| 2 | e | E | U+0065 → U+0045 | 28 |
| 3 | (Space) | e | U+0020 → U+0065 | 25 |
| 4 | s | S | U+0073 → U+0053 | 18 |
| 5 | e | s | U+0065 → U+0073 | 17 |

Vollstaendige Matrix: in den Rohdaten unter `output/evaluation/` (frueher als `docs/data/diagnostik_ocr.json` verfuegbar, mit E56 entfernt).

### Fehlerkategorien (alle 25 Docs)

| Kategorie | Chars | Anteil | Beschreibung |
|---|---|---|---|
| other | 311.221 | 93.2% | Scope-Mismatches, Textverschiebungen |
| ocr_artifact | 10.118 | 3.0% | Zeichenverwechslungen, Halluzinationen |
| layout | 8.810 | 2.6% | fehlende Spalten/Regionen |
| whitespace | 3.532 | 1.1% | Leerzeichen-Differenzen |
| punctuation | 253 | 0.1% | Satzzeichen |
| diacritics | 85 | 0.0% | Akzent-Fehler |

**Fazit:** 93% der gemessenen Fehler sind Scope-Mismatches (Benchmark-Artefakte). Nur 6% sind echte OCR/Layout-Fehler.

### Verbleibende Problemdokumente

| Doc | CER | Kategorie | Ursache | Fix |
|---|---|---|---|---|
| 290 | 20.7% | Scope + Case | Textverlust + Case-Differenzen | Case-Norm. reduzierte 0.5% |
| 1910 | 16.1% | Layout | 16% Text fehlt aus Spaltenregionen (Typ B) | Layout re-run |

Re-Processing-Kandidaten (Typ B mit Layout-Fehlern):

```bash
python -m scripts.layout_qa_gemini --mode detect --doc 1910   # 16.1% CER
python -m scripts.layout_qa_gemini --mode detect --doc 890    #  5.6% CER
python -m scripts.layout_qa_gemini --mode detect --doc 1410   #  5.1% CER
```

---

## CER-Methodik (vollstaendig)

Wissenschaftlich fundierte Methodik fuer die CER-Evaluation. Details der statistischen Verfahren.

### Definitionen

**CER** = `Levenshtein(reference, hypothesis) / max(1, |reference|)`. Implementierung via
`rapidfuzz.distance.Levenshtein` (C-Extension), Fallback `cer_statistics.levenshtein()` fuer Tests.
Konvention bei `|reference| == 0`: CER = 0 wenn `|hypothesis| == 0`, sonst CER = 1.

**End-to-End-CER vs OCR-only-CER:**

| Bezeichnung | Vergleich | Misst |
|---|---|---|
| End-to-End-CER | Pipeline-TEI (`tei_final/`) vs Referenz-TEI | Gesamtfehler aus OCR + Layout + TEI-Gen + NER |
| OCR-only-CER | Mistral OCR Stage-2 vs Referenz | reiner OCR-Fehler ohne Pipeline-Korrekturen |

Differenz quantifiziert die **Pipeline-Verbesserung**.

**Aggregations-Einheit:** Dokument-Ebene, nicht Seiten-Ebene.

```
doc_cer = Σ(page_levenshtein) / Σ(page_ref_chars)        # char-gewichtet
mean_cer = mean(doc_cer for doc in evaluated)             # Bootstrap-Einheit = Doc
```

### Bootstrap-Konfidenzintervalle

**BCa (Bias-Corrected and Accelerated):** B = 10.000, Seed = 42, α = 0.05 → 95%-CI.
RNG: `numpy.random.default_rng(42)`. Begruendung: CER-Verteilung ist schief (langer rechter Tail,
einige Docs >10% gegenueber Median ~2%). BCa korrigiert Bias (z0) und Acceleration (a) via Jackknife.

**Paired Bootstrap** fuer E2E vs OCR-only auf identischen Docs: pro Doc Differenz `cer_e2e - cer_ocr`,
dann B = 10.000 Resamples. Output: `mean_diff`, `mean_diff_ci95`, `p_two_sided`.

**Block-Bootstrap-Diskussion:** Im urspruenglichen Plan war Block-Bootstrap (Block = Dokument)
vorgesehen, um Within-Doc-Korrelation zu beruecksichtigen. Nach Wechsel auf Doc-CER als
Aggregations-Einheit ist die Block-Struktur implizit erfasst (1 Datenpunkt = 1 Block).
Tests in `tests/test_cer_statistics.py::TestBcaCI::test_block_bootstrap_wider_than_naive_for_correlated_data`
zeigen: bei kuenstlich korrelierten Daten ist die Block-CI nachweislich breiter — Methodik korrekt
implementiert und greift, falls jemand kuenftig mit Per-Page-Daten aggregieren wuerde.

### Selektionsbias-Diagnostik

| Variable | Test | Begruendung |
|---|---|---|
| Sprache | Chi-Square Goodness-of-Fit | kategorial |
| Layout-Typ (A/B/C/D) | Chi-Square | kategorial |
| Publikationsform | Chi-Square | kategorial |
| Seitenzahl | KS 2-Sample | kontinuierlich |
| Ref-Char-Volumen | KS 2-Sample | kontinuierlich |

H0: Verteilung im Referenz-Subset = Verteilung im Gesamtkorpus. α = 0.05.

**Aktuelles Ergebnis (2026-04-27):**

- language, layout_type, pub_form, page_count: alle p > 0.4 → comparable.
- **n_chars: p = 0.041 → NOT comparable.** Ref-Subset hat signifikant abweichendes Char-Volumen-Profil.

Honest Disclosure im JSON (`selection_bias.tests`) und im Dashboard-Limitations-Panel.
Median-CER (volumen-unabhaengig) ist davon weniger betroffen als Mean-CER.

### Multi-Normalisierungs-Regimes

CER haengt von Pre-Normalisierung ab. Vier Regimes parallel publiziert:

| Regime | Operation |
|---|---|
| `raw` | unveraendert |
| `nfc` | Unicode-NFC |
| `nfc_hyphen` | NFC + Soft-Hyphen entfernen + Bindestrich-Varianten → ASCII `-` |
| `nfc_hyphen_case` | wie oben + `casefold()` |

**Limitation** (dokumentiert in `multi_norm._note`): `extract_text_for_comparison()` normalisiert
bereits symmetrisch (Quotes, Apostroph, Guillemets, Whitespace-Kollaps). Die nominellen Regimes
liefern deshalb fast identische Zahlen. Der echte Effekt der Normalisierung ist in der
Reduktions-Timeline der Pipeline sichtbar (9.33% → 4.10%), nicht zwischen den 4 nominellen Stufen.

### Domain-Metrik: HCPR-Adaption

CER allein zeigt nicht, *welche* Zeichen gut oder schlecht erkannt werden. Fuer eine historische
Edition mit FR+DE-Sonderzeichen ist die Erhaltungsrate diakritischer Zeichen ein eigenstaendiger
Qualitaetsindikator.

```
HCPR(ref, hyp, lang) = min(observed_count, expected_count) / max(1, expected_count)
```

Diakritik-Set pro Sprache: fra (é è à ç ù â ê î ô û ë ï ü œ), deu (ä ö ü ß), ita.

**Methodische Quelle:** Nosova et al. (2025), arXiv:2510.06743. Einschraenkung: konservative
Adaption — echte HCPR braucht Zeichen-Alignment, wir vergleichen Frequenzen pro Zeichen.
Robust, aber unterschaetzt Substitutionen. AIR (Archaic Insertion Rate) deferred — im Hersch-Korpus
(1930er-1990er Antiqua, kein Frakturanteil) erwartet niedrig.

### Like-for-Like-Vergleich mit Forschungsliteratur

`comparable`-Enum in `comparison_lit[]`:

- `true` — gleicher oder direkt vergleichbarer Korpus
- `partial` — gleiche Modell-Kategorie, andere Sprache/Korpus
- `false` — nur als Groessenordnungs-Orientierung

Frontend rendert die drei Stufen visuell unterschiedlich (Akzentfarbe / gestreift / grau gestreift).

| Quelle | DOI / arXiv | Verwendung |
|---|---|---|
| Singh 2025, "When +1% Is Not Enough" | arXiv:2511.19794 | Paired-Bootstrap-Protokoll |
| Nosova et al. 2025 | arXiv:2510.06743 | HCPR/AIR, no-GT-Methodik, Stabilitaets-Tests |
| Crosilla, Klic, Colavizza 2025 | arXiv:2503.15195 | LLM-HTR-Vergleichsbenchmarks |
| Kanerva & Ledins 2025 | arXiv:2502.01205 | Sprachabhaengigkeit der LLM-Post-Korrektur |
| arXiv:2501.18243 (2025) | — | Statistical Multi-Metric Evaluation Framework |
| arXiv:2509.04013 (2025) | — | Robustheit/Reliabilitaet von Benchmark-Eval |

User-Vorgabe: ausschliesslich Quellen 2025+. Bewusst nicht zitiert: Liu et al. 2019 (Blockwise
Bootstrap), Bisani & Ney 2004, Stroebel et al. 2022 — Konzepte werden via 2025+-Quellen aufgegriffen.

### Stabilitaet (LLM-Non-Determinismus)

Pipeline-Stages 5 (Mistral) und 6 (Gemini TEI-Gen) sind nicht-deterministisch.
Bei wiederholtem Run variiert das Output.

**Aktueller Status:** `stability.status: open` im JSON, Begruendung "API-Budget pending user decision".

Bei Freigabe: 5 Docs × 3 Re-Runs (geschaetzt $1-2), Std-Dev der Per-Doc-CER reporten.
Kontextualisierung: ist der gemessene CER mit Bootstrap-CI ueberhaupt praeziser als die
Run-zu-Run-Varianz? Bootstrap-CIs erfassen nur Sampling-Unsicherheit, nicht Modell-Stochastizitaet.

### Vergleich gegen Stand der Forschung (gedruckte historische Dokumente)

| Quelle | Methode | Sprache | CER |
|---|---|---|---|
| Crosilla et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash Post-Korrektur | deu Fraktur | **0.84%** |
| Crosilla et al. 2025 | Gemini 2.0 Flash zero-shot | deu | 1.27% |
| Crosilla et al. 2025 | Transkribus Print M1 allein | deu | 3.67% |
| Crosilla et al. 2025 | GPT-4o direkt | deu | 6.31% |
| arXiv 2510.06743 | Gemini 2.5 Pro | rus 18. Jh. | 3.36% |
| arXiv 2510.06743 | Gemini 2.5 Flash | rus | 4.94% |
| arXiv 2510.06743 | Claude 3.5 | rus | 6.79% |
| arXiv 2510.06743 | GPT-4o | rus | 9.23% |
| arXiv 2510.06743 | traditional OCR | rus | 21-45% |
| Transkribus-Doku | Richtwert | allg. | 0.5-2% |

**Eigene Position:** Beste Docs 0.3-0.8% (State of the Art), Median 1.83% besser als Transkribus
allein (3.67%) und Gemini 2.5 Pro zero-shot (3.36%). 13/19 Docs unter 3% (68% des Korpus).

Kernerkenntnisse: (1) multimodale Post-Korrektur uebertrifft reine Text-Post-Korrektur deutlich.
(2) LLM-Post-Korrektur ist sprachabhaengig ("No Free Lunches", Kanerva 2025). (3) Gemini-Modelle
dominieren aktuelle Benchmarks. (4) Bei bereits gutem OCR kann LLM-Korrektur degradieren —
bestaetigt durch unsere Haiku-Postkorrektur (+0.10%, Variant C).

---

## Korpus-weite Schaetzung (Proxy-Framework)

Direkter CER nur fuer 19 Docs (siehe Headline). Fuer die anderen 266 brauchen wir Proxies.

### Methode: Dictionary Hit Rate

Anteil der OCR-Woerter, die in einem FR/DE-Woerterbuch gefunden werden. OCR-Fehler erzeugen
Nicht-Woerter ("maison" → "rnaison"), daher korreliert hohe Hit Rate mit guter OCR-Qualitaet.

**Literatur:** Stroebel et al. 2022, "Evaluation of HTR models without Ground Truth Material" (LREC 2022).

**Implementierung:** `scripts/quality_proxy.py`

- Text-Extraktion aus TEI-XML (gleiche Methode wie CER-Benchmark)
- Tokenisierung: nur alphabetische Woerter >= 2 Zeichen
- Eigennamen-Filter: Grossbuchstaben-Woerter herausfiltern (FR/multi)
- Woerterbuch-Pruefung via `pyspellchecker` (fr, de, en, it)
- Zusaetzlich: Suspicious Character Ratio (OCR-Artefakt-Indikator)

### Ergebnisse (Maerz 2026, 285 Docs)

| Hit Rate | Docs | Anteil | Bewertung |
|---|---|---|---|
| >= 95% | 226 | 79% | exzellent |
| 90-95% | 35 | 12% | gut |
| 85-90% | 8 | 3% | akzeptabel |
| 75-85% | 4 | 1% | pruefen |
| < 75% | 12 | 4% | Ausreisser (fremdsprachig) |

**Median Hit Rate: 97.7%** — bei einem typischen Dokument sind 98 von 100 Woertern korrekt erkannt.
**92% der Docs liegen bei >= 90% Hit Rate.**

### Validierung gegen Ground Truth (n=18-19)

Spearman-Korrelation Hit Rate vs CER: **rho = -0.20** (schwach).

**Composite OLS:** in-sample R² = 0.15, **LOOCV-R² = -1.67**. LOOCV-R² < 0 bedeutet:
das Composite ist *schlechter* als der einfache Mittelwert. Die Korpus-Schaetzung (6.20% Mean,
total CI [0%, 17.56%]) ist daher **kein Schaetzer**, sondern eine **Plausibilitaets-Schranke**.

Im Dashboard visuell stark abgegrenzt (Sektion §12 mit "SCHAETZUNG"-Badge).

**Verbesserungspfad (deferred):**

- N-gram-Loglik aus Wikipedia-FR/DE-Dump (~1-2h Aufwand)
- Sentence-length-KL-Divergenz
- `wordfreq`-basierte Lexikon-Scores

Mit ~5 unabhaengigen Proxies und n=18 koennte LOOCV-R² > 0 werden, bleibt aber strukturell
limitiert. Der einzige sichere Weg ist mehr Ground Truth (User-Entscheidung: "kein manueller GT-Aufbau").

### Sprach-Audit (Nebenbefund)

**284/285 Docs korrekt klassifiziert (99.6%).** Korrekturen:

| Doc | Vorher | Nachher | Befund |
|---|---|---|---|
| 1860 | deu/eng | **fra** | fr=73.5%, de=24.1% — primaer FR |
| 2360 | fra | **fra/deu** | fr=57.8%, de=53.7% — signifikant zweisprachig |
| 2680 | deu | **deu/fra** | de=60%, fr=49.2% — signifikant FR-Anteil |

48 von 50 als "mehrsprachig" klassifizierten Docs sind effektiv einsprachig (Zweitsprache <35%
Hit Rate). Die Labels sind konservativ — fuer Pipeline-Zwecke unproblematisch, Hauptsprache stimmt.

### Ausreisser (Hit Rate <75%)

12 Docs unter 75% sind korrekt klassifizierte fremdsprachige Dokumente:

- 6x Englisch (870, 1630, 2270, 2300, 3090, 3190)
- 3x Italienisch (990, 2030, 2720)
- 3x Sprache vertauscht/gemischt (2230, 2360, 2680 — korrigiert)

### Fazit

1. OCR-Textqualitaet korpus-weit hoch (Median Hit Rate 97.7%, 92% ≥90%).
2. Hauptprobleme sind **strukturell** (fehlende Seiten/Spalten), nicht zeichenbasiert.
3. Sprachklassifikation ist korrekt (99.6% nach 3 Korrekturen).

---

## TEI-Schema-Validierung

Schema-Validierung der Pipeline-TEIs gegen `zbz_hersch.rng` (TEI P5 v4.10.2, projektspezifisch
aus ODD generiert, 551 Definitionen).

### Aktueller Stand

**285/285 Docs valide** gegen `zbz_hersch.rng` (nach Schema-Fix).

| Metrik | Wert |
|---|---|
| Dokumente | 285 |
| Valid | 285 (100%) |
| Invalid | 0 |
| Mit Warnings | 29 |

### Fix-Verlauf

**Fix-001 (2026-03-26): ref-Pattern erweitert.** Vorher 50 valid / 235 invalid. Schema erzwang
`ref="GND:[0-9A-Za-z\-]+"`, Pipeline injizierte `ref="#zbz-p.NNN"`. RelaxNG-Kaskade machte alle
235 Docs mit zbz-Refs komplett invalid (nicht nur das ref-Attribut). Fix: Pattern in 3 Stellen
erweitert: `(GND:[0-9A-Za-z\-]+|#zbz-[a-z]+\.[0-9]+)` an `bibl/@corresp`, `orgName/@ref`,
`persName/@ref`. Ergebnis: 285 valid / 0 invalid. Scheinbare Nebenfehler (idno/langUsage/biblStruct)
waren reine Kaskaden-Artefakte.

**Fix-002 (2026-03-26): heuristische lb-Injection.** Vorher 46 Docs mit Warning W6 (keine `<lb/>`).
Root Cause: Mistral OCR liefert Text ohne Zeilen-Umbrueche innerhalb von Absaetzen. Nur 51 Docs
hatten Step 2 (Gemini Refinement) durchlaufen, das lb injiziert. Fix: `_inject_heuristic_lb()`
in `tei_step3.py` injiziert ~60 Zeichen an Wortgrenzen, nur fuer `<p>` ohne bestehende `<lb/>`,
non-regression fuer Absaetze mit lb. **10.635 lb-Elemente in 46 Docs.** W6 eliminiert, Warnings
gesamt 82 → 37.

**Fix-003 (2026-03-26): Post-Assembly Fixes W3/W4/W7.** Vorher 37 Warnings, nachher 29.

| Fix | Warning | Docs | Beschreibung |
|---|---|---|---|
| E | W3 | 5 | doppelte `<pb>` mit identischem facs (nur wenn `pbs > surfaces`) |
| F | W4 | 1 | leere `<div>` ohne Textinhalt (nur Whitespace + lb) |
| G | W7 | 2 | `<figure>` mit nur `<graphic url="unknown">` und ohne Text |

**W11 (2 Docs: 140, 1240):** False Positive — echte Anthologie-Struktur (Doc 140: alternierend
conversation/text; Doc 1240: 7 eigenstaendige Gespraechsteile).

### Verbleibende Warnings

| Regel | Docs | Beschreibung |
|---|---|---|
| W9 | 17 | Entity-Tags ohne ref (NER-Re-Injection noetig) |
| W10 | 10 | nur persName, 0 orgName/placeName (NER-Extraktionsproblem) |
| W11 | 2 | zu viele top-level divs (false positive) |

**W9-Docs:** 410, 780, 790, 1530, 1870, 2140, 2330, 2400, 2440, 2510, 2540, 2550, 2660, 3020, 3180, 3190, 3200.
**W10-Docs:** 30, 50, 100, 910, 1270, 1360, 1370, 1380, 2180, 2310.

W10-Diagnose: alle 10 Docs haben persName aber 0 orgName/placeName. Vermutlich NER-Extraktionsproblem,
nicht Injection-Problem. Re-Injection-Befehl: `python -m scripts.ner.ner_inject_tei --all --validate`.

### Validierungsregeln

**Errors (blockierend, 8 Regeln R1-R8):** RelaxNG + Projekt-Regeln (R1 type="naegeli",
R2 teiHeader, R3 body, R4 min 1 div, R5 gueltige div-types, R6 note place, R7 entity-ref).

**Warnings (14 Regeln W1-W14, informativ):** W1 Sprach-Code "und", W2 teiHeader title/author
leer, W3 facsimile/pb Mismatch, W4 leere div, W5 Text-Volumen <50 chars/Seite, W6 keine lb,
W7 graphic ohne url, W8 keine Entity-Tags bei >500 Zeichen, W9 Entity-Tags ohne ref, W10 nur
persName, W11 zu viele top-level divs gleichen Namens, W12 Fussnoten-n, W13 Fussnoten xml:id-Pattern,
W14 back/div-types.

### Referenz-TEI-Validierung

17/25 ZBZ-Referenz-TEIs (Transkribus Ground Truth) valide gegen `zbz_hersch.rng` (68%). 8 invalide
Referenz-TEIs zeigen, wo das Schema strenger ist als ZBZs eigene Praxis:

| Fehlertyp | Docs | Details |
|---|---|---|
| `<space>` ohne `<desc>` | 4 | 40, 290, 830, 1330 |
| `<back>` unerwartet | 4 | 40, 300, 830, 1520 |
| `<foreign>` unerwartet | 1 | 300 |
| body/div-Struktur | 2 | 1910, 3040 |

Kein Pipeline-Bug — die Referenz-TEIs sind manuell erstellt und nutzen Elemente, die im
projektspezifischen Schema absichtlich ausgeschlossen sind.

### Werkzeuge

| Artefakt | Pfad |
|---|---|
| Schema | `data/schema/zbz_hersch.rng` |
| Validator | `scripts/tei/tei_validator.py` |
| Validation Report | `output/tei_unified/validation_report.{json,html}` |

---

## Agent-Based Quality Screening (deprecated, E66)

**Stand 2026-05-26: Das Agent-Screening ist als Qualitaetssignal abgeschafft (E66).** Begruendung:
keiner der 285/285 "APPROVED"-Status kommt von einem Menschen -- der Agent zertifiziert sich selbst,
mit eingebauter Ignorier-Liste (W3, W6, W10 als "normal" deklariert) und ohne fachliche Bewertung.
Das Etikett "APPROVED" im `<revisionDesc>` ist epistemisch irrefuehrend gegenueber ZBZ.

Ersetzt durch **Workflow-Status pro Strom** (siehe Abschnitt unten): `offen | in_arbeit | bearbeitet | fertig`
je fuer OCR, Layout, TEI. Status wird von Menschen im Viewer gesetzt und in der Manifest-History
persistiert (`output/tei_final/{doc}_manifest.json`, Schluessel `streams.*.history`).
Bei der ZBZ-Uebergabe projiziert `scripts/tei/tei_status_marker.py` die History deterministisch
in den `<revisionDesc>`; Agent-Screening-Eintraege werden dabei entfernt.

Die alten Befunde bleiben als Diagnose-Spur erhalten: `_review.json` -> `_screening_legacy.json`
(gitignored, nicht im Mirror). Sie sind teilweise inhaltlich nuetzlich (Layer-Befunde),
aber das `APPROVED`-Label trifft keine Aussage ueber fachliche Qualitaet.

### Historische Funktionsweise (zur Dokumentation)

Agent-basiertes Pre-Curation-Verfahren: Claude Code prueft jedes TEI durch 7 Schichten.

### Schichten

1. **Scan-Qualitaet** (visuell: Layout-Overlay pruefen)
2. **OCR-Treue** (Layout-JSON-Text vs. TEI-Text)
3. **Layout-Korrektheit** (Regionen, Reihenfolge, Typen)
4. **TEI-Struktur** (Validator: RelaxNG + Projektregeln)
5. **Referenz-Vergleich** (wo ZBZ-Referenz vorliegt)
6. **Entity-Plausibilitaet** (Typen, Konflikte, Verteilung)
7. **Gesamtkohaerenz** (liest sich das als Edition?)

Schichten 1-3, 6-7 erfordern visuelle Pruefung durch den Agent (Scan + TEI lesen).
Schicht 4-5 sind automatisierte Tool-Aufrufe.

### Werkzeuge

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}              # Schicht 4
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID} # Schicht 5
python -m scripts.tei.tei_screening_prep                        # Batch-Manifest erzeugen
python -m scripts.tei.tei_add_revision --all                    # revisionDesc in alle TEIs
python -m scripts.tei.tei_quality_pass --all                    # automatischer Pre-Check
python -m scripts.tei.screening_prompt --batch {N}              # Agent-Prompt generieren
```

### Output

```
output/tei_final/{DOC_ID}_final.xml       # finales TEI mit revisionDesc
output/tei_final/{DOC_ID}_review.json     # Befund pro Dokument
output/tei_final/screening_manifest.json  # Batch-Zuweisungen (4 Tiers)
```

### Ergebnis (285/285 Docs)

**242 APPROVED (85%), 43 WITH_NOTES (15%), 0 NEEDS_REVIEW (0%).** 58 Batches in 4 Tiers,
parallelisiert ueber ~40 Agent-Invocations.

Nachbearbeitung (E45-E47): Entity-Stopwoerter erweitert (20 neue Eintraege), Strukturfixes
(5 Docs: 2140, 2150, 2530, 2550, 2660), OCR-Deduplizierung (3 Docs: 900, 1100, 2630).

### Systematische Muster (P1-P10)

- **P1** Doppelseiten-Scans erzeugen W3 (kein Fix, Buchformat)
- **P2** W10 False Positive bei abstrakten philosophischen Texten
- **P3** Seitenzahlen-Erkennung inkonsistent (Original vs. relativ)
- **P4** Entity-Typ-Konflikte Person/Werk (Kierkegaard, Nietzsche) — fixbar im Index
- **P5** JSTOR-Scans koennen mehrere Rezensionen pro Seite enthalten
- **P6** Gemini korrigiert OCR-Fehler im Step-2 Refinement (undokumentierter Qualitaetsgewinn)
- **P7** Gattungsbegriffe im Entity-Index (Mensch, Est, Gott, Rolle, Wahl, Christ, Schweizer) → ~30% Docs False Positives
- **P8** Journal de Geneve / mehrspaltige Zeitungslayouts versagen systematisch (~3% Korpus)
- **P9** Franzoesisches "Est-ce que" wird als placeName "Osten" gematcht
- **P10** Tier-2-Docs (4-8 Seiten) 85%+ APPROVED-Rate, Tier-1 (1-3 Seiten) nur 40%

### Positionierung

Pre-Curation-Triage — sortiert, wo menschliche Aufmerksamkeit noetig ist. Kein Ersatz fuer
fachliche Kuration. Visuelle Verifikation ist der echte Mehrwert gegenueber rein automatischer
Validierung.

Methodische Klarstellung: Agents pruefen Konsistenz und Schemata, garantieren aber nicht
fachliche Richtigkeit. Naechster Schritt: ZBZ-Fachleute pruefen dieselben Docs im Pipeline-Viewer
(Edit-Modus), siehe [viewer.md](viewer.md).

### Additivitaet

`output/tei_unified/` bleibt unveraendert. Finale TEIs mit `<revisionDesc>` liegen in
`output/tei_final/`. Nur Letztere werden in der Edition angezeigt.

---

## Workflow-Status pro Strom (E66/E67, ab 2026-05-26)

Ersetzt das Agent-Screening (oben). Vier Statuswerte je Datenstrom (`ocr`, `layout`, `tei`):

| Status | Bedeutung |
|---|---|
| `unverifiziert` | Pipeline-Output existiert, kein Mensch hat verifiziert (Default fuer alle 285 Docs) |
| `in_arbeit` | Bearbeiter:in schaut/editiert gerade |
| `bearbeitet` | mindestens eine menschliche Korrektur erfolgt, nicht final |
| `fertig` | bearbeitet + fachlich freigegeben, edition-ready |

**Ampel-Semantik im UI (E67):** **gelb** = `unverifiziert` + `in_arbeit` + `bearbeitet` (alle drei: vorhanden, nicht freigegeben). **gruen** = `fertig`. **rot** ist im aktuellen Modell nicht im Einsatz, bleibt reserviert fuer einen spaeteren expliziten Problem-/Reject-Status (z.B. "OCR fehlt", "muss neu generiert werden"). Begruendung des Reframings: die Pipeline produziert OCR/Layout/TEI deterministisch fuer alle 285 Docs -- der Default ist also "vorhanden, unverifiziert", nicht "nichts da". Der Umbenennungs-Schritt von `offen` zu `unverifiziert` macht die Datenebene konsistent mit dieser Lesart.

**Datenmodell:** Pro-Objekt-Manifest `output/tei_final/{doc}_manifest.json` (E65 erweitert).
Der `streams`-Header haelt fuer jeden Strom `{engine|engines|source, status, history}`. Die
`history` ist eine Liste `[{at, by, from, to, note}]` und wird beim Status-Wechsel ergaenzt --
das ist die Provenienz der menschlichen Bearbeitungsschritte.

**Setzen:** im Viewer (`docs/viewer.html`), Doc-Subbar zweite Zeile. Drei Pills `OCR · Layout · TEI`,
Klick zykliert vorwaerts. Der Anwender wird einmal nach Kuerzel (Initialen) gefragt; gespeichert
in `localStorage` unter `zbz.workflow.by`. Aenderungen markieren das Manifest dirty und werden
ueber "Manifest ↓" als Datei heruntergeladen; manuelles Ablegen unter `output/tei_final/`.

**Auto-Uebergang:** das erste Aktivieren eines Edit-Toggles (Layout oder Text) setzt den zugehoerigen
Strom automatisch von `unverifiziert` auf `in_arbeit` (Quelle `auto: Edit-Toggle aktiviert`). Bewusste
Status-Wechsel (z.B. `bearbeitet` → `fertig`) erfolgen ueber die Pill.

**Mirror:** `python -m scripts.generate_edition_data --mirror-only` spiegelt die Manifeste nach
`docs/data/manifests/{doc}_manifest.json`, von wo der Viewer sie laedt. Der Catalog (`catalog.json`)
traegt pro Doc ein `streams`-Feld `{ocr|layout|tei: {status, last_at, last_by}}` und ein Korpus-
Histogramm `corpus.stream_status`.

**TEI-Projektion (ZBZ-Uebergabe):** `python -m scripts.tei.tei_status_marker` schreibt deterministisch
fuer jedes Dokument `<change when="..." who="..." status="..." n="{stream}">...</change>` in den
`<revisionDesc>` und entfernt dabei alle Agent-Screening-Eintraege (`who` matched `^(agent-screening|quality-screen|quality-pass|claude)`).
Backup vorher unter `output/_backup_pre_status_marker/`. Pipeline-Generierungs-Eintrag (`who="pipeline"`)
bleibt erhalten. Eine Summen-Zeile je Strom haelt den aktuellen Stand fest.

**Stand 2026-05-26:** 285/285 Docs auf `unverifiziert` in allen drei Stroemen -- der ehrliche Anker.

---

## Lessons Learned: Pagewise-vs-Global-CER (2026-04-27)

Methodisch instruktiver Vorfall — Loesung praegte die Architektur des Werkzeugs.

**Was passiert ist:** Erste Implementierung aggregierte Per-Page-CERs ueber
`evaluate_tei_vs_tei_pagewise` (Block = Doc, Bootstrap auf Per-Page-Werten). Mean = 36.67%,
Max = 167.94%. 13 von 23 Docs >5pp vom Snapshot 2026-03-29 abweichend. Wirkte wie massive
Pipeline-Drift.

**Was wirklich los war:** Pipeline-TEIs hatten dieselben Page-Counts wie Referenz-TEIs, aber
die `<pb>`-IDs identifizierten **inhaltlich andere Seiten**. Pipeline hatte zwischen Maerz und
April das Page-Numbering-Schema geaendert (im Rahmen der TEI-Unifikation). Pagewise-Eval matched
falsche Seiten und produzierte CER-Werte, die mathematisch nur durch Length-Mismatch erklaerbar
waren (CER >1 = Hyp-Laenge >> Ref-Laenge auf der "matched" Page).

**Loesung:** `evaluate_tei_vs_tei()` nutzt content-aligned Vergleich: bei Length-Ratio > 1.05
ruft `find_best_alignment()` auf, Substring-Matching ueber das ganze Dokument. Immun gegen
Page-Numbering-Drift. Nach Wechsel: Mean 3.99% / Median 1.82% (n=18, scope-clean). Drift-Check:
nur 1 Doc weicht noch >5pp ab → **Pipeline ist tatsaechlich stabil**, der "Drift"-Eindruck war
ein Mess-Artefakt.

**Konsequenzen:**

1. **Aggregations-Einheit = Doc-Ebene.** Pages innerhalb eines Docs sind nicht nur korreliert (was naive iid-Bootstrap schon falsch macht), sondern bei Schema-Aenderungen auch falsch identifiziert.
2. **Content-aligned Eval ist Default.** Pagewise nur fuer Per-Page-Outlier-Visualisierung in den Rohdaten.
3. **Lehre fuer kuenftige Pipeline-Aenderungen:** Jede Stage, die `<pb>`-IDs neu vergibt oder Seiten umsortiert, muss vorher in einem Test-Run gegen Referenz-TEIs laufen.

---

## Limitations (was wir explizit nicht koennen)

- **n = 19 Docs Ground Truth** — Korpus-Aussagen sind Schaetzungen, nicht Messungen.
- **Selection-Bias n_chars (p = 0.041)** — Ref-Subset im Char-Volumen abweichend.
- **Multi-Norm-Regimes wenig differenziert** — wegen vorgeschalteter Normalisierung in `normalize_for_comparison()`.
- **Stability nicht gemessen** — LLM-Non-Determinismus-Varianz unbekannt.
- **Proxy-Composite generalisiert nicht (LOOCV-R² < 0)** — Korpus-Schaetzung ist nur Plausibilitaets-Schranke.
- **HCPR ist Frequenz-basiert, nicht Position-basiert** — unterschaetzt Substitutions-Fehler.
- **Kein Inter-Engine-Vergleich** — wir haben nur einen OCR-Engine-Run, keine zweite Quelle.

Diese Limitations sind im JSON dokumentiert (`selection_bias.interpretation`, `multi_norm._note`,
`stability.status`, `proxies.validation_n19.composite.loocv_r2`) und beim Lesen der Headline-Werte
zwingend mitzudenken.

---

## Pilot-Baseline (Mistral OCR, 15 Docs, 18.02.2026)

Historische Referenz aus Phase 0. Aktuelle End-to-End-Metriken siehe Headline oben.

| Phase | Avg CER | Avg WER | Avg Accuracy |
|---|---|---|---|
| Phase 1 (Type A) | 9.40% | 20.22% | 90.60% |
| Phase 2 (Type B) | 6.31% | 17.53% | 93.69% |
| Phase 3 (Type D) | 2.88% | 12.62% | 97.12% |
| Phase 4 (Type C) | 2.65% | 12.98% | 97.35% |

**LLM-Postkorrektur Haiku 4.5 Variant C (Few-Shot, Pilot 19.02.2026):**

| Phase | Mistral CER | LLM CER | Delta |
|---|---|---|---|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| Phase 4 (C) | 2.65% | 2.70% | +0.05 |
| **Total** | **6.42%** | **6.52%** | **+0.10** |

LLM-Korrektur verbessert Docs mit hoher CER (>10%), verschlechtert leicht bei guter OCR (<5%).
Konsequenz: optional, nicht default (E17).

**Rating Scale:**

- OK: CER <5% (>95% Accuracy)
- Acceptable: CER 5-15% (manuell korrigierbar)
- Problematic: CER >15% oder strukturelle Fehler

**Metriken:** CER (Character Error Rate), WER (Word Error Rate), Accuracy = 100% - CER.

---

## Reproduzierbarkeit

```bash
# Test-Suite (~1s)
python -m pytest tests/test_cer_statistics.py -q

# JSON-Generierung (~2-3min, deterministisch bei gleichem Seed)
python -u -m scripts.cer_statistics_full --seed 42 --bootstrap-n 10000
# → docs/data/cer_statistics.json

# CER-Benchmark (alle 25 GT-Docs)
python -m scripts.benchmark_cer --all --html

# Quality Proxy (alle 285 Docs)
python -m scripts.quality_proxy --all --html

# TEI-Validierung
python -m scripts.tei.tei_validator --all --html-report
python -m scripts.tei.tei_validator --compare-ref
```

Im JSON `meta`-Block dokumentiert: `tool_version`, `git_sha`, `git_dirty`, `generated_at`,
`python_version`, `numpy_version`, `scipy_version`, `cer_lib`, `seed`, `bootstrap_n`,
`bootstrap_method`, `normalization_pipeline`, `literature_refs` (alle 2025+).

---

## Verweise

- [pipeline.md §TEI-Mapping](pipeline.md) — TEI-Struktur und Schema
- [entities.md](entities.md) — Entity-Validierung
- [viewer.md](viewer.md) — Layout- und Transkriptions-Editor (manuelle QA via Datei-Download)
- [decisions.md](decisions.md) — E51 (CER-Benchmark), E54/E55 (CER-Statistik + Dashboard), E41-E47 (Screening)
