"""Validate an agentic entity decision and render a schema-checked TEI preview.

The input is a context packet from :mod:`scripts.entity.entity_agent_context` and a
structured response produced by an external AI harness. Accepted decisions may promote
only candidates and GND identifiers supplied by that packet. The renderer writes a new
preview under ``output/entity_agent_review`` and a machine-readable provenance record;
the delivered TEI and the browser mirror remain untouched.

An optional independent LLM judgment is recorded as its own responsibility. It does not
become editorial verification. The latter requires a separate, person-bound record.

Usage:
    python -m scripts.entity.entity_agent_review context.json response.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.config import OUTPUT_DIR, PROJECT_ROOT
from scripts.entity.entity_agent_context import (
    CONTEXT_SCHEMA_VERSION,
    context_fingerprint,
)
from scripts.entity.tei_entity_preview import load_schema, preview_document

REVIEW_SCHEMA_VERSION = "zbz-entity-agent-review-1"
DEFAULT_OUT_DIR = OUTPUT_DIR / "entity_agent_review"
ALLOWED_VERDICTS = frozenset({"accept", "reject", "needs_expert"})
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_input(record: dict, project_root: Path) -> Path:
    """Resolve a recorded repository path and verify its bound digest."""
    raw = str(record.get("path") or "")
    if not raw:
        raise ValueError("context input has no path")
    path = (project_root / raw).resolve()
    try:
        path.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"context input escapes the repository: {raw}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"context input not found: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record.get("sha256"):
        raise ValueError(f"context input changed after packet creation: {raw}")
    return path


def validate_context(context: dict) -> None:
    """Verify the packet schema and its self-binding identifier."""
    if context.get("schema_version") != CONTEXT_SCHEMA_VERSION:
        raise ValueError("unsupported entity agent context schema")
    expected = f"ctx-{context_fingerprint(context)[:20]}"
    if context.get("context_id") != expected:
        raise ValueError("context packet fingerprint does not match context_id")
    contract = context.get("decision_contract") or {}
    if contract.get("closed_world") is not True or contract.get("may_assign_new_gnd") is not False:
        raise ValueError("context packet does not enforce the closed-world contract")


def validate_run(run: dict) -> None:
    """Validate the minimum reproducibility record of the producing agent run."""
    required = ("id", "harness", "model", "prompt_sha256", "tool_calls")
    missing = [field for field in required if not run.get(field) and field != "tool_calls"]
    if missing:
        raise ValueError(f"agent run is missing: {', '.join(missing)}")
    if not _SHA256_RE.fullmatch(str(run.get("prompt_sha256") or "")):
        raise ValueError("agent run prompt_sha256 must be a lowercase SHA-256 digest")
    if not isinstance(run.get("tool_calls"), list):
        raise ValueError("agent run tool_calls must be a list")


def normalize_decisions(context: dict, response: dict) -> list[dict]:
    """Validate decisions against the packet and return them in candidate order."""
    if response.get("context_id") != context.get("context_id"):
        raise ValueError("agent response refers to another context packet")
    run = response.get("run") or {}
    validate_run(run)
    required_checks = set((context.get("tool_contract") or {}).get("required_checks") or ())
    missing_checks = sorted(required_checks - set(run["tool_calls"]))
    if missing_checks:
        raise ValueError(f"agent run is missing required checks: {', '.join(missing_checks)}")
    candidates = {candidate["candidate_id"]: candidate
                  for candidate in context.get("candidates") or ()}
    decisions = response.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("agent response decisions must be a list")
    by_id = {}
    for raw in decisions:
        candidate_key = raw.get("candidate_id")
        if candidate_key not in candidates:
            raise ValueError(f"decision names an unknown candidate: {candidate_key}")
        if candidate_key in by_id:
            raise ValueError(f"duplicate decision for candidate: {candidate_key}")
        verdict = raw.get("verdict")
        if verdict not in ALLOWED_VERDICTS:
            raise ValueError(f"unsupported agent verdict: {verdict}")
        if not str(raw.get("reason") or "").strip():
            raise ValueError(f"decision {candidate_key} has no reason")
        evidence_refs = raw.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            raise ValueError(f"decision {candidate_key} has no evidence_refs")
        unknown_evidence = sorted(set(evidence_refs) - set(context.get("inputs") or {}))
        if unknown_evidence:
            raise ValueError(
                f"decision {candidate_key} names unknown evidence: {', '.join(unknown_evidence)}"
            )
        decision = {
            "candidate_id": candidate_key,
            "verdict": verdict,
            "reason": str(raw["reason"]).strip(),
            "evidence_refs": [str(value) for value in evidence_refs],
        }
        if verdict == "accept":
            selected_gid = str(raw.get("selected_gid") or "")
            if selected_gid not in candidates[candidate_key]["allowed_gids"]:
                raise ValueError(
                    f"accepted GND id {selected_gid!r} is outside candidate {candidate_key}"
                )
            decision["selected_gid"] = selected_gid
            judge = raw.get("judge")
            if judge is not None:
                judge_fields = ("run_id", "harness", "model", "prompt_sha256", "verdict")
                if not all(str(judge.get(field) or "").strip() for field in judge_fields):
                    raise ValueError(f"judge record for {candidate_key} is incomplete")
                if judge["run_id"] == run["id"]:
                    raise ValueError("LLM judge run must be independent from the agent run")
                if not _SHA256_RE.fullmatch(str(judge["prompt_sha256"])):
                    raise ValueError("LLM judge prompt_sha256 must be a lowercase SHA-256 digest")
                if judge["verdict"] not in {"accept", "agree"}:
                    raise ValueError("an accepted annotation requires an agreeing judge verdict")
                decision["judge"] = {
                    "run_id": str(judge["run_id"]),
                    "harness": str(judge["harness"]),
                    "model": str(judge["model"]),
                    "prompt_sha256": str(judge["prompt_sha256"]),
                    "verdict": str(judge["verdict"]),
                }
        elif raw.get("selected_gid"):
            raise ValueError(f"non-accepted decision {candidate_key} must not select a GND id")
        if raw.get("editor_verification_ref"):
            raise ValueError("an AI-agent response cannot claim editor verification")
        by_id[candidate_key] = decision
    missing_decisions = [candidate_id for candidate_id in candidates if candidate_id not in by_id]
    if missing_decisions:
        raise ValueError(f"agent response omits candidates: {', '.join(missing_decisions)}")
    return [by_id[candidate_id] for candidate_id in candidates if candidate_id in by_id]


def _document_result(report: dict, doc_id: str) -> dict:
    for result in report.get("documents") or ():
        if str(result.get("doc")) == doc_id:
            return result
    raise ValueError(f"document {doc_id} is absent from the bound entity report")


def _candidate_key(doc_id: str, candidate: dict) -> tuple:
    return (
        doc_id,
        candidate["start"],
        candidate["end"],
        candidate["gid"],
        candidate["rule"],
    )


def _context_key(doc_id: str, candidate: dict) -> tuple:
    span = candidate["span"]
    return (
        doc_id,
        span["start"],
        span["end"],
        candidate["allowed_gids"][0],
        candidate["rule"],
    )


def project_candidates(context: dict, response: dict, doc_result: dict) -> tuple[list[dict], list[dict]]:
    """Promote accepted page candidates and attach role-specific run provenance."""
    decisions = normalize_decisions(context, response)
    context_candidates = {candidate["candidate_id"]: candidate
                          for candidate in context.get("candidates") or ()}
    by_report_key = {
        _candidate_key(str(context["document"]["doc"]), candidate): candidate
        for candidate in doc_result.get("worklist") or ()
    }
    candidates = [dict(candidate) for candidate in doc_result.get("wrapped") or ()]
    candidates.extend(dict(candidate) for candidate in doc_result.get("worklist") or ())
    run_id = str(response["run"]["id"])
    normalized = []
    for decision in decisions:
        context_candidate = context_candidates[decision["candidate_id"]]
        report_candidate = by_report_key.get(
            _context_key(str(context["document"]["doc"]), context_candidate)
        )
        if report_candidate is None:
            raise ValueError(f"candidate is absent from the bound report: {decision['candidate_id']}")
        if decision["verdict"] == "accept":
            selected_gid = decision["selected_gid"]
            target = next(
                candidate for candidate in candidates
                if _candidate_key(str(context["document"]["doc"]), candidate)
                == _candidate_key(str(context["document"]["doc"]), report_candidate)
            )
            target["gid"] = selected_gid
            identity = next(
                identity for identity in context_candidate["identities"]
                if identity["gid"] == selected_gid
            )
            target["category"] = identity["category"]
            target["tier"] = 1
            target["alternatives"] = []
            target["agent_annotation_run"] = run_id
            if decision.get("judge"):
                target["llm_judge_run"] = decision["judge"]["run_id"]
        normalized.append(decision)
    return candidates, normalized


def apply_review(
    context: dict,
    response: dict,
    *,
    context_path: Path,
    project_root: Path = PROJECT_ROOT,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> dict:
    """Validate one response, render its full-document preview and record provenance."""
    validate_context(context)
    project_root = Path(project_root).resolve()
    context_path = Path(context_path).resolve()
    try:
        context_label = context_path.relative_to(project_root).as_posix()
    except ValueError as exc:
        raise ValueError("context packet must live inside the repository") from exc
    if _load_json(context_path) != context:
        raise ValueError("context packet on disk differs from the supplied context")
    inputs = context.get("inputs") or {}
    source_path = _resolve_input(inputs["source_tei"], project_root)
    report_path = _resolve_input(inputs["entity_report"], project_root)
    _resolve_input(inputs["facsimile"], project_root)
    _resolve_input(inputs["tei_page"], project_root)
    _resolve_input(inputs["transcription"], project_root)
    schema_path = _resolve_input(inputs["schema"], project_root)
    _resolve_input(inputs["guidelines"], project_root)

    doc_id = str(context["document"]["doc"])
    report = _load_json(report_path)
    doc_result = _document_result(report, doc_id)
    candidates, decisions = project_candidates(context, response, doc_result)
    out_dir = Path(out_dir)
    result = preview_document(
        doc_id,
        source_path.read_bytes().decode("utf-8"),
        candidates,
        out_dir,
        relaxng=load_schema(Path(schema_path)),
        snapshot="bound mention-verdict store",
    )
    if not result["rng_valid"] or not result["text_invariant"]:
        raise ValueError(
            "agent annotation preview failed validation: "
            f"rng_valid={result['rng_valid']}, text_invariant={result['text_invariant']}"
        )

    record = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "context_id": context["context_id"],
        "context_packet": {
            "path": context_label,
            "sha256": hashlib.sha256(context_path.read_bytes()).hexdigest(),
        },
        "document": context["document"],
        "run": response["run"],
        "decisions": decisions,
        "result": {
            "tei_preview": Path(result["output"]).resolve().relative_to(project_root).as_posix(),
            "tei_sha256": hashlib.sha256(Path(result["output"]).read_bytes()).hexdigest(),
            "rng_valid": True,
            "text_invariant": True,
        },
    }
    record_path = out_dir / f"{response['run']['id']}.json"
    record_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    record["record_path"] = record_path
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a closed-world AI-agent entity review")
    parser.add_argument("context", type=Path, help="Context packet JSON")
    parser.add_argument("response", type=Path, help="Structured agent response JSON")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    record = apply_review(
        _load_json(args.context),
        _load_json(args.response),
        context_path=args.context,
        out_dir=args.out_dir,
    )
    print(record["record_path"])


if __name__ == "__main__":
    main()
