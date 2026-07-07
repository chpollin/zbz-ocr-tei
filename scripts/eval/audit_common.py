"""Shared scaffolding for the guideline-conformity audits in scripts/eval.

Each audit reads output/tei_final/{doc}_final.xml (the delivered TEI source of truth),
stays read-only w.r.t. those files, and writes a JSON report into output/audits/. This
module holds only what several audits share literally: the audit output directory, TEI
discovery + doc-id derivation, a tolerant parse, the report writer, and the --dir CLI.
"""
import argparse
import json
import xml.etree.ElementTree as ET
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
