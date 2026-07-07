"""
Zeichen-Lint: prueft den Lieferbestand output/tei_final gegen die Zeichen-Regeln aus
dem Editionsrichtlinien-Kapitel "Allgemeines" (data/source/guidelines/Editionsrichtlinien_ZBZ.md).

NUR DIAGNOSE -- liest output/tei_final, aendert keine TEIs, ist KEIN Pass/Fail-Gate. Erzeugt
einen JSON-Report (output/audits/) und eine ASCII-Konsolen-Zusammenfassung.

Gemeldete Klassen (nur Textknoten im <body>, keine Attribute, kein teiHeader):
  straight_apostrophe   gerader Apostroph U+0027 zwischen Buchstaben (Richtlinie: U+2019)
  guillemets            "<<" / ">>" (Richtlinie normalisiert doppelte Anfuehrungszeichen auf gerade ")
  space_before_punct    echtes Zusatz-Leerzeichen vor . , (immer) und vor ; : ! ? (nur ausserhalb
                        franzoesischem Sprachkontext)
  space_type            franzoesischer Sprachkontext: regulaeres U+0020 vor ; : ? ! ">>" statt
                        schmalem geschuetztem U+202F (falscher Leerzeichen-TYP, Schweregrad niedrig)
  hyphenation_residue   Silbentrennungs-Nichtzeichen U+00AC

Der Sprachkontext kommt aus dem teiHeader (langUsage/language ident bzw. xml:lang der TEI-Wurzel);
franzoesisch heisst: mindestens ein ident beginnt mit "fr". Die franzoesische Setzerkonvention
verlangt vor ; : ? ! ">>" eine (schmale geschuetzte) Spatie, weshalb dort nur der Leerzeichen-TYP,
nicht ein Zusatzzeichen, der reale Normalisierungsbefund ist (Faksimile-Kalibrierung 2026-07-07).

Aufruf:
    python -m scripts.eval.char_lint_audit                # Summen (stdout) + JSON
    python -m scripts.eval.char_lint_audit --dir PFAD     # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR).
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR, TEI_NS

AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audits"

# U+0027 with a Unicode letter on both sides (not digit, not underscore).
_APOSTROPHE_RE = re.compile(r"(?<=[^\W\d_])'(?=[^\W\d_])")
_GUILLEMET_RE = re.compile("[«»]")
_HYPHEN_RESIDUE_RE = re.compile("¬")

# Pure-regex classes: count = number of matches.
_REGEX_CATEGORIES = {
    "straight_apostrophe": _APOSTROPHE_RE,
    "guillemets": _GUILLEMET_RE,
    "hyphenation_residue": _HYPHEN_RESIDUE_RE,
}

# Space-before-punctuation is language-aware, so it is not a plain regex class.
# Group 1 = the run of space-like chars, group 2 = the punctuation mark.
# Space-like = regular U+0020, NBSP U+00A0, narrow NBSP U+202F.
_SPACE_PUNCT_RE = re.compile("([   ]+)([.,;:!?»])")
_LOW_PUNCT = set(".,")                    # never take a French space: always an extra char
_HIGH_PUNCT = set(";:!?»")           # French convention: preceded by a thin no-break space
_FRENCH_SPACES = (" ", " ")     # already-correct (narrow) no-break spaces

# Full ordered class list (drives report structure + totals).
_CATEGORIES = [
    "straight_apostrophe",
    "guillemets",
    "space_before_punct",
    "space_type",
    "hyphenation_residue",
]

# Self-describing metadata so a later stock correction can target only the sharp class.
_CLASS_META = {
    "straight_apostrophe": {"severity": "normal", "suggestion": "U+2019"},
    "guillemets": {"severity": "normal", "suggestion": "straight double quote"},
    "space_before_punct": {"severity": "normal", "suggestion": "remove space"},
    "space_type": {"severity": "low", "suggestion": "U+202F"},
    "hyphenation_residue": {"severity": "normal", "suggestion": "join across line break"},
}

_XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _classify_space(spaces: str, punct: str, french_context: bool):
    """Route a space-before-punctuation match to its class, or None if it is clean.

    French context reinterprets ; : ? ! and the closing guillemet: there a thin no-break
    space is the correct setting, so only a plain U+0020 is a wrong space TYPE. Low
    punctuation (. ,) and every non-French high mark stay the sharp extra-char class,
    matching the historic regex (which never tracked the closing guillemet at all).
    """
    if punct in _LOW_PUNCT:
        return "space_before_punct"
    if french_context:
        if any(sp in spaces for sp in _FRENCH_SPACES):
            return None
        return "space_type"
    if punct == "»":
        return None
    return "space_before_punct"


def _ascii(s: str) -> str:
    """Fold to ASCII for the Windows console (JSON report keeps full Unicode)."""
    return s.encode("ascii", "replace").decode("ascii")


def _snippet(text: str, start: int, end: int, pad: int = 15) -> str:
    """Compact one-line context window around a match (ASCII-safe collapse of whitespace)."""
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def _record(out: dict, cat: str, text: str, start: int, end: int, max_examples: int) -> None:
    out[cat]["count"] += 1
    if len(out[cat]["examples"]) < max_examples:
        out[cat]["examples"].append(_snippet(text, start, end))


def lint_text_nodes(text_nodes, french_context: bool = False, max_examples: int = 5) -> dict:
    """Apply the character rules to a list of text-node strings.

    Returns {category: {"count": int, "examples": [snippet, ...]}}. Pure: independent
    of any XML structure so the regex behaviour can be tested directly. french_context
    routes a space before ; : ? ! or a closing guillemet into the soft space_type class.
    """
    out = {cat: {"count": 0, "examples": []} for cat in _CATEGORIES}
    for node in text_nodes:
        if not node:
            continue
        for cat, rx in _REGEX_CATEGORIES.items():
            for m in rx.finditer(node):
                _record(out, cat, node, m.start(), m.end(), max_examples)
        for m in _SPACE_PUNCT_RE.finditer(node):
            cat = _classify_space(m.group(1), m.group(2), french_context)
            if cat:
                _record(out, cat, node, m.start(), m.end(), max_examples)
    return out


def _document_is_french(root) -> bool:
    """French context signal: any langUsage ident (or the root xml:lang) begins with "fr"."""
    for lang in root.iter(f"{{{TEI_NS}}}language"):
        if (lang.get("ident") or "").lower().startswith("fr"):
            return True
    return (root.get(_XML_LANG_ATTR) or "").lower().startswith("fr")


def _body_text_nodes(root) -> list:
    """All text nodes inside <body> (element text + descendant tails), in document order."""
    body = root.find(f".//{{{TEI_NS}}}body")
    if body is None:
        return []
    nodes = []
    if body.text:
        nodes.append(body.text)
    for el in body.iter():
        for child in el:
            if child.text:
                nodes.append(child.text)
            if child.tail:
                nodes.append(child.tail)
    return nodes


# ElementTree double-decodes non-ASCII when a str still carries an encoding declaration;
# strip it so callers can pass the raw document text safely.
_XML_DECL_RE = re.compile(r"^\s*<\?xml[^>]*\?>")


def find_issues(xml_text: str, max_examples: int = 5) -> dict:
    """Lint the <body> text of a TEI document string. Attributes and teiHeader are excluded."""
    root = ET.fromstring(_XML_DECL_RE.sub("", xml_text, count=1))
    return lint_text_nodes(
        _body_text_nodes(root),
        french_context=_document_is_french(root),
        max_examples=max_examples,
    )


def audit_document(path, max_examples: int = 5):
    """Lint one TEI file. Returns (findings, error_text). findings is None on parse error.

    Parses from the file (bytes) so the XML encoding declaration is honoured correctly.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError) as exc:
        return None, str(exc)
    findings = lint_text_nodes(
        _body_text_nodes(root),
        french_context=_document_is_french(root),
        max_examples=max_examples,
    )
    return findings, None


def audit_corpus(tei_dir) -> dict:
    files = sorted(Path(tei_dir).glob("*_final.xml"))
    docs = {}
    errors = []
    for f in files:
        doc_id = f.stem.replace("_final", "")
        findings, err = audit_document(f)
        if err:
            errors.append((doc_id, err))
            continue
        if any(v["count"] for v in findings.values()):
            docs[doc_id] = findings
    return {"total_files": len(files), "docs": docs, "errors": errors}


def _corpus_totals(docs) -> dict:
    totals = {cat: 0 for cat in _CATEGORIES}
    doc_hits = {cat: 0 for cat in _CATEGORIES}
    for findings in docs.values():
        for cat in _CATEGORIES:
            c = findings[cat]["count"]
            totals[cat] += c
            if c:
                doc_hits[cat] += 1
    return {"occurrences": totals, "documents": doc_hits}


def _print_summary(summary):
    docs = summary["docs"]
    tot = _corpus_totals(docs)
    print(f"Zeichen-Lint ueber {summary['total_files']} Dokumente (Editionsrichtlinien Allgemeines)\n")
    print(f"  Dokumente mit mindestens einem Fund: {len(docs)}")
    print("  Befundklasse (Dokumente / Vorkommen):")
    labels = {
        "straight_apostrophe": "gerader Apostroph U+0027",
        "guillemets": "Guillemets << >>",
        "space_before_punct": "Zusatz-Leerzeichen vor Interpkt.",
        "space_type": "frz. Leerzeichen-Typ (soll U+202F)",
        "hyphenation_residue": "Trennungs-Residuum U+00AC",
    }
    for cat in _CATEGORIES:
        print(f"    {labels[cat]:34} {tot['documents'][cat]:4} / {tot['occurrences'][cat]}")
    if summary["errors"]:
        print(f"  Parse-Fehler: {len(summary['errors'])}")
    for cat in _CATEGORIES:
        top = sorted(docs.items(), key=lambda kv: -kv[1][cat]["count"])
        top = [(d, f[cat]["count"]) for d, f in top if f[cat]["count"]][:8]
        if top:
            print(f"\n  Top {cat} (doc: Vorkommen):")
            for d, c in top:
                ex = docs[d][cat]["examples"][:1]
                extra = f"  z.B. {_ascii(repr(ex[0]))}" if ex else ""
                print(f"    {d}: {c}{extra}")


def _write_report(summary, tei_dir):
    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_OUTPUT_DIR / "char_lint_audit.json"
    payload = {
        "audit": "char_lint",
        "tei_dir": str(tei_dir),
        "total_files": summary["total_files"],
        "classes": _CLASS_META,
        "corpus_totals": _corpus_totals(summary["docs"]),
        "documents": summary["docs"],
        "errors": summary["errors"],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON-Report: {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Zeichen-Lint (Diagnose, schreibt nichts an den TEI-Daten)"
    )
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    args = parser.parse_args()
    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    _write_report(summary, tei_dir)


if __name__ == "__main__":
    main()
