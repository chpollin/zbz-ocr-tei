"""
Leerseiten-Text-Audit: findet Text im ausgelieferten TEI auf Seiten, die als leer gelten.

NUR DIAGNOSE -- liest output/tei_final (TEI + Manifest) und den Layout-Mirror unter
docs/data/pages, aendert nichts, ist KEIN Gate. Erzeugt output/audits/blank_text_audit.json
und eine ASCII-Konsolen-Zusammenfassung.

Anlass: die Entity-Evaluation fand eine vollstaendig halluzinierte OCR-Seite auf einer
leeren Vorlage (Dok 1520, S. 130) und eine OCR-Wiederholungsschleife (Dok 900, S. 2).
Traegt eine leere Vorlage im gelieferten TEI substanziellen Text, ist dieser Text verdaechtig
(Halluzination oder Seitenversatz) und verzerrt zusaetzlich den CER-Kontext.

Zwei Leer-Signale, weil eines allein den Anlassfall nicht sieht:

  1. `manifest`: die Leerseiten aus `output/tei_final/{doc}_manifest.json` (Klasse `blank`,
     gesetzt von scripts/edition/page_manifest.py aus OCR-Regel + Docling-Nullregionen).
     Dieses Signal ist OCR-getrieben; halluziniert die OCR auf einer leeren Vorlage genug
     Text, wird die Seite nie als blank klassifiziert und faellt hier durch.
  2. `layout`: Seiten mit `num_regions == 0` im Docling-Mirror, die das Manifest NICHT als
     blank fuehrt. Das Layout-Signal ist von der OCR unabhaengig und faengt genau den Fall
     halluzinierter Text auf leerer Vorlage.

Die Seitenzahl ist die sequenzielle <pb>-Position (NICHT @n), segmentiert ueber
scripts/tei/pb_split.iter_page_spans -- dieselbe Regel wie Mirror-Splitter und Blank-Marker.

Aufruf:
    python -m scripts.eval.blank_text_audit                  # Korpus-Audit + JSON
    python -m scripts.eval.blank_text_audit --dir PFAD       # alternatives TEI-Verzeichnis
    python -m scripts.eval.blank_text_audit --page 1520:130  # eine Seite im Detail
"""
import argparse
import html
import json
import re
from pathlib import Path

from scripts.config import DOCS_DIR, TEI_FINAL_DIR
from scripts.eval.audit_common import (
    iter_final_tei,
    write_audit_report,
)
from scripts.tei.pb_split import BODY_INNER_RE, iter_page_spans

MIRROR_PAGES_DIR = DOCS_DIR / "data" / "pages"

# Textmenge einer Seite nach Markup-Entfernung und Whitespace-Normalisierung.
# <=20 Zeichen: eine Seitenzahl, ein Kolumnentitel oder ein Rest-Artefakt -- fuer eine
# Leerseite unauffaellig. >=200 Zeichen: mehrere Saetze, die auf einer leeren Vorlage
# keine Entsprechung haben koennen. Dazwischen bleibt die Grauzone `marginal`, die der
# Operator sichtet, ohne dass sie den Befund traegt.
EMPTY_MAX_CHARS = 20
SUBSTANTIAL_MIN_CHARS = 200
SNIPPET_CHARS = 150

# Anlassfaelle der Entity-Evaluation; im Report als benannte Bodenproben mitgefuehrt.
GROUND_CASES = (("1520", 130), ("900", 2))

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PI_RE = re.compile(r"<\?.*?\?>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]*>")
_WS_RE = re.compile(r"\s+")
_LAYOUT_FILE_RE = re.compile(r"_p(\d+)_layout\.json$")


def strip_markup(fragment: str) -> str:
    """Sichtbarer Text eines XML-Fragments, Whitespace auf einfache Blanks normalisiert."""
    if not fragment:
        return ""
    text = _COMMENT_RE.sub(" ", fragment)
    text = _PI_RE.sub(" ", text)
    # Entities erst nach der Tag-Entfernung aufloesen, sonst wird &lt;p&gt; zum Tag.
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def classify(n_chars: int) -> str:
    """Klasse der Textmenge einer Leerseite: empty | marginal | substantial."""
    if n_chars <= EMPTY_MAX_CHARS:
        return "empty"
    if n_chars >= SUBSTANTIAL_MIN_CHARS:
        return "substantial"
    return "marginal"


def facsimile_path(doc_id: str, page: int) -> str:
    """Repo-relativer Pfad des Seitenbildes, damit der Operator den Befund ansehen kann."""
    return f"docs/images/{doc_id}/{doc_id}_p{page:03d}.png"


def page_texts(tei_text: str) -> dict:
    """{Seitenzahl(int): bereinigter Text} eines assemblierten TEI-Dokuments."""
    match = BODY_INNER_RE.search(tei_text)
    if not match:
        return {}
    body_inner = match.group(1)
    spans = iter_page_spans(body_inner)
    if not spans:
        return {1: strip_markup(body_inner)}
    return {s.page: strip_markup(body_inner[s.content_start:s.content_end]) for s in spans}


def manifest_blank_pages(manifest) -> list:
    """Seitenzahlen der Klasse `blank`. Tolerant gegen fehlende oder kaputte Abschnitte."""
    pages = (manifest or {}).get("pages") if isinstance(manifest, dict) else None
    if not isinstance(pages, dict):
        return []
    out = []
    for key, value in pages.items():
        if not isinstance(value, dict) or value.get("class") != "blank":
            continue
        try:
            out.append(int(key))
        except (TypeError, ValueError):
            continue
    return sorted(out)


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def layout_zero_pages(doc_id: str, mirror_dir) -> list:
    """Seiten, deren Docling-Layout null Regionen meldet (OCR-unabhaengiges Leer-Signal)."""
    doc_dir = Path(mirror_dir) / str(doc_id)
    if not doc_dir.is_dir():
        return []
    out = []
    for f in doc_dir.glob(f"{doc_id}_p*_layout.json"):
        m = _LAYOUT_FILE_RE.search(f.name)
        if not m:
            continue
        data = _load_json(f)
        if not isinstance(data, dict):
            continue
        regions = data.get("num_regions")
        if regions is None:
            listed = data.get("regions")
            regions = len(listed) if isinstance(listed, list) else None
        if regions == 0:
            out.append(int(m.group(1)))
    return sorted(out)


def _finding(doc_id, page, text, signal, docling_regions=None):
    return {
        "doc_id": doc_id,
        "page": page,
        "chars": len(text),
        "class": classify(len(text)),
        "signal": signal,
        "docling_regions": docling_regions,
        "snippet": text[:SNIPPET_CHARS],
        "facsimile": facsimile_path(doc_id, page),
    }


def audit_document(doc_id, tei_dir, mirror_dir=MIRROR_PAGES_DIR) -> dict:
    """Diagnose eines Dokuments. Fehlende Manifeste oder Layout-Daten sind kein Fehler."""
    tei_dir = Path(tei_dir)
    tei_path = tei_dir / f"{doc_id}_final.xml"
    report = {
        "doc_id": doc_id,
        "manifest_found": (tei_dir / f"{doc_id}_manifest.json").exists(),
        "pages_in_tei": 0,
        "blank_pages": 0,
        "by_class": {"empty": 0, "marginal": 0, "substantial": 0},
        "findings": [],
        "blank_pages_missing_in_tei": [],
        "non_blank_empty_pages": [],
        "error": None,
    }
    try:
        tei_text = tei_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        report["error"] = str(exc)
        return report

    texts = page_texts(tei_text)
    report["pages_in_tei"] = len(texts)
    if not texts:
        report["error"] = "kein <body>"

    manifest = _load_json(tei_dir / f"{doc_id}_manifest.json")
    blank_pages = manifest_blank_pages(manifest)
    blank_set = set(blank_pages)
    report["blank_pages"] = len(blank_pages)

    for page in blank_pages:
        if page not in texts:
            report["blank_pages_missing_in_tei"].append(page)
            continue
        text = texts[page]
        klass = classify(len(text))
        report["by_class"][klass] += 1
        if klass != "empty":
            report["findings"].append(_finding(doc_id, page, text, "manifest"))

    for page in layout_zero_pages(doc_id, mirror_dir):
        if page in blank_set or page not in texts:
            continue
        text = texts[page]
        if classify(len(text)) == "empty":
            continue
        report["findings"].append(_finding(doc_id, page, text, "layout", docling_regions=0))

    report["non_blank_empty_pages"] = sorted(
        p for p, t in texts.items() if p not in blank_set and len(t) <= EMPTY_MAX_CHARS
    )
    report["findings"].sort(key=lambda f: f["page"])
    return report


def audit_corpus(tei_dir=TEI_FINAL_DIR, mirror_dir=MIRROR_PAGES_DIR) -> dict:
    """Korpus-Audit. Dokumente numerisch sortiert, damit der Report stabil bleibt."""
    doc_ids = [doc_id for doc_id, _ in iter_final_tei(tei_dir)]
    doc_ids.sort(key=lambda d: (0, int(d)) if d.isdigit() else (1, 0))
    docs = {d: audit_document(d, tei_dir, mirror_dir) for d in doc_ids}

    totals = {
        "blank_pages": sum(r["blank_pages"] for r in docs.values()),
        "by_class": {
            k: sum(r["by_class"][k] for r in docs.values())
            for k in ("empty", "marginal", "substantial")
        },
        "manifest_findings": sum(
            1 for r in docs.values() for f in r["findings"] if f["signal"] == "manifest"),
        "layout_findings": sum(
            1 for r in docs.values() for f in r["findings"] if f["signal"] == "layout"),
        "substantial_findings": sum(
            1 for r in docs.values() for f in r["findings"] if f["class"] == "substantial"),
        "blank_pages_missing_in_tei": sum(
            len(r["blank_pages_missing_in_tei"]) for r in docs.values()),
        "non_blank_empty_pages": sum(len(r["non_blank_empty_pages"]) for r in docs.values()),
        "docs_with_findings": sum(1 for r in docs.values() if r["findings"]),
        "docs_without_manifest": sum(1 for r in docs.values() if not r["manifest_found"]),
    }
    return {
        "tei_dir": str(tei_dir),
        "total_docs": len(docs),
        "totals": totals,
        "docs": docs,
        "errors": sorted((d, r["error"]) for d, r in docs.items() if r["error"]),
    }


def top_findings(summary: dict, limit: int = 5) -> list:
    """Die textreichsten Funde des Korpus, absteigend nach Zeichenzahl."""
    flat = [f for r in summary["docs"].values() for f in r["findings"]]
    flat.sort(key=lambda f: (-f["chars"], f["doc_id"], f["page"]))
    return flat[:limit]


def inspect_page(doc_id, page, tei_dir=TEI_FINAL_DIR, mirror_dir=MIRROR_PAGES_DIR) -> dict:
    """Vollbild einer einzelnen Seite (Bodenproben, Operator-Nachschau ueber --page)."""
    tei_dir = Path(tei_dir)
    manifest = _load_json(tei_dir / f"{doc_id}_manifest.json")
    blank = page in set(manifest_blank_pages(manifest))
    layout = _load_json(Path(mirror_dir) / str(doc_id) / f"{doc_id}_p{page:03d}_layout.json")
    regions = layout.get("num_regions") if isinstance(layout, dict) else None

    info = {
        "doc_id": doc_id,
        "page": page,
        "manifest_found": (tei_dir / f"{doc_id}_manifest.json").exists(),
        "manifest_blank": blank,
        "docling_regions": regions,
        "in_tei": False,
        "chars": 0,
        "class": None,
        "snippet": "",
        "facsimile": facsimile_path(doc_id, page),
    }
    try:
        tei_text = (tei_dir / f"{doc_id}_final.xml").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return info
    texts = page_texts(tei_text)
    if page not in texts:
        return info
    text = texts[page]
    info.update({"in_tei": True, "chars": len(text), "class": classify(len(text)),
                 "snippet": text[:SNIPPET_CHARS]})
    return info


def build_payload(summary: dict, ground_cases=GROUND_CASES, tei_dir=None, mirror_dir=None) -> dict:
    """Deterministischer JSON-Payload: stabile Reihenfolge, keine Zeitstempel."""
    tei_dir = tei_dir if tei_dir is not None else summary["tei_dir"]
    mirror_dir = mirror_dir if mirror_dir is not None else MIRROR_PAGES_DIR
    documents = {}
    for doc_id, r in summary["docs"].items():
        if not (r["findings"] or r["non_blank_empty_pages"] or r["blank_pages_missing_in_tei"]
                or r["error"]):
            continue
        documents[doc_id] = {
            "blank_pages": r["blank_pages"],
            "by_class": r["by_class"],
            "findings": r["findings"],
            "blank_pages_missing_in_tei": r["blank_pages_missing_in_tei"],
            "non_blank_empty_pages": r["non_blank_empty_pages"],
            "error": r["error"],
        }
    cases = [inspect_page(d, p, tei_dir, mirror_dir) for d, p in ground_cases
             if d in summary["docs"]]
    return {
        "audit": "blank_text",
        "tei_dir": str(summary["tei_dir"]),
        "thresholds": {
            "empty_max_chars": EMPTY_MAX_CHARS,
            "substantial_min_chars": SUBSTANTIAL_MIN_CHARS,
        },
        "total_docs": summary["total_docs"],
        "corpus_totals": summary["totals"],
        "ground_cases": cases,
        "top_findings": top_findings(summary, limit=20),
        "documents": documents,
        "errors": summary["errors"],
    }


def _ascii(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def _print_summary(summary, payload):
    t = summary["totals"]
    print(f"Leerseiten-Text-Audit ueber {summary['total_docs']} Dokumente\n")
    print(f"  Leerseiten laut Manifest:            {t['blank_pages']}")
    print(f"    davon ohne Text (empty):           {t['by_class']['empty']}")
    print(f"    davon marginal:                    {t['by_class']['marginal']}")
    print(f"    davon substanziell (Befund):       {t['by_class']['substantial']}")
    print(f"    ohne pb-Abschnitt im TEI:          {t['blank_pages_missing_in_tei']}")
    print("  Zweitkanal Layout (Docling 0 Regionen, nicht manifest-blank):")
    print(f"    Seiten mit Text (Befund):          {t['layout_findings']}")
    print(f"  Befunde gesamt / substanziell:       "
          f"{t['manifest_findings'] + t['layout_findings']} / {t['substantial_findings']}"
          f"  (in {t['docs_with_findings']} Dok)")
    print(f"  Inverssignal: Seiten ohne Text, nicht als blank gefuehrt: "
          f"{t['non_blank_empty_pages']}")
    if t["docs_without_manifest"]:
        print(f"  Dokumente ohne Manifest:             {t['docs_without_manifest']}")
    if summary["errors"]:
        print(f"  Parse-Fehler:                        {len(summary['errors'])}")

    print("\n  Bodenproben (Anlassfaelle der Entity-Evaluation):")
    for c in payload["ground_cases"]:
        state = "manifest-blank" if c["manifest_blank"] else "nicht manifest-blank"
        print(f"    Dok {c['doc_id']} S. {c['page']}: {state}, Docling-Regionen "
              f"{c['docling_regions']}, TEI-Text {c['chars']} Zeichen ({c['class']})")
        if c["snippet"]:
            print(f"      {_ascii(c['snippet'][:100])}")

    top = payload["top_findings"][:5]
    if top:
        print("\n  Textreichste Befunde:")
        for f in top:
            print(f"    Dok {f['doc_id']:>5} S. {f['page']:>3}  {f['chars']:>6} Zeichen  "
                  f"[{f['signal']}]  {f['facsimile']}")
            print(f"      {_ascii(f['snippet'][:100])}")


def _parse_page_arg(value):
    doc_id, _, page = value.partition(":")
    if not doc_id or not page.isdigit():
        raise argparse.ArgumentTypeError("Format: DOC:SEITE, z.B. 1520:130")
    return doc_id, int(page)


def main():
    parser = argparse.ArgumentParser(
        description="Leerseiten-Text-Audit (Diagnose, schreibt nichts an den TEI-Daten)")
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    parser.add_argument("--page", type=_parse_page_arg,
                        help="Nur eine Seite im Detail zeigen, Format DOC:SEITE")
    args = parser.parse_args()
    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR

    if args.page:
        doc_id, page = args.page
        info = inspect_page(doc_id, page, tei_dir)
        for key in ("doc_id", "page", "manifest_found", "manifest_blank", "docling_regions",
                    "in_tei", "chars", "class", "facsimile"):
            print(f"  {key:<16} {info[key]}")
        print(f"  snippet          {_ascii(info['snippet'])}")
        return

    summary = audit_corpus(tei_dir)
    payload = build_payload(summary, tei_dir=tei_dir)
    _print_summary(summary, payload)
    write_audit_report("blank_text_audit", payload)


if __name__ == "__main__":
    main()
