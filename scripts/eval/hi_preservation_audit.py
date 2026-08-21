"""
hi-Erhaltung: prueft, ob typografische Hervorhebungen aus der Basis-OCR im ausgelieferten
TEI als <hi> erhalten sind.

NUR DIAGNOSE -- liest output/tei_final + output/mistral_results, aendert nichts, ist KEIN Gate.
Erzeugt einen JSON-Report (output/audits/) und eine ASCII-Konsolen-Zusammenfassung.

Regel: fuer jede Seite, deren OCR-Markdown (output/mistral_results/{doc}_p{N}.md) eine Markdown-
Emphasis (*wort* / **wort** / _wort_) traegt, muss der zugehoerige TEI-Seitenabschnitt mindestens
ein <hi> enthalten. Die Seite ist die sequenzielle <pb>-Position (NICHT @n), segmentiert ueber
scripts/core/pb_split.iter_page_spans (dieselbe Regel wie Mirror-Splitter und Blank-Marker).
Gemeldet werden Seiten mit Emphasis-Signal, aber ohne <hi> im TEI-Abschnitt.

Aufruf:
    python -m scripts.eval.hi_preservation_audit             # Summen (stdout) + JSON
    python -m scripts.eval.hi_preservation_audit --dir PFAD  # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR, MISTRAL_RESULTS_DIR).
"""
import re
from pathlib import Path

from scripts.config import MISTRAL_RESULTS_DIR
from scripts.core.pb_split import BODY_INNER_RE, iter_page_spans
from scripts.eval.audit_common import (
    doc_id_from_path,
    iter_final_tei,
    resolve_tei_dir,
    write_audit_report,
)

# Markdown emphasis: runs of * or _ around non-space content (bold ** counts as a signal too).
# Underscore needs non-word boundaries so snake_case identifiers do not match.
_EMPH_STAR_RE = re.compile(r"\*+(?!\s)([^*\n]+?)(?<!\s)\*+")
_EMPH_UNDER_RE = re.compile(r"(?<![\w])_+(?!\s)([^_\n]+?)(?<!\s)_+(?![\w])")
_MISTRAL_FILE_RE = re.compile(r"_p(\d+)\.md$")


def has_emphasis(md_text: str) -> bool:
    """True iff the markdown carries at least one emphasis span."""
    return bool(_EMPH_STAR_RE.search(md_text) or _EMPH_UNDER_RE.search(md_text))


def mistral_pages(mistral_dir, doc_id) -> dict:
    """{page(int): Path} for a document's OCR markdown pages."""
    out = {}
    for f in Path(mistral_dir).glob(f"{doc_id}_p*.md"):
        m = _MISTRAL_FILE_RE.search(f.name)
        if m:
            out[int(m.group(1))] = f
    return out


def page_span_content(body_inner: str, page: int):
    """TEI text of the given sequential page (1-based pb position), or None if absent."""
    for span in iter_page_spans(body_inner):
        if span.page == page:
            return body_inner[span.content_start:span.content_end]
    return None


def span_has_hi(content: str) -> bool:
    return "<hi" in content


def audit_document(tei_path, mistral_dir=MISTRAL_RESULTS_DIR):
    """Diagnose one document. Returns (findings, error_text)."""
    doc_id = doc_id_from_path(tei_path)
    try:
        tei_text = Path(tei_path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, str(exc)
    m = BODY_INNER_RE.search(tei_text)
    body_inner = m.group(1) if m else ""
    has_any_hi = "<hi" in body_inner

    pages = mistral_pages(mistral_dir, doc_id)
    emphasis_pages = 0
    missing_hi = []
    no_tei_page = []
    for page in sorted(pages):
        try:
            md = pages[page].read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not has_emphasis(md):
            continue
        emphasis_pages += 1
        content = page_span_content(body_inner, page)
        if content is None:
            no_tei_page.append(page)
        elif not span_has_hi(content):
            missing_hi.append({"page": page})
    return {
        "emphasis_pages": emphasis_pages,
        "has_any_hi": has_any_hi,
        "missing_hi": missing_hi,
        "no_tei_page": no_tei_page,
    }, None


def audit_corpus(tei_dir, mistral_dir=MISTRAL_RESULTS_DIR) -> dict:
    docs = {}
    errors = []
    total = 0
    for doc_id, f in iter_final_tei(tei_dir):
        total += 1
        findings, err = audit_document(f, mistral_dir=mistral_dir)
        if err:
            errors.append((doc_id, err))
            continue
        docs[doc_id] = findings
    return {"total_files": total, "docs": docs, "errors": errors}


def _print_summary(summary):
    docs = summary["docs"]
    emph_total = sum(f["emphasis_pages"] for f in docs.values())
    docs_with_hi = sum(1 for f in docs.values() if f["has_any_hi"])
    miss_docs = {d: f["missing_hi"] for d, f in docs.items() if f["missing_hi"]}
    miss_total = sum(len(v) for v in miss_docs.values())
    notei_total = sum(len(f["no_tei_page"]) for f in docs.values())
    print(f"hi-Erhaltung ueber {summary['total_files']} Dokumente\n")
    print(f"  OCR-Seiten mit Emphasis-Signal:        {emph_total}")
    print(f"  TEIs mit mindestens einem <hi>:        {docs_with_hi}")
    print(f"  Seiten Signal-aber-kein-hi:            {miss_total}  (in {len(miss_docs)} Dok)")
    print(f"  Seiten Signal-aber-kein-TEI-Abschnitt: {notei_total}  (Count-Mismatch)")
    if summary["errors"]:
        print(f"  Parse-Fehler: {len(summary['errors'])}")
    top = sorted(miss_docs.items(), key=lambda kv: -len(kv[1]))[:12]
    if top:
        print("\n  Top Signal-ohne-hi (doc: Seiten):")
        for d, v in top:
            has_any = "hat sonst hi" if docs[d]["has_any_hi"] else "gar kein hi"
            pages = ", ".join(str(x["page"]) for x in v[:8])
            print(f"    {d}: {len(v)}  ({pages})  [{has_any}]")


def _write_report(summary, tei_dir):
    docs = summary["docs"]
    payload = {
        "audit": "hi_preservation",
        "tei_dir": str(tei_dir),
        "total_files": summary["total_files"],
        "corpus_totals": {
            "emphasis_pages": sum(f["emphasis_pages"] for f in docs.values()),
            "docs_with_any_hi": sum(1 for f in docs.values() if f["has_any_hi"]),
            "missing_hi_pages": sum(len(f["missing_hi"]) for f in docs.values()),
            "no_tei_page": sum(len(f["no_tei_page"]) for f in docs.values()),
        },
        "documents": docs,
        "errors": summary["errors"],
    }
    write_audit_report("hi_preservation_audit", payload)


def main():
    tei_dir = resolve_tei_dir("hi-Erhaltung (Diagnose, schreibt nichts an den TEI-Daten)")
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    _write_report(summary, tei_dir)


if __name__ == "__main__":
    main()
