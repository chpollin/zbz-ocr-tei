"""
Quality Proxy: OCR-Qualitaetsschaetzung ohne Ground Truth.

Methode: Dictionary Hit Rate (Woerterbuch-Trefferquote)
- Extrahiert Text aus finalen TEI-Dateien
- Prueft jedes Wort gegen franzoesisches/deutsches Woerterbuch
- Berechnet Anteil erkannter Woerter als Proxy fuer OCR-Qualitaet
- Validiert Proxy gegen echte CER (25 Ground-Truth-Docs)

Literatur:
  Stroebel et al. 2022: "Evaluation of HTR models without Ground Truth Material"
  (LREC 2022, https://aclanthology.org/2022.lrec-1.467/)

Usage:
  python -m scripts.eval.quality_proxy                  # nur 25 GT-Docs (Validierung)
  python -m scripts.eval.quality_proxy --all            # alle 285 Docs
  python -m scripts.eval.quality_proxy --doc 100        # einzelnes Dokument
  python -m scripts.eval.quality_proxy --html           # mit HTML-Report
"""

import argparse
import json
import re
import statistics
import unicodedata
from datetime import datetime
from pathlib import Path

from spellchecker import SpellChecker

from scripts.config import (
    DOC_METADATA_PATH,
    EVALUATION_DIR,
    REFERENZ_TEI_DIR,
    TEI_FINAL_DIR,
)
from scripts.eval.evaluate_ocr import extract_text_for_comparison


# ---------------------------------------------------------------------------
# Woerterbuecher laden (einmalig)
# ---------------------------------------------------------------------------

_spell_fr = SpellChecker(language="fr")
_spell_de = SpellChecker(language="de")


def _detect_language(doc_id: str, metadata: dict) -> str:
    """Sprache fuer ein Dokument aus Metadaten holen."""
    docs = metadata.get("documents", {})
    if doc_id in docs:
        lang = docs[doc_id].get("language", "fra")
        if "/" in lang:
            return "multi"
        if lang.startswith("deu") or lang == "de":
            return "de"
        return "fr"
    return "fr"


# ---------------------------------------------------------------------------
# Kern: Dictionary Hit Rate
# ---------------------------------------------------------------------------

MIN_WORD_LENGTH = 2  # Einzelbuchstaben ignorieren (a, e, I, ...)

# Zeichen, die in sauberem fr/de Text normalerweise nicht vorkommen.
# Ihr Auftreten deutet auf OCR-Artefakte hin.
_SUSPICIOUS_CHARS = set("@#$%^&*{}[]|\\<>~`_=+")
# Erwartete Zeichen fuer franzoesisch/deutsch
_EXPECTED_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " \t\n\r"
    ".,;:!?-()\"'/\u2013\u2014\u2018\u2019\u201c\u201d\u00ab\u00bb"
    "\u00e0\u00e2\u00e4\u00e6\u00e7\u00e8\u00e9\u00ea\u00eb\u00ee\u00ef"
    "\u00f4\u00f6\u00f9\u00fb\u00fc\u00ff\u0153"
    "\u00c0\u00c2\u00c4\u00c6\u00c7\u00c8\u00c9\u00ca\u00cb\u00ce\u00cf"
    "\u00d4\u00d6\u00d9\u00db\u00dc\u0152"
    "\u00df"
)


def tokenize(text: str) -> list[str]:
    """Text in Woerter aufteilen. Nur alphabetische Tokens behalten."""
    tokens = re.findall(r"[a-zA-Z\u00C0-\u024F]+", text)
    return [t for t in tokens if len(t) >= MIN_WORD_LENGTH]


def suspicious_char_ratio(text: str) -> dict:
    """Anteil verdaechtiger Zeichen im Text (OCR-Artefakt-Indikator).

    Returns:
        dict mit ratio, total_chars, suspicious_count, suspicious_sample
    """
    if not text:
        return {"ratio": 0.0, "total_chars": 0, "suspicious_count": 0,
                "suspicious_sample": []}

    suspicious_count = 0
    suspicious_freq = {}
    for ch in text:
        if ch in _SUSPICIOUS_CHARS or (ord(ch) > 127 and ch not in _EXPECTED_CHARS
                                        and unicodedata.category(ch) not in ("Zs", "Zl", "Zp")):
            suspicious_count += 1
            suspicious_freq[ch] = suspicious_freq.get(ch, 0) + 1

    sample = sorted(suspicious_freq.items(), key=lambda x: -x[1])[:10]
    return {
        "ratio": suspicious_count / len(text) if text else 0.0,
        "total_chars": len(text),
        "suspicious_count": suspicious_count,
        "suspicious_sample": [
            {"char": ch, "codepoint": f"U+{ord(ch):04X}", "count": c}
            for ch, c in sample
        ],
    }


def dictionary_hit_rate(text: str, language: str) -> dict:
    """Berechnet Woerterbuch-Trefferquote fuer einen Text.

    Filtert Eigennamen (Grossbuchstaben-Woerter die nicht am Satzanfang
    stehen) heraus, da diese die Hit Rate verzerren wuerden.

    Returns:
        dict mit hit_rate, total_words, known_words, unknown_words,
             unknown_sample (bis zu 20 Beispiele)
    """
    words = tokenize(text)
    if not words:
        return {
            "hit_rate": 0.0,
            "total_words": 0,
            "known_words": 0,
            "unknown_words": 0,
            "unknown_sample": [],
        }

    # Eigennamen-Filter: Woerter mit Grossbuchstabe am Anfang, die NICHT
    # am Satzanfang stehen, sind wahrscheinlich Eigennamen.
    # Einfache Heuristik: Wir behalten nur lowercase-Woerter und Woerter
    # die komplett UPPER sind (Akronyme = wenige, vernachlaessigbar).
    # Fuer Deutsch: alle Nomen sind gross → kein Filter moeglich,
    # daher nur fuer FR/multi filtern.
    if language in ("fr", "multi"):
        # Eigennamen rausfiltern: Woerter die mit Grossbuchstabe beginnen
        # und laenger als 1 Zeichen sind
        words_filtered = [w for w in words if not w[0].isupper() or w.isupper()]
        # Mindestens 50% der Woerter behalten, sonst kein Filter
        if len(words_filtered) >= len(words) * 0.5:
            words = words_filtered

    # Woerter lowercase fuer Woerterbuch-Check
    words_lower = [w.lower() for w in words]

    if language == "de":
        unknown = _spell_de.unknown(words_lower)
    elif language == "multi":
        # Beide Woerterbuecher pruefen, Union der bekannten Woerter
        unknown_fr = _spell_fr.unknown(words_lower)
        unknown_de = _spell_de.unknown(words_lower)
        unknown = unknown_fr & unknown_de  # nur unbekannt wenn in BEIDEN unbekannt
    else:
        unknown = _spell_fr.unknown(words_lower)

    total = len(words_lower)
    unknown_count = sum(1 for w in words_lower if w in unknown)
    known_count = total - unknown_count

    # Haeufigste unbekannte Woerter als Sample
    unknown_freq = {}
    for w in words_lower:
        if w in unknown:
            unknown_freq[w] = unknown_freq.get(w, 0) + 1
    unknown_sample = sorted(unknown_freq.items(), key=lambda x: -x[1])[:20]

    return {
        "hit_rate": known_count / total if total > 0 else 0.0,
        "total_words": total,
        "known_words": known_count,
        "unknown_words": unknown_count,
        "unknown_sample": [{"word": w, "count": c} for w, c in unknown_sample],
    }


# ---------------------------------------------------------------------------
# Ground-Truth-CER laden
# ---------------------------------------------------------------------------

def load_ground_truth_cer() -> dict[str, float]:
    """Laedt echte CER-Werte aus dem Benchmark."""
    benchmark_path = EVALUATION_DIR / "benchmark_tei_vs_tei.json"
    if not benchmark_path.exists():
        return {}
    with open(benchmark_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        doc_id: doc["cer"]
        for doc_id, doc in data.get("documents", {}).items()
        if "cer" in doc
    }


# ---------------------------------------------------------------------------
# Korrelation (Spearman Rank — ohne scipy)
# ---------------------------------------------------------------------------

def _rank(values: list[float]) -> list[float]:
    """Einfache Rangberechnung (ohne Bindungskorrektur)."""
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    for rank, (idx, _) in enumerate(indexed, 1):
        ranks[idx] = float(rank)
    return ranks


def spearman_correlation(x: list[float], y: list[float]) -> float:
    """Spearman-Rangkorrelation (ohne externe Abhaengigkeiten)."""
    n = len(x)
    if n < 3:
        return 0.0
    rx = _rank(x)
    ry = _rank(y)
    d_sq = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - (6 * d_sq) / (n * (n ** 2 - 1))


# ---------------------------------------------------------------------------
# HTML-Report
# ---------------------------------------------------------------------------

def generate_html_report(results: dict, output_path: Path) -> None:
    """Erzeugt einen einfachen HTML-Report."""
    docs = results["documents"]
    validation = results.get("validation", {})

    rows = []
    for doc_id, doc in sorted(docs.items(), key=lambda x: x[1]["hit_rate"]):
        hr = doc["hit_rate"]
        cer = doc.get("ground_truth_cer")
        cer_str = f"{cer:.2%}" if cer is not None else "-"
        lang = doc["language"]
        total = doc["total_words"]

        # Farbe nach hit_rate
        if hr >= 0.85:
            color = "#27ae60"
        elif hr >= 0.70:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        bar_width = hr * 100
        rows.append(f"""
        <tr>
            <td>{doc_id}</td>
            <td>{lang}</td>
            <td>{total:,}</td>
            <td>
                <div style="display:flex;align-items:center;gap:8px">
                    <div style="background:{color};width:{bar_width}%;height:18px;border-radius:3px;min-width:2px"></div>
                    <span>{hr:.1%}</span>
                </div>
            </td>
            <td>{cer_str}</td>
        </tr>""")

    corr_html = ""
    if validation:
        rho = validation.get("spearman_rho", 0)
        n = validation.get("n_docs", 0)
        corr_html = f"""
        <div style="background:#f0f0f0;padding:16px;border-radius:8px;margin:16px 0">
            <h3>Validierung gegen Ground Truth</h3>
            <p><strong>Spearman rho = {rho:.3f}</strong> (n={n} Dokumente)</p>
            <p>Interpretation: {"Starke" if abs(rho) > 0.7 else "Moderate" if abs(rho) > 0.4 else "Schwache"}
               {"negative" if rho < 0 else "positive"} Korrelation
               {"(erwartet: negativ, da hohe Hit-Rate = niedriger CER)" if rho < 0 else "(unerwartet positiv!)"}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Quality Proxy Report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 1rem 0; }}
        .stat {{ background: #ecf0f1; padding: 12px; border-radius: 6px; text-align: center; }}
        .stat .value {{ font-size: 1.8em; font-weight: bold; color: #2c3e50; }}
        .stat .label {{ font-size: 0.85em; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>Quality Proxy: Dictionary Hit Rate</h1>
    <p>Generiert: {results['generated']}</p>

    <div class="summary">
        <div class="stat">
            <div class="value">{results['summary']['total_documents']}</div>
            <div class="label">Dokumente</div>
        </div>
        <div class="stat">
            <div class="value">{results['summary']['mean_hit_rate']:.1%}</div>
            <div class="label">Mean Hit Rate</div>
        </div>
        <div class="stat">
            <div class="value">{results['summary']['median_hit_rate']:.1%}</div>
            <div class="label">Median Hit Rate</div>
        </div>
        <div class="stat">
            <div class="value">{results['summary']['min_hit_rate']:.1%}</div>
            <div class="label">Min Hit Rate</div>
        </div>
    </div>

    {corr_html}

    <table>
        <thead>
            <tr><th>Doc ID</th><th>Sprache</th><th>Woerter</th><th>Hit Rate</th><th>CER (GT)</th></tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>

    <p style="color:#95a5a6;font-size:0.85em">
        Methode: Stroebel et al. 2022 (LREC). Woerterbuch: pyspellchecker (fr/de).
        Hit Rate = Anteil im Woerterbuch gefundener Woerter. Hohe Hit Rate ≈ gute OCR.
    </p>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"  HTML-Report: {output_path}")


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def run(doc_ids: list[str] | None = None, all_docs: bool = False,
        generate_html: bool = False) -> dict:
    """Fuehrt Quality-Proxy-Analyse durch."""

    # Metadaten laden
    with open(DOC_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Ground-Truth CER (fuer Validierung)
    gt_cer = load_ground_truth_cer()
    gt_doc_ids = set(gt_cer.keys())

    # Dokumente bestimmen
    if doc_ids:
        target_ids = doc_ids
    elif all_docs:
        # Alle TEI-Final-Dateien finden
        target_ids = sorted(
            p.stem.replace("_final", "")
            for p in TEI_FINAL_DIR.glob("*_final.xml")
        )
    else:
        # Default: nur Ground-Truth-Docs (Validierungsmodus)
        target_ids = sorted(gt_doc_ids)

    print(f"Quality Proxy: {len(target_ids)} Dokumente analysieren")
    print(f"  Ground-Truth verfuegbar: {len(gt_cer)} Docs")
    print()

    documents = {}
    for doc_id in target_ids:
        tei_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
        if not tei_path.exists():
            print(f"  {doc_id}: SKIP (kein TEI)")
            continue

        # Text extrahieren (gleiche Methode wie CER-Benchmark)
        text = extract_text_for_comparison(tei_path)
        if not text.strip():
            print(f"  {doc_id}: SKIP (leerer Text)")
            continue

        # Sprache bestimmen
        language = _detect_language(doc_id, metadata)

        # Dictionary Hit Rate berechnen
        result = dictionary_hit_rate(text, language)
        result["language"] = language
        result["char_count"] = len(text)

        # Suspicious Character Ratio
        susp = suspicious_char_ratio(text)
        result["suspicious_char_ratio"] = susp["ratio"]
        result["suspicious_chars"] = susp

        # Composite Score: gewichtete Kombination
        # hit_rate geht von 0-1 (1=gut), suspicious von 0-1 (0=gut)
        # Score = 0-100, hoeher = besser
        result["quality_score"] = round(
            (result["hit_rate"] * 0.8 + (1 - susp["ratio"]) * 0.2) * 100, 1
        )

        # Ground Truth CER anfuegen falls vorhanden
        if doc_id in gt_cer:
            result["ground_truth_cer"] = gt_cer[doc_id]
        else:
            result["ground_truth_cer"] = None

        documents[doc_id] = result
        hr = result["hit_rate"]
        qs = result["quality_score"]
        cer_str = f"  CER={gt_cer[doc_id]:.2%}" if doc_id in gt_cer else ""
        print(f"  {doc_id}: hit_rate={hr:.1%}  score={qs}  susp={susp['ratio']:.3%}{cer_str}")

    # Zusammenfassung
    hit_rates = [d["hit_rate"] for d in documents.values()]
    summary = {
        "total_documents": len(documents),
        "mean_hit_rate": statistics.mean(hit_rates) if hit_rates else 0,
        "median_hit_rate": statistics.median(hit_rates) if hit_rates else 0,
        "std_hit_rate": statistics.stdev(hit_rates) if len(hit_rates) > 1 else 0,
        "min_hit_rate": min(hit_rates) if hit_rates else 0,
        "max_hit_rate": max(hit_rates) if hit_rates else 0,
    }

    # Validierung: Korrelation aller Signale vs CER
    validation = {}
    gt_docs = [
        d for d in documents.values() if d["ground_truth_cer"] is not None
    ]
    if len(gt_docs) >= 3:
        cers = [d["ground_truth_cer"] for d in gt_docs]
        signals = {
            "hit_rate": ([d["hit_rate"] for d in gt_docs], "negativ"),
            "suspicious_char_ratio": ([d["suspicious_char_ratio"] for d in gt_docs], "positiv"),
            "quality_score": ([d["quality_score"] for d in gt_docs], "negativ"),
        }
        validation = {"n_docs": len(gt_docs), "correlations": {}}
        print()
        print(f"=== Validierung (n={len(gt_docs)}) ===")
        for name, (values, expected_dir) in signals.items():
            rho = spearman_correlation(values, cers)
            validation["correlations"][name] = round(rho, 4)
            quality = (
                "stark" if abs(rho) > 0.7 else
                "moderat" if abs(rho) > 0.4 else
                "schwach"
            )
            print(f"  {name:>25}: rho = {rho:+.4f}  ({quality})")

    results = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "scripts/eval/quality_proxy.py",
        "method": "dictionary_hit_rate",
        "reference": "Stroebel et al. 2022 (LREC)",
        "summary": summary,
        "validation": validation,
        "documents": documents,
    }

    # JSON speichern
    output_json = EVALUATION_DIR / "quality_proxy.json"
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON: {output_json}")

    # HTML-Report
    if generate_html:
        output_html = EVALUATION_DIR / "quality_proxy.html"
        generate_html_report(results, output_html)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quality Proxy (Dictionary Hit Rate)")
    parser.add_argument("--doc", help="Einzelnes Dokument (ID)")
    parser.add_argument("--all", action="store_true", help="Alle 285 Dokumente")
    parser.add_argument("--html", action="store_true", help="HTML-Report generieren")
    args = parser.parse_args()

    doc_ids = [args.doc] if args.doc else None
    run(doc_ids=doc_ids, all_docs=args.all, generate_html=args.html)
