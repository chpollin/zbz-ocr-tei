"""
TEI Quality Pass: Automatisierte Qualitaetspruefung und Finalisierung.

Prueft Header, Struktur, Entities und kopiert finale TEIs nach output/tei_final/.
Erzeugt ein Review-JSON pro Dokument.

Aufruf:
    python -m scripts.tei.tei_quality_pass --docs 290 2310 100
    python -m scripts.tei.tei_quality_pass --batch 1 --batch-size 48
    python -m scripts.tei.tei_quality_pass --all
"""

import argparse
import json
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import TEI_NS, TEI_UNIFIED_DIR

TEI_FINAL_DIR = Path(__file__).parent.parent.parent / "output" / "tei_final"

NS = {"tei": TEI_NS}


def get_all_doc_ids():
    """Alle Doc-IDs aus tei_unified."""
    ids = []
    for d in TEI_UNIFIED_DIR.iterdir():
        if d.is_dir() and (d / f"{d.name}_final.xml").exists():
            ids.append(d.name)
    return sorted(ids, key=lambda x: int(x))


def check_header(root):
    """Prueft teiHeader: Titel, Autor, Sprache, Datum."""
    findings = []
    header = root.find(".//tei:teiHeader", NS)
    if header is None:
        findings.append({"severity": "error", "code": "H1", "msg": "Kein teiHeader"})
        return findings

    title_el = header.find(".//tei:titleStmt/tei:title", NS)
    title = (title_el.text or "").strip() if title_el is not None else ""
    if not title:
        findings.append({"severity": "warning", "code": "H2", "msg": "Kein Titel"})

    author_el = header.find(".//tei:titleStmt/tei:author", NS)
    author = (author_el.text or "").strip() if author_el is not None else ""
    if not author:
        findings.append({"severity": "warning", "code": "H3", "msg": "Kein Autor"})

    langs = header.findall(".//tei:langUsage/tei:language", NS)
    if not langs:
        findings.append({"severity": "warning", "code": "H4", "msg": "Keine Sprache"})
    for lang in langs:
        ident = lang.get("ident", "")
        if ident == "und":
            findings.append({"severity": "warning", "code": "H5", "msg": f"Sprache undefiniert: {ident}"})

    return findings


def check_structure(root):
    """Prueft body-Struktur: divs, pb, facsimile."""
    findings = []
    body = root.find(".//tei:body", NS)
    if body is None:
        findings.append({"severity": "error", "code": "S1", "msg": "Kein body"})
        return findings

    divs = body.findall("tei:div", NS)
    if not divs:
        findings.append({"severity": "warning", "code": "S2", "msg": "Kein div im body"})

    for div in divs:
        div_type = div.get("type", "")
        if div_type and div_type not in {
            "review", "interview", "conversation", "entry",
            "bibliography", "editorial", "text", "translation",
            "reprint", "redactional", "speech", "conference",
            "letter", "preface", "sub-section", "standard",
        }:
            findings.append({"severity": "warning", "code": "S3", "msg": f"Unbekannter div-type: {div_type}"})

    pbs = root.findall(".//tei:pb", NS)
    surfaces = root.findall(".//tei:surface", NS)
    if len(pbs) != len(surfaces) and len(surfaces) > 0:
        findings.append({
            "severity": "info", "code": "S4",
            "msg": f"pb/surface Mismatch: {len(pbs)} pb, {len(surfaces)} surfaces"
        })

    notes = root.findall(".//tei:note[@place='foot']", NS)
    if notes:
        findings.append({"severity": "info", "code": "S5", "msg": f"{len(notes)} Fussnoten"})

    return findings


def check_entities(root):
    """Prueft Entity-Tags: Typen, Konflikte, Verteilung."""
    findings = []
    entity_tags = {"persName", "orgName", "placeName", "bibl"}
    counts = Counter()

    for tag in entity_tags:
        elements = root.findall(f".//tei:{tag}", NS)
        counts[tag] = len(elements)

    total = sum(counts.values())
    if total == 0:
        findings.append({"severity": "info", "code": "E1", "msg": "Keine Entities"})
    else:
        # Nur persName, keine anderen?
        if counts["persName"] > 0 and counts["orgName"] == 0 and counts["placeName"] == 0:
            findings.append({
                "severity": "info", "code": "E2",
                "msg": f"Nur persName ({counts['persName']}), keine org/place"
            })

        findings.append({
            "severity": "info", "code": "E0",
            "msg": f"Entities: {counts['persName']}p {counts['orgName']}o {counts['placeName']}l {counts['bibl']}w = {total}"
        })

    return findings


def quality_pass(doc_id):
    """Fuehrt Quality Pass fuer ein Dokument durch."""
    src = TEI_UNIFIED_DIR / doc_id / f"{doc_id}_final.xml"
    if not src.exists():
        return {"doc_id": doc_id, "status": "MISSING", "findings": []}

    try:
        tree = ET.parse(str(src))
        root = tree.getroot()
    except ET.ParseError as e:
        return {"doc_id": doc_id, "status": "PARSE_ERROR", "findings": [str(e)]}

    findings = []
    findings.extend(check_header(root))
    findings.extend(check_structure(root))
    findings.extend(check_entities(root))

    errors = [f for f in findings if f.get("severity") == "error"]
    warnings = [f for f in findings if f.get("severity") == "warning"]

    if errors:
        status = "NEEDS_REWORK"
    elif warnings:
        status = "APPROVED_WITH_NOTES"
    else:
        status = "APPROVED"

    # Finale TEI kopieren
    TEI_FINAL_DIR.mkdir(parents=True, exist_ok=True)
    dst = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    shutil.copy2(str(src), str(dst))

    # Review-JSON
    review = {
        "doc_id": doc_id,
        "reviewer": "quality-pass-auto",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": status,
        "errors": len(errors),
        "warnings": len(warnings),
        "findings": findings,
    }
    review_path = TEI_FINAL_DIR / f"{doc_id}_review.json"
    with open(str(review_path), "w", encoding="utf-8") as f:
        json.dump(review, f, indent=2, ensure_ascii=False)

    return review


def main():
    parser = argparse.ArgumentParser(description="TEI Quality Pass")
    parser.add_argument("--docs", nargs="+", help="Einzelne Doc-IDs")
    parser.add_argument("--batch", type=int, help="Batch-Nummer (1-basiert)")
    parser.add_argument("--batch-size", type=int, default=48, help="Docs pro Batch")
    parser.add_argument("--all", action="store_true", help="Alle Dokumente")
    args = parser.parse_args()

    all_ids = get_all_doc_ids()

    if args.docs:
        doc_ids = args.docs
    elif args.batch is not None:
        start = (args.batch - 1) * args.batch_size
        end = start + args.batch_size
        doc_ids = all_ids[start:end]
    elif args.all:
        doc_ids = all_ids
    else:
        parser.print_help()
        return

    results = []
    for i, doc_id in enumerate(doc_ids, 1):
        result = quality_pass(doc_id)
        status_char = "V" if result["status"] == "APPROVED" else "N" if result["status"] == "APPROVED_WITH_NOTES" else "X"
        print(f"  [{i}/{len(doc_ids)}] {doc_id}: {result['status']} ({status_char})")
        results.append(result)

    # Summary
    statuses = Counter(r["status"] for r in results)
    print(f"\n=== Quality Pass: {len(results)} Docs ===")
    print(f"  APPROVED: {statuses.get('APPROVED', 0)}")
    print(f"  APPROVED_WITH_NOTES: {statuses.get('APPROVED_WITH_NOTES', 0)}")
    print(f"  NEEDS_REWORK: {statuses.get('NEEDS_REWORK', 0)}")
    print(f"  MISSING: {statuses.get('MISSING', 0)}")

    # Summary JSON
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "method": "Automated Quality Pass (Header + Structure + Entity checks)",
        "docs_total": len(results),
        "approved": statuses.get("APPROVED", 0),
        "approved_with_notes": statuses.get("APPROVED_WITH_NOTES", 0),
        "needs_rework": statuses.get("NEEDS_REWORK", 0),
        "documents": [
            {"doc_id": r["doc_id"], "status": r["status"], "errors": r["errors"], "warnings": r["warnings"]}
            for r in results
        ],
    }
    summary_path = TEI_FINAL_DIR / "quality_pass_summary.json"
    with open(str(summary_path), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary: {summary_path}")


if __name__ == "__main__":
    main()
