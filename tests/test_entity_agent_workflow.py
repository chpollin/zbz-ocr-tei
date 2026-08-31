"""Closed-world context and review contract of the AI-agent entity phase."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.config import TEI_SCHEMA_PATH
from scripts.entity.entity_agent_context import build_context, write_context
from scripts.entity.entity_agent_review import apply_review, normalize_decisions
from scripts.entity.entity_provenance import (
    AGENT_ANNOTATION_RESP_ID,
    EDITOR_VERIFICATION_RESP_ID,
    LLM_JUDGE_RESP_ID,
    MATCHER_RESP_ID,
)
from tests.conftest import delivery_doc

DOC_ID = "9999"
GID_A = "118522175"
GID_B = "118815679"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fixture_project(root: Path) -> tuple[dict, Path]:
    source = delivery_doc(
        '<pb facs="#facs_1" n="1"/><div type="text"><p>Corneille schrieb.</p></div>'
    )
    start = source.index("Corneille")
    candidate = {
        "gid": GID_A,
        "category": "person",
        "surface": "Corneille",
        "start": start,
        "end": start + len("Corneille"),
        "tier": 2,
        "rule": "bare-surname:ambiguous",
        "alternatives": [GID_B],
        "matched_form": "Corneille",
        "form_source": "surname-index",
        "context": "Corneille schrieb.",
    }

    source_path = root / "output" / "tei_final" / f"{DOC_ID}_final.xml"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(source.encode("utf-8"))
    pages = root / "docs" / "data" / "pages" / DOC_ID
    pages.mkdir(parents=True)
    (pages / f"{DOC_ID}_entity_p1.xml").write_text(
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<pb facs="#facs_1" n="1"/><p>Corneille schrieb.</p>'
        "</body></text></TEI>",
        encoding="utf-8",
    )
    (pages / f"{DOC_ID}_p1.md").write_text("Corneille schrieb.\n", encoding="utf-8")
    worklist_entry = {field: candidate.get(field) for field in (
        "gid", "category", "surface", "rule", "alternatives", "matched_form",
        "form_source", "context",
    )}
    worklist_entry.update({"text": "Corneille", "occurrence": 1})
    _write_json(
        pages / f"{DOC_ID}_entity_worklist.json",
        {"doc": DOC_ID, "pages": {"1": [worklist_entry]}},
    )

    image = root / "docs" / "images" / DOC_ID / f"{DOC_ID}_p001.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"synthetic image")
    report_path = root / "output" / "entity_preview" / "entity_pilot_report.json"
    _write_json(report_path, {
        "documents": [{"doc": DOC_ID, "wrapped": [], "worklist": [candidate]}],
    })
    entities_path = root / "docs" / "data" / "entities.json"
    _write_json(entities_path, {
        GID_A: {"label": "Corneille, Pierre", "category": "person",
                "dates": "1606-1684", "lobid": f"https://lobid.org/gnd/{GID_A}"},
        GID_B: {"label": "Hersch, Jeanne", "category": "person",
                "dates": "1910-2000", "lobid": f"https://lobid.org/gnd/{GID_B}"},
    })
    schema_path = root / "data" / "schema" / "zbz_hersch.rng"
    schema_path.parent.mkdir(parents=True)
    shutil.copyfile(TEI_SCHEMA_PATH, schema_path)
    guidelines_path = root / "data" / "source" / "guidelines" / "Editionsrichtlinien_ZBZ.md"
    guidelines_path.parent.mkdir(parents=True)
    guidelines_path.write_text("# Synthetic guidelines\n", encoding="utf-8")

    packet = build_context(
        DOC_ID,
        1,
        project_root=root,
        pages_dir=root / "docs" / "data" / "pages",
        report_path=report_path,
        entities_path=entities_path,
        schema_path=schema_path,
        guidelines_path=guidelines_path,
        verdicts_path=root / "data" / "entities" / "absent.json",
    )
    context_path = root / "output" / "entity_agent_context" / f"{DOC_ID}_p1.json"
    write_context(packet, context_path)
    return packet, context_path


def _response(packet: dict, *, selected_gid: str = GID_A, with_judge: bool = True) -> dict:
    decision = {
        "candidate_id": packet["candidates"][0]["candidate_id"],
        "verdict": "accept",
        "selected_gid": selected_gid,
        "reason": "The facsimile and sentence context identify the listed person.",
        "evidence_refs": ["facsimile", "tei_page", "transcription"],
    }
    if with_judge:
        decision["judge"] = {
            "run_id": "judge-run-1",
            "harness": "subagent",
            "model": "independent-model",
            "prompt_sha256": "b" * 64,
            "verdict": "agree",
        }
    return {
        "context_id": packet["context_id"],
        "run": {
            "id": "agent-run-1",
            "harness": "codex",
            "model": "agent-model",
            "prompt_sha256": "a" * 64,
            "tool_calls": [
                "inspect_facsimile",
                "compare_transcription_and_tei",
                "validate_relaxng_after_annotation",
            ],
        },
        "decisions": [decision],
    }


def test_context_packet_binds_all_modalities_and_keeps_the_candidate_set_closed(tmp_path):
    packet, _ = _fixture_project(tmp_path)
    assert packet["context_id"].startswith("ctx-")
    assert packet["decision_contract"] == {
        "closed_world": True,
        "allowed_verdicts": ["accept", "reject", "needs_expert"],
        "may_assign_new_gnd": False,
        "accepted_gid_must_be_listed_in": "candidate.allowed_gids",
        "agent_review_is_editor_verification": False,
        "editor_verification_must_be_person_bound": True,
    }
    assert set(packet["inputs"]) == {
        "facsimile", "tei_page", "transcription", "source_tei", "worklist",
        "entity_report", "entity_index", "schema", "guidelines",
    }
    assert packet["inputs"]["tei_page"]["content"].startswith("<TEI")
    assert packet["inputs"]["transcription"]["content"] == "Corneille schrieb.\n"
    assert packet["candidates"][0]["allowed_gids"] == [GID_A, GID_B]
    assert [identity["gid"] for identity in packet["candidates"][0]["identities"]] == [
        GID_A, GID_B,
    ]


def test_context_builder_fails_when_the_facsimile_is_missing(tmp_path):
    packet, _ = _fixture_project(tmp_path)
    image_path = tmp_path / packet["inputs"]["facsimile"]["path"]
    image_path.unlink()
    with pytest.raises(FileNotFoundError, match=r"facsimile|context input"):
        build_context(
            DOC_ID,
            1,
            project_root=tmp_path,
            report_path=tmp_path / packet["inputs"]["entity_report"]["path"],
            entities_path=tmp_path / packet["inputs"]["entity_index"]["path"],
            schema_path=tmp_path / packet["inputs"]["schema"]["path"],
            guidelines_path=tmp_path / packet["inputs"]["guidelines"]["path"],
            verdicts_path=tmp_path / "absent.json",
        )


def test_response_cannot_select_an_identifier_outside_the_packet(tmp_path):
    packet, _ = _fixture_project(tmp_path)
    response = _response(packet, selected_gid="invented-gnd")
    with pytest.raises(ValueError, match="outside candidate"):
        normalize_decisions(packet, response)


def test_ai_agent_cannot_claim_editor_verification(tmp_path):
    packet, _ = _fixture_project(tmp_path)
    response = _response(packet)
    response["decisions"][0]["editor_verification_ref"] = "editor-1"
    with pytest.raises(ValueError, match="cannot claim editor verification"):
        normalize_decisions(packet, response)


def test_review_writes_a_schema_valid_preview_with_role_provenance(tmp_path):
    packet, context_path = _fixture_project(tmp_path)
    response = _response(packet, selected_gid=GID_B)
    record = apply_review(
        packet,
        response,
        context_path=context_path,
        project_root=tmp_path,
        out_dir=tmp_path / "output" / "entity_agent_review",
    )
    written = (tmp_path / record["result"]["tei_preview"]).read_text(encoding="utf-8")
    expected_resp = " ".join((
        f"#{MATCHER_RESP_ID}",
        f"#{AGENT_ANNOTATION_RESP_ID}",
        f"#{LLM_JUDGE_RESP_ID}",
    ))
    assert (
        f'<persName ref="GND:{GID_B}" source="bare-surname:ambiguous" '
        f'resp="{expected_resp}">Corneille</persName>'
    ) in written
    assert ' cert=' not in written
    assert f'<respStmt xml:id="{EDITOR_VERIFICATION_RESP_ID}">' not in written
    assert record["result"]["rng_valid"] is True
    assert record["result"]["text_invariant"] is True
    assert record["result"]["tei_sha256"] == hashlib.sha256(
        (tmp_path / record["result"]["tei_preview"]).read_bytes()
    ).hexdigest()


def test_review_refuses_inputs_changed_after_context_creation(tmp_path):
    packet, context_path = _fixture_project(tmp_path)
    source_path = tmp_path / packet["inputs"]["source_tei"]["path"]
    source_path.write_text(source_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after packet creation"):
        apply_review(
            packet,
            _response(packet),
            context_path=context_path,
            project_root=tmp_path,
            out_dir=tmp_path / "output" / "entity_agent_review",
        )
