"""
Helper: Generiert Agent-Prompts fuer Screening-Batches aus dem Manifest.

Aufruf:
    python -m scripts.tei.screening_prompt --batch 7
    python -m scripts.tei.screening_prompt --batches 7-12
"""

import argparse
import json
import sys
from pathlib import Path

MANIFEST = Path(__file__).parent.parent.parent / "output" / "tei_final" / "screening_manifest.json"
ROOT = "c:\\Users\\Chrisi\\Documents\\GitHub\\DHCraft\\zbz-ocr-tei"

PROMPT_TEMPLATE = """Du bist ein TEI Quality Screener. Pruefe diese {n_docs} Docs (Tier {tier}, {inspect}) und schreibe Review-JSONs.

DOCS: {doc_ids}

PRO DOC:
1. LESE TEI: {root}\\output\\tei_unified\\{{ID}}\\{{ID}}_final.xml
2. SCHAUE Overlay (wenn vorhanden): {root}\\output\\layout\\{{ID}}\\{{ID}}_p001_overlay.png
3. PRUEFE: Titel/Autor/Sprache korrekt? div-Typ passend? Entities plausibel? Text vollstaendig?
4. RUN: python -m scripts.tei.tei_validator --doc {{ID}}

SCHREIBE pro Doc: {root}\\output\\tei_final\\{{ID}}_review.json
Format: {{"doc_id":"...","reviewer":"agent-screening-v2","date":"2026-03-15","status":"APPROVED|APPROVED_WITH_NOTES|NEEDS_REVIEW","layers":{{"L1_scan":{{"score":"ok|warning|n/a","pages_inspected":[...],"notes":"..."}},"L2_ocr":{{"score":"ok|warning","notes":"..."}},"L3_layout":{{"score":"ok|warning","notes":"..."}},"L4_tei":{{"score":"ok|warning","validator_warnings":[],"notes":"..."}},"L5_reference":{{"score":"n/a"}},"L6_entities":{{"score":"ok|warning","counts":{{"persName":0,"orgName":0,"placeName":0,"bibl":0}},"notes":"..."}},"L7_coherence":{{"score":"ok|warning","notes":"..."}}}},"findings":["..."],"overall_notes":"..."}}

Bekannte Muster (ignorieren): W3=Doppelseiten normal, W10=nur persName bei Philosophie normal, W6=keine lb normal.
Sei EHRLICH. NEEDS_REVIEW wenn echte Probleme (Halluzinationen, fehlender Text, falscher Inhalt)."""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int)
    parser.add_argument("--batches", help="Range, e.g. 7-12")
    args = parser.parse_args()

    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    if args.batch:
        batch_ids = [args.batch]
    elif args.batches:
        start, end = map(int, args.batches.split("-"))
        batch_ids = list(range(start, end + 1))
    else:
        parser.print_help()
        return

    for bid in batch_ids:
        batch = manifest["batches"][bid - 1]
        doc_ids = ", ".join(d["doc_id"] for d in batch["docs"])
        prompt = PROMPT_TEMPLATE.format(
            n_docs=len(batch["docs"]),
            tier=batch["tier"],
            inspect=batch["inspect_strategy"],
            doc_ids=doc_ids,
            root=ROOT,
        )
        print(f"=== BATCH {bid} (Tier {batch['tier']}, {len(batch['docs'])} docs) ===")
        print(prompt)
        print()


if __name__ == "__main__":
    main()
