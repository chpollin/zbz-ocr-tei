---
type: knowledge
created: 2026-04-27
updated: 2026-04-27
tags: [zbz-ocr-tei, evaluation, cer, methodik, statistics, bootstrap]
status: active
---

# CER-Methodik

Wissenschaftlich fundierte Methodik fuer die Character-Error-Rate-Evaluation
der ZBZ-OCR-TEI-Pipeline (Jeanne-Hersch-Edition).

**Dependencies:** [CER-BENCHMARK](CER-BENCHMARK.md) (Ergebnisse), [TESTPLAN](TESTPLAN.md)
(Metriken-Definitionen), [QUALITY-PROXY](QUALITY-PROXY.md) (Korpus-weite Proxies).

**Verwandte Implementierung:**
- `scripts/cer_statistics.py` (Library: BCa-Bootstrap, paired-bootstrap, Selektionsbias)
- `scripts/cer_statistics_full.py` (Orchestrator: produziert `docs/data/cer_statistics.json`)
- `tests/test_cer_statistics.py` (55 Unit-Tests, alle gruen)
- `docs/infrastruktur/cer.html` (interaktives Dashboard)

---

## 1. Forschungsfrage

Wie hoch ist die Transkriptionsqualitaet der ZBZ-OCR-TEI-Pipeline auf dem
Hersch-Korpus, **mit quantifizierter Unsicherheit, ehrlich kommunizierten
Limitierungen und like-for-like Einbettung in den Stand der Forschung 2025+**?

Was wir absichtlich **nicht** beanspruchen:
- Direkte CER-Messung fuer alle 285 Korpus-Dokumente. Wir haben Ground Truth
  nur fuer 25 (Subset n=18 nach Pipeline-Filterung); der Rest wird ueber
  validierte Proxies (siehe §9) **geschaetzt**, nicht gemessen.
- Aussagen zur Stabilitaet bei wiederholten Pipeline-Runs (`stability.status: open`,
  siehe §10).

---

## 2. Definitionen

### 2.1 Character Error Rate (CER)

```
CER = Levenshtein(reference, hypothesis) / max(1, |reference|)
```

- Levenshtein-Distanz: minimale Anzahl von Einzelzeichen-Edits (Insertion,
  Deletion, Substitution), die `reference` in `hypothesis` ueberfuehren.
- Implementierung via `rapidfuzz.distance.Levenshtein` (C-Extension; ~1000x
  schneller als reine Python-Loesung); Fallback `cer_statistics.levenshtein()`
  fuer Tests.
- Konvention bei `|reference| == 0`: CER = 0 wenn `|hypothesis| == 0`,
  sonst CER = 1.

### 2.2 End-to-End-CER vs OCR-only-CER

Die Pipeline hat zwei Stufen, deren CER-Anteile separat zu interpretieren sind:

| Bezeichnung | Vergleich | Misst |
|---|---|---|
| **End-to-End-CER** | Pipeline-TEI (`tei_final/`) vs ZBZ-Referenz-TEI | Gesamtfehler aus OCR + Layout + TEI-Generation + NER |
| **OCR-only-CER** | Mistral OCR Stage-2-Output vs ZBZ-Referenz-Text | Reiner OCR-Fehler ohne Pipeline-Korrekturen |

Beide werden parallel publiziert; die Differenz quantifiziert die **Pipeline-Verbesserung**.

### 2.3 Aggregations-Einheit (kritisch!)

Wir aggregieren auf der **Dokumenten-Ebene**, nicht auf der Seiten-Ebene:

```
doc_cer = Σ (page_levenshtein) / Σ (page_ref_chars)        # char-gewichtet
mean_cer = mean(doc_cer for doc in evaluated)               # Bootstrap-Einheit = Doc
```

**Begruendung** — siehe §6 (Lessons Learned, Pagewise-Drift-Vorfall vom 2026-04-27).

---

## 3. Bootstrap-Konfidenzintervalle

### 3.1 BCa (Bias-Corrected and Accelerated)

Wir verwenden **BCa-Bootstrap** statt naivem Perzentil-Bootstrap, weil die
CER-Verteilung schief ist (langer rechter Tail, einige Docs mit > 10 % CER
gegenueber dem Median bei ~2 %). BCa korrigiert sowohl Bias (`z0`) als auch
Acceleration (`a`) via Jackknife auf Block-Ebene.

**Parameter:**
- B = 10 000 Resamples
- Seed = 42 (deterministisch, im JSON `meta.seed` dokumentiert)
- α = 0.05 → 95 %-CI
- RNG: `numpy.random.default_rng(42)`

**Methodische Quelle (2025+):**
> Singh, A. (2025). *When +1% Is Not Enough: A Paired Bootstrap Protocol for
> Evaluating Small Improvements*. arXiv:2511.19794.

Singh fordert explizit: Seed-Fixierung auf Python- *und* Framework-Ebene,
Per-Seed-Metric-Logging, Reproduzierbarkeit auf Standard-Hardware. Wir folgen
diesem Protokoll.

### 3.2 Paired Bootstrap

Fuer den Vergleich End-to-End-CER vs OCR-only-CER (auf den gleichen Docs)
nutzen wir **paired bootstrap**: pro Doc die Differenz `cer_e2e - cer_ocr`,
dann B = 10 000 Resamples mit Zuruecklegen aus den n=18 Differenzen.

Output:
- `mean_diff` (Punktwert)
- `mean_diff_ci95` (95 %-Perzentil-CI)
- `p_two_sided` (Anteil Resamples, die das Vorzeichen wechseln, × 2)

### 3.3 Block-Bootstrap-Diskussion (warum doch nicht im Endprodukt)

Im urspruenglichen Plan (siehe `CLAUDES-WORKING-SESSION.md` Forschungsplan v2)
war **Blockwise Bootstrap mit Block = Dokument** vorgesehen, um die
Within-Doc-Korrelation der Per-Page-CERs zu beruecksichtigen.

In der Implementierung haben wir festgestellt: nach Wechsel auf
**Doc-CER als Aggregations-Einheit** (siehe §6) ist die Block-Struktur
implizit erfasst — jeder Datenpunkt repraesentiert genau einen Block.
Block-Bootstrap reduziert sich damit auf normalen Bootstrap ueber n = Docs.

Tests in `tests/test_cer_statistics.py::TestBcaCI::test_block_bootstrap_wider_than_naive_for_correlated_data`
zeigen: bei kuenstlich konstruierten korrelierten Daten ist die Block-CI
**nachweislich breiter** als die naive iid-CI — die Methodik ist also korrekt
implementiert und wuerde greifen, falls jemand zukuenftig mit Per-Page-Daten
aggregieren wollte.

---

## 4. Selektionsbias-Diagnostik

### 4.1 Problem

Die ZBZ hat 25 von 285 Korpus-Dokumenten als Referenz transkribiert (in
Transkribus). Diese Auswahl ist **nicht zufaellig** — die ZBZ hat aus
editorischen Erwaegungen waehlen muessen. Frage: ist dieses Subset
repraesentativ fuer den Gesamtkorpus, oder verzerrt?

### 4.2 Tests

Pro Strata-Variable:

| Variable | Test | Begruendung |
|---|---|---|
| Sprache | Chi-Square Goodness-of-Fit | kategorial |
| Layout-Typ (A/B/C/D) | Chi-Square | kategorial |
| Publikationsform | Chi-Square | kategorial |
| Seitenzahl | Kolmogorov-Smirnov 2-Sample | kontinuierlich |
| Ref-Char-Volumen | Kolmogorov-Smirnov 2-Sample | kontinuierlich |

H0: Verteilung im Referenz-Subset = Verteilung im Gesamtkorpus.
α = 0.05 → wenn p > 0.05: Subset gilt als "comparable", sonst geflaggt.

Implementierung: `cer_statistics.chi_square_categorical()` und
`cer_statistics.ks_continuous()`. Nutzt `scipy.stats` falls verfuegbar,
sonst eigene Wilson-Hilferty-/Numerical-Recipes-Approximationen
(getestet in `tests/test_cer_statistics.py::TestChiSquare`/`TestKS`).

### 4.3 Aktuelles Ergebnis

Aktuell (Stand 2026-04-27):
- language, layout_type, pub_form, page_count: alle p > 0.4 → comparable.
- **n_chars: p = 0.041 → NOT comparable.** Das Referenz-Subset hat ein
  signifikant abweichendes Char-Volumen-Profil. Honest disclosure im JSON
  (`selection_bias.tests`) und im Dashboard-Limitations-Panel.

**Konsequenz:** alle korpus-weiten Aussagen, die auf Char-Volumen sensitiv
sind, sind zusaetzlich limitiert. Median-CER (volumen-unabhaengig) ist davon
weniger betroffen als Mean-CER.

---

## 5. Multi-Normalisierungs-Regimes

CER ist nicht eindeutig — sie haengt davon ab, *welche* Normalisierung vorher
auf beide Seiten des Vergleichs angewandt wurde. Wir publizieren CER unter
vier Regimes:

| Regime | Was wird gemacht |
|---|---|
| `raw` | unveraendert (Identitaet) |
| `nfc` | Unicode-NFC-Normalisierung |
| `nfc_hyphen` | NFC + Soft-Hyphen entfernen + alle Bindestrich-Varianten → ASCII '-' |
| `nfc_hyphen_case` | wie oben + `casefold()` |

**Wichtige Limitation** (transparent dokumentiert in `multi_norm._note`):
Die Eingabe-Texte aus `extract_text_for_comparison()` werden bereits durch
`normalize_for_comparison()` symmetrisch vorbehandelt (Quotes, Apostroph,
Guillemets → ASCII; Whitespace-Kollaps). Die nominellen Regimes liefern
deshalb fast identische Zahlen. Der **echte** Effekt der Normalisierung
ist in der Reduktions-Timeline der Pipeline-Entwicklung sichtbar
(9.33 % → 4.18 %, siehe [CER-BENCHMARK](CER-BENCHMARK.md) §Reduktions-Timeline),
nicht zwischen den vier nominellen Stufen.

**Verbesserung fuer naechste Iteration:** Pre-normalize-Hook in
`extract_text_for_comparison()` wahlweise abschaltbar, um den `raw`-Regime
wirklich roh zu sehen.

---

## 6. Lessons Learned: Pagewise-vs-Global-CER (2026-04-27)

Am 2026-04-27 trat ein methodisch instruktiver Vorfall auf, der hier
dokumentiert wird, weil seine Loesung die Architektur des Werkzeugs gepraegt hat.

### 6.1 Was passiert ist

Die erste Implementierung hat Per-Page-CERs ueber `evaluate_tei_vs_tei_pagewise`
aggregiert (Block = Doc, Bootstrap auf Per-Page-Werten). Ergebnis:
- Mean = 36.67 %, Max = 167.94 %.
- 13 von 23 Docs wichen > 5 pp vom Snapshot 2026-03-29 ab.

Das wirkte wie eine massive Pipeline-Drift seit Maerz.

### 6.2 Was wirklich los war

Diagnostischer Spike auf Doc 830 + 1330 zeigte:
- Pipeline-TEIs hatten dieselben Page-Counts wie die Referenz-TEIs.
- Aber die `<pb>`-IDs identifizierten **inhaltlich andere Seiten**: Page 2
  in der neuen Pipeline-TEI entsprach Page 4 in der Referenz, etc.
- Die Pipeline hatte zwischen Maerz und April das Page-Numbering-Schema
  geaendert (vermutlich im Rahmen der TEI-Unifikation).

Pagewise-Eval matched dadurch falsche Seiten und produzierte CER-Werte,
die mathematisch nur durch Length-Mismatch erklaerbar waren (CER > 1
heisst: Hypothese-Laenge >> Referenz-Laenge auf der "matched" Page).

### 6.3 Wie es geloest wurde

`evaluate_tei_vs_tei()` (im Gegensatz zu `evaluate_tei_vs_tei_pagewise()`)
nutzt **content-aligned** Vergleich: bei Length-Ratio > 1.05 ruft die
Funktion `find_best_alignment()` auf, das Substring-Matching ueber das
ganze Dokument macht. Das ist immun gegen Page-Numbering-Drift.

Nach Wechsel auf `evaluate_tei_vs_tei`:
- Mean (n=18, scope-clean): 3.99 %
- Median: 1.82 %
- Drift-Check: nur 1 Doc weicht noch > 5 pp vom Snapshot ab → **Pipeline
  ist tatsaechlich stabil**, der "Drift"-Eindruck war ein Mess-Artefakt.

### 6.4 Methodische Konsequenzen

1. **Aggregations-Einheit ist die Doc-Ebene**, nicht die Page-Ebene. Pages
   innerhalb eines Docs sind nicht nur korreliert (was naive iid-Bootstrap
   schon falsch macht), sondern bei Schema-Aenderungen auch **falsch
   identifiziert**. Doc-Ebene ist robust dagegen.

2. **Content-aligned Eval ist Default**, Pagewise nur fuer Per-Page-Outlier-
   Visualisierung im Dashboard. Im Code: `cer_statistics_full.py` nutzt
   `evaluate_tei_vs_tei` als Quelle der Wahrheit.

3. **Drift-Check eingebaut**: `cer_statistics_full.py` vergleicht bei jedem
   Run die aktuellen Per-Doc-CERs gegen den letzten persistierten Snapshot
   (`docs/data/diagnostik_ocr.json`). Status `in_sync` / `minor` / `stale`
   wird im JSON `drift_check` publiziert. Wenn `stale`: Snapshot oder
   Pipeline hat sich geaendert, manuelle Diagnose noetig.

4. **Lehre fuer kuenftige Pipeline-Aenderungen**: jede Stage, die `<pb>`-IDs
   neu vergibt oder Seiten umsortiert, muss vorher in einem Test-Run gegen
   die Referenz-TEIs laufen, sonst kann das Eval-Werkzeug die Aenderung
   nicht von einem Qualitaets-Verlust unterscheiden.

---

## 7. Domain-Metrik: Diakritik-Erhaltungsrate (HCPR-Adaption)

CER allein zeigt nicht, *welche* Zeichen gut oder schlecht erkannt werden.
Fuer eine historische Edition mit franzoesischen und deutschen Sonderzeichen
ist die **Erhaltungsrate diakritischer Zeichen** ein eigenstaendiger
Qualitaetsindikator.

### 7.1 Definition (HCPR-Adaption)

```
HCPR(ref, hyp, lang) = min(observed_count, expected_count) / max(1, expected_count)
```

wobei `expected_count` = Anzahl Diakritika in `ref`, `observed_count` =
Anzahl Diakritika in `hyp`. Wertebereich [0, 1].

Diakritik-Set pro Sprache:
- `fra`: é è à ç ù â ê î ô û ë ï ü œ + Grossbuchstaben
- `deu`: ä ö ü ß + Grossbuchstaben
- `ita`: à è é ì ò ù + Grossbuchstaben

Einschraenkung: das ist eine **konservative Adaption** der echten HCPR
nach Nosova (s.u.); echte HCPR braucht Zeichen-Alignment, wir vergleichen
Frequenzen pro Zeichen — robust, aber unterschaetzt Substitutionen
(z.B. ä → a wird durch eine Insertion eines anderen ä an anderer Stelle
kompensiert).

**Methodische Quelle (2025+):**
> Nosova, E. et al. (2025). *Evaluating LLMs for Historical Document OCR:
> A Methodological Framework for Digital Humanities*. arXiv:2510.06743.

Nosova fuehrt HCPR (Historical Character Preservation Rate) und AIR
(Archaic Insertion Rate) als domain-spezifische Metriken fuer historische
LLM-OCR ein.

### 7.2 AIR (Archaic Insertion Rate) — deferred

AIR misst Halluzinationen archaischer Zeichen, die im Referenz-Text *nicht*
vorkommen (z.B. ß-Insertion in franzoesischem Text). Im Hersch-Korpus
(1930er–1990er Antiqua, kein Frakturanteil) erwartet niedrig. Im JSON
`domain_metrics.air.status: deferred`. Bei Bedarf in 30 min nachruestbar.

---

## 8. Like-for-Like-Vergleich mit Forschungsliteratur

CER-Werte sind nur dann zwischen Studien vergleichbar, wenn folgende
Dimensionen uebereinstimmen:

1. Korpus (Sprache, Schrift, Epoche, Domain)
2. Eval-Protokoll (Normalisierung, Alignment, Footnote-Behandlung)
3. Modell-Kategorie (Transkribus / LLM / hybrid)

Wir kennzeichnen jeden Vergleich im JSON `comparison_lit[]` mit einem
`comparable`-Enum:

- `true` — gleicher oder direkt vergleichbarer Korpus
- `partial` — gleiche Modell-Kategorie, aber andere Sprache/Korpus
- `false` — nur als Groessenordnungs-Orientierung

Das Frontend (`docs/infrastruktur/cer.html`) rendert die drei Stufen
visuell unterschiedlich (Akzentfarbe / gestreift / grau gestreift).

### 8.1 Aktuell zitierte Quellen (alle 2025+, User-Vorgabe)

| Quelle | DOI / arXiv | Verwendung |
|---|---|---|
| Singh 2025, "When +1% Is Not Enough" | arXiv:2511.19794 | Paired-Bootstrap-Protokoll |
| Nosova et al. 2025 | arXiv:2510.06743 | HCPR/AIR, no-GT-Methodik, Stabilitaets-Tests |
| Crosilla, Klic, Colavizza 2025 | arXiv:2503.15195 | LLM-HTR-Vergleichsbenchmarks |
| Kanerva & Ledins 2025 | arXiv:2502.01205 | Sprachabhaengigkeit der LLM-Post-Korrektur |
| arXiv:2501.18243 (2025) | — | Statistical Multi-Metric Evaluation Framework |
| arXiv:2509.04013 (2025) | — | Robustheit/Reliabilitaet von Benchmark-Eval |

Bewusst **nicht** zitiert (Vor-2025): Liu et al. 2019 (Blockwise Bootstrap),
Bisani & Ney 2004 (ASR-Bootstrap-CIs), Stroebel et al. 2022 (HTR ohne GT).
Methodisch greifen wir die Konzepte ueber die 2025+-Quellen (Singh, Nosova) auf.

---

## 9. Korpus-weite Schaetzung (Proxy-Framework)

Wir messen CER nur fuer 18 Docs. Fuer die anderen 267 brauchen wir Proxies.

### 9.1 Verfuegbare Proxies

| Proxy | Quelle | Verfuegbarkeit |
|---|---|---|
| Dictionary Hit Rate | `scripts/quality_proxy.py` | alle 285 Docs |
| Suspicious Char Ratio | `scripts/quality_proxy.py` | alle 285 Docs |
| OOV-Rate | abgeleitet aus Hit Rate | alle 285 Docs |
| Layout-Confidence-Score | `summary_gemini.json` | alle 285 Docs |
| Diakritik-Frequenz vs. erwartet | `cer_statistics_full.py` | alle 285 Docs (kuenftig) |

### 9.2 Validierungs-Protokoll

1. Auf den 18 Docs mit gemessener CER: Pearson + Spearman zwischen jedem
   Proxy und der echten CER.
2. Composite-Score via Linear Regression (Ordinary Least Squares).
3. **Cross-Validation: Leave-One-Out (LOOCV)** — bei n=18 die ehrlichste
   Out-of-Sample-Schaetzung.
4. R²: `in_sample` (overfitted) und `loocv` (Generalisierungs-Metrik).

### 9.3 Aktueller Befund (ehrliches Negativergebnis)

- Dictionary Hit Rate korreliert nur schwach mit CER (Pearson ≈ −0.20).
- Suspicious Char Ratio: Pearson ≈ −0.05 (sehr schwach).
- Composite OLS: in-sample R² = 0.15, **LOOCV-R² = −1.67**.

**LOOCV-R² < 0** bedeutet: das Composite ist *schlechter* als der einfache
Mittelwert als Vorhersage. Die Korpus-Schaetzung (6.20 % Mean,
total CI [0 %, 17.56 %]) ist daher **kein Schaetzer**, sondern eine
**Plausibilitaets-Schranke**.

Im Dashboard ist das visuell stark abgegrenzt (Sektion §12, "SCHAETZUNG"-
Badge, andere Akzentfarbe). In `CER-BENCHMARK.md` wird klar als
Negativ-Ergebnis kommuniziert.

### 9.4 Verbesserungspfad (deferred)

- N-gram-Loglik aus Wikipedia-FR/DE-Dump (Aufwand ~1-2 h)
- Sentence-length-KL-Divergenz
- `wordfreq`-basierte Lexikon-Scores

Mit ~5 unabhaengigen Proxies und n=18 koennte LOOCV-R² > 0 werden, aber
bleibt strukturell limitiert. Der einzig sichere Weg ist mehr Ground Truth
(User-Entscheidung: "kein manueller GT-Aufbau").

---

## 10. Stabilitaet (LLM-Non-Determinismus)

Pipeline-Stages 5 (Mistral OCR) und 6 (Gemini TEI-Generation) sind
nicht-deterministisch. Bei wiederholtem Run auf identischem Input
variiert das Output.

**Aktueller Status: `stability.status: open`** im JSON, mit Begruendung
"API-Budget pending user decision (Forschungsplan v2 §9 b)".

**Wenn User freigibt:**
- 5 Docs × 3 Re-Runs der Pipeline (geschaetzt $1–2 API-Kosten)
- Std-Dev der Per-Doc-CER reporten
- Kontextualisierung: ist der gemessene CER mit Bootstrap-CI ueberhaupt
  praeziser, als die Run-zu-Run-Varianz das erlauben wuerde?

Bis das gemessen ist, ist die **wahre** Praezision unserer Aussage unbekannt.
Bootstrap-CIs erfassen nur die Sampling-Unsicherheit, nicht die Modell-
Stochastizitaet.

---

## 11. Limitations (was wir explizit nicht koennen)

- **n = 18 Docs Ground Truth** — Korpus-Aussagen sind Schaetzungen, nicht Messungen.
- **Selection-Bias n_chars: p = 0.041** — Ref-Subset ist im Char-Volumen abweichend.
- **Multi-Norm-Regimes wenig differenziert** — wegen vorgeschalteter Normalisierung
  in `normalize_for_comparison()`.
- **Stability nicht gemessen** — LLM-Non-Determinismus-Varianz unbekannt.
- **Proxy-Composite generalisiert nicht (LOOCV-R² < 0)** — Korpus-Schaetzung
  ist nur Plausibilitaets-Schranke, kein Schaetzer.
- **HCPR ist Frequenz-basiert, nicht Position-basiert** — unterschaetzt
  Substitutions-Fehler.
- **Kein Inter-Engine-Vergleich** — wir haben nur einen OCR-Engine-Run im
  Vergleich, keine zweite Quelle als Cross-Validation.

Diese Limitations werden im Dashboard (`docs/infrastruktur/cer.html` §1)
sticky angezeigt und in `CER-BENCHMARK.md` referenziert.

---

## 12. Reproduzierbarkeit

```bash
# Test-Suite (~1 s)
python -m pytest tests/test_cer_statistics.py -q

# JSON-Generierung (~2-3 min, deterministisch bei gleichem Seed)
python -u -m scripts.cer_statistics_full --seed 42 --bootstrap-n 10000
# -> docs/data/cer_statistics.json
```

Im JSON `meta`-Block dokumentiert:
- `tool_version`, `git_sha`, `git_dirty`, `generated_at`
- `python_version`, `numpy_version`, `scipy_version`, `cer_lib`
- `seed`, `bootstrap_n`, `bootstrap_method`
- `normalization_pipeline` (welche Schritte in welcher Reihenfolge)
- `literature_refs` (alle 2025+, vollstaendige Liste)

---

## 13. Quellen (alle 2025+, User-Vorgabe)

1. Singh, A. (2025). *When +1% Is Not Enough: A Paired Bootstrap Protocol
   for Evaluating Small Improvements*. arXiv:2511.19794.
2. Nosova, E. et al. (2025). *Evaluating LLMs for Historical Document OCR:
   A Methodological Framework for Digital Humanities*. arXiv:2510.06743.
3. Crosilla, L., Klic, M., Colavizza, G. (2025). *Benchmarking large
   language models for handwritten text recognition*. Journal of
   Documentation. arXiv:2503.15195.
4. Kanerva, J., Ledins, G. (2025). *OCR Error Post-Correction with LLMs in
   Historical Documents: No Free Lunches*. RESOURCEFUL-2025.
   arXiv:2502.01205.
5. (2025). *Statistical multi-metric evaluation and visualization*.
   arXiv:2501.18243.
6. (2025). *On Robustness and Reliability of Benchmark-Based Evaluation of
   LLMs*. arXiv:2509.04013.

---

*Erstellt: 2026-04-27 | Verwandte Implementierung: `scripts/cer_statistics.py`,
`scripts/cer_statistics_full.py`, `tests/test_cer_statistics.py`,
`docs/infrastruktur/cer.html`*
