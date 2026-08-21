"""Shared scaffolding for the guideline-conformity audits in scripts/eval.

Each audit reads output/tei_final/{doc}_final.xml (the delivered TEI source of truth),
stays read-only w.r.t. those files, and writes a JSON report into output/audits/. This
module holds only what several audits share literally: the audit output directory, TEI
discovery + doc-id derivation, a tolerant parse, the report writer, the --dir CLI, and the
small console/report helpers the entity and eval diagnoses repeat (ASCII folding for the
Windows console, doc-id argument parsing, the facsimile path, deterministic count views).
"""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR

AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audits"


def doc_id_from_path(path) -> str:
    """Doc id from a '{doc}_final.xml' path."""
    return Path(path).stem.replace("_final", "")


def iter_final_tei(tei_dir):
    """Yield (doc_id, path) for each delivered TEI in tei_dir, ordered by filename."""
    for f in sorted(Path(tei_dir).glob("*_final.xml")):
        yield doc_id_from_path(f), f


def parse_tei(path):
    """Parse a TEI file to its root. Returns (root, None) or (None, error_text)."""
    try:
        return ET.parse(str(path)).getroot(), None
    except (ET.ParseError, OSError) as exc:
        return None, str(exc)


def write_audit_report(name: str, payload: dict) -> Path:
    """Write payload to output/audits/{name}.json (utf-8, indent 2) and print the path."""
    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_OUTPUT_DIR / f"{name}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON-Report: {out}")
    return out


def resolve_tei_dir(description: str) -> Path:
    """Standard --dir CLI for a diagnosis audit; returns the TEI dir (default tei_final)."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    args = parser.parse_args()
    return Path(args.dir) if args.dir else TEI_FINAL_DIR


def ascii_only(value) -> str:
    """Fold to ASCII for the Windows console (the JSON reports keep full Unicode)."""
    return str(value).encode("ascii", "replace").decode("ascii")


def parse_doc_ids(values: list[str]) -> list[str]:
    """Accept both comma-separated and space-separated document ids."""
    return [d.strip() for value in values for d in value.split(",") if d.strip()]


def text_digests(docs, tei_dir) -> dict[str, str | None]:
    """doc -> sha256 of the delivered TEI bytes, None where the document is missing.

    A stored judgment binds the bytes it was made on, so every consumer of the verdict
    store fingerprints the same way.
    """
    digests: dict[str, str | None] = {}
    for doc in sorted(set(docs)):
        path = Path(tei_dir) / f"{doc}_final.xml"
        digests[doc] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return digests


def facsimile_path(doc_id: str, page: int) -> str:
    """Repo-relative page image of a document page, so a finding can be looked at."""
    return f"docs/images/{doc_id}/{doc_id}_p{page:03d}.png"


def sorted_counts(counter: Counter) -> dict:
    """Counts as a plain dict, most frequent first, ties by key (deterministic output)."""
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))
