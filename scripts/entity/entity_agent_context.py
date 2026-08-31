"""Build a self-contained context packet for agentic entity annotation.

The packet binds one facsimile page, its transcription, the current TEI preview, the
page worklist, the curated GND identities, the project schema and the editorial
guidelines by path and SHA-256. Textual page inputs travel inline; the facsimile remains
a local image path that an AI harness can open with its image tool.

The decision space is closed-world. An agent may accept one of the GND identifiers
already attached to a candidate, reject the candidate, or refer it to an editor. The
packet never authorizes a newly invented identifier and never writes the TEI.

Usage:
    python -m scripts.entity.entity_agent_context --doc 1060 --page 5
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.config import (
    DATA_DIR,
    DOCS_DIR,
    OUTPUT_DIR,
    PROJECT_ROOT,
    TEI_FINAL_DIR,
    TEI_SCHEMA_PATH,
)
from scripts.eval.audit_common import facsimile_path

CONTEXT_SCHEMA_VERSION = "zbz-entity-agent-context-1"
DEFAULT_OUT_DIR = OUTPUT_DIR / "entity_agent_context"
REPORT_PATH = OUTPUT_DIR / "entity_preview" / "entity_pilot_report.json"
ENTITIES_PATH = DOCS_DIR / "data" / "entities.json"
VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
GUIDELINES_PATH = DATA_DIR / "source" / "guidelines" / "Editionsrichtlinien_ZBZ.md"

_SIGNATURE_FIELDS = (
    "gid",
    "category",
    "surface",
    "rule",
    "matched_form",
    "form_source",
    "context",
)


def sha256_path(path: Path) -> str:
    """Return the SHA-256 digest of one required file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path: Path, project_root: Path = PROJECT_ROOT) -> str:
    """Return a stable repository-relative path, failing outside the repository."""
    return Path(path).resolve().relative_to(Path(project_root).resolve()).as_posix()


def input_record(
    path: Path,
    *,
    project_root: Path,
    media_type: str,
    include_text: bool = False,
) -> dict:
    """Describe one immutable context input and optionally carry its text inline."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"required agent context input not found: {path}")
    record = {
        "path": repo_path(path, project_root),
        "sha256": sha256_path(path),
        "media_type": media_type,
    }
    if include_text:
        record["content"] = path.read_text(encoding="utf-8")
    return record


def candidate_id(doc_id: str, candidate: dict) -> str:
    """Return a stable identifier for one span-bound closed-world candidate."""
    material = (
        f"{doc_id}\0{candidate['start']}\0{candidate['end']}\0"
        f"{candidate['gid']}\0{candidate['rule']}"
    ).encode()
    return f"cand-{hashlib.sha256(material).hexdigest()[:16]}"


def _signature(record: dict) -> tuple:
    return tuple(record.get(field) for field in _SIGNATURE_FIELDS)


def _document_result(report: dict, doc_id: str) -> dict:
    for result in report.get("documents") or ():
        if str(result.get("doc")) == doc_id:
            return result
    raise ValueError(f"document {doc_id} is absent from the entity preview report")


def page_candidates(doc_result: dict, worklist: dict, page: int) -> list[dict]:
    """Bind page-mirror entries back to their offset-bearing report candidates."""
    pools: dict[tuple, list[dict]] = {}
    for candidate in sorted(doc_result.get("worklist") or (), key=lambda item: item["start"]):
        pools.setdefault(_signature(candidate), []).append(candidate)

    bound = []
    for entry in (worklist.get("pages") or {}).get(str(page), ()):
        signature = _signature(entry)
        matches = pools.get(signature) or []
        if not matches:
            raise ValueError(
                f"page worklist entry is stale for document {doc_result.get('doc')}: "
                f"{entry.get('surface')!r}"
            )
        candidate = dict(matches.pop(0))
        candidate["occurrence"] = entry.get("occurrence")
        bound.append(candidate)
    return bound


def _identity(gid: str, entities: dict) -> dict:
    record = entities.get(gid)
    if record is None:
        raise ValueError(f"candidate GND id is absent from the curated entity index: {gid}")
    return {
        "gid": gid,
        "label": record.get("label"),
        "category": record.get("category"),
        "dates": record.get("dates"),
        "lobid": record.get("lobid"),
    }


def context_candidate(doc_id: str, candidate: dict, entities: dict) -> dict:
    """Project one matcher candidate into the agent's closed decision space."""
    allowed_gids = []
    for gid in (candidate["gid"], *(candidate.get("alternatives") or ())):
        if gid not in allowed_gids:
            allowed_gids.append(gid)
    return {
        "candidate_id": candidate_id(doc_id, candidate),
        "span": {"start": candidate["start"], "end": candidate["end"]},
        "surface": candidate["surface"],
        "category": candidate["category"],
        "rule": candidate["rule"],
        "matched_form": candidate.get("matched_form"),
        "form_source": candidate.get("form_source"),
        "local_context": candidate.get("context"),
        "occurrence": candidate.get("occurrence"),
        "allowed_gids": allowed_gids,
        "identities": [_identity(gid, entities) for gid in allowed_gids],
    }


def context_fingerprint(packet: dict) -> str:
    """Digest the complete packet except its self-referential context id."""
    material = dict(packet)
    material.pop("context_id", None)
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_context(
    doc_id: str,
    page: int,
    *,
    project_root: Path = PROJECT_ROOT,
    pages_dir: Path | None = None,
    report_path: Path | None = None,
    entities_path: Path | None = None,
    schema_path: Path | None = None,
    guidelines_path: Path | None = None,
    verdicts_path: Path | None = None,
) -> dict:
    """Build and fingerprint the context packet for one document page."""
    project_root = Path(project_root)
    pages_dir = Path(pages_dir or (project_root / "docs" / "data" / "pages"))
    report_path = Path(report_path or (project_root / REPORT_PATH.relative_to(PROJECT_ROOT)))
    entities_path = Path(entities_path or (project_root / ENTITIES_PATH.relative_to(PROJECT_ROOT)))
    schema_path = Path(schema_path or (project_root / TEI_SCHEMA_PATH.relative_to(PROJECT_ROOT)))
    guidelines_path = Path(
        guidelines_path or (project_root / GUIDELINES_PATH.relative_to(PROJECT_ROOT))
    )
    verdicts_path = Path(verdicts_path or (project_root / VERDICTS_PATH.relative_to(PROJECT_ROOT)))
    doc_dir = pages_dir / doc_id
    paths = {
        "facsimile": project_root / facsimile_path(doc_id, page),
        "tei_page": doc_dir / f"{doc_id}_entity_p{page}.xml",
        "transcription": doc_dir / f"{doc_id}_p{page}.md",
        "source_tei": project_root / TEI_FINAL_DIR.relative_to(PROJECT_ROOT) / f"{doc_id}_final.xml",
        "worklist": doc_dir / f"{doc_id}_entity_worklist.json",
        "entity_report": report_path,
        "entity_index": entities_path,
        "schema": schema_path,
        "guidelines": guidelines_path,
    }
    records = {
        "facsimile": input_record(
            paths["facsimile"], project_root=project_root, media_type="image/png"
        ),
        "tei_page": input_record(
            paths["tei_page"], project_root=project_root,
            media_type="application/tei+xml", include_text=True,
        ),
        "transcription": input_record(
            paths["transcription"], project_root=project_root,
            media_type="text/markdown", include_text=True,
        ),
        "source_tei": input_record(
            paths["source_tei"], project_root=project_root,
            media_type="application/tei+xml",
        ),
        "worklist": input_record(
            paths["worklist"], project_root=project_root, media_type="application/json"
        ),
        "entity_report": input_record(
            paths["entity_report"], project_root=project_root, media_type="application/json"
        ),
        "entity_index": input_record(
            paths["entity_index"], project_root=project_root, media_type="application/json"
        ),
        "schema": input_record(
            paths["schema"], project_root=project_root, media_type="application/xml"
        ),
        "guidelines": input_record(
            paths["guidelines"], project_root=project_root, media_type="text/markdown"
        ),
    }
    if verdicts_path.is_file():
        records["agent_review_store"] = input_record(
            verdicts_path, project_root=project_root, media_type="application/json"
        )

    report = json.loads(paths["entity_report"].read_text(encoding="utf-8"))
    worklist = json.loads(paths["worklist"].read_text(encoding="utf-8"))
    entities = json.loads(paths["entity_index"].read_text(encoding="utf-8"))
    candidates = page_candidates(_document_result(report, doc_id), worklist, page)
    packet = {
        "schema_version": CONTEXT_SCHEMA_VERSION,
        "document": {"doc": doc_id, "page": page},
        "task": (
            "Inspect the facsimile, transcription and TEI page. Decide each supplied "
            "entity candidate inside the closed GND candidate set."
        ),
        "inputs": records,
        "candidates": [context_candidate(doc_id, candidate, entities)
                       for candidate in candidates],
        "tool_contract": {
            "required_checks": [
                "inspect_facsimile",
                "compare_transcription_and_tei",
                "validate_relaxng_after_annotation",
            ],
            "optional_checks": ["independent_llm_judge"],
        },
        "decision_contract": {
            "closed_world": True,
            "allowed_verdicts": ["accept", "reject", "needs_expert"],
            "may_assign_new_gnd": False,
            "accepted_gid_must_be_listed_in": "candidate.allowed_gids",
            "agent_review_is_editor_verification": False,
            "editor_verification_must_be_person_bound": True,
        },
        "response_contract": {
            "required_run_fields": ["id", "harness", "model", "prompt_sha256", "tool_calls"],
            "required_decision_fields": ["candidate_id", "verdict", "reason", "evidence_refs"],
            "accept_requires": ["selected_gid"],
            "judge_fields": ["run_id", "harness", "model", "prompt_sha256", "verdict"],
        },
    }
    packet["context_id"] = f"ctx-{context_fingerprint(packet)[:20]}"
    return packet


def write_context(packet: dict, out_path: Path) -> Path:
    """Write one deterministic context packet."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an AI-agent entity context packet")
    parser.add_argument("--doc", required=True, help="Document id")
    parser.add_argument("--page", type=int, required=True, help="One-based page number")
    parser.add_argument("--out", type=Path, help="Output JSON path")
    args = parser.parse_args()
    packet = build_context(args.doc, args.page)
    out_path = args.out or DEFAULT_OUT_DIR / f"{args.doc}_p{args.page}.json"
    print(write_context(packet, out_path))


if __name__ == "__main__":
    main()
