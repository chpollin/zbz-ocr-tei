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

Mark provenance
---------------
Every wrapped mark carries its own provenance and verification state, so the annotation
stays auditable outside this pipeline (vocabulary: knowledge/entity-integration.md, section
"Mark provenance and verification state"). Three separate things:

``@resp``   who asserted the mark, as a pointer into the ``respStmt`` declarations this
            runner adds to the preview ``teiHeader``. Only responsibilities a document's
            own marks use are declared.
``@cert``   whether a human checked the mark. ``high`` for a mark the facsimile
            adjudication judged correct and whose document text still carries the digest
            that judgment was made on, ``medium`` for a plain matcher assertion. Never a
            number, although the schema would take one.
``@source`` the matcher rule that produced the mark. It is the one attribute the schema
            allows on all three wrapped elements; ``@evidence`` fails on ``bibl`` and
            ``@ana`` exists nowhere in ``zbz_hersch.rng``.

The verdict store ``data/entities/mention_verdicts.json`` stays the source of truth of the
judgments; the attributes are a regenerable projection of it. The projection reuses the
classification of ``scripts.eval.entity_verdict_guard``, so a document whose text moved
since the adjudication (guard class ``text_changed``) falls back to unverified instead of
claiming a verification its bytes no longer support.

Deterministic, offline, no model call.

Usage:
    python -m scripts.tei.tei_entity_preview --panel
    python -m scripts.tei.tei_entity_preview --docs 1060,100
    python -m scripts.tei.tei_entity_preview --all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from lxml import etree

from scripts.config import DATA_DIR, OUTPUT_DIR, TEI_FINAL_DIR, TEI_NS, TEI_SCHEMA_PATH

# The verification state is a projection of the adjudicated judgments, so the key
# comparison lives in one place: the guard that gates them (E110). Same direction as
# tei_reading_order_fix, which reuses the classifier of its own audit.
from scripts.eval.entity_verdict_guard import (
    _doc_index,
    _span_index,
    classify_mark,
    text_digests,
)

ENTITY_PREVIEW_DIR = OUTPUT_DIR / "entity_preview"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
LEGACY_MENTIONS_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"
MARKING_POLICY_PATH = DATA_DIR / "entities" / "marking_policy.json"
VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"

REPORT_STEM = "entity_pilot_report"

# M3 pilot panel (knowledge/entity-integration.md): gold half, then transfer half.
PANEL_DOCS = ["1060", "100", "290", "1440", "890", "1350", "1360", "2030", "1220", "3090"]

# ZBZ inline GND model (E88): one element per category, ref carries the GND id.
CATEGORY_ELEMENT = {"person": "persName", "organisation": "orgName", "work": "bibl"}

# The two responsibilities that exist today. No third one is declared: a model judge has
# no producer yet, and an unused declaration would assert a provenance nothing carries.
MATCHER_RESP_ID = "resp-entity-matcher"
ADJUDICATION_RESP_ID = "resp-entity-adjudication"
RESP_AGENT = "DHCraft"
MATCHER_RESP_TEXT = ("Automatic entity matching, deterministic and closed-world "
                     "(scripts/tei/entity_matcher.py, rule set {fingerprint})")
ADJUDICATION_RESP_TEXT = ("Facsimile adjudication of the entity evaluation sample, "
                          "wave {snapshot}")

# The modules that decide which mention becomes a mark; their digest is the version of
# the assertion. The lexicon inputs (curated list, GND cache, variant review) are data
# and are not part of it.
RULE_MODULES = ("entity_matcher.py", "entity_lexicon.py", "running_heads.py")

_HI_OPEN_RE = re.compile(r"<hi(?:\s[^<>]*)?>")
_HI_CLOSE_RE = re.compile(r"</hi\s*>")
_TITLESTMT_CLOSE_RE = re.compile(r"([ \t]*)</titleStmt>")


# ---------------------------------------------------------------------------
# Mark provenance
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def matcher_fingerprint(module_dir: Path | None = None) -> str:
    """Short digest over the rule-bearing matcher modules."""
    module_dir = module_dir or Path(__file__).parent
    digest = hashlib.sha256()
    for name in RULE_MODULES:
        digest.update((module_dir / name).read_bytes())
    return digest.hexdigest()[:12]


def mark_attributes(cand: dict) -> dict[str, str]:
    """Attributes of one wrapped mark, in emission order.

    ``verified`` on the candidate is the only input for the certainty: it is set by the
    verdict projection and absent for every mark no adjudication reaches.
    """
    verified = bool(cand.get("verified"))
    attributes = {"ref": f"GND:{cand['gid']}"}
    if cand.get("rule"):
        attributes["source"] = cand["rule"]
    attributes["cert"] = "high" if verified else "medium"
    attributes["resp"] = (f"#{MATCHER_RESP_ID} #{ADJUDICATION_RESP_ID}" if verified
                          else f"#{MATCHER_RESP_ID}")
    return attributes


def opening_tag(cand: dict) -> str:
    """Opening tag the wrapping writes for a candidate; rebuildable from its report record."""
    element = CATEGORY_ELEMENT[cand["category"]]
    attributes = " ".join(f"{name}={quoteattr(value)}"
                          for name, value in mark_attributes(cand).items())
    return f"<{element} {attributes}>"


def resp_statements(candidates: list[dict], snapshot: str | None) -> list[tuple[str, str]]:
    """(xml:id, prose) of the responsibilities this document's own marks point to."""
    tier1 = [c for c in candidates if c.get("tier") == 1]
    if not tier1:
        return []
    statements = [(MATCHER_RESP_ID,
                   MATCHER_RESP_TEXT.format(fingerprint=matcher_fingerprint()))]
    if any(c.get("verified") for c in tier1):
        statements.append((ADJUDICATION_RESP_ID,
                           ADJUDICATION_RESP_TEXT.format(snapshot=snapshot or "unnamed")))
    return statements


def insert_resp_stmts(xml_string: str, statements: list[tuple[str, str]]) -> str:
    """Declare the responsibilities in the ``titleStmt``; idempotent, header only.

    Runs after the wrapping, never before: the header sits in front of the body, so an
    insertion here would shift every candidate offset.
    """
    match = _TITLESTMT_CLOSE_RE.search(xml_string)
    if match is None:
        return xml_string
    pending = [(rid, text) for rid, text in statements
               if f'<respStmt xml:id="{rid}">' not in xml_string]
    if not pending:
        return xml_string
    at = match.start()
    block = xml_string[:at].endswith("\n")
    indent = match.group(1) + "  " if block else ""
    rendered = "".join(
        f'{indent}<respStmt xml:id="{rid}"><resp>{escape(text)}</resp>'
        f"<orgName>{RESP_AGENT}</orgName></respStmt>" + ("\n" if block else "")
        for rid, text in pending
    )
    return xml_string[:at] + rendered + xml_string[at:]


# ---------------------------------------------------------------------------
# Verification state (projection of the adjudicated verdict store)
# ---------------------------------------------------------------------------

def load_verdict_store(path: Path) -> dict | None:
    """The mention verdict store, or None where it is absent (everything unverified)."""
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def verified_spans(store: dict, doc_id: str, candidates: list[dict],
                   digests: dict[str, str | None]) -> set[tuple[int, int, str]]:
    """(start, end, gid) of every candidate an adjudication verifies as it stands.

    Verification survives only what the guard calls ``kept_tier1``: the judgment was
    ``correct``, the document digest still matches the one it was made on, and the mark
    sits at exactly the adjudicated span in tier 1. The gid is compared strictly, so a
    judgment about another bearer of an ambiguous surface verifies nothing.
    """
    scoped = [dict(cand, doc=doc_id) for cand in candidates]
    span_index, doc_index = _span_index(scoped), _doc_index(scoped)
    verified = set()
    for mark in store.get("marks", ()):
        if mark["doc"] != doc_id or mark["verdict"] != "correct":
            continue
        klass, _ = classify_mark(mark, span_index, doc_index, digests)
        if klass == "kept_tier1":
            verified.add((mark["start"], mark["end"], mark["gid"]))
    return verified


def flag_verified(candidates: list[dict], spans: set[tuple[int, int, str]]) -> None:
    """Set the ``verified`` flag on the tier-1 candidates the adjudication covers."""
    for cand in candidates:
        if cand.get("tier") == 1:
            cand["verified"] = (cand["start"], cand["end"], cand["gid"]) in spans


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
        wrapped = f"{opening_tag(cand)}{content}</{element}>"
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
                     out_dir: Path, relaxng=None, snapshot: str | None = None) -> dict:
    """Write the wrapped preview of one document and check schema plus text invariance.

    ``counts.by_rule`` and ``counts.by_category`` cover all candidates of the document,
    tier 1 and tier 2 alike; ``wrapped``/``worklist`` give the split.
    """
    wrapped_xml = apply_candidates(xml_string, candidates)
    body_only = len(wrapped_xml)
    wrapped_xml = insert_resp_stmts(wrapped_xml, resp_statements(candidates, snapshot))
    header_shift = len(wrapped_xml) - body_only
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
        "header_shift": header_shift,
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
            # certainty of the written marks; tier 2 is not wrapped and carries none
            "by_certainty": _sorted_counts(
                Counter(mark_attributes(c)["cert"] for c in tier1)
            ),
        },
        "rng_valid": not rng_errors,
        "rng_errors": rng_errors[:5],
        "text_invariant": check_text_invariance(xml_string, written),
        "output": str(out_path),
    }


def discover_doc_ids(src_dir: Path) -> list[str]:
    """Doc ids of every ``{doc}_final.xml`` in src_dir, numeric ones first and in numeric order.

    Kept local rather than imported from the eval audits: scripts/tei must not depend on
    scripts/eval. A non-numeric id keeps its filename order and follows the numeric block.
    """
    doc_ids = [path.stem.removesuffix("_final")
               for path in sorted(Path(src_dir).glob("*_final.xml"))]
    return sorted(doc_ids, key=lambda d: (0, int(d)) if d.isdigit() else (1, 0))


def run_preview(doc_ids: list[str], find_candidates, lexicon: dict,
                src_dir: Path | None = None, out_dir: Path | None = None,
                verdicts_path: Path | None = None) -> dict:
    """Preview over doc_ids; ``find_candidates`` is injected so this stays matcher-agnostic."""
    src_dir = src_dir or TEI_FINAL_DIR
    out_dir = out_dir or ENTITY_PREVIEW_DIR
    if out_dir.resolve() == TEI_FINAL_DIR.resolve():
        raise ValueError("refusing to write the preview into output/tei_final")
    relaxng = load_schema()
    store = load_verdict_store(VERDICTS_PATH if verdicts_path is None else verdicts_path)
    # digests of the very files the offsets index into, so a judgment made on other
    # bytes shows up as text_changed rather than as a claimed verification
    digests = text_digests(doc_ids, src_dir) if store else {}
    snapshot = store.get("snapshot") if store else None
    results = []
    for i, doc_id in enumerate(doc_ids, 1):
        src = src_dir / f"{doc_id}_final.xml"
        if not src.exists():
            print(f"  [{i}/{len(doc_ids)}] {doc_id}: SKIP (no final TEI)")
            continue
        xml_string = src.read_bytes().decode("utf-8")
        candidates = find_candidates(xml_string, lexicon)
        if store:
            flag_verified(candidates, verified_spans(store, doc_id, candidates, digests))
        res = preview_document(doc_id, xml_string, candidates, out_dir, relaxng,
                               snapshot=snapshot)
        results.append(res)
        verified = res["counts"]["by_certainty"].get("high", 0)
        print(f"  [{i}/{len(doc_ids)}] {doc_id}: wrapped {res['counts']['wrapped']}, "
              f"verified {verified}, "
              f"worklist {res['counts']['worklist']}, schema "
              f"{'PASS' if res['rng_valid'] else 'FAIL'}, text "
              f"{'PASS' if res['text_invariant'] else 'FAIL'}")
    return build_report(results)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _sorted_counts(counter) -> dict:
    """Counts as a plain dict, most frequent first, ties by key (deterministic output)."""
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def build_report(results: list[dict]) -> dict:
    """Per-document results plus corpus totals."""
    by_rule, by_category, by_evidence, by_certainty = Counter(), Counter(), Counter(), Counter()
    for res in results:
        by_rule.update(res["counts"]["by_rule"])
        by_category.update(res["counts"]["by_category"])
        by_evidence.update(res["counts"].get("by_evidence", {}))
        by_certainty.update(res["counts"].get("by_certainty", {}))
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
            "by_certainty": _sorted_counts(by_certainty),
            "rng_valid": sum(1 for r in results if r["rng_valid"]),
            "text_invariant": sum(1 for r in results if r["text_invariant"]),
        },
    }


def write_report(report: dict, out_dir: Path) -> Path:
    """Write the JSON report next to the preview files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REPORT_STEM}.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path


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
    group.add_argument("--all", action="store_true", help="Every document in --src-dir")
    ap.add_argument("--entities", type=Path, default=ENTITIES_PATH, help="Curated entity list")
    ap.add_argument("--cache", type=Path, default=GND_CACHE_PATH, help="GND variant cache")
    ap.add_argument("--legacy", type=Path, default=LEGACY_MENTIONS_PATH,
                    help="Old mention index (optional, used when present)")
    ap.add_argument("--review", type=Path, default=VARIANT_REVIEW_PATH,
                    help="Variant review verdicts (optional, used when present)")
    ap.add_argument("--policy", type=Path, default=MARKING_POLICY_PATH,
                        help="Markierungspolitik (JSON, optional)")
    ap.add_argument("--verdicts", type=Path, default=VERDICTS_PATH,
                    help="Mention verdict store (optional; absent means every mark unverified)")
    ap.add_argument("--src-dir", type=Path, default=TEI_FINAL_DIR, help="Source TEI directory (read only)")
    ap.add_argument("--out-dir", type=Path, default=ENTITY_PREVIEW_DIR, help="Preview directory")
    args = ap.parse_args()

    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    if args.all:
        doc_ids = discover_doc_ids(args.src_dir)
    else:
        doc_ids = PANEL_DOCS if args.panel else _parse_doc_ids(args.docs)
    legacy = args.legacy if args.legacy and args.legacy.exists() else None
    review = args.review if args.review.exists() else None
    policy = args.policy if args.policy.exists() else None
    lexicon = build_lexicon(args.entities, args.cache, legacy_path=legacy,
                            review_path=review, policy_path=policy)

    print(f"Entity preview over {len(doc_ids)} document(s); tei_final is not written.")
    report = run_preview(doc_ids, find_candidates, lexicon,
                         src_dir=args.src_dir, out_dir=args.out_dir,
                         verdicts_path=args.verdicts)

    totals = report["totals"]
    print(f"\n  Documents: {totals['documents']}  wrapped: {totals['wrapped']}  "
          f"worklist: {totals['worklist']}  ambiguous: {totals['ambiguous']}")
    certainty = "  ".join(f"{k}: {v}" for k, v in totals["by_certainty"].items()) or "-"
    print(f"  Mark certainty: {certainty}")
    if totals["by_evidence"]:
        evidence = "  ".join(f"{k}: {v}" for k, v in totals["by_evidence"].items())
        print(f"  One-word titles by evidence: {evidence}")
    print(f"  Schema PASS: {totals['rng_valid']}/{totals['documents']}  "
          f"text invariance PASS: {totals['text_invariant']}/{totals['documents']}")
    json_path = write_report(report, args.out_dir)
    print(f"  Report: {json_path}")


if __name__ == "__main__":
    main()
