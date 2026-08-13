"""M4 gold benchmark of the entity integration: matcher against the ZBZ reference TEIs.

Design plan: knowledge/entity-integration.md (sections "Target model", "Instruments",
"Verification"). The measurement follows the principle of the CER benchmark
(knowledge/cer-methodology.md): the references are partial transcriptions, so the
comparison runs only in the text both sides share; everything outside that scope counts
neutral, is counted and reported, and never becomes a hit or an error.

DIAGNOSIS ONLY -- reads data/source/reference_tei, output/tei_final and the entity data,
writes one report to output/audits/, changes no TEI, and is no pass/fail gate (exit code
always 0).

What is scored, per reference mention (persName/orgName/bibl carrying a GND reference in
@ref or @corresp, with or without the "GND:" prefix, see ground-truth-map.md exception 7):

  hit                    a tier-1 candidate carries the same id at the same place
  worklist_available     only a tier-2 candidate knows it; the mention is on the worklist,
                         which is a state of its own rather than a loss. A tier-2
                         candidate counts here also when it reports another owner of the
                         same form while the reference id is among the alternatives the
                         lexicon carries, because the judge stage picks from exactly that
                         set (the anchor collision of the Jaspers spouses)
  miss                   neither tier reaches the mention
  neutral_out_of_scope   the mention sits outside the shared text
  neutral_unlisted       the id is not in the curated entity list (closed world, E71)
  neutral_wide_span      the reference wraps the wider citation span including imprint
                         while our candidate carries the title (title-only, E88 detail rule)
  neutral_empty          the reference element carries no word (W17 curation slot)

and per tier-1 candidate inside the shared text that no reference mention consumed:

  neutral_nested         it sits inside a reference span with another id; nesting is
                         permitted, the references never nest, so this is no error
  fp_author              a mention of the corpus author; the reference practice marks her
                         almost never and her scope is an open operator decision, so these
                         are counted apart and never enter the main precision
  false_positive         everything else

Tier-2 candidates are never false positives: they are worklist material and no delivery.

Deliberate simplification: the shared scope comes from a word-level difflib alignment of
the two normalized token streams (matching blocks, fused across gaps up to GAP_TOLERANCE,
regions below MIN_REGION_MATCHED matched tokens dropped). That is exact where the two
sides agree literally and degrades to a bounded offset drift inside a gap; a reference
page whose text the pipeline read very differently therefore falls out of scope and
counts neutral rather than as a miss. The upgrade path is a page-anchored alignment over
the pb sequence, which needs the pb numbering of both sides to be trustworthy.

Usage:
    python -m scripts.eval.entity_gold_benchmark
    python -m scripts.eval.entity_gold_benchmark --docs 100 290
    python -m scripts.eval.entity_gold_benchmark --out output/audits/entity_gold_benchmark.json
"""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from bisect import bisect_left, bisect_right
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from scripts.config import DATA_DIR, REFERENCE_TEI_DIR, TEI_FINAL_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR

ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"
MARKING_POLICY_PATH = DATA_DIR / "entities" / "marking_policy.json"
LEGACY_MENTIONS_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "entity_gold_benchmark.json"

# Jeanne Hersch; the id is read from data/entities/all_entities.json, never guessed.
AUTHOR_GID = "118815679"

# Reference 1520 carries a large share of the gold, the known well-formedness defect and
# the anchor-collision case no evaluation panel saw. It is always its own split.
SPECIAL_DOC = "1520"

GAP_TOLERANCE = 25        # tokens; a shorter divergence stays inside one shared region
MIN_REGION_MATCHED = 5    # matched tokens a shared region needs (kills accidental blocks)
POSITION_TOLERANCE = 8    # tokens the projection may be off before a pairing is refused

VERDICTS = (
    "hit",
    "worklist_available",
    "miss",
    "false_positive",
    "fp_author",
    "neutral_nested",
    "neutral_wide_span",
    "neutral_out_of_scope",
    "neutral_out_of_scope_candidate",
    "neutral_unlisted",
    "neutral_empty",
)

ERROR_VERDICTS = (
    "miss", "worklist_available", "false_positive", "fp_author",
    "neutral_nested", "neutral_wide_span",
)

MAX_PRINTED = 10

_ELEMENT_CATEGORY = {"persName": "person", "orgName": "organisation", "bibl": "work"}
_GID_RE = re.compile(r"\d+(?:-[\dX]|X)?")

_TAG_RE = re.compile(r"<[^>]*>", re.DOTALL)
_LB_RE = re.compile(r"<lb\b[^>]*>", re.DOTALL)
_LB_JOIN_RE = re.compile(r"<lb\b[^>]*\bbreak\s*=\s*([\"'])no\1[^>]*>", re.DOTALL)
_LB_JOIN_WS_RE = re.compile(r"\s*<lb\b[^>]*\bbreak\s*=\s*([\"'])no\1[^>]*>\s*", re.DOTALL)
_WORD_RE = re.compile(r"\w+")
_ENTITY_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
_TEXT_OPEN_RE = re.compile(r"<text\b[^>]*>", re.DOTALL)
_NAME_RE = re.compile(r"</?([A-Za-z][\w.:-]*)")
_ATTR_RE = re.compile(r"([\w.:-]+)\s*=\s*(\"([^\"]*)\"|'([^']*)')")


@dataclass(frozen=True)
class Token:
    """One word of the normalized text stream, with the raw span it came from."""

    word: str
    start: int
    end: int


@dataclass(frozen=True)
class Region:
    """A stretch of text both sides share, as index ranges into the two streams."""

    ref_start: int
    ref_end: int
    pipe_start: int
    pipe_end: int
    blocks: tuple[tuple[int, int, int], ...]  # (ref index, pipe index, size)


# ---------------------------------------------------------------------------
# Text stream
# ---------------------------------------------------------------------------

def _fold(text: str) -> str:
    """Comparison form: diacritics removed, case folded (the matcher's own fold)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def text_region(xml: str) -> tuple[int, int]:
    """Content range of the <text> element; the whole string when there is none."""
    opening = _TEXT_OPEN_RE.search(xml)
    closing = xml.rfind("</text>")
    if opening is None or closing < opening.end():
        return 0, len(xml)
    return opening.end(), closing


def _mask_entities(xml: str) -> str:
    """Character references become spaces of equal length: offsets hold, '&amp;' is no word."""
    return _ENTITY_RE.sub(lambda m: " " * len(m.group(0)), xml)


def build_stream(xml: str) -> list[Token]:
    """Word tokens of the <text> subtree, folded, with raw offsets.

    Markup contributes nothing and a plain `lb` separates words, both as in the matcher;
    `<lb break="no"/>` joins the broken word again, provided only whitespace stands
    between the tag and the two word halves.
    """
    lo, hi = text_region(xml)
    masked = _mask_entities(xml)
    tokens: list[Token] = []
    join = False
    pos = lo
    for tag in _TAG_RE.finditer(masked, lo, hi):
        _emit_run(masked, pos, tag.start(), tokens, join)
        join = (bool(_LB_JOIN_RE.fullmatch(tag.group(0)))
                and _tail_clean(masked, tokens, tag.start()))
        pos = tag.end()
    _emit_run(masked, pos, hi, tokens, join)
    return tokens


def _tail_clean(masked: str, tokens: list[Token], upto: int) -> bool:
    """True when only whitespace stands between the last emitted word and `upto`."""
    return bool(tokens) and not masked[tokens[-1].end:upto].strip()


def _emit_run(masked: str, lo: int, hi: int, tokens: list[Token], join: bool) -> None:
    """Append the words of masked[lo:hi]; `join` merges the first one into the last token."""
    first = True
    for match in _WORD_RE.finditer(masked, lo, hi):
        word = _fold(match.group(0))
        if first and join and tokens and not masked[lo:match.start()].strip():
            previous = tokens[-1]
            tokens[-1] = Token(previous.word + word, previous.start, match.end())
        else:
            tokens.append(Token(word, match.start(), match.end()))
        first = False


def surface_text(fragment: str) -> str:
    """Readable surface of a raw fragment, lb-normalized the way the matcher matches."""
    text = _LB_JOIN_WS_RE.sub("", fragment)
    text = _LB_RE.sub(" ", text)
    text = _TAG_RE.sub("", text)
    return " ".join(html.unescape(text).split())


def _token_range(starts: list[int], ends: list[int],
                 raw_start: int, raw_end: int) -> tuple[int, int]:
    """Index range of the tokens a raw span covers (empty range when it covers no word)."""
    first = bisect_right(ends, raw_start)
    last = bisect_left(starts, raw_end)
    return first, max(last, first)


# ---------------------------------------------------------------------------
# Reference mentions
# ---------------------------------------------------------------------------

def normalize_reference_gid(value: str) -> str | None:
    """GND id of a reference attribute value, or None when it carries no id.

    Whitespace inside the value is real in the corpus (1520), and the "GND:" prefix is
    missing in four references (ground-truth-map.md, exception 7).
    """
    cleaned = "".join(value.split())
    if cleaned[:4].upper() == "GND:":
        cleaned = cleaned[4:]
    return cleaned if _GID_RE.fullmatch(cleaned) else None


def _parse_attrs(token: str) -> dict[str, str]:
    return {
        m.group(1): (m.group(3) if m.group(3) is not None else m.group(4))
        for m in _ATTR_RE.finditer(token)
    }


def _gid_of(token: str) -> str | None:
    attrs = _parse_attrs(token)
    for key in ("ref", "corresp"):
        gid = normalize_reference_gid(attrs.get(key, ""))
        if gid:
            return gid
    return None


def reference_mentions(xml: str) -> list[dict]:
    """Every GND mention of a reference TEI, in document order, with raw content offsets."""
    lo, hi = text_region(xml)
    stack: list[tuple[str, str | None, int]] = []
    found: list[dict] = []
    for tag in _TAG_RE.finditer(xml, lo, hi):
        token = tag.group(0)
        if token.startswith(("<!", "<?")):
            continue
        name_match = _NAME_RE.match(token)
        if name_match is None:
            continue
        name = name_match.group(1)
        if name not in _ELEMENT_CATEGORY:
            continue
        if token.startswith("</"):
            index = _find_open(stack, name)
            if index is None:
                continue
            open_name, gid, content_start = stack[index]
            del stack[index:]
            if gid:
                found.append(_mention(open_name, gid, xml, content_start, tag.start()))
        elif token.endswith("/>"):
            # empty element (the W17 speaker curation slot): a mention without text
            gid = _gid_of(token)
            if gid:
                found.append(_mention(name, gid, xml, tag.start(), tag.start()))
        else:
            stack.append((name, _gid_of(token), tag.end()))
    found.sort(key=lambda m: m["start"])
    for order, mention in enumerate(found):
        mention["order"] = order
    return found


def _find_open(stack: list[tuple[str, str | None, int]], name: str) -> int | None:
    for index in range(len(stack) - 1, -1, -1):
        if stack[index][0] == name:
            return index
    return None


def _mention(name: str, gid: str, xml: str, start: int, end: int) -> dict:
    surface = surface_text(xml[start:end])
    return {
        "gid": gid,
        "category": _ELEMENT_CATEGORY[name],
        "surface": surface,
        "folded": _fold(surface),
        "start": start,
        "end": end,
        "order": 0,
    }


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

def shared_regions(ref_words: list[str], pipe_words: list[str]) -> list[Region]:
    """Regions of shared text, as index ranges into the two token streams."""
    blocks = [
        (b.a, b.b, b.size)
        for b in difflib.SequenceMatcher(None, ref_words, pipe_words, autojunk=False)
        .get_matching_blocks()
        if b.size
    ]
    regions: list[Region] = []
    current: list[tuple[int, int, int]] = []
    for block in blocks:
        if current and _fits(current, block):
            current.append(block)
            continue
        _close(regions, current)
        current = [block]
    _close(regions, current)
    return regions


def _fits(current: list[tuple[int, int, int]], block: tuple[int, int, int]) -> bool:
    ref_end = current[-1][0] + current[-1][2]
    pipe_end = current[-1][1] + current[-1][2]
    return block[0] - ref_end <= GAP_TOLERANCE and block[1] - pipe_end <= GAP_TOLERANCE


def _close(regions: list[Region], current: list[tuple[int, int, int]]) -> None:
    if sum(block[2] for block in current) < MIN_REGION_MATCHED:
        return
    regions.append(Region(
        ref_start=current[0][0],
        ref_end=current[-1][0] + current[-1][2],
        pipe_start=current[0][1],
        pipe_end=current[-1][1] + current[-1][2],
        blocks=tuple(current),
    ))


def project(regions: list[Region], index: int) -> int | None:
    """Pipeline token index for a reference token index, None outside the shared text.

    Exact inside a matching block; inside a gap the projection is anchored at the
    nearest block, so the drift stays below the gap length.
    """
    for region in regions:
        if not region.ref_start <= index < region.ref_end:
            continue
        previous = None
        for ref_at, pipe_at, size in region.blocks:
            if ref_at <= index < ref_at + size:
                return pipe_at + (index - ref_at)
            if ref_at > index:
                return pipe_at - (ref_at - index)
            previous = (ref_at, pipe_at, size)
        if previous:
            return previous[1] + previous[2] + (index - previous[0] - previous[2])
    return None


def _in_pipe_scope(regions: list[Region], index: int) -> bool:
    return any(region.pipe_start <= index < region.pipe_end for region in regions)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _wellformedness_error(xml: str) -> str | None:
    try:
        ET.fromstring(xml.encode("utf-8"))
    except (ET.ParseError, ValueError) as exc:
        return str(exc)
    return None


def _empty_counts() -> dict:
    return dict.fromkeys(VERDICTS, 0)


def _skipped(doc_id: str, status: str, error: str | None = None) -> dict:
    return {
        "doc": doc_id,
        "status": status,
        "error": error,
        "counts": _empty_counts(),
        "records": [],
        "scope": _scope_summary([], 0, 0),
        "reference_mentions": 0,
        "candidates": {"tier1": 0, "tier2": 0},
    }


def _scope_summary(regions: list[Region], ref_tokens: int, pipe_tokens: int) -> dict:
    """How much of each side the shared regions cover; the audit trail of the restriction."""
    shared_ref = sum(r.ref_end - r.ref_start for r in regions)
    shared_pipe = sum(r.pipe_end - r.pipe_start for r in regions)
    return {
        "regions": len(regions),
        "reference_tokens": ref_tokens,
        "shared_reference_tokens": shared_ref,
        "shared_reference_share": _rate(shared_ref, ref_tokens),
        "pipeline_tokens": pipe_tokens,
        "shared_pipeline_tokens": shared_pipe,
        "shared_pipeline_share": _rate(shared_pipe, pipe_tokens),
    }


def benchmark_document(
    doc_id: str,
    ref_xml: str,
    pipe_xml: str | None,
    find_candidates,
    known_gids: set[str] | None = None,
    alternatives=None,
) -> dict:
    """Score one reference against its pipeline TEI; both files are only read.

    `find_candidates` takes the pipeline XML string and returns matcher candidates, so
    this stays lexicon-agnostic and testable. A reference that does not parse is reported
    as "unreadable" (reference 1520 is the known case) instead of aborting the run.
    """
    error = _wellformedness_error(ref_xml)
    if error:
        return _skipped(doc_id, "unreadable", error)
    if pipe_xml is None:
        return _skipped(doc_id, "no_pipeline")

    ref_tokens = build_stream(ref_xml)
    pipe_tokens = build_stream(pipe_xml)
    regions = shared_regions([t.word for t in ref_tokens], [t.word for t in pipe_tokens])
    mentions = _locate_mentions(reference_mentions(ref_xml), ref_tokens)
    candidates = _locate_candidates(find_candidates(pipe_xml), pipe_tokens)

    records = _score(doc_id, mentions, candidates, regions, known_gids or set(),
                     alternatives)
    return {
        "doc": doc_id,
        "status": "ok",
        "error": None,
        "counts": _count_verdicts(records),
        "records": records,
        "scope": _scope_summary(regions, len(ref_tokens), len(pipe_tokens)),
        "reference_mentions": len(mentions),
        "candidates": {
            "tier1": sum(1 for c in candidates if c["tier"] == 1),
            "tier2": sum(1 for c in candidates if c["tier"] == 2),
        },
    }


def _locate_mentions(mentions: list[dict], tokens: list[Token]) -> list[dict]:
    starts = [t.start for t in tokens]
    ends = [t.end for t in tokens]
    for mention in mentions:
        first, last = _token_range(starts, ends, mention["start"], mention["end"])
        mention["token_start"], mention["token_end"] = first, last
        mention["words"] = [t.word for t in tokens[first:last]]
    return mentions


def _locate_candidates(candidates: list[dict], tokens: list[Token]) -> list[dict]:
    starts = [t.start for t in tokens]
    ends = [t.end for t in tokens]
    located = []
    for cand in candidates:
        first, last = _token_range(starts, ends, cand["start"], cand["end"])
        surface = surface_text(cand["surface"])
        located.append({
            **cand,
            "surface": surface,
            "folded": _fold(surface),
            "token_start": first,
            "token_end": last,
            "words": [t.word for t in tokens[first:last]],
        })
    located.sort(key=lambda c: c["start"])
    return located


def _score(
    doc_id: str,
    mentions: list[dict],
    candidates: list[dict],
    regions: list[Region],
    known_gids: set[str],
    alternatives=None,
) -> list[dict]:
    """Verdict records for every reference mention and every unconsumed tier-1 candidate."""
    records: list[dict] = []
    used: set[int] = set()
    projected: list[tuple[dict, tuple[int, int]]] = []

    for mention in mentions:
        record = _score_mention(doc_id, mention, candidates, regions, known_gids, used,
                                alternatives)
        records.append(record)
        if record["verdict"] not in ("neutral_out_of_scope", "neutral_empty"):
            span = _projected_span(mention, regions)
            if span:
                projected.append((mention, span))

    for index, cand in enumerate(candidates):
        if index in used or cand["tier"] != 1:
            continue
        records.append(_score_candidate(doc_id, cand, regions, projected))
    return records


def _projected_span(mention: dict, regions: list[Region]) -> tuple[int, int] | None:
    start = project(regions, mention["token_start"])
    if start is None:
        return None
    end = project(regions, max(mention["token_end"] - 1, mention["token_start"]))
    return start, (end + 1 if end is not None else start + 1)


def _score_mention(
    doc_id: str,
    mention: dict,
    candidates: list[dict],
    regions: list[Region],
    known_gids: set[str],
    used: set[int],
    alternatives=None,
) -> dict:
    if mention["token_end"] <= mention["token_start"]:
        return _record(doc_id, "neutral_empty", mention=mention)
    span = _projected_span(mention, regions)
    if span is None:
        return _record(doc_id, "neutral_out_of_scope", mention=mention)
    if known_gids and mention["gid"] not in known_gids:
        return _record(doc_id, "neutral_unlisted", mention=mention)

    picked = _pick_candidate(mention, span, candidates, used, alternatives)
    if picked is None:
        return _record(doc_id, "miss", mention=mention)
    index, by_alternative = picked
    used.add(index)
    cand = candidates[index]
    if cand["tier"] != 1:
        record = _record(doc_id, "worklist_available", mention=mention, cand=cand)
        record["reference_gid"] = mention["gid"]
        record["resolved_by"] = "alternative_id" if by_alternative else "reported_id"
        return record
    if _is_wide_span(mention, cand):
        return _record(doc_id, "neutral_wide_span", mention=mention, cand=cand)
    return _record(doc_id, "hit", mention=mention, cand=cand)


def _pick_candidate(
    mention: dict,
    span: tuple[int, int],
    candidates: list[dict],
    used: set[int],
    alternatives=None,
) -> tuple[int, bool] | None:
    """Nearest unused candidate for a mention, plus whether an alternative id resolved it.

    First pass: the same id, tier 1 winning over tier 2 at equal distance. Second pass:
    a tier-2 candidate whose reported id differs while the mention's id is among the
    alternatives its form carries in the lexicon. The matcher reports the
    lexicographically first owner of an ambiguous form and leaves the choice to the judge
    stage, so such a mention sits on the worklist rather than being lost (the anchor
    collision of the Jaspers spouses is the corpus case).
    """
    best = _nearest(mention, span, candidates, used, lambda c: c["gid"] == mention["gid"])
    if best is not None:
        return best, False
    if alternatives is None:
        return None
    best = _nearest(mention, span, candidates, used, lambda c: (
        c["tier"] != 1 and mention["gid"] in alternatives(c["surface"])))
    return (best, True) if best is not None else None


def _nearest(mention: dict, span: tuple[int, int], candidates: list[dict],
             used: set[int], accepts) -> int | None:
    best: tuple[int, int, int] | None = None
    for index, cand in enumerate(candidates):
        if index in used or not accepts(cand):
            continue
        distance = abs(cand["token_start"] - span[0])
        overlaps = cand["token_start"] < span[1] and span[0] < cand["token_end"]
        same_surface = cand["folded"] == mention["folded"]
        if not overlaps and not (same_surface and distance <= POSITION_TOLERANCE):
            continue
        key = (cand["tier"], distance, index)
        if best is None or key < best:
            best = key
    return best[2] if best else None


def candidate_alternatives(lexicon: dict, surface: str) -> set[str]:
    """Every listed id the matcher's own indexes attach to a surface form.

    A tier-2 candidate reports one owner and leaves the rest to the judge stage, so the
    alternatives decide whether a reference id is reachable at that position at all.
    """
    forms = [surface]
    if surface.endswith("s"):
        forms.append(surface[:-1])
    out: set[str] = set()
    for form in forms:
        for index in ("forms", "caps_forms"):
            for owner in lexicon.get(index, {}).get(form, ()):
                out.add(owner[0])
        for index in ("surnames", "caps_surnames"):
            out.update(lexicon.get(index, {}).get(form, ()))
    return out


def _is_wide_span(mention: dict, cand: dict) -> bool:
    """True when the reference wraps the wider citation and our candidate the title only.

    Restricted to works, because that is where the title-only decision of 2026-08-12
    binds; a person span narrower than the reference stays a hit and is flagged instead.
    """
    return (
        mention["category"] == "work"
        and len(cand["words"]) < len(mention["words"])
        and _is_contiguous_part(cand["words"], mention["words"])
    )


def _is_contiguous_part(part: list[str], whole: list[str]) -> bool:
    if not part:
        return False
    return any(whole[i:i + len(part)] == part for i in range(len(whole) - len(part) + 1))


def _score_candidate(
    doc_id: str,
    cand: dict,
    regions: list[Region],
    projected: list[tuple[dict, tuple[int, int]]],
) -> dict:
    if not _in_pipe_scope(regions, cand["token_start"]):
        return _record(doc_id, "neutral_out_of_scope_candidate", cand=cand)
    for mention, span in projected:
        if mention["gid"] == cand["gid"]:
            continue
        if span[0] <= cand["token_start"] and cand["token_end"] <= span[1]:
            return _record(doc_id, "neutral_nested", cand=cand, mention=mention)
    if cand["gid"] == AUTHOR_GID:
        return _record(doc_id, "fp_author", cand=cand)
    return _record(doc_id, "false_positive", cand=cand)


def _record(doc_id: str, verdict: str, mention: dict | None = None,
            cand: dict | None = None) -> dict:
    """One scored mention; the candidate side fills rule, tier and context where present.

    Identity follows the candidate where there is one, so a nesting verdict names the
    candidate that nests rather than the reference span it sits in.
    """
    source = cand or mention
    record = {
        "doc": doc_id,
        "verdict": verdict,
        "gid": source["gid"],
        "category": source["category"],
        "surface": source["surface"],
        "rule": cand["rule"] if cand else None,
        "tier": cand["tier"] if cand else None,
        "ref_offset": mention["start"] if mention else None,
        "pipe_offset": cand["start"] if cand else None,
        "context": cand.get("context") if cand else None,
    }
    if mention and cand and mention["folded"] != cand["folded"]:
        record["ref_surface"] = mention["surface"]
    if verdict == "neutral_nested" and mention:
        record["nested_in"] = mention["gid"]
    return record


def _count_verdicts(records: list[dict]) -> dict:
    counts = Counter(r["verdict"] for r in records)
    return {verdict: counts.get(verdict, 0) for verdict in VERDICTS}


# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------

def legacy_indexed_docs(legacy_path: Path | str | None) -> set[str]:
    """Reference documents the legacy mention index was harvested from (its `files` lists).

    These are the documents whose gold forms historically leaked into the lexicon, so
    they form the dev split; the rest is held out.
    """
    if legacy_path is None or not Path(legacy_path).exists():
        return set()
    payload = json.loads(Path(legacy_path).read_text(encoding="utf-8"))
    docs: set[str] = set()
    for group in payload.values():
        if not isinstance(group, dict):
            continue
        for entry in group.values():
            for name in (entry.get("files") or []) if isinstance(entry, dict) else []:
                docs.add(Path(str(name)).stem)
    return docs


def split_of(doc_id: str, legacy_docs: set[str]) -> str:
    if doc_id == SPECIAL_DOC:
        return f"special_{SPECIAL_DOC}"
    return "dev" if doc_id in legacy_docs else "held_out"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def metrics(records: list[dict]) -> dict:
    """Precision and recall of tier 1 plus the tier-1+2 candidate coverage."""
    counts = _count_verdicts(records)
    hits = counts["hit"]
    worklist = counts["worklist_available"]
    scoreable = hits + counts["miss"] + worklist
    return {
        "counts": counts,
        "scoreable_reference_mentions": scoreable,
        "precision_tier1": _rate(hits, hits + counts["false_positive"]),
        "recall_tier1": _rate(hits, scoreable),
        "coverage_tier12": _rate(hits + worklist, scoreable),
        "author_false_positives": counts["fp_author"],
    }


def _group(records: list[dict], key) -> dict:
    buckets: dict[str, list[dict]] = {}
    for record in records:
        buckets.setdefault(key(record), []).append(record)
    return {name: metrics(items) for name, items in sorted(buckets.items())}


def _doc_key(doc_id: str) -> tuple[int, str]:
    return (int(doc_id), "") if doc_id.isdigit() else (10**9, doc_id)


def build_report(results: list[dict], sources: dict) -> dict:
    """Aggregate the per-document results into the deterministic report."""
    ordered = sorted(results, key=lambda r: _doc_key(r["doc"]))
    records = [record for result in ordered for record in result["records"]]
    by_split: dict[str, list[dict]] = {}
    for result in ordered:
        by_split.setdefault(result.get("split", "unassigned"), []).extend(result["records"])
    return {
        "generated_from": {**sources, "code": "entity_matcher"},
        "parameters": {
            "gap_tolerance_tokens": GAP_TOLERANCE,
            "min_region_matched_tokens": MIN_REGION_MATCHED,
            "position_tolerance_tokens": POSITION_TOLERANCE,
            "author_gid": AUTHOR_GID,
            "special_doc": SPECIAL_DOC,
        },
        "totals": {
            "documents": len(ordered),
            "scored": sum(1 for r in ordered if r["status"] == "ok"),
            "unreadable": [r["doc"] for r in ordered if r["status"] == "unreadable"],
            "no_pipeline": [r["doc"] for r in ordered if r["status"] == "no_pipeline"],
            **metrics(records),
        },
        "splits": {
            name: {"documents": sorted({r["doc"] for r in items}, key=_doc_key),
                   **metrics(items),
                   "by_category": _group(items, lambda r: r["category"]),
                   "by_rule": _group(items, lambda r: r["rule"] or "(no candidate)")}
            for name, items in sorted(by_split.items())
        },
        "by_category": _group(records, lambda r: r["category"]),
        "by_rule": _group(records, lambda r: r["rule"] or "(no candidate)"),
        "documents": [
            {
                "doc": result["doc"],
                "split": result.get("split", "unassigned"),
                "status": result["status"],
                "error": result["error"],
                "reference_mentions": result["reference_mentions"],
                "candidates": result["candidates"],
                "scope": result["scope"],
                "counts": result["counts"],
            }
            for result in ordered
        ],
        "errors": {
            verdict: [r for r in records if r["verdict"] == verdict]
            for verdict in ERROR_VERDICTS
        },
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def reference_doc_ids(ref_dir: Path) -> list[str]:
    """Document ids with a reference TEI (the Pilot subfolder is a superseded precursor)."""
    return sorted({p.stem for p in Path(ref_dir).glob("*.xml")}, key=_doc_key)


def run_benchmark(doc_ids: list[str], ref_dir: Path, pipe_dir: Path,
                  find_candidates, known_gids: set[str], legacy_docs: set[str],
                  alternatives=None) -> list[dict]:
    """Score every document; reference and pipeline files are only read."""
    results = []
    for doc_id in doc_ids:
        ref_path = Path(ref_dir) / f"{doc_id}.xml"
        pipe_path = Path(pipe_dir) / f"{doc_id}_final.xml"
        if not ref_path.exists():
            print(f"  {doc_id}: SKIP (no reference TEI)")
            continue
        pipe_xml = pipe_path.read_bytes().decode("utf-8") if pipe_path.exists() else None
        result = benchmark_document(doc_id, ref_path.read_bytes().decode("utf-8"),
                                    pipe_xml, find_candidates, known_gids, alternatives)
        result["split"] = split_of(doc_id, legacy_docs)
        results.append(result)
        print(f"  {doc_id} [{result['split']}]: {_doc_line(result)}")
    return results


def _doc_line(result: dict) -> str:
    if result["status"] != "ok":
        return f"{result['status'].upper()} ({_ascii(result['error'] or '')[:60]})"
    counts = result["counts"]
    neutral = sum(counts[v] for v in VERDICTS if v.startswith("neutral"))
    return (f"hit {counts['hit']}, miss {counts['miss']}, "
            f"worklist {counts['worklist_available']}, fp {counts['false_positive']}, "
            f"author-fp {counts['fp_author']}, neutral {neutral}")


def _ascii(text) -> str:
    """Fold to ASCII for the Windows console (the JSON report keeps full Unicode)."""
    return str(text).encode("ascii", "replace").decode("ascii")


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _print_summary(report: dict) -> None:
    totals = report["totals"]
    print(f"\n  Documents: {totals['documents']}  scored: {totals['scored']}  "
          f"unreadable: {len(totals['unreadable'])} {totals['unreadable']}")
    print(f"  Reference mentions scoreable: {totals['scoreable_reference_mentions']}  "
          f"neutral: {sum(totals['counts'][v] for v in VERDICTS if v.startswith('neutral'))}")

    print("\n  Split                 mentions  precision  recall  coverage(T1+T2)  author-fp")
    for name, split in report["splits"].items():
        print(f"    {_ascii(name):20} {split['scoreable_reference_mentions']:8}  "
              f"{_pct(split['precision_tier1']):>9}  {_pct(split['recall_tier1']):>6}  "
              f"{_pct(split['coverage_tier12']):>15}  {split['author_false_positives']:9}")

    print("\n  Verdicts (all splits):")
    for verdict in VERDICTS:
        print(f"    {verdict:32} {totals['counts'][verdict]}")

    for verdict in ("false_positive", "miss", "worklist_available"):
        items = report["errors"][verdict]
        print(f"\n  Top {verdict} classes ({len(items)} total):")
        key = (lambda r: r["rule"] or "(no candidate)") if verdict != "miss" else (
            lambda r: r["category"])
        for name, count in sorted(Counter(key(r) for r in items).items(),
                                  key=lambda kv: (-kv[1], kv[0]))[:MAX_PRINTED]:
            print(f"    {_ascii(name):32} {count}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_doc_ids(values: list[str]) -> list[str]:
    """Accept both comma-separated and space-separated document ids."""
    return [d.strip() for value in values for d in value.split(",") if d.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gold benchmark of the entity matcher against the reference TEIs")
    parser.add_argument("--docs", nargs="+", help="Document ids, e.g. --docs 100 290")
    parser.add_argument("--out", type=Path, default=REPORT_PATH, help="Report path")
    parser.add_argument("--entities", type=Path, default=ENTITIES_PATH, help="Curated entity list")
    parser.add_argument("--cache", type=Path, default=GND_CACHE_PATH,
                        help="GND variant cache (optional, used when present)")
    parser.add_argument("--legacy", type=Path, default=LEGACY_MENTIONS_PATH,
                        help="Old mention index (optional; also defines the dev split)")
    parser.add_argument("--review", type=Path, default=VARIANT_REVIEW_PATH,
                        help="Variant review verdicts (optional, used when present)")
    parser.add_argument("--policy", type=Path, default=MARKING_POLICY_PATH,
                        help="Markierungspolitik (JSON, optional)")
    parser.add_argument("--ref-dir", type=Path, default=REFERENCE_TEI_DIR,
                        help="Reference TEI directory (read only)")
    parser.add_argument("--src-dir", type=Path, default=TEI_FINAL_DIR,
                        help="Pipeline TEI directory (read only)")
    args = parser.parse_args()

    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    legacy = args.legacy if args.legacy and args.legacy.exists() else None
    review = args.review if args.review.exists() else None
    policy = args.policy if args.policy.exists() else None
    lexicon = build_lexicon(args.entities, args.cache, legacy_path=legacy,
                            review_path=review, policy_path=policy)
    doc_ids = _parse_doc_ids(args.docs) if args.docs else reference_doc_ids(args.ref_dir)

    def find(xml_string):
        return find_candidates(xml_string, lexicon)

    print(f"Entity gold benchmark over {len(doc_ids)} reference document(s); "
          "nothing is written to TEI.")
    results = run_benchmark(doc_ids, args.ref_dir, args.src_dir, find,
                            set(lexicon["entries"]), legacy_indexed_docs(legacy),
                            lambda surface: candidate_alternatives(lexicon, surface))
    report = build_report(results, {
        "entities": str(args.entities),
        "cache": str(args.cache) if Path(args.cache).exists() else None,
        "legacy": str(legacy) if legacy else None,
        "reference_dir": str(args.ref_dir),
        "pipeline_dir": str(args.src_dir),
    })
    _print_summary(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
