from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
RUN = ROOT / "runs" / "gpt-5.6-sol-local-probe"
EXACT_RQ = "How does Jeanne Hersch define the institutional conditions under which schools can foster critical judgement?"
HERSCH_START = "L'ÉCOLE, LIEU DE RENCONTRE DE MÉMOIRE ET D'INVENTION"
ILLICH_START = "POURQUOI IVAN ILLICH VEUT-IL DÉSCOLARISER LA SOCIÉTÉ ?"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_invalid(validator: Draft202012Validator, data: dict, label: str) -> None:
    try:
        validator.validate(data)
    except ValidationError:
        return
    raise AssertionError(f"negative schema case accepted: {label}")


def page_sections(text: str) -> dict[str, str]:
    p003_marker = "[PAGE_ID 1000_p003 | PRINTED_PAGE 965]"
    p004_marker = "[PAGE_ID 1000_p004 | PRINTED_PAGE 966]"
    require(p003_marker in text and p004_marker in text, "page markers missing")
    p003 = text.split(p003_marker, 1)[1].split(p004_marker, 1)[0]
    p004 = text.split(p004_marker, 1)[1]
    return {"1000_p003": p003, "1000_p004": p004}


def check_structured_quotes(data: dict, pages: dict[str, str], label: str) -> int:
    checked = 0
    for entity in data["entities"]:
        require(entity["evidence_quote"] in pages[entity["page_id"]], f"{label}: entity quote/page mismatch")
        checked += 1
    for topic in data["topic_annotations"]:
        for evidence in topic["evidence"]:
            require(evidence["exact_quote"] in pages[evidence["page_id"]], f"{label}: topic quote/page mismatch")
            checked += 1
    return checked


def main() -> None:
    schema = load_json(ROOT / "schema" / "annotation.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    example = load_json(ROOT / "examples" / "annotation-example.json")
    run03 = load_json(RUN / "03-schema-topics-output.json")
    run04 = load_json(RUN / "04-evidence-annotation-output.json")
    metadata = load_json(RUN / "input" / "metadata.json")
    provenance = load_json(RUN / "provenance.json")
    for label, data in (("example", example), ("run03", run03), ("run04", run04)):
        validator.validate(data)
        print(f"PASS schema: {label}")
    boolean_variant = copy.deepcopy(run03)
    boolean_variant["run_metadata"]["local_probe"] = False
    boolean_variant["run_metadata"]["gemini_output"] = True
    validator.validate(boolean_variant)
    print("PASS boolean provenance fields accept both Boolean values")
    accepted_variant = copy.deepcopy(run03)
    accepted_variant["entities"][0]["source_check_status"] = "source_checked"
    accepted_variant["entities"][0]["review_status"] = "accepted"
    validator.validate(accepted_variant)
    rejected_variant = copy.deepcopy(run03)
    rejected_variant["topic_annotations"][0]["source_check_status"] = "source_checked"
    rejected_variant["topic_annotations"][0]["review_status"] = "rejected"
    validator.validate(rejected_variant)
    print("PASS accepted/rejected require and accept source_checked")
    for item in example["entities"] + example["topic_annotations"]:
        require(item["source_check_status"] == "unchecked", "sample annotation claims unsupported source_checked status")
        require(item["review_status"] == "unreviewed", "sample annotation claims unsupported scholarly review")
    print("PASS sample annotation remains unchecked and unreviewed")

    full_text = (RUN / "01-transcription-output.md").read_text(encoding="utf-8")
    verified_text = (ROOT / "examples" / "transcription-agent-verified.md").read_text(encoding="utf-8")
    full_pages = page_sections(full_text)
    verified_pages = page_sections(verified_text)
    require("source_check_status: unchecked" in full_text.split("---", 2)[1], "run01 source-check initialization missing")
    require("review_status: unreviewed" in full_text.split("---", 2)[1], "run01 review initialization missing")
    require("M. Bandelier." in full_pages["1000_p003"], "Bandelier passage missing from full transcription")
    require(HERSCH_START in full_pages["1000_p003"], "Hersch start missing from full transcription")
    require(ILLICH_START in full_pages["1000_p004"], "Illich start missing from full transcription")
    require(ILLICH_START not in verified_text, "Illich passage leaked into agent-verified Hersch reference")
    require("M. Bandelier." not in verified_text, "Bandelier passage leaked into agent-verified Hersch reference")
    require("verification_status: agent_verified" in verified_text, "agent verification status missing")
    require("source_check_status: unchecked" in verified_text, "agent-verified reference must remain unchecked")
    require("human_source_review: not_performed" in verified_text, "human-review limit missing")
    print("PASS transcription scope and fail-closed agent-verified Hersch reference")

    baseline = (RUN / "02-baseline-topics-output.txt").read_text(encoding="utf-8")
    try:
        json.loads(baseline)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("run02 baseline is unexpectedly JSON")
    baseline_pairs = re.findall(r'(1000_p00[34])(?:\. Evidence:|,) "([^"]+)"', baseline)
    require(len(baseline_pairs) >= 12, "baseline evidence extraction unexpectedly small")
    for page_id, quote in baseline_pairs:
        require(quote in full_pages[page_id], f"baseline quote/page mismatch: {quote[:50]}")
    for marker in ("M. Bandelier", "Jeanne HERSCH", "Ivan Illich"):
        require(marker in baseline, f"baseline does not expose full-page scope: {marker}")
    baseline_quote_count = len(baseline_pairs)
    print(f"PASS baseline exact quotes and scope contamination: {baseline_quote_count} quotes")

    run03_quote_count = check_structured_quotes(run03, full_pages, "run03")
    run04_quote_count = check_structured_quotes(run04, verified_pages, "run04")
    require(run03["research_question"] == "unspecified in this run", "run03 research-question placeholder mismatch")
    require(run03["dataset_id"].endswith("full-pages"), "run03 dataset does not identify full-page scope")
    require(run04["research_question"] == EXACT_RQ, "run04 exact research question mismatch")
    require(run04["dataset_id"].endswith("hersch"), "run04 dataset does not identify Hersch scope")
    require({topic["topic_id"] for topic in run04["topic_annotations"]} == {
        "school_as_encounter",
        "memory_for_judgement",
        "pedagogical_invention",
        "social_compensation",
        "political_neutrality",
    }, "run04 controlled-code set mismatch")
    run03_text = json.dumps(run03, ensure_ascii=False)
    run04_text = json.dumps(run04, ensure_ascii=False)
    for marker in ("Bandelier", "Hersch", "Illich"):
        require(marker in run03_text, f"run03 does not expose adjacent contribution: {marker}")
    for forbidden in ("Bandelier", "Oury", "Illich", "Verne", "Orientations"):
        require(forbidden not in run04_text, f"run04 scope contamination: {forbidden}")
    print(f"PASS structured quote/page checks: run03={run03_quote_count}, run04={run04_quote_count}")
    print("PASS research-question, dataset, segment and five-code contracts")

    for label, data in (("run03", run03), ("run04", run04)):
        for item in data["entities"] + data["topic_annotations"]:
            require(item["evidence_status"] in {"direct", "indirect", "ambiguous"}, f"{label}: evidence status")
            require(item["source_check_status"] == "unchecked", f"{label}: source-check initialization")
            require(item["review_status"] == "unreviewed", f"{label}: review initialization")
    require("confidence" not in run03_text and "confidence" not in run04_text, "confidence field found")
    print("PASS status-axis initialization")

    negative_cases: list[tuple[str, dict]] = []
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["confidence"] = 0.9
    negative_cases.append(("confidence", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["evidence_status"] = "supported"
    negative_cases.append(("old evidence status", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["source_check_status"] = "verified"
    negative_cases.append(("old source-check status", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["review_status"] = "verified"
    negative_cases.append(("old review status", mutated))
    mutated = copy.deepcopy(run03)
    mutated["topic_annotations"][0]["evidence"][0]["page_id"] = "1000_p005"
    negative_cases.append(("invalid page", mutated))
    mutated = copy.deepcopy(run03)
    mutated["topic_annotations"][0]["extra"] = "x"
    negative_cases.append(("extra topic field", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["identifier"] = "X"
    mutated["entities"][0]["identifier_source"] = None
    negative_cases.append(("identifier without source", mutated))
    mutated = copy.deepcopy(run03)
    mutated["research_question"] = ""
    negative_cases.append(("empty research-question field", mutated))
    mutated = copy.deepcopy(run03)
    mutated["dataset_id"] = ""
    negative_cases.append(("empty dataset field", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["source_check_status"] = "source_mismatch"
    mutated["entities"][0]["review_status"] = "accepted"
    negative_cases.append(("source-mismatched accepted entity", mutated))
    mutated = copy.deepcopy(run03)
    mutated["topic_annotations"][0]["source_check_status"] = "source_mismatch"
    mutated["topic_annotations"][0]["review_status"] = "rejected"
    negative_cases.append(("source-mismatched rejected topic", mutated))
    mutated = copy.deepcopy(run03)
    mutated["entities"][0]["review_status"] = "accepted"
    negative_cases.append(("unchecked accepted entity", mutated))
    mutated = copy.deepcopy(run03)
    mutated["topic_annotations"][0]["review_status"] = "rejected"
    negative_cases.append(("unchecked rejected topic", mutated))
    mutated = copy.deepcopy(run03)
    mutated["run_metadata"]["date"] = "2026-02-30"
    negative_cases.append(("invalid calendar date", mutated))
    mutated = copy.deepcopy(run03)
    mutated["run_metadata"]["local_probe"] = "true"
    negative_cases.append(("non-Boolean local_probe", mutated))
    mutated = copy.deepcopy(run03)
    mutated["run_metadata"]["gemini_output"] = 0
    negative_cases.append(("non-Boolean gemini_output", mutated))
    for label, data in negative_cases:
        expect_invalid(validator, data, label)
    print(f"PASS negative schema cases: {len(negative_cases)}")

    prompt01 = (ROOT / "prompts" / "01-transcription.txt").read_text(encoding="utf-8")
    prompt02 = (ROOT / "prompts" / "02-baseline-topics.txt").read_text(encoding="utf-8")
    prompt03 = (ROOT / "prompts" / "03-schema-topics.txt").read_text(encoding="utf-8")
    prompt04 = (ROOT / "prompts" / "04-evidence-annotation.txt").read_text(encoding="utf-8")
    require("gesamten sichtbaren Text" in prompt01 and "keinen Beitrag analytisch" in prompt01, "prompt01 full-page contract missing")
    require("local_probe: <true|false>" in prompt01 and "gemini_output: <true|false>" in prompt01, "prompt01 provenance fields are not variable")
    require("local_probe: true" not in prompt01 and "gemini_output: false" not in prompt01, "prompt01 fixes local-run provenance")
    require(EXACT_RQ not in prompt02 and "annotation.schema.json" not in prompt02 and "codebook.md" not in prompt02, "prompt02 context leakage")
    require(EXACT_RQ not in prompt03 and "codebook.md" not in prompt03 and "annotation.schema.json" in prompt03, "prompt03 context contract mismatch")
    require(HERSCH_START not in prompt02 and ILLICH_START not in prompt02, "prompt02 segment leakage")
    require(HERSCH_START not in prompt03 and ILLICH_START not in prompt03, "prompt03 segment leakage")
    for required in (EXACT_RQ, HERSCH_START, ILLICH_START, "codebook.md", "annotation.schema.json", "source_check_status", "review_status"):
        require(required in prompt04, f"prompt04 contract missing: {required}")
    for label, prompt in (("prompt03", prompt03), ("prompt04", prompt04)):
        require("Set local_probe to true only for a local probe." in prompt, f"{label} local_probe is not run-specific")
        require("Set gemini_output to true only when Gemini actually produced the output." in prompt, f"{label} Gemini provenance is not run-specific")
    require("const" not in schema["properties"]["research_question"], "schema leaks exact research question")
    require("const" not in schema["properties"]["dataset_id"], "schema fixes analytic dataset")
    require(schema["$id"] == "urn:dhcraft:clariah-at-2026:annotation-schema:2.0", "schema identifier is not stable")
    require(schema["$defs"]["run_metadata"]["properties"]["local_probe"] == {"type": "boolean"}, "local_probe is not a regular Boolean")
    require(schema["$defs"]["run_metadata"]["properties"]["gemini_output"] == {"type": "boolean"}, "gemini_output is not a regular Boolean")
    print("PASS four-prompt context-isolation contract")

    prompt_paths = [
        "prompts/01-transcription.txt",
        "prompts/02-baseline-topics.txt",
        "prompts/03-schema-topics.txt",
        "prompts/04-evidence-annotation.txt",
    ]
    output_paths = [
        "runs/gpt-5.6-sol-local-probe/01-transcription-output.md",
        "runs/gpt-5.6-sol-local-probe/02-baseline-topics-output.txt",
        "runs/gpt-5.6-sol-local-probe/03-schema-topics-output.json",
        "runs/gpt-5.6-sol-local-probe/04-evidence-annotation-output.json",
    ]
    metadata_runs = metadata["run_sequence"]
    provenance_runs = [provenance["transcription"]] + provenance["extraction_runs"]
    for index, rel_path in enumerate(prompt_paths):
        actual = sha256(ROOT / rel_path)
        require(metadata_runs[index]["prompt_sha256"] == actual, f"metadata prompt hash mismatch: {rel_path}")
        require(provenance_runs[index]["prompt_sha256"] == actual, f"provenance prompt hash mismatch: {rel_path}")
    for index, rel_path in enumerate(output_paths):
        actual = sha256(ROOT / rel_path)
        require(metadata_runs[index]["output_sha256"] == actual, f"metadata output hash mismatch: {rel_path}")
        require(provenance_runs[index]["raw_output_sha256" if index == 0 else "output_sha256"] == actual, f"provenance output hash mismatch: {rel_path}")
    for document in (metadata, provenance):
        params = document["model_parameters"]
        require(params["availability"].startswith("not exposed"), "parameter availability missing")
        require(all(params[key] is None for key in ("temperature", "top_p", "seed", "reasoning_effort")), "undocumented model parameter")
    print("PASS prompt/output hashes and parameter provenance")

    rubric = (ROOT / "evaluation-rubric.md").read_text(encoding="utf-8")
    objective_scores = {"01": (5, 5), "02": (5, 5), "03": (6, 6), "04": (8, 8)}
    for run_id, (score, maximum) in objective_scores.items():
        require(f"Summe Lauf {run_id}: {score}/{maximum}" in rubric, f"rubric total mismatch: run {run_id}")
    require("Fachliche Kriterien erhalten vor ihrer Abnahme keine Punkte." in rubric, "rubric scores unreviewed scholarly criteria")
    print("PASS objective rubric scores: 01=5/5, 02=5/5, 03=6/6, 04=8/8; scholarly criteria unreviewed")

    protocol = provenance["request_response_protocol_capture"]
    require(protocol["availability"].startswith("not exposed"), "protocol-capture limitation missing")
    require(all(protocol[key] is None for key in ("request_id", "response_id", "transport_metadata", "request_envelope", "response_envelope")), "invented request/response protocol data")
    require(protocol["reconstruction"] == "not attempted", "protocol reconstruction must remain absent")
    for contract_name in ("annotation_schema", "codebook"):
        contract = provenance["validation_contracts"][contract_name]
        require(sha256(REPO / contract["path"]) == contract["current_sha256"], f"validation-contract hash mismatch: {contract_name}")
        require(contract["generation_snapshot_sha256"] is None, f"invented generation snapshot: {contract_name}")
        require(contract["generation_snapshot_status"].startswith("not captured"), f"generation-snapshot limit missing: {contract_name}")
    narrative = provenance["provenance_narrative"]
    require(sha256(REPO / narrative["path"]) == narrative["sha256"], "provenance-narrative hash mismatch")
    gate_registry = load_json(ROOT / "critical-expert-gates.json")
    registry_ref = provenance["critical_expert_gate_registry"]
    require(sha256(REPO / registry_ref["path"]) == registry_ref["sha256"], "critical-expert gate registry hash mismatch")
    require(registry_ref["gate_count"] == len(gate_registry["gates"]) == 5, "critical-expert gate count mismatch")
    gates = {gate["gate_id"]: gate for gate in gate_registry["gates"]}
    require(set(gates) == {
        "research_question",
        "codebook",
        "sample_annotation",
        "didactic_scope_boundary",
        "political_neutrality_evidence_status",
    }, "critical-expert gate set mismatch")
    for gate in gate_registry["gates"]:
        require(gate["status"] == "unreviewed", f"gate status changed without review: {gate['gate_id']}")
        require(gate["required_role"] == "critical_expert", f"gate authority mismatch: {gate['gate_id']}")
        require(gate["operational_change_applied"] is False, f"gate changed operationally: {gate['gate_id']}")
        for rel_path in gate["artifact_paths"]:
            require((REPO / rel_path).exists(), f"gate artifact missing: {rel_path}")
    require(gates["research_question"]["current_value"] == EXACT_RQ, "research-question gate value mismatch")
    require({signal["text"] for signal in gates["research_question"]["source_signals"]} == {
        "Exposé de Madame Jeanne HERSCH, professeur de philosophie à l'Université de Genève :",
        "Jean Fluck.",
    }, "research-question attribution signals missing")
    require(gates["codebook"]["current_value"]["topic_ids"] == [
        "school_as_encounter",
        "memory_for_judgement",
        "pedagogical_invention",
        "social_compensation",
        "political_neutrality",
    ], "codebook gate mismatch")
    require(gates["sample_annotation"]["current_value"]["source_check_status"] == "unchecked", "sample-annotation gate is not fail-closed")
    require(gates["didactic_scope_boundary"]["current_value"]["run_04_start_inclusive"] == HERSCH_START, "scope start gate mismatch")
    require(gates["didactic_scope_boundary"]["current_value"]["run_04_end_exclusive"] == ILLICH_START, "scope end gate mismatch")
    political_gate = gates["political_neutrality_evidence_status"]
    require(political_gate["current_value"] == "direct" and political_gate["proposed_value"] == "indirect", "political-neutrality gate mismatch")
    political = next(topic for topic in run04["topic_annotations"] if topic["topic_id"] == "political_neutrality")
    require(political["evidence_status"] == "direct", "raw political_neutrality status changed operationally")
    print("PASS protocol limitation, provenance narrative and five critical-expert gates")

    with (ROOT / "source-manifest.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 2, "manifest row count")
    for row in rows:
        commit_check = subprocess.run(
            ["git", "cat-file", "-e", f'{row["repo_commit"]}^{{commit}}'],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        require(commit_check.returncode == 0, "manifest source commit does not exist")
        require(row["annotation_input_scope"] == "full-page", "manifest full-page scope missing")
        require(row["hersch_reference_status"] == "agent_verified_unchecked", "manifest Hersch status")
        require(row["outside_hersch_status"] == "unverifiziert", "manifest outside-scope status")
        require(sha256(REPO / row["agent_verified_transcription_path"]) == row["agent_verified_transcription_sha256"], "manifest agent-verified transcription hash mismatch")
        require(row["verification_activity"] == "agentic_visual_and_automated_quote_page_and_segment_check", "manifest verification activity")
        require(row["verification_responsible_role"] == "gpt-5.6-sol_agentic_checker", "manifest verification role")
        require(row["human_source_review_status"] == "not_performed", "manifest human-review limit")
        require(sha256(REPO / row["sample_annotation_path"]) == row["sample_annotation_sha256"], "manifest sample annotation hash mismatch")
        require(row["sample_annotation_activity"] == "agentic_source_anchor_and_schema_check", "manifest sample activity")
        require(row["sample_annotation_verification_role"] == "gpt-5.6-sol_agentic_checker", "manifest sample role")
        require(row["sample_annotation_source_check_status"] == "unchecked", "manifest sample source-check status")
        require(sha256(REPO / row["local_image_path"]) == row["sha256_image"], "manifest image hash mismatch")
        require(sha256(REPO / row["local_reference_text_path"]) == row["sha256_reference_text"], "manifest reference hash mismatch")
        require(row["rights_status"] == "zu prüfen" and row["rights_note"], "manifest rights note")
    artifact_map = {item["path"]: item for item in provenance["agent_verified_reference_artifacts"]}
    for rel_path, expected_activity in (
        ("workshops/clariah-at-2026/examples/transcription-agent-verified.md", "agentic_visual_and_automated_quote_page_and_segment_check"),
        ("workshops/clariah-at-2026/examples/annotation-example.json", "agentic_source_anchor_and_schema_check"),
    ):
        item = artifact_map[rel_path]
        require(sha256(REPO / rel_path) == item["sha256"], f"provenance reference hash mismatch: {rel_path}")
        require(item["activity"] == expected_activity, f"provenance reference activity mismatch: {rel_path}")
        require(item["responsible_role"] == "gpt-5.6-sol_agentic_checker", f"provenance reference role mismatch: {rel_path}")
        require(item["source_check_status"] == "unchecked", f"provenance source-check overclaim: {rel_path}")
        require(item["human_source_review_status"] == "not_performed", f"provenance human-review overclaim: {rel_path}")
    require("human_source_reviewer" not in json.dumps(provenance), "unsupported person-bound source-review role remains")
    print("PASS manifest and provenance reference paths, hashes, activities and roles")
    print("PASS manifest source paths, statuses and rights note")

    rights = (ROOT / "rights-clearance.md").read_text(encoding="utf-8")
    for phrase in (
        "status:: pending institutional clarification",
        "Display the two facsimile pages",
        "registered participants",
        "public teaching repository",
        "Operational rule while pending",
        "decision status | pending",
    ):
        require(phrase in rights, f"rights-clearance contract missing: {phrase}")
    print("PASS rights-clearance dossier and pending-use contract")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for rel_path in prompt_paths + output_paths + [
        "codebook.md",
        "critical-expert-gates.json",
        "evaluation-rubric.md",
        "rights-clearance.md",
        "source-manifest.csv",
        "schema/annotation.schema.json",
        "examples/transcription-agent-verified.md",
        "examples/annotation-example.json",
        "runs/gpt-5.6-sol-local-probe/comparison-and-corrections.md",
        "runs/gpt-5.6-sol-local-probe/provenance.json",
        "runs/gpt-5.6-sol-local-probe/provenance-narrative.md",
        "runs/gpt-5.6-sol-local-probe/validation-report.md",
    ]:
        require((ROOT / rel_path).exists(), f"referenced artifact missing: {rel_path}")
    for phrase in ("vollständigen Seiten", "Bandelier-Text", "Illich-Text", "unverifiziert", "unspecified in this run", "python workshops/clariah-at-2026/validate.py", "Vollständiger Wiederholungsablauf"):
        require(phrase in readme, f"README contract missing: {phrase}")
    print("PASS README artifact and status contract")

    validation_report = (RUN / "validation-report.md").read_text(encoding="utf-8")
    for forbidden in (
        "source-checked Hersch-Kontrolltext",
        "Der source-checked Kontrolltext",
        "hersch_reference_status: source_checked",
        "source-checked Transkription",
    ):
        require(forbidden not in validation_report, f"validation report retains unsupported source-check claim: {forbidden}")
    for phrase in (
        "agentisch verifizierten Hersch-Referenztext",
        "source_check_status: unchecked",
        "hersch_reference_status: agent_verified_unchecked",
        "human_source_review_status: not_performed",
        "16/16 PASS",
        "fünf Critical-Expert-Gates",
        "Hersch-/Fluck-Attributionssignale",
        "01=5/5",
        "02=5/5",
        "03=6/6",
        "04=8/8",
    ):
        require(phrase in validation_report, f"validation report fail-closed contract missing: {phrase}")
    print("PASS validation-report fail-closed status and score contract")
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    main()
