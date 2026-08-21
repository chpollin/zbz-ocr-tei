"""Corpus-wide report of name-shaped surfaces OUTSIDE the curated entity list.

The closed-world principle (E71, knowledge/entity-integration.md) keeps mentions of
unlisted entities out of the delivered markup. This instrument is the proposal channel
that makes the excluded material visible: it collects capitalized word sequences that
no lexicon form covers, with frequency, documents and contexts, so ZBZ can decide which
of them belong on the list. The design plan names it the "frequency report of unmatched
capitalized candidates" (section "Matching method").

BINDING: the report never assigns a GND id and never guesses an identity. It carries
surface forms only; curation and id assignment stay with ZBZ.

DIAGNOSIS ONLY -- reads output/tei_final, the entity data and the viewer catalog, writes
one JSON plus one CSV to output/audits/, changes no TEI and is no gate (exit code 0).

What counts as name-shaped:

  multi-word    2 to 4 capitalized words, particles (de, von, van, der, du, d', Le, La)
                and single dotted initials ("W. James") allowed between them
  single-word   one capitalized word, only in documents whose catalog language is a
                known non-German one (German capitalizes every noun, so single words
                would be pure noise there) and never at a sentence start
  caps          the same sequences written in capitals ("YEHUDA AMICHAI")

Excluded: everything the matcher already reports as a candidate (listed entities plus
their worklist), everything outside <text>, figures, bibliography divs, already marked
entity elements and the apparatus zones (E-Periodica cover sheet, photo credits). The
exclusion zones and the offset-preserving text normalization are taken from
scripts.entity.entity_matcher, so both instruments see literally the same text; its private
helpers are imported on purpose to keep that single source.

Deliberate simplifications (the report is a proposal channel, not a gate):

- A run keeps at most one already reported name, and only as its last word, so the
  homograph case the design plan asks for stays visible ("Hans Mayer" where only
  "Mayer" is listed); everything else the matcher already reports is trimmed away.
- Particles may only stand directly before the last name of a run, which keeps
  "Simone de Beauvoir" whole and splits the German genitive pattern "Buch von Hilde
  Domin" into its noun and its name.
- A name beginning with a particle ("Van Gogh", "Le Corbusier") is reported by its head
  word only, because a leading particle cannot be told from a sentence-initial article.
- The German articles der, den, des bind only behind another particle ("van der
  Waals"); alone they carry the genitive noise of German prose rather than a name.
- Only single-letter initials count ("W. James"); "Th. Mann" loses its initial.
- Month names are stoplisted, so a forename like "August" is lost as a single word.

Usage:
    python -m scripts.entity.entity_unlisted_scan
    python -m scripts.entity.entity_unlisted_scan --docs 1540 1350
    python -m scripts.entity.entity_unlisted_scan --min-count 3
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from bisect import bisect_left
from collections import Counter
from pathlib import Path

from scripts.config import DATA_DIR, DOCS_DIR, TEI_FINAL_DIR
from scripts.entity.entity_corpus_scan import resolve_docs
from scripts.entity.entity_matcher import (
    FUNCTION_WORDS,
    MIN_TOKEN_LEN,
    SENTINEL,
    _normalize,
    _scan_zones,
    _starts_sentence,
)
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, ascii_only

ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"
MARKING_POLICY_PATH = DATA_DIR / "entities" / "marking_policy.json"
LEGACY_MENTIONS_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
CATALOG_PATH = DOCS_DIR / "data" / "catalog.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "entity_unlisted_report.json"

CLASS_MULTI = "multi-word"
CLASS_SINGLE = "single-word"
CLASS_CAPS = "caps"
CLASSES = (CLASS_MULTI, CLASS_SINGLE, CLASS_CAPS)

DEFAULT_MIN_SINGLE = 2
DEFAULT_MIN_MULTI = 1
MAX_EXAMPLES = 3
MAX_NAME_WORDS = 4
CONTEXT_RADIUS = 30
TOP_PRINTED = 20

NAME, PARTICLE, BREAK = "name", "particle", "break"

# One dotted initial, or a run of letters; digits and punctuation separate tokens.
_TOKEN_RE = re.compile(r"[^\W\d_]\.|[^\W\d_]+")
# Tokens of one run are joined by a single space, an apostrophe or a hyphen.
_SEP_RE = re.compile(r"[ ]|['’ʼ]|[-‐‑]")  # noqa: RUF001
_APOSTROPHES = frozenset("'’ʼ")  # noqa: RUF001
_LANG_SPLIT_RE = re.compile(r"[/,;+ ]+")

# Name particles; they carry no name signal of their own but stay inside a surface.
PARTICLES = frozenset({
    "d", "da", "de", "del", "della", "di", "do", "dos", "du",
    "l", "la", "le", "van", "von", "y",
})
# Articles that bind only behind another particle ("van der Waals", "von der Vogel-
# weide"). Standing alone they are German grammar, not a name.
SECONDARY_PARTICLES = frozenset({"den", "der", "des", "ten", "ter"})

_WEEKDAYS = frozenset(["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonnabend", "sonntag", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "lunedi", "martedi", "mercoledi", "giovedi", "venerdi", "sabato", "domenica"])

_MONTHS = frozenset(["januar", "februar", "maerz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember", "janvier", "fevrier", "mars", "avril", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre", "january", "february", "march", "may", "june", "july", "september", "october", "december", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "dicembre"]) | {"märz", "février", "août", "décembre"}

# Frequent sentence starters and grammatical words. Only closed word classes belong
# here; common nouns stay out, so a real name ("Thomas Mann") is never split.
_GRAMMAR_DE = frozenset(["aber", "alle", "allein", "allem", "allen", "aller", "alles", "als", "also", "am", "an", "andere", "anderen", "auch", "auf", "aus", "bei", "beim", "bis", "da", "dabei", "dadurch", "dafuer", "daher", "damit", "dann", "daran", "darauf", "daraus", "darin", "darum", "das", "dass", "dazu", "dem", "den", "denen", "denn", "dennoch", "der", "deren", "des", "deshalb", "dessen", "die", "dies", "diese", "diesem", "diesen", "dieser", "dieses", "doch", "dort", "du", "durch", "ein", "eine", "einem", "einen", "einer", "eines", "er", "es", "etwa", "euch", "fuer", "gegen", "hat", "hatte", "hier", "ich", "ihm", "ihn", "ihnen", "ihr", "ihre", "im", "immer", "in", "indem", "ist", "ja", "jede", "jedem", "jeden", "jeder", "jedes", "jene", "jener", "jetzt", "kann", "kein", "keine", "man", "mehr", "mit", "nach", "nein", "nicht", "nichts", "noch", "nun", "nur", "ob", "obwohl", "oder", "ohne", "schon", "sein", "seine", "seit", "sich", "sie", "sind", "so", "sondern", "sowie", "ueber", "um", "und", "uns", "unser", "unter", "viel", "vom", "von", "vor", "waehrend", "war", "waren", "was", "weil", "weiter", "welche", "welcher", "wenn", "wer", "werden", "wie", "wir", "wird", "wo", "zu", "zum", "zur", "zwar", "zwischen"]) | {"für", "über", "während"}

_GRAMMAR_FR = frozenset(["afin", "ainsi", "alors", "apres", "au", "aussi", "autre", "autres", "aux", "avant", "avec", "car", "ce", "cela", "celle", "celles", "celui", "ces", "cet", "cette", "ceux", "chaque", "chez", "comme", "comment", "dans", "de", "depuis", "des", "donc", "dont", "du", "elle", "elles", "en", "encore", "entre", "est", "et", "etre", "fait", "il", "ils", "je", "la", "le", "les", "leur", "leurs", "lui", "mais", "me", "meme", "moins", "mon", "ne", "ni", "non", "nos", "notre", "nous", "on", "ou", "par", "parce", "pas", "peu", "peut", "plus", "pour", "pourquoi", "quand", "que", "quel", "quelle", "qui", "quoi", "sa", "sans", "se", "selon", "ses", "si", "son", "sont", "sous", "sur", "ta", "tandis", "te", "tes", "toi", "ton", "tous", "tout", "toute", "toutes", "tres", "tu", "un", "une", "vers", "voici", "vos", "votre", "vous", "cependant", "enfin", "ensuite", "lorsque", "puisque", "toutefois", "voir", "cf", "ibid"]) | {"après", "être", "même", "très", "où"}

_GRAMMAR_EN = frozenset(["about", "after", "all", "also", "an", "and", "another", "any", "are", "as", "at", "be", "because", "been", "before", "but", "by", "can", "could", "did", "do", "does", "for", "from", "had", "has", "have", "her", "here", "him", "his", "how", "however", "if", "in", "into", "is", "it", "its", "just", "may", "might", "more", "most", "must", "my", "no", "not", "now", "of", "on", "one", "only", "or", "other", "our", "out", "over", "said", "same", "she", "should", "since", "so", "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those", "though", "through", "thus", "to", "too", "under", "until", "up", "upon", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whose", "why", "will", "with", "within", "without", "would", "you", "your"])

_GRAMMAR_IT = frozenset(["anche", "che", "ci", "coi", "col", "come", "con", "cui", "da", "dal", "dalla", "degli", "dei", "del", "della", "delle", "dello", "di", "due", "ed", "gli", "ha", "hanno", "il", "in", "io", "la", "le", "lo", "loro", "ma", "me", "mi", "ne", "nel", "nella", "no", "noi", "non", "per", "perche", "piu", "quale", "quando", "quanto", "quel", "quella", "quelli", "quello", "questa", "queste", "questi", "questo", "se", "sono", "su", "sua", "sue", "sui", "sul", "sulla", "suo", "suoi", "tra", "tu", "tutti", "tutto", "un", "una", "uno", "va", "vi", "voi"]) | {"perché", "più"}

_POSSESSIVES = frozenset(["mein", "meine", "meinem", "meinen", "meiner", "meines", "dein", "deine", "deinem", "deinen", "deiner", "deines", "seinem", "seinen", "seiner", "seines", "ihrem", "ihren", "ihrer", "ihres", "unsere", "unserem", "unseren", "unserer", "unseres", "euer", "eure", "eurem", "euren", "eurer", "eures", "mon", "ma", "mes", "ton", "ta", "tes", "leur", "leurs", "my", "your", "his", "her", "its", "our", "their"])

# Apparatus and heading words; a section heading is no entity proposal.
_HEADINGS = frozenset(["introduction", "sommaire", "chapitre", "chapitres", "preface", "avant", "propos", "annexe", "annexes", "notes", "bibliographie", "table", "matieres", "inhalt", "inhaltsverzeichnis", "vorwort", "nachwort", "einleitung", "kapitel", "register", "anhang", "abbildung", "abbildungen", "contents", "chapter", "appendix", "index", "seite", "seiten", "page", "pages", "band", "heft", "nummer", "jahrgang", "copyright"]) | {"préface", "matières"}

STOPWORDS = (_WEEKDAYS | _MONTHS | _GRAMMAR_DE | _GRAMMAR_FR | _GRAMMAR_EN
             | _GRAMMAR_IT | _POSSESSIVES | _HEADINGS)

# Catalog language codes; unknown or German ones suppress the single-word class.
_GERMAN_CODES = frozenset({"de", "deu", "ger", "deutsch", "german"})
_KNOWN_CODES = frozenset({
    "en", "eng", "english", "es", "spa", "spanish", "fr", "fra", "fre", "french",
    "it", "ita", "italian", "la", "lat", "latin", "nl", "nld", "pt", "por",
}) | _GERMAN_CODES


# ---------------------------------------------------------------------------
# Language rule
# ---------------------------------------------------------------------------

def load_languages(catalog_path: Path | str) -> dict[str, str]:
    """doc id -> catalog language; an absent catalog yields an empty mapping."""
    path = Path(catalog_path)
    if not path.exists():
        return {}
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(doc.get("id")): str(doc.get("lang") or "")
        for doc in catalog.get("documents", []) or []
        if doc.get("id") is not None
    }


def single_words_allowed(lang: str | None) -> bool:
    """True only for a recognized language without a German share.

    German capitalizes every noun, so a single capitalized word carries no name signal
    there. An unknown code is treated like German, which keeps the report conservative.
    """
    codes = {part.casefold() for part in _LANG_SPLIT_RE.split(lang or "") if part}
    return bool(codes & _KNOWN_CODES) and not (codes & _GERMAN_CODES)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _token_kind(word: str, next_char: str, prev_kind: str) -> str:
    """NAME, PARTICLE or BREAK for one token of the normalized text."""
    folded = word.casefold()
    if word.endswith("."):
        return NAME if word[0].isupper() else BREAK
    if len(word) == 1:
        return PARTICLE if folded in PARTICLES and next_char in _APOSTROPHES else BREAK
    if word[0].isupper() and folded not in STOPWORDS:
        return NAME
    if folded in PARTICLES:
        return PARTICLE
    return PARTICLE if folded in SECONDARY_PARTICLES and prev_kind == PARTICLE else BREAK


def _names_after(run: list[tuple], index: int) -> int:
    return sum(1 for token in run[index + 1:] if token[3] == NAME)


def _split_at_particles(run: list[tuple]) -> list[list[tuple]]:
    """Cut where a particle carries more than one name behind it.

    "Simone de Beauvoir" stays whole; the German genitive "Buch von Hilde Domin" falls
    apart into its noun and the name, which is where the particle really binds.
    """
    parts: list[list[tuple]] = []
    current: list[tuple] = []
    for index, token in enumerate(run):
        if token[3] == PARTICLE and _names_after(run, index) > 1:
            parts.append(current)
            current = []
        else:
            current.append(token)
    parts.append(current)
    return [part for part in parts if part]


def _emit(run: list[tuple]):
    """Yield the name tokens of every usable part of a token run.

    Leading and trailing particles fall away with the tokens between the names, whose
    span the surface covers anyway.
    """
    for part in _split_at_particles(run):
        names = [token for token in part if token[3] == NAME]
        if 1 <= len(names) <= MAX_NAME_WORDS:
            yield names


def _runs(text: str):
    """Yield the name tokens of every name-shaped run, left to right."""
    run: list[tuple] = []
    for match in _TOKEN_RE.finditer(text):
        start, end, word = match.start(), match.end(), match.group(0)
        kind = _token_kind(word, text[end:end + 1], run[-1][3] if run else BREAK)
        if kind == BREAK:
            yield from _emit(run)
            run = []
        elif run and _SEP_RE.fullmatch(text[run[-1][1]:start]):
            run.append((start, end, word, kind))
        else:
            yield from _emit(run)
            run = [(start, end, word, kind)]
    yield from _emit(run)


def _reported_mask(norm, candidates: list[dict]) -> bytearray:
    """Normalized positions the matcher already reports as a candidate."""
    mask = bytearray(len(norm.text))
    for candidate in candidates:
        start = bisect_left(norm.starts, candidate["start"])
        end = bisect_left(norm.starts, candidate["end"])
        for index in range(start, min(end, len(mask))):
            mask[index] = 1
    return mask


def _is_covered(mask: bytearray, start: int, end: int) -> bool:
    return all(mask[index] for index in range(start, end))


def _trim_reported(names: list[tuple], mask: bytearray) -> list[tuple]:
    """Drop the names the matcher already reports, keeping at most one trailing hit.

    A run lying entirely inside reported spans is known material and falls away. One
    reported name directly behind the unreported part stays, because that is the
    homograph case ZBZ has to see ("Hans Mayer" where only the surname is listed).
    """
    flags = [_is_covered(mask, token[0], token[1]) for token in names]
    if all(flags):
        return []
    first = flags.index(False)
    last = len(flags) - 1 - flags[::-1].index(False)
    tail = len(flags) - last - 1
    return names[first:last + 1 + (1 if tail == 1 else 0)]


def _is_known(surface: str, lexicon: dict) -> bool:
    """True when the surface is a lexicon form of a listed entity."""
    return any(surface in lexicon[index]
               for index in ("forms", "surnames", "caps_forms", "caps_surnames"))


def _is_known_surname(word: str, lexicon: dict) -> bool:
    key = word.rstrip(".")
    return key in lexicon["surnames"] or key in lexicon["caps_surnames"]


def _is_caps(word: str) -> bool:
    return word.isupper() and len(word.rstrip(".")) > 1


def _class_of(names: list[tuple]) -> str:
    if all(_is_caps(token[2]) for token in names):
        return CLASS_CAPS
    return CLASS_SINGLE if len(names) == 1 else CLASS_MULTI


def _single_word_ok(text: str, start: int, word: str, allow: bool) -> bool:
    if not allow or _starts_sentence(text, start) or len(word) < MIN_TOKEN_LEN:
        return False
    folded = word.casefold()
    return folded not in STOPWORDS and folded not in FUNCTION_WORDS


def _context(text: str, start: int, end: int) -> str:
    window = text[max(0, start - CONTEXT_RADIUS):end + CONTEXT_RADIUS]
    return " ".join(window.replace(SENTINEL, " ").split())


def find_unlisted(
    xml_string: str,
    lexicon: dict,
    find_candidates,
    allow_single_words: bool = False,
) -> list[dict]:
    """Name-shaped surfaces of one TEI that no lexicon form covers, left to right.

    `find_candidates(xml_string, lexicon)` supplies the spans that are already known;
    a run lying entirely inside them is dropped, a run that extends beyond them stays.
    """
    zones = _scan_zones(xml_string)
    norm = _normalize(xml_string, zones)
    reported = _reported_mask(norm, find_candidates(xml_string, lexicon))
    text = norm.text
    out: list[dict] = []
    for run_names in _runs(text):
        names = _trim_reported(run_names, reported)
        if not names:
            continue
        start, end = names[0][0], names[-1][1]
        surface = text[start:end]
        if _is_known(surface, lexicon):
            continue
        if len(names) == 1 and not _single_word_ok(text, start, names[0][2],
                                                   allow_single_words):
            continue
        out.append({
            "surface": surface,
            "class": _class_of(names),
            "words": len(names),
            "start": start,
            "context": _context(text, start, end),
            "known_surname_overlap": _is_known_surname(names[-1][2], lexicon),
        })
    return out


def scan_document(
    doc_id: str,
    xml_string: str,
    lexicon: dict,
    find_candidates,
    allow_single_words: bool,
) -> list[dict]:
    """Occurrences of one document, each stamped with its document id."""
    return [
        {"doc": doc_id, **occurrence}
        for occurrence in find_unlisted(xml_string, lexicon, find_candidates,
                                        allow_single_words)
    ]


# ---------------------------------------------------------------------------
# Aggregation and report
# ---------------------------------------------------------------------------

def aggregate(
    occurrences: list[dict],
    min_single: int = DEFAULT_MIN_SINGLE,
    min_multi: int = DEFAULT_MIN_MULTI,
) -> list[dict]:
    """One entry per surface, most frequent first, ties alphabetically."""
    groups: dict[str, dict] = {}
    for occurrence in occurrences:
        entry = groups.get(occurrence["surface"])
        if entry is None:
            entry = groups[occurrence["surface"]] = {
                "surface": occurrence["surface"],
                "class": occurrence["class"],
                "words": occurrence["words"],
                "count": 0,
                "docs": [],
                "known_surname_overlap": False,
                "examples": [],
            }
        entry["count"] += 1
        if occurrence["doc"] not in entry["docs"]:
            entry["docs"].append(occurrence["doc"])
        entry["known_surname_overlap"] |= bool(occurrence["known_surname_overlap"])
        if (len(entry["examples"]) < MAX_EXAMPLES
                and occurrence["context"] not in entry["examples"]):
            entry["examples"].append(occurrence["context"])
    kept = [entry for entry in groups.values()
            if entry["count"] >= (min_single if entry["words"] == 1 else min_multi)]
    for entry in kept:
        entry["docs"] = sorted(entry["docs"])
    return sorted(kept, key=lambda entry: (-entry["count"], entry["surface"]))


def build_report(entries: list[dict], occurrences: list[dict], doc_count: int,
                 sources: dict, params: dict) -> dict:
    """The full snapshot; every view deterministic."""
    surfaces = {entry["surface"] for entry in entries}
    by_doc = Counter(occurrence["doc"] for occurrence in occurrences
                     if occurrence["surface"] in surfaces)
    by_class = Counter(entry["class"] for entry in entries)
    return {
        "generated_from": {**sources, "code": "entity_matcher"},
        "params": params,
        "totals": {
            "documents": doc_count,
            "entries": len(entries),
            "occurrences": sum(entry["count"] for entry in entries),
            "by_class": {name: by_class.get(name, 0) for name in CLASSES},
        },
        "by_doc": {doc: by_doc[doc] for doc in sorted(by_doc)},
        "entries": entries,
    }


def write_csv(entries: list[dict], path: Path | str) -> Path:
    """Curation view: surface;class;count;docs;example (utf-8 BOM for spreadsheets)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\n")
        writer.writerow(["surface", "class", "count", "docs", "example"])
        for entry in entries:
            writer.writerow([
                entry["surface"],
                entry["class"],
                entry["count"],
                ",".join(entry["docs"]),
                entry["examples"][0] if entry["examples"] else "",
            ])
    return out


def run_scan(doc_paths, lexicon: dict, find_candidates, languages: dict,
             min_single: int, min_multi: int, sources: dict) -> dict:
    """Scan every document and build the report; the TEI files are only read."""
    occurrences: list[dict] = []
    for doc_id, path in doc_paths:
        allow = single_words_allowed(languages.get(doc_id))
        found = scan_document(doc_id, path.read_bytes().decode("utf-8"), lexicon,
                              find_candidates, allow)
        occurrences.extend(found)
        scope = "all classes" if allow else "multi-word only"
        print(f"  {doc_id}: {len(found)} candidate(s), {scope}")
    entries = aggregate(occurrences, min_single, min_multi)
    params = {"min_count_single": min_single, "min_count_multi": min_multi}
    return build_report(entries, occurrences, len(doc_paths), sources, params)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(report: dict) -> None:
    totals = report["totals"]
    print(f"\n  Documents: {totals['documents']}  entries: {totals['entries']}  "
          f"occurrences: {totals['occurrences']}")
    print("\n  By class:")
    for name, count in totals["by_class"].items():
        print(f"    {name:12} {count}")

    print(f"\n  Top {TOP_PRINTED} (proposals for ZBZ curation, no ids assigned):")
    for entry in report["entries"][:TOP_PRINTED]:
        docs = ",".join(entry["docs"][:4])
        more = "..." if len(entry["docs"]) > 4 else ""
        flag = " [known surname]" if entry["known_surname_overlap"] else ""
        print(f"    {entry['count']:5}  {ascii_only(entry['surface']):40} "
              f"{entry['class']:12} {ascii_only(docs)}{more}{flag}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Name-shaped candidates outside the curated entity list (read-only)")
    parser.add_argument("--docs", nargs="+", help="Document ids, e.g. --docs 1540 1350")
    parser.add_argument("--out", type=Path, default=REPORT_PATH,
                        help="JSON report path; the CSV is written next to it")
    parser.add_argument("--min-count", type=int, default=None,
                        help=f"Threshold for every class (default: {DEFAULT_MIN_SINGLE} "
                             f"for single words, {DEFAULT_MIN_MULTI} otherwise)")
    parser.add_argument("--entities", type=Path, default=ENTITIES_PATH,
                        help="Curated entity list")
    parser.add_argument("--cache", type=Path, default=GND_CACHE_PATH,
                        help="GND variant cache (optional, used when present)")
    parser.add_argument("--legacy", type=Path, default=LEGACY_MENTIONS_PATH,
                        help="Old mention index (optional, used when present)")
    parser.add_argument("--review", type=Path, default=VARIANT_REVIEW_PATH,
                        help="Variant review verdicts (optional, used when present)")
    parser.add_argument("--policy", type=Path, default=MARKING_POLICY_PATH,
                        help="Markierungspolitik (JSON, optional)")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH,
                        help="Viewer catalog, source of the document language")
    parser.add_argument("--src-dir", type=Path, default=TEI_FINAL_DIR,
                        help="Source TEI directory (read only)")
    args = parser.parse_args()

    from scripts.entity.entity_matcher import build_lexicon, find_candidates

    doc_ids = [d.strip() for value in (args.docs or []) for d in value.split(",") if d.strip()]
    doc_paths = resolve_docs(args.src_dir, doc_ids or None)
    legacy = args.legacy if args.legacy and args.legacy.exists() else None
    review = args.review if args.review.exists() else None
    policy = args.policy if args.policy.exists() else None
    lexicon = build_lexicon(args.entities, args.cache, legacy_path=legacy,
                            review_path=review, policy_path=policy)
    languages = load_languages(args.catalog)
    if not languages:
        print(f"  WARNING: no catalog at {args.catalog}; single words stay suppressed")
    sources = {
        "entities": str(args.entities),
        "cache": str(args.cache) if Path(args.cache).exists() else None,
        "legacy": str(legacy) if legacy else None,
        "catalog": str(args.catalog) if languages else None,
    }

    min_single = DEFAULT_MIN_SINGLE if args.min_count is None else args.min_count
    min_multi = DEFAULT_MIN_MULTI if args.min_count is None else args.min_count
    print(f"Unlisted-name scan over {len(doc_paths)} document(s); "
          f"nothing is written to TEI, no ids are assigned.")
    report = run_scan(doc_paths, lexicon, find_candidates, languages,
                      min_single, min_multi, sources)
    _print_summary(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_path = write_csv(report["entries"], args.out.with_suffix(".csv"))
    print(f"\n  JSON report: {args.out}")
    print(f"  CSV report:  {csv_path}")


if __name__ == "__main__":
    main()
