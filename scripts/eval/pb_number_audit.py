"""
pb-n-Plausibilitaet: prueft im Lieferbestand output/tei_final, ob die Druckseitenzahlen
konsistent im <pb n="..."> gefuehrt sind, und stellt Indizien fuer verlorene Original-
Paginierung zusammen.

NUR DIAGNOSE -- liest output/tei_final + output/layout, aendert nichts, ist KEIN Gate.
Erzeugt einen JSON-Report (output/audits/) und eine ASCII-Konsolen-Zusammenfassung.

Drei Signale je Dokument:
  scan_sequence   die @n-Folge der <pb> ist exakt 1..N (== Scan-Reihenfolge). Verdacht, dass
                  die Original-Druckpaginierung nicht erfasst wurde.
  digit_paragraphs reine Ziffern-Absaetze im body (Text nur Ziffern / Punkt-Notation 7.14 /
                  Zahl+lb+Zahl). Fundorte echter Seitenzahlen, die im Text stehen geblieben sind.
  layout_mismatch _filter-Regionen (Kopf-/Fusszeile) im Layout-JSON tragen eine reine Zahl,
                  die von pb@n derselben Seite abweicht (die Druckseitenzahl fehlt am <pb>).

Aufruf:
    python -m scripts.eval.pb_number_audit               # Summen (stdout) + JSON
    python -m scripts.eval.pb_number_audit --dir PFAD    # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR, LAYOUT_DIR).
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from scripts.config import LAYOUT_DIR, OUTPUT_DIR, TEI_FINAL_DIR, TEI_NS

AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audits"

# pure digits or dot-notation page numbers (7.14, 248); whitespace stripped by caller
_DIGIT_RE = re.compile(r"^\d+(?:\.\d+)*$")
_LAYOUT_FILE_RE = re.compile(r"_p(\d+)_layout_gemini\.json$")
_BRACKET_RE = re.compile(r"[\[\]()]")

# Classification thresholds (deterministic; tuned on the calibrated known cases).
_MIN_NUMERIC = 3          # below this a document carries too little signal
_SCAN_MATCH_MIN = 0.5     # split between "mostly scan" and "mostly non-scan"
_SCAN_HIGH = 0.85         # scan-match ratio that alone confirms scan_sequence
_WILD_DEVIATION = 50      # |pb@n - scan position| above which a page is a wild outlier
_WILD_MIN_COUNT = 2       # wild pages inside an otherwise-scan doc -> mixed regime
_FOOTER_MATCH_MIN = 0.5   # pb@n == printed footer on this share of pages -> printed_folio
_ASC_MIN = 0.8            # share of ascending steps that makes a non-scan pagination plausible
_BRACKET_MIN = 0.5        # share of bracketed @n values that flips the orthogonal flag


def is_scan_sequence(ns) -> bool:
    """True iff the @n list is exactly ['1','2',...,'N'] (matches the scan sequence)."""
    return bool(ns) and all(n == str(i + 1) for i, n in enumerate(ns))


def _element_text(el) -> str:
    """Concatenate all descendant text of an element (joins number+lb+number)."""
    return "".join(el.itertext())


def analyze_body(root) -> dict:
    """Extract pb @n order and pure-digit paragraphs (with their sequential page) from <body>."""
    body = root.find(f".//{{{TEI_NS}}}body")
    if body is None:
        return {"pb_ns": [], "digit_paragraphs": []}
    pb_tag = f"{{{TEI_NS}}}pb"
    p_tag = f"{{{TEI_NS}}}p"
    pb_ns = []
    digit_paragraphs = []
    page = 0
    for el in body.iter():
        if el.tag == pb_tag:
            page += 1
            pb_ns.append(el.get("n"))
        elif el.tag == p_tag:
            txt = _element_text(el).strip()
            if txt and _DIGIT_RE.match(txt):
                digit_paragraphs.append({"page": page, "value": txt})
    return {"pb_ns": pb_ns, "digit_paragraphs": digit_paragraphs}


def read_layout_page_numbers(layout_doc_dir) -> dict:
    """Print-page-number candidates from a document's Gemini layout JSONs.

    Returns {sequential_page(int): [number(str), ...]} for _filter regions whose text is a
    pure number. Silently skips missing dir / unreadable files (diagnosis, not a gate).
    """
    out = {}
    d = Path(layout_doc_dir)
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*_layout_gemini.json")):
        m = _LAYOUT_FILE_RE.search(f.name)
        if not m:
            continue
        page = int(m.group(1))
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        nums = []
        for region in data.get("regions", []):
            if region.get("zbz_tag") != "_filter":
                continue
            txt = (region.get("text") or "").strip()
            if txt and _DIGIT_RE.match(txt):
                nums.append(txt)
        if nums:
            out[page] = nums
    return out


def compare_layout_to_pb(pb_ns, layout_page_numbers) -> list:
    """Mismatches between layout print numbers and pb@n of the same sequential page."""
    out = []
    for page in sorted(layout_page_numbers):
        if page < 1 or page > len(pb_ns):
            continue
        pb_n = pb_ns[page - 1]
        for num in layout_page_numbers[page]:
            if num != pb_n:
                out.append({"page": page, "layout_number": num, "pb_n": pb_n})
    return out


def _pb_to_int(n):
    """Parse a pb@n into an int, tolerating brackets/parens; None if not a plain number."""
    if not n:
        return None
    s = _BRACKET_RE.sub("", n).strip()
    if s.isdigit():
        return int(s)
    return None


def _footer_stats(pb_ints, layout_page_numbers):
    """How often pb@n equals a printed footer number on the same sequential page."""
    footer_pages = 0
    footer_match = 0
    offsets = []
    for page in sorted(layout_page_numbers or {}):
        if page < 1 or page > len(pb_ints):
            continue
        pb_val = pb_ints[page - 1]
        if pb_val is None:
            continue
        nums = [int(x) for x in layout_page_numbers[page] if x.isdigit()]
        if not nums:
            continue
        footer_pages += 1
        if pb_val in nums:
            footer_match += 1
        if len(nums) == 1:
            offsets.append(pb_val - nums[0])
    ratio = footer_match / footer_pages if footer_pages else 0.0
    offset_mode = Counter(offsets).most_common(1)[0][0] if offsets else None
    return footer_pages, footer_match, round(ratio, 3), offset_mode


def classify_document(pb_ns, layout_page_numbers=None):
    """Classify the semantics of pb@n for one document (deterministic).

    class: scan_sequence | printed_folio | mixed | undetermined.
    bracket: orthogonal flag whether the @n values are bracketed ("[7]").
    Uses the layout footer numbers (per sequential page) as a corroborating signal.
    """
    n_total = len(pb_ns)
    pb_ints = [_pb_to_int(n) for n in pb_ns]
    numeric = [(i, v) for i, v in enumerate(pb_ints) if v is not None]
    n_numeric = len(numeric)

    bracket_hits = sum(1 for n in pb_ns if n and _BRACKET_RE.search(n))
    bracket_ratio = bracket_hits / n_total if n_total else 0.0

    scan_match = sum(1 for i, v in numeric if v == i + 1)
    scan_ratio = scan_match / n_numeric if n_numeric else 0.0
    wild = [i for i, v in numeric if abs(v - (i + 1)) > _WILD_DEVIATION]

    seq = [v for _, v in numeric]
    asc_pairs = sum(1 for a, b in zip(seq, seq[1:]) if b > a)
    asc_ratio = asc_pairs / (len(seq) - 1) if len(seq) > 1 else 0.0

    footer_pages, footer_match, footer_ratio, footer_offset = _footer_stats(
        pb_ints, layout_page_numbers
    )

    if n_numeric < _MIN_NUMERIC:
        klass = "undetermined"
    elif scan_ratio >= _SCAN_MATCH_MIN:
        if len(wild) >= _WILD_MIN_COUNT:
            klass = "mixed"
        elif scan_ratio >= _SCAN_HIGH:
            klass = "scan_sequence"
        elif footer_ratio >= _FOOTER_MATCH_MIN:
            klass = "printed_folio"
        else:
            klass = "scan_sequence"
    else:
        if footer_ratio >= _FOOTER_MATCH_MIN:
            klass = "printed_folio"
        elif asc_ratio >= _ASC_MIN:
            klass = "printed_folio"
        else:
            klass = "undetermined"

    if bracket_ratio >= _BRACKET_MIN:
        bracket = "bracketed"
    elif n_numeric:
        bracket = "unbracketed"
    else:
        bracket = "undetermined"

    confidence = _confidence(klass, scan_ratio, footer_ratio, asc_ratio, len(wild), n_numeric)

    return {
        "class": klass,
        "bracket": bracket,
        "confidence": confidence,
        "signals": {
            "pb_count": n_total,
            "numeric_pb": n_numeric,
            "blank_or_nonnumeric_pb": n_total - n_numeric,
            "scan_match_ratio": round(scan_ratio, 3),
            "ascending_ratio": round(asc_ratio, 3),
            "wild_count": len(wild),
            "footer_pages": footer_pages,
            "footer_match_ratio": footer_ratio,
            "footer_offset_mode": footer_offset,
            "bracket_ratio": round(bracket_ratio, 3),
        },
        "examples": [n for n in pb_ns[:12]],
    }


def _confidence(klass, scan_ratio, footer_ratio, asc_ratio, wild_count, n_numeric):
    if klass == "undetermined":
        return "low"
    if n_numeric < 5:
        return "medium"
    if klass == "scan_sequence" and scan_ratio >= 0.95:
        return "high"
    if klass == "printed_folio" and (footer_ratio >= 0.8 or asc_ratio >= 0.95):
        return "high"
    if klass == "mixed" and wild_count >= _WILD_MIN_COUNT and scan_ratio >= 0.6:
        return "high"
    return "medium"


def classification_summary(docs) -> dict:
    """Corpus tallies per class and per bracket flag over classified documents."""
    by_class = Counter()
    by_bracket = Counter()
    for f in docs.values():
        cl = f.get("classification")
        if not cl:
            continue
        by_class[cl["class"]] += 1
        by_bracket[cl["bracket"]] += 1
    return {"by_class": dict(by_class), "by_bracket": dict(by_bracket)}


def audit_document(tei_path, layout_dir=LAYOUT_DIR):
    """Diagnose one document. Returns (findings, error_text)."""
    doc_id = Path(tei_path).stem.replace("_final", "")
    try:
        root = ET.parse(str(tei_path)).getroot()
    except (ET.ParseError, OSError) as exc:
        return None, str(exc)
    body = analyze_body(root)
    layout_nums = read_layout_page_numbers(Path(layout_dir) / doc_id)
    return {
        "scan_sequence": is_scan_sequence(body["pb_ns"]),
        "pb_count": len(body["pb_ns"]),
        "digit_paragraphs": body["digit_paragraphs"],
        "layout_mismatch": compare_layout_to_pb(body["pb_ns"], layout_nums),
        "classification": classify_document(body["pb_ns"], layout_nums),
    }, None


def audit_corpus(tei_dir, layout_dir=LAYOUT_DIR) -> dict:
    files = sorted(Path(tei_dir).glob("*_final.xml"))
    docs = {}
    errors = []
    for f in files:
        doc_id = f.stem.replace("_final", "")
        findings, err = audit_document(f, layout_dir=layout_dir)
        if err:
            errors.append((doc_id, err))
            continue
        docs[doc_id] = findings
    return {"total_files": len(files), "docs": docs, "errors": errors}


def _print_summary(summary):
    docs = summary["docs"]
    scan_docs = [d for d, f in docs.items() if f["scan_sequence"]]
    dp_docs = {d: f["digit_paragraphs"] for d, f in docs.items() if f["digit_paragraphs"]}
    mm_docs = {d: f["layout_mismatch"] for d, f in docs.items() if f["layout_mismatch"]}
    dp_total = sum(len(v) for v in dp_docs.values())
    mm_total = sum(len(v) for v in mm_docs.values())
    print(f"pb-n-Plausibilitaet ueber {summary['total_files']} Dokumente\n")
    print(f"  Dokumente mit pb@n == Scan-Sequenz 1..N: {len(scan_docs)}")
    print(f"  Dokumente mit Ziffern-Absaetzen im body:  {len(dp_docs)}  ({dp_total} Absaetze)")
    print(f"  Dokumente mit Layout/pb-Abweichung:       {len(mm_docs)}  ({mm_total} Seiten)")
    if summary["errors"]:
        print(f"  Parse-Fehler: {len(summary['errors'])}")
    top_dp = sorted(dp_docs.items(), key=lambda kv: -len(kv[1]))[:8]
    if top_dp:
        print("\n  Top Ziffern-Absaetze (doc: Anzahl, Beispiele):")
        for d, v in top_dp:
            ex = ", ".join(f"S{x['page']}={x['value']}" for x in v[:4])
            print(f"    {d}: {len(v)}  ({ex})")
    top_mm = sorted(mm_docs.items(), key=lambda kv: -len(kv[1]))[:8]
    if top_mm:
        print("\n  Top Layout/pb-Abweichung (doc: Anzahl, Beispiele):")
        for d, v in top_mm:
            ex = ", ".join(f"S{x['page']} layout={x['layout_number']} pb={x['pb_n']}" for x in v[:3])
            print(f"    {d}: {len(v)}  ({ex})")

    summ = classification_summary(docs)
    print("\n  pb@n-Semantik je Dokument (Klasse: Anzahl):")
    for cls in ("scan_sequence", "printed_folio", "mixed", "undetermined"):
        print(f"    {cls:14s}: {summ['by_class'].get(cls, 0)}")
    print("  Klammerung (orthogonal):")
    for br in ("bracketed", "unbracketed", "undetermined"):
        print(f"    {br:14s}: {summ['by_bracket'].get(br, 0)}")
    pf = [d for d, f in docs.items() if f.get("classification", {}).get("class") == "printed_folio"]
    mx = [d for d, f in docs.items() if f.get("classification", {}).get("class") == "mixed"]
    if pf:
        print(f"\n  printed_folio-Dokumente: {', '.join(sorted(pf, key=_doc_sort)[:20])}")
    if mx:
        print(f"  mixed-Dokumente:         {', '.join(sorted(mx, key=_doc_sort)[:20])}")


def _doc_sort(d):
    return (0, int(d)) if d.isdigit() else (1, d)


def _write_report(summary, tei_dir):
    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_OUTPUT_DIR / "pb_number_audit.json"
    docs = summary["docs"]
    payload = {
        "audit": "pb_number",
        "tei_dir": str(tei_dir),
        "total_files": summary["total_files"],
        "corpus_totals": {
            "scan_sequence_docs": sum(1 for f in docs.values() if f["scan_sequence"]),
            "digit_paragraph_docs": sum(1 for f in docs.values() if f["digit_paragraphs"]),
            "layout_mismatch_docs": sum(1 for f in docs.values() if f["layout_mismatch"]),
        },
        "classification_summary": classification_summary(docs),
        "documents": docs,
        "errors": summary["errors"],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON-Report: {out}")


def main():
    parser = argparse.ArgumentParser(
        description="pb-n-Plausibilitaet (Diagnose, schreibt nichts an den TEI-Daten)"
    )
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    args = parser.parse_args()
    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    _write_report(summary, tei_dir)


if __name__ == "__main__":
    main()
