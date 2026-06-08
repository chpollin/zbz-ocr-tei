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

## Korrektheits-Welle (2026-05-27): korrigierte CER-Methodik [AKTUELLE SOT]

Diese Sektion ist die **verbindliche aktuelle Quelle** fuer die CER. Die darunter folgenden
Abschnitte (alte Headline, Timeline) sind **historisch** und teils ueberholt -- sie bleiben zur
Nachvollziehbarkeit stehen, gelten aber nur, wo sie dieser Sektion nicht widersprechen.

### Befund: die ZBZ-Referenzen sind selektive Teiltranskriptionen

Konkret belegt (siehe Beispiel-Dump): Doc 580 enthaelt in der Pipeline **zwei** Rezensionen
(Piguet + Gehlen), in der Referenz nur **eine**; Doc 570 hat zusaetzlich den Journal-Masthead;
Doc 90 ein Inhaltsverzeichnis. Die Pipeline ist also oft **vollstaendiger** als die Referenz.
Eine naive Volltext-CER bestraft das (Doc 570: 113 %, obwohl die OCR fehlerfrei ist). Das alte
alignment-getrimmte Verfahren verbarg umgekehrt sowohl diesen Mehrtext als auch echte Verluste.

### Drei-Zahlen-Zerlegung (kanonisch, `classify_edit_operations`)

Jede Levenshtein-Editieroperation wird klassifiziert. `cer_fidelity + scope_insertion_rate = cer`.

| Topf | Operation | Bedeutung | OCR-Fehler? |
|---|---|---|---|
| **Fidelity (B+C)** | Substitutionen, kleine Indels, **alle Loeschungen** | falsch/nicht erfasster Text | **ja** |
| **Scope (A)** | grosse Einfuegungen (>= 50 Zeichen) | Pipeline-Mehrtext ggue. Referenz | nein |

Asymmetrie ist beabsichtigt: vollstaendiger sein als die Referenz ist kein Fehler, unvollstaendiger schon.

### Headline-Werte (n=25, alle Docs, Seed 42, B=10000, 2026-06-08)

| Metrik | Mean | Median | 95%-CI (Mean) | misst |
|---|---|---|---|---|
| **Fidelity-CER (PRIMAER)** | **2.79 %** | **1.58 %** | [1.85 %, 3.90 %] | echte OCR-/Transkriptionstreue |
| Volltext-CER (Diagnose, scope-inkl.) | 19.02 % | 12.13 % | [10.35 %, 30.11 %] | volle Divergenz inkl. Mehrtext — **KEIN Qualitaetsmass** |
| Scope-Rate (Mehrtext) | 16.23 % | 7.06 % | — | Pipeline-Mehrtext (kein Fehler) |

Alle Werte ueber **alle 25 Docs** (E73: das fruehere n=19-scope-clean-Subset wurde entfernt, da es keinem reproduzierbaren Kriterium folgte). Volltext/Scope sind Diagnose-Groessen; das Qualitaetsmass ist die Fidelity-CER.

Der Fidelity-Median **1.58 %** (Stand 2026-06-08) wird sauber gemessen: ohne deflationaeres
Trimming, ohne zirkulaeren Ausschluss, case-sensitiv, ueber das ganze Korpus.

Stand 2026-06-08: Bei Doc 30 wurde ein OCR-Blockduplikat (ein doppelt erfasster Absatz) entfernt -- das senkte dessen Fidelity-CER von 18.25 % auf 11.59 % und den Korpus-Mean auf 3.99 % (damaliger Stand; die anschliessende Fussnoten-Demotion vom 2026-06-08, siehe Korrektur unten, senkte ihn weiter auf 2.79 % / Median 1.58 %). Eine **automatische** Block-Deduplikation existiert derzeit nicht in der Pipeline (das in Anhang A des Arbeitsberichts und in CLAUDE.md referenzierte `scripts/ocr/ocr_dedup.py` ist nicht im Repo). Bis eine Dedup-Stufe existiert, ist diese eine Korrektur manuell; alle uebrigen 24 Docs sind reines Pipeline-Output.

Einordnung **print-kalibriert** (E80): Die Transkribus-Qualitaetsbaender (<2 % exzellent, 2-5 % gut)
stammen primaer aus der HTR-Praxis (Handschrift); fuer eine reine **Druck**-OCR-Aufgabe schmeicheln
sie, weil dort die Messlatte hoeher liegt. Massgeblich ist daher der **Print-OCR-Literaturvergleich**
(Abschnitt „Vergleich gegen Stand der Forschung" unten): Median 1.58 % liegt **zwischen** dem besten
spezialisierten Print-Stack (Transkribus + LLM-Post 0.84 %) und Transkribus allein (3.67 %) -- solide
fuer historischen Druck, aber **nicht** an der Spitze. Zusaetzlich misst die CER gegen eine selbst
fehlerbehaftete Transkribus-Referenz (siehe Doc 1440), ist also eine Obergrenze der wahren Fehlerrate.

### Korrektur 2026-06-08: referenz-verifizierte Fussnoten-Demotion

Drei Objekte trugen Fliesstext faelschlich als `<note place="foot">` (Gemini Stufe 6); da der
Vergleich Fussnoten ausschliesst (E5), zaehlte dieser Text als Loeschung und blaehte ihre CER auf.
Verifiziert gegen die ZBZ-Referenz (der Text steht dort im Body) wurden sie nach `<p>` demoted --
evidenzbasiert, nicht geraten. Ergebnis (gegen `zbz_hersch.rng` validiert, Mirror regeneriert):

| Doc | Bloecke | Fidelity vorher | nachher |
|---|---|---|---|
| 290 | 2 (1352 + 685) | 17,7 % | 2,6 % |
| 1910 | 1 (912) | 16,4 % | 7,7 % |
| 90 | 1 (609) | 7,6 % | 1,4 % |

**Korpus-Fidelity neu: Mean 2,79 % / Median 1,58 % / micro 2,70 % (n=25).** Die Headline-Tabelle
oben ist mit dem `cer_statistics_full`-Lauf vom 2026-06-08 auf diesen Stand aktualisiert
(BCa-CI [1,85 %, 3,90 %]); der Pipeline-Mehrwert gegenueber reiner OCR ist dadurch signifikant
geworden (-9,38 pp, p=0,013). Diskriminator: eine `<note place="foot">` ist verifizierter
Fliesstext, wenn ihre ersten 120 Zeichen im Body der Referenz vorkommen. Vollstaendige Worklist der
verbleibenden Faelle (6 referenz-verifiziert zurueckgehalten, 11 zur Handpruefung, 1 Seitenzahl):
[reports/fussnoten-kuration-2026-06-08.md](../reports/fussnoten-kuration-2026-06-08.md).

### Pipeline-Mehrwert (Paired, like-for-like Fidelity)

Pipeline-E2E vs. reine Mistral-OCR: **-9.38 pp** (p = 0.013, n=25, **signifikant**
bei alpha=0.05; Stand 2026-06-08 nach der Fussnoten-Demotion). Die fruehere Angabe „-14.83 pp,
p=0.0004" war ein Artefakt des getrimmten/kleingeschriebenen Vergleichs und ist **zurueckgezogen**;
der Zwischenstand vor der Demotion war -7.90 pp (p=0.07, n.s.). Die Demotion verbesserte die
End-to-End-Treue und vergroesserte damit den Abstand zur reinen OCR.

### Was sich im Code aenderte (E70)

1. **Kein Alignment-Trimming mehr** in der Headline: Volltext-Levenshtein; `find_best_alignment`
   nur noch Diagnose, Padding-auf-Referenzlaenge entfernt.
2. **Case-sensitiv** als Default (`normalize_for_comparison(casefold=False)`); pauschales `.lower()`
   entfernt. Effekt auf die Zahl ~0 (Case-Differenzen liegen fast nur in Versal-Lauftiteln).
3. **Drei CER-Pfade vereinheitlicht**: `benchmark_cer`, `cer_statistics(_full)` und
   `tei_validator --compare-ref` nutzen jetzt `extract_text_for_comparison` + `calculate_cer`.
   `--compare-ref` vergleicht `tei_final/` (statt `tei_unified/{id}/`) und nicht mehr rohes `itertext()`.
4. **Scope-Ausschluss entzirkelt**: `cer>50%` als Ausschlussgrund entfernt (war zirkulaer); nur noch
   strukturelles Seitenzahl-Ratio. Latenter Bug behoben (`ref_pages_total` -> `ref_pages`).
5. **Blank-`<pb>`** aus dem Seiten-Count ausgenommen.
6. **Fehlerkategorien via `rapidfuzz` editops** (statt `difflib`): summieren exakt zur Levenshtein-Distanz.
7. **Goldene Regressionstests** `tests/test_cer_extraction.py` (18 Tests) sichern den Vertrag.

### Externe Verifikation (2026-05-27)

| Frage | Standard | Konform? |
|---|---|---|
| Denominator `dist/len(ref)` | Transkribus | ja |
| case-sensitiv als Default | OCR-D, dinglehopper, jiwer (ToLowerCase opt-in) | ja (jetzt) |
| NFC-Normalisierung | OCR-D, dinglehopper, W3C | ja |
| globales Volltext-Alignment, kein Trimming | dinglehopper, jiwer | ja (jetzt) |
| Paired Bootstrap: Perzentil-CI auf Deltas, p = Anteil Vorzeichenwechsel | Singh 2025 (arXiv:2511.19794) | ja |

Quellen: [OCR-D Eval Spec](https://ocr-d.de/en/spec/ocrd_eval.html), [Transkribus CER](https://www.transkribus.org/character-error-rate-cer-explained), [dinglehopper](https://github.com/qurator-spk/dinglehopper), [jiwer](https://github.com/jitsi/jiwer), Singh 2025 (arXiv:2511.19794).

### Zitations-Korrektur

arXiv:2510.06743 (HCPR/AIR) ist von **M. Levchenko 2025**, *nicht* „Nosova et al." -- frueher falsch attribuiert.

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
| End-to-End-CER | Pipeline-TEI (`tei_final/`) vs Referenz-TEI | Gesamtfehler aus OCR + Layout + TEI-Gen |
| OCR-only-CER | Mistral OCR Stage-2 vs Referenz | reiner OCR-Fehler ohne Pipeline-Korrekturen |

Differenz quantifiziert die **Pipeline-Verbesserung**.

**Aggregations-Einheit:** Dokument-Ebene, nicht Seiten-Ebene.

```
doc_cer = Levenshtein(ref_volltext, hyp_volltext) / |ref_volltext|   # Volltext, KEIN Trimming
mean_cer = mean(doc_cer for doc in evaluated)                        # Bootstrap-Einheit = Doc
```

KORREKTUR (E70): Frueher stand hier `Σ(page_levenshtein)/Σ(page_ref_chars)` (char-gewichtete
Per-Page-Aggregation). Real wird der Doc-CER als Volltext-Levenshtein berechnet
(`evaluate_tei_vs_tei`); die Per-Page-Werte dienen nur der Outlier-Visualisierung. Der primaere
Headline-Wert ist die **Fidelity-CER** (siehe Korrektheits-Welle oben), nicht diese Volltext-CER.

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
Pipeline-Reduktion von ~9 % Ausgangslage auf die heutige Fidelity-CER (2,79 %, siehe
Korrektheits-Welle oben) sichtbar, nicht zwischen den 4 nominellen Stufen.

### Domain-Metrik: HCPR-Adaption

CER allein zeigt nicht, *welche* Zeichen gut oder schlecht erkannt werden. Fuer eine historische
Edition mit FR+DE-Sonderzeichen ist die Erhaltungsrate diakritischer Zeichen ein eigenstaendiger
Qualitaetsindikator.

```
HCPR(ref, hyp, lang) = min(observed_count, expected_count) / max(1, expected_count)
```

Diakritik-Set pro Sprache: fra (é è à ç ù â ê î ô û ë ï ü œ), deu (ä ö ü ß), ita.

**Methodische Quelle:** Levchenko (2025), arXiv:2510.06743. Einschraenkung: konservative
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
| Levchenko 2025 | arXiv:2510.06743 | HCPR/AIR, no-GT-Methodik, Stabilitaets-Tests |
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

Bei Freigabe: 5 Docs × 3 Re-Runs, Std-Dev der Per-Doc-CER reporten.
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
allein (3.67%) und Gemini 2.5 Pro zero-shot (3.36%).

Kernerkenntnisse: (1) multimodale Post-Korrektur uebertrifft reine Text-Post-Korrektur deutlich.
(2) LLM-Post-Korrektur ist sprachabhaengig ("No Free Lunches", Kanerva 2025). (3) Gemini-Modelle
dominieren aktuelle Benchmarks. (4) Bei bereits gutem OCR kann LLM-Korrektur degradieren —
bestaetigt durch unsere Haiku-Postkorrektur (+0.10%, Variant C).

---

## Korpus-weite Schaetzung (Proxy-Framework)

Direkter CER nur fuer 25 Docs (siehe Headline). Fuer die anderen 260 brauchen wir Proxies.

### Methode: Dictionary Hit Rate

Anteil der OCR-Woerter, die in einem FR/DE-Woerterbuch gefunden werden. OCR-Fehler erzeugen
Nicht-Woerter ("maison" → "rnaison"), daher korreliert hohe Hit Rate mit guter OCR-Qualitaet.

**Literatur:** Stroebel et al. 2022, "Evaluation of HTR models without Ground Truth Material" (LREC 2022).

**Implementierung:** `scripts/eval/quality_proxy.py`

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

**285/285 Docs valide** gegen `zbz_hersch.rng` (E68, 2026-05-27). Davor real **0/285** — die
Schema-Erweiterung E68 schloss die Luecke; gegen Regression gesichert durch `tests/test_tei_schema.py`.

| Metrik | Wert |
|---|---|
| Dokumente | 285 |
| Valid | 285 (100%) |
| Invalid | 0 |
| Mit Warnings | 29 |

### Fix-Verlauf

**Fix-004 / E68 (2026-05-27): fehlende Standard-TEI-Elemente im Schema ergaenzt.** Erste
korpusweite Validierung der ausgelieferten Schicht ergab **0/285** valide — alle Fehler im
teiHeader: `revisionDesc`/`change` (E42/E66), `langUsage`/`language`, `idno` (im `publicationStmt`),
`monogr`/`imprint` (im `biblStruct`). Das ODD-Subset (E48) hatte diese Standard-TEI/DTA-Elemente
weggelassen; gegen das alte `tei_all.rng` validieren dieselben Dokumente 8/8. Fix: 7 Definitionen +
4 Inhaltsmodelle in `zbz_hersch.rng` (Inhalt minimal am korpusweit erhobenen Datenvertrag).
`source-metadata` als div-Typ registriert (Doc 1170). Ergebnis: **285/285 valide**, gegen Regression
gesichert durch `tests/test_tei_schema.py`. Korrigiert den Fehlschluss aus Fix-001 (siehe unten).

**Fix-001 (2026-03-26): ref-Pattern erweitert.** Vorher 50 valid / 235 invalid. Schema erzwang
`ref="GND:[0-9A-Za-z\-]+"`, Pipeline injizierte `ref="#zbz-p.NNN"`. RelaxNG-Kaskade machte alle
235 Docs mit zbz-Refs komplett invalid (nicht nur das ref-Attribut). Fix: Pattern in 3 Stellen
erweitert: `(GND:[0-9A-Za-z\-]+|#zbz-[a-z]+\.[0-9]+)` an `bibl/@corresp`, `orgName/@ref`,
`persName/@ref`. Ergebnis (damals): 285 valid / 0 invalid. **Fehlschluss, 2026-05-27 widerlegt:** die
idno/langUsage/biblStruct-Fehler wurden hier als Kaskaden-Artefakte abgetan — sie waren real,
das ODD-Subset liess diese Standard-Elemente nicht zu. Als der Header spaeter (E65/E66) reicher
wurde, fiel `tei_final` auf 0/285, unbemerkt mangels Batch-Validierung der ausgelieferten Schicht.
Behoben in Fix-004 / E68.

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
| W11 | 2 | zu viele top-level divs (false positive) |

Die fruehere Entity-Validierung (W9 "Entity-Tags ohne ref", W10 "nur persName, 0 orgName/placeName")
ist mit **E71** (NER entfernt) hinfaellig: das ausgelieferte TEI traegt keine Entity-Tags mehr.

### Validierungsregeln

**Errors (blockierend, 8 Regeln R1-R8):** RelaxNG + Projekt-Regeln (R1 type="naegeli",
R2 teiHeader, R3 body, R4 min 1 div, R5 gueltige div-types, R6 note place, R7 entity-ref).

**Warnings (18 Regeln W1-W18, informativ):** W1 Sprach-Code "und", W2 teiHeader title/author
leer, W3 facsimile/pb Mismatch, W4 leere div, W5 Text-Volumen <50 chars/Seite, W6 keine lb,
W7 graphic ohne url, W8 keine Entity-Tags bei >500 Zeichen, W9 Entity-Tags ohne ref, W10 nur
persName, W11 zu viele top-level divs gleichen Namens, W12 Fussnoten-n, W13 Fussnoten xml:id-Pattern,
W14 back/div-types, W15 div mit type UND n (exklusiv), W16 figure ohne xml:id, W17 leerer speaker
(Kurations-Slot, E71), W18 foreign xml:lang nicht normalisiert. W15-W18 aus dem Konformitaets-Audit
2026-06-08 (siehe `reports/tei-konformitaet-audit-welle1-2026-06-08.md`).

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

## Agent-Based Quality Screening (abgeschafft, E66 -- nur Provenienz)

**2026-05-26 abgeschafft (E66):** Das agentische 7-Schichten-Screening war epistemisch
irrefuehrend -- keiner der 285/285 "APPROVED"-Status kam von einem Menschen, der Agent
zertifizierte sich selbst (eingebaute Ignorier-Liste W3/W6/W10). Das "APPROVED"-Etikett im
revisionDesc traf keine Aussage ueber fachliche Qualitaet.

Ersetzt durch **Workflow-Status pro Strom** (Abschnitt unten): unverifiziert | in_arbeit |
verifiziert, menschlich im Viewer gesetzt. Die Alt-Befunde leben als _screening_legacy.json
(gitignored, nicht im Mirror) -- inhaltlich teils nuetzlich, aber ohne Qualitaetsaussage.

Real erhalten gebliebene Fixes aus der Nachbearbeitung (E45-E47): Entity-Stopwoerter erweitert,
Strukturfixes (2140/2150/2530/2550/2660), OCR-Deduplizierung (900/1100/2630). Belastbare
empirische Muster: Gemini korrigiert OCR-Fehler im Step-2-Refinement (Qualitaetsgewinn);
mehrspaltige Zeitungslayouts (Journal de Geneve) versagen systematisch (~3% Korpus).
Detail-Provenienz: [decisions.md E41-E47](decisions.md).

---

## Workflow-Status pro Strom (E66/E67/E77, ab 2026-05-26)

Ersetzt das Agent-Screening (oben). Drei Statuswerte je Datenstrom (`ocr`, `layout`, `tei`),
seit E77 (Kollaps von vier auf drei Stufen, Variante A):

| Status | Bedeutung |
|---|---|
| `unverifiziert` | Pipeline-Output existiert, kein Mensch hat verifiziert (Default fuer alle 285 Docs) |
| `in_arbeit` | mindestens eine menschliche Sichtung/Korrektur begonnen, nicht freigegeben |
| `verifiziert` | menschlich geprueft und freigegeben, edition-ready |

**Ampel-Semantik im UI (E77, drei Stufen, E67-konform):** **neutral/grau** = `unverifiziert`
(vorhanden, noch nicht angefasst), **gelb** = `in_arbeit` (in Bearbeitung), **gruen** =
`verifiziert` (menschlich freigegeben). **rot** bleibt reserviert fuer einen spaeteren
expliziten Problem-/Reject-Status (z.B. "OCR fehlt", "muss neu generiert werden"). E77 legt
die frueheren vier Stufen zusammen: altes `bearbeitet` → `in_arbeit`, altes `fertig` →
`verifiziert`; damit gibt es genau eine Farbe je Stufe statt vier Stufen in zwei Farben.
Begruendung (unveraendert aus E67): die Pipeline produziert OCR/Layout/TEI deterministisch fuer
alle 285 Docs -- der Default ist "vorhanden, unverifiziert", nicht "nichts da", und `unverifiziert`
ist daher neutral, kein Alarm.

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
Status-Wechsel (z.B. `in_arbeit` → `verifiziert`) erfolgen ueber die Pill.

**Mirror:** `python -m scripts.edition.generate_edition_data --mirror-only` spiegelt die Manifeste nach
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
Page-Numbering-Drift. Nach Wechsel: Mean 3.99% / Median 1.82% (n=18, scope-clean -- historischer Zwischenstand vom 2026-04-27; aktuelle Headline siehe oben: Mean 2.79% / Median 1.58%). Drift-Check:
nur 1 Doc weicht noch >5pp ab → **Pipeline ist tatsaechlich stabil**, der "Drift"-Eindruck war
ein Mess-Artefakt.

**Konsequenzen:**

1. **Aggregations-Einheit = Doc-Ebene.** Pages innerhalb eines Docs sind nicht nur korreliert (was naive iid-Bootstrap schon falsch macht), sondern bei Schema-Aenderungen auch falsch identifiziert.
2. **Content-aligned Eval war Default (bis E70).** UEBERHOLT: seit E70 ist die Headline die
   Fidelity-CER auf dem Volltext (kein Trimming, da Trimming Insertions/Verluste verbarg). Volltext-
   Levenshtein ist gegen `<pb>`-Drift ohnehin immun (Text in Lesereihenfolge, Page-IDs egal).
   `find_best_alignment` lebt nur noch als Diagnose-/Within-Doc-Chunk-Werkzeug.
3. **Lehre fuer kuenftige Pipeline-Aenderungen:** Jede Stage, die `<pb>`-IDs neu vergibt oder Seiten umsortiert, muss vorher in einem Test-Run gegen Referenz-TEIs laufen.

---

## Limitations (was wir explizit nicht koennen)

- **n = 25 Docs Ground Truth** — Korpus-Aussagen sind Schaetzungen, nicht Messungen.
- **Selection-Bias n_chars (p = 0.041)** — Ref-Subset im Char-Volumen abweichend.
- **Multi-Norm-Regimes wenig differenziert** — wegen vorgeschalteter Normalisierung in `normalize_for_comparison()`.
- **Stability nicht gemessen** — LLM-Non-Determinismus-Varianz unbekannt.
- **Proxy-Composite generalisiert nicht (LOOCV-R² < 0)** — Korpus-Schaetzung ist nur Plausibilitaets-Schranke.
- **HCPR ist Frequenz-basiert, nicht Position-basiert** — unterschaetzt Substitutions-Fehler.
- **Kein Inter-Engine-Vergleich** — wir haben nur einen OCR-Engine-Run, keine zweite Quelle.

Diese Limitations sind im JSON dokumentiert (`selection_bias.interpretation`, `multi_norm._note`,
`stability.status`, `proxies.validation.composite.loocv_r2`) und beim Lesen der Headline-Werte
zwingend mitzudenken.

---

## Pilot-Baseline (Mistral OCR, Phase 0, Feb 2026) -- nur Provenienz

Historische Referenz; aktuelle Metriken siehe Headline oben. Ein Befund bleibt relevant und wird
oben zitiert: die LLM-Postkorrektur (Haiku 4.5, Variant C, Few-Shot) verbessert Docs mit hoher CER
(>10%), verschlechtert aber leicht bei bereits guter OCR (<5%) -- netto +0.10pp ueber den Pilot.
Konsequenz: optional, nicht Default (E17).

---

## Reproduzierbarkeit

```bash
# Test-Suite (~1s)
python -m pytest tests/test_cer_statistics.py -q

# JSON-Generierung (~2-3min, deterministisch bei gleichem Seed)
python -u -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000
# → docs/data/cer_statistics.json

# CER-Benchmark (alle 25 GT-Docs)
python -m scripts.eval.benchmark_cer --all --html

# Quality Proxy (alle 285 Docs)
python -m scripts.eval.quality_proxy --all --html

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
- [viewer.md](viewer.md) — Layout- und Transkriptions-Editor (manuelle QA via Datei-Download)
- [decisions.md](decisions.md) — E51 (CER-Benchmark), E54/E55 (CER-Statistik + Dashboard), E41-E47 (Screening)
