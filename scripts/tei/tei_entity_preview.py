"""M3 entity pilot: preview run of the inline GND markup on ten documents.

Wraps the tier-1 candidates found by ``scripts.tei.entity_matcher`` in the ZBZ inline
GND elements (``persName`` / ``orgName`` / ``bibl`` with ``ref="GND:..."``) and writes the
result to ``output/entity_preview/{doc}_final.xml``. Tier-2 candidates are reported as a
worklist and never written into the XML.

``output/tei_final`` is never touched: the source of truth is read only, every write goes
to the preview directory (same reversible pattern as ``tei_reassemble_preview``). The
stock run on ``tei_final`` is a separate, operator-gated tool (``tei_entity_marker``).

The wrapping itself is pure string splicing on the raw file text, applied back to front so
earlier offsets stay valid. No character of the original is changed, which is exactly what
the two per-document checks prove: the preview validates against ``data/schema/zbz_hersch.rng``,
and the concatenated text of the ``<text>`` subtree is identical before and after.

One placement rule beyond the plain span: a candidate that covers the complete content of an
existing ``<hi>`` is wrapped around that ``hi`` instead of inside it, which is the ZBZ
convention for work titles set in italics (knowledge/entity-integration.md, target model).

Deterministic, offline, no model call.

Usage:
    python -m scripts.tei.tei_entity_preview --panel
    python -m scripts.tei.tei_entity_preview --docs 1060,100
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from functools import lru_cache
from html import escape
from pathlib import Path

from lxml import etree

from scripts.config import DATA_DIR, OUTPUT_DIR, TEI_FINAL_DIR, TEI_NS, TEI_SCHEMA_PATH

ENTITY_PREVIEW_DIR = OUTPUT_DIR / "entity_preview"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
LEGACY_MENTIONS_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"

REPORT_STEM = "entity_pilot_report"

# M3 pilot panel (knowledge/entity-integration.md): gold half, then transfer half.
PANEL_DOCS = ["1060", "100", "290", "1440", "890", "1350", "1360", "2030", "1220", "3090"]

# ZBZ inline GND model (E88): one element per category, ref carries the GND id.
CATEGORY_ELEMENT = {"person": "persName", "organisation": "orgName", "work": "bibl"}

_HI_OPEN_RE = re.compile(r"<hi(?:\s[^<>]*)?>")
_HI_CLOSE_RE = re.compile(r"</hi\s*>")


# ---------------------------------------------------------------------------
# Wrapping (pure string work)
# ---------------------------------------------------------------------------

def hi_envelope(xml_string: str, start: int, end: int) -> tuple[int, int] | None:
    """Span of the ``hi`` element whose complete content is ``[start:end)``, else None.

    Exact rule: the opening tag ends at ``start`` and the closing tag begins at ``end``.
    Anything in between the tags that the candidate does not cover (a trailing space,
    another element) keeps the wrapper inside the ``hi``.
    """
    open_at = xml_string.rfind("<", 0, start)
    if open_at < 0 or xml_string[start - 2:start] == "/>":
        return None
    if not _HI_OPEN_RE.fullmatch(xml_string, open_at, start):
        return None
    close = _HI_CLOSE_RE.match(xml_string, end)
    return (open_at, close.end()) if close else None


def apply_candidates(xml_string: str, candidates: list[dict]) -> str:
    """Wrap every tier-1 candidate in its TEI element; tier 2 stays untouched.

    Splices back to front so the offsets of the not yet applied candidates stay valid.
    The candidate contract (``xml_string[start:end] == surface``, non-overlapping) is
    verified here, because a violated offset would silently corrupt the file rather
    than fail; the matcher is a separate module. A candidate covering the whole content
    of an ``hi`` widens the splice to that element, so the wrapper lands outside it.
    """
    tier1 = sorted((c for c in candidates if c.get("tier") == 1),
                   key=lambda c: c["start"], reverse=True)
    previous_start = None
    for cand in tier1:
        start, end = cand["start"], cand["end"]
        if xml_string[start:end] != cand["surface"]:
            raise ValueError(
                f"offset mismatch for {cand['gid']}: [{start}:{end}] is "
                f"{xml_string[start:end]!r}, candidate claims {cand['surface']!r}"
            )
        wrap_start, wrap_end = hi_envelope(xml_string, start, end) or (start, end)
        if previous_start is not None and wrap_end > previous_start:
            raise ValueError(f"overlapping candidates at offset {start} (gid {cand['gid']})")
        element = CATEGORY_ELEMENT[cand["category"]]
        content = xml_string[wrap_start:wrap_end]
        wrapped = f'<{element} ref="GND:{cand["gid"]}">{content}</{element}>'
        xml_string = xml_string[:wrap_start] + wrapped + xml_string[wrap_end:]
        previous_start = wrap_start
    return xml_string


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def text_signature(xml_string: str) -> str:
    """Concatenated text of the <text> subtree, the invariant the wrapping must preserve."""
    root = etree.fromstring(xml_string.encode("utf-8"))
    text_el = root.find(f"{{{TEI_NS}}}text")
    if text_el is None:
        raise ValueError("no <text> element")
    return "".join(text_el.itertext())


def check_text_invariance(before_xml: str, after_xml: str) -> bool:
    """True when both sides carry the same text. An unusable side counts as a failed check."""
    try:
        return text_signature(before_xml) == text_signature(after_xml)
    except (etree.XMLSyntaxError, ValueError):
        return False


@lru_cache(maxsize=2)
def load_schema(schema_path: Path = TEI_SCHEMA_PATH):
    """Compiled RelaxNG for zbz_hersch.rng (cached; the schema is read once per run)."""
    return etree.RelaxNG(etree.parse(str(schema_path)))


def validate_rng(xml_string: str, relaxng=None) -> list[str]:
    """RelaxNG error messages for xml_string; an empty list means valid."""
    relaxng = relaxng or load_schema()
    try:
        doc = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return [f"XML syntax: {exc}"]
    if relaxng.validate(doc):
        return []
    return [f"line {err.line}: {err.message}" for err in relaxng.error_log]


# ---------------------------------------------------------------------------
# Per document
# ---------------------------------------------------------------------------

def preview_document(doc_id: str, xml_string: str, candidates: list[dict],
                     out_dir: Path, relaxng=None) -> dict:
    """Write the wrapped preview of one document and check schema plus text invariance.

    ``counts.by_rule`` and ``counts.by_category`` cover all candidates of the document,
    tier 1 and tier 2 alike; ``wrapped``/``worklist`` give the split.
    """
    wrapped_xml = apply_candidates(xml_string, candidates)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{doc_id}_final.xml"
    # bytes in, bytes out: text-mode IO would rewrite line endings on Windows
    out_path.write_bytes(wrapped_xml.encode("utf-8"))

    written = out_path.read_bytes().decode("utf-8")  # check what is on disk, not what we held
    rng_errors = validate_rng(written, relaxng)
    tier1 = [c for c in candidates if c.get("tier") == 1]
    tier2 = [c for c in candidates if c.get("tier") == 2]
    return {
        "doc": doc_id,
        "wrapped": tier1,
        "worklist": tier2,
        "counts": {
            "wrapped": len(tier1),
            "worklist": len(tier2),
            # candidates whose form has more than one bearer; the report must never
            # show one of them as the decided id
            "ambiguous": sum(1 for c in candidates if c.get("alternatives")),
            "by_rule": _sorted_counts(Counter(c.get("rule", "?") for c in candidates)),
            "by_category": _sorted_counts(Counter(c.get("category", "?") for c in candidates)),
            "by_evidence": _sorted_counts(
                Counter(c["evidence"] for c in candidates if c.get("evidence"))
            ),
        },
        "rng_valid": not rng_errors,
        "rng_errors": rng_errors[:5],
        "text_invariant": check_text_invariance(xml_string, written),
        "output": str(out_path),
    }


def run_preview(doc_ids: list[str], find_candidates, lexicon: dict,
                src_dir: Path | None = None, out_dir: Path | None = None) -> dict:
    """Preview over doc_ids; ``find_candidates`` is injected so this stays matcher-agnostic."""
    src_dir = src_dir or TEI_FINAL_DIR
    out_dir = out_dir or ENTITY_PREVIEW_DIR
    if out_dir.resolve() == TEI_FINAL_DIR.resolve():
        raise ValueError("refusing to write the preview into output/tei_final")
    relaxng = load_schema()
    results = []
    for i, doc_id in enumerate(doc_ids, 1):
        src = src_dir / f"{doc_id}_final.xml"
        if not src.exists():
            print(f"  [{i}/{len(doc_ids)}] {doc_id}: SKIP (no final TEI)")
            continue
        xml_string = src.read_bytes().decode("utf-8")
        res = preview_document(doc_id, xml_string, find_candidates(xml_string, lexicon),
                               out_dir, relaxng)
        results.append(res)
        print(f"  [{i}/{len(doc_ids)}] {doc_id}: wrapped {res['counts']['wrapped']}, "
              f"worklist {res['counts']['worklist']}, schema "
              f"{'PASS' if res['rng_valid'] else 'FAIL'}, text "
              f"{'PASS' if res['text_invariant'] else 'FAIL'}")
    return build_report(results)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _sorted_counts(counter) -> dict:
    """Counts as a plain dict, most frequent first, ties by key (deterministic output)."""
    return {k: v for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))}


def build_report(results: list[dict]) -> dict:
    """Per-document results plus corpus totals."""
    by_rule, by_category, by_evidence = Counter(), Counter(), Counter()
    for res in results:
        by_rule.update(res["counts"]["by_rule"])
        by_category.update(res["counts"]["by_category"])
        by_evidence.update(res["counts"].get("by_evidence", {}))
    return {
        "documents": results,
        "totals": {
            "documents": len(results),
            "wrapped": sum(r["counts"]["wrapped"] for r in results),
            "worklist": sum(r["counts"]["worklist"] for r in results),
            "ambiguous": sum(r["counts"].get("ambiguous", 0) for r in results),
            "by_rule": _sorted_counts(by_rule),
            "by_category": _sorted_counts(by_category),
            "by_evidence": _sorted_counts(by_evidence),
            "rng_valid": sum(1 for r in results if r["rng_valid"]),
            "text_invariant": sum(1 for r in results if r["text_invariant"]),
        },
    }


_HTML_STYLE = """
    body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto;
           padding: 0 1rem; color: #222; }
    h1 { font-size: 1.5rem; } h2 { font-size: 1.15rem; margin-top: 2rem; }
    h3 { font-size: 1rem; margin-bottom: 0.3rem; }
    table { width: 100%; border-collapse: collapse; margin: 0.6rem 0 1.2rem; font-size: 0.9em; }
    th, td { padding: 5px 9px; text-align: left; border-bottom: 1px solid #ddd;
             vertical-align: top; }
    th { background: #eee; }
    td.num { text-align: right; }
    .pass { color: #1a6b2a; font-weight: bold; }
    .fail { color: #a01515; font-weight: bold; }
    .empty { color: #777; font-style: italic; }
    .ctx { color: #444; }
"""


def _status(ok: bool) -> str:
    return '<span class="pass">PASS</span>' if ok else '<span class="fail">FAIL</span>'


def _mention_ids(mention: dict) -> str:
    """Ids of a mention: an undecided candidate names every bearer without a lead.

    A tier-1 hit carries the id that goes into the file, so it leads and the remaining
    bearers follow as alternatives. A tier-2 hit is undecided, and listing its reported
    id first would read as a decision the matcher did not take.
    """
    gid = str(mention.get("gid", ""))
    alternatives = mention.get("alternatives") or []
    if not alternatives:
        return gid
    if mention.get("tier") != 1:
        return ", ".join(alternatives)
    others = [other for other in alternatives if other != gid]
    return f"{gid} (alt: {', '.join(others)})" if others else gid


def _mention_rule(mention: dict) -> str:
    """Rule plus the typographic verdict of a one-word title, where there is one."""
    rule = str(mention.get("rule", ""))
    evidence = mention.get("evidence")
    return f"{rule} (evidence: {evidence})" if evidence else rule


def _mention_origin(mention: dict) -> str:
    """Which lexicon form produced the hit, and from which data channel."""
    form = mention.get("matched_form")
    return f"{mention.get('form_source', '')}: {form}" if form else ""


def _mention_table(mentions: list[dict]) -> str:
    if not mentions:
        return '<p class="empty">none</p>'
    rows = "".join(
        "<tr><td>{surface}</td><td>{gid}</td><td>{rule}</td><td>{origin}</td>"
        "<td class=\"ctx\">{context}</td></tr>".format(
            surface=escape(m.get("surface", "")),
            gid=escape(_mention_ids(m)),
            rule=escape(_mention_rule(m)),
            origin=escape(_mention_origin(m)),
            context=escape(m.get("context", "")),
        )
        for m in mentions
    )
    return ("<table><thead><tr><th>Surface</th><th>GND</th><th>Rule</th><th>Found via</th>"
            f"<th>Context</th></tr></thead><tbody>{rows}</tbody></table>")


def build_html_report(report: dict) -> str:
    """Standalone HTML report: overview with both check columns, then one section per document."""
    totals = report["totals"]
    overview = "".join(
        "<tr><td>{doc}</td><td class=\"num\">{w}</td><td class=\"num\">{wl}</td>"
        "<td>{rng}</td><td>{txt}</td></tr>".format(
            doc=escape(res["doc"]), w=res["counts"]["wrapped"], wl=res["counts"]["worklist"],
            rng=_status(res["rng_valid"]), txt=_status(res["text_invariant"]),
        )
        for res in report["documents"]
    )
    rules = "".join(
        f'<tr><td>{escape(k)}</td><td class="num">{v}</td></tr>'
        for k, v in totals["by_rule"].items()
    )
    categories = "".join(
        f'<tr><td>{escape(k)}</td><td class="num">{v}</td></tr>'
        for k, v in totals["by_category"].items()
    )
    evidence = "".join(
        f'<tr><td>{escape(k)}</td><td class="num">{v}</td></tr>'
        for k, v in totals.get("by_evidence", {}).items()
    ) or '<tr><td class="empty">none</td><td class="num">0</td></tr>'
    sections = []
    for res in report["documents"]:
        errors = ""
        if res.get("rng_errors"):
            errors = "<p>Schema errors: " + escape("; ".join(res["rng_errors"])) + "</p>"
        sections.append(
            f'<h2>Document {escape(res["doc"])}</h2>{errors}'
            f'<h3>Wrapped mentions (tier 1)</h3>{_mention_table(res["wrapped"])}'
            f'<h3>Worklist (tier 2)</h3>{_mention_table(res["worklist"])}'
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Entity pilot preview</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<h1>Entity pilot preview</h1>
<p>Inline GND markup written to the preview directory. The delivered TEI
(output/tei_final) is not touched. Schema: data/schema/zbz_hersch.rng. Text invariance:
concatenated text of the &lt;text&gt; subtree before and after wrapping.</p>
<h2>Overview</h2>
<p>Documents: {totals["documents"]} &middot; wrapped: {totals["wrapped"]} &middot;
worklist: {totals["worklist"]} &middot; ambiguous (several bearers):
{totals.get("ambiguous", 0)} &middot; schema PASS: {totals["rng_valid"]}/{totals["documents"]}
&middot; text PASS: {totals["text_invariant"]}/{totals["documents"]}</p>
<table><thead><tr><th>Document</th><th>Wrapped</th><th>Worklist</th><th>Schema</th>
<th>Text invariance</th></tr></thead><tbody>{overview}</tbody></table>
<h3>Candidates by rule</h3>
<table><thead><tr><th>Rule</th><th>Count</th></tr></thead><tbody>{rules}</tbody></table>
<h3>Candidates by category</h3>
<table><thead><tr><th>Category</th><th>Count</th></tr></thead><tbody>{categories}</tbody></table>
<h3>One-word titles by typographic evidence</h3>
<table><thead><tr><th>Evidence</th><th>Count</th></tr></thead><tbody>{evidence}</tbody></table>
{"".join(sections)}
</body>
</html>"""


def write_reports(report: dict, out_dir: Path) -> tuple[Path, Path]:
    """Write the JSON and HTML report next to the preview files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REPORT_STEM}.json"
    html_path = out_dir / f"{REPORT_STEM}.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(build_html_report(report), encoding="utf-8")
    return json_path, html_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_doc_ids(values: list[str]) -> list[str]:
    """Accept both comma-separated and space-separated document ids."""
    return [d for value in values for d in value.split(",") if d.strip()]


def main():
    ap = argparse.ArgumentParser(
        description="Entity pilot preview (inline GND markup; tei_final stays untouched)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--docs", nargs="+", help="Document ids, e.g. --docs 1060,100")
    group.add_argument("--panel", action="store_true", help="The ten M3 pilot documents")
    ap.add_argument("--entities", type=Path, default=ENTITIES_PATH, help="Curated entity list")
    ap.add_argument("--cache", type=Path, default=GND_CACHE_PATH, help="GND variant cache")
    ap.add_argument("--legacy", type=Path, default=LEGACY_MENTIONS_PATH,
                    help="Old mention index (optional, used when present)")
    ap.add_argument("--review", type=Path, default=VARIANT_REVIEW_PATH,
                    help="Variant review verdicts (optional, used when present)")
    ap.add_argument("--src-dir", type=Path, default=TEI_FINAL_DIR, help="Source TEI directory (read only)")
    ap.add_argument("--out-dir", type=Path, default=ENTITY_PREVIEW_DIR, help="Preview directory")
    args = ap.parse_args()

    from scripts.tei.entity_matcher import CORPUS_AUTHOR_LABELS, build_lexicon, find_candidates

    doc_ids = PANEL_DOCS if args.panel else _parse_doc_ids(args.docs)
    legacy = args.legacy if args.legacy and args.legacy.exists() else None
    review = args.review if args.review.exists() else None
    lexicon = build_lexicon(args.entities, args.cache, legacy_path=legacy,
                            review_path=review)

    def find_with_author(xml_string, lex):
        return find_candidates(xml_string, lex, author_labels=CORPUS_AUTHOR_LABELS)

    print(f"Entity preview over {len(doc_ids)} document(s); tei_final is not written.")
    report = run_preview(doc_ids, find_with_author, lexicon,
                         src_dir=args.src_dir, out_dir=args.out_dir)

    totals = report["totals"]
    print(f"\n  Documents: {totals['documents']}  wrapped: {totals['wrapped']}  "
          f"worklist: {totals['worklist']}  ambiguous: {totals['ambiguous']}")
    if totals["by_evidence"]:
        evidence = "  ".join(f"{k}: {v}" for k, v in totals["by_evidence"].items())
        print(f"  One-word titles by evidence: {evidence}")
    print(f"  Schema PASS: {totals['rng_valid']}/{totals['documents']}  "
          f"text invariance PASS: {totals['text_invariant']}/{totals['documents']}")
    json_path, html_path = write_reports(report, args.out_dir)
    print(f"  Report: {json_path}")
    print(f"  Report: {html_path}")


if __name__ == "__main__":
    main()
