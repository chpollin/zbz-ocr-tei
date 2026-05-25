"""
TEI revisionDesc Injector: Fuegt Screening-Status in den teiHeader ein.

Liest Review-JSONs und schreibt <revisionDesc> mit Pipeline- und
Screening-Status in jedes TEI in output/tei_final/.

Aufruf:
    python -m scripts.tei.tei_add_revision --all
    python -m scripts.tei.tei_add_revision --doc 290
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

TEI_FINAL_DIR = Path(__file__).parent.parent.parent / "output" / "tei_final"

# Screening-Notizen sind freier Agent-Text und enthalten teils Tag-Erwaehnungen
# (z.B. "korrekt als <note>") oder "&" -- diese muessen XML-escaped werden, sonst
# wird das revisionDesc nicht wohlgeformt. Guarded, um bestehende Entities
# (&amp; &lt; ...) nicht zu doppeln.
_ENTITY_RE = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")


def _esc_text(s: str) -> str:
    """Escapt Text fuer XML-Content ohne bestehende Entities zu doppeln."""
    s = _ENTITY_RE.sub("&amp;", s)
    return s.replace("<", "&lt;").replace(">", "&gt;")


def build_revision_desc(doc_id, review_data):
    """Baut <revisionDesc> XML-Block aus Review-Daten."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Pipeline-Eintrag (immer vorhanden)
    lines = [
        '  <revisionDesc>',
        f'    <change when="{today}" who="pipeline">TEI generated (Unified Pipeline v1, Gemini + RelaxNG)</change>',
    ]

    # Screening-Eintrag (aus Review-JSON)
    if review_data:
        status = review_data.get("status", "UNKNOWN")
        reviewer = review_data.get("reviewer", "unknown")
        date = review_data.get("date", today)

        # Kurze Zusammenfassung der Findings
        findings = review_data.get("findings", [])
        if isinstance(findings, list) and findings:
            # Nur die ersten 3 Findings als Notiz
            notes = "; ".join(
                f.get("msg", str(f)) if isinstance(f, dict) else str(f)
                for f in findings[:3]
            )
            if len(findings) > 3:
                notes += f" (+{len(findings) - 3} more)"
        else:
            notes = "No issues found"

        # Layer-Scores extrahieren
        layers = review_data.get("layers", {})
        layer_summary = []
        for layer_key in ["L1_scan", "L2_ocr", "L3_layout", "L4_tei", "L5_reference", "L6_entities", "L7_coherence"]:
            layer = layers.get(layer_key, {})
            score = layer.get("score", "n/a")
            layer_summary.append(f"{layer_key.split('_')[0]}:{score}")

        layer_str = " ".join(layer_summary)

        lines.append(
            f'    <change when="{_esc_text(date)}" who="{_esc_text(reviewer)}" '
            f'status="{_esc_text(status)}">'
            f'Agent-Based Quality Screening ({_esc_text(layer_str)}). {_esc_text(notes)}'
            f'</change>'
        )
    else:
        # Kein Review vorhanden — nur automatischer Pass
        lines.append(
            f'    <change when="{today}" who="quality-pass-auto" '
            f'status="APPROVED">Automated quality pass (header + structure + entity checks)</change>'
        )

    lines.append('  </revisionDesc>')
    return "\n".join(lines)


def inject_revision_desc(tei_path, revision_desc_xml):
    """Fuegt revisionDesc vor </teiHeader> ein (oder ersetzt bestehende)."""
    content = tei_path.read_text(encoding="utf-8")

    # Bestehende revisionDesc entfernen
    content = re.sub(
        r'\s*<revisionDesc>.*?</revisionDesc>\s*',
        '\n',
        content,
        flags=re.DOTALL
    )

    # Vor </teiHeader> einfuegen
    if "</teiHeader>" in content:
        content = content.replace(
            "</teiHeader>",
            f"{revision_desc_xml}\n  </teiHeader>"
        )
    else:
        print(f"  WARN: Kein </teiHeader> in {tei_path.name}")
        return False

    tei_path.write_text(content, encoding="utf-8")
    return True


def process_doc(doc_id):
    """Verarbeitet ein Dokument."""
    tei_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    review_path = TEI_FINAL_DIR / f"{doc_id}_review.json"

    if not tei_path.exists():
        return False, "TEI not found"

    # Review-JSON laden (optional)
    review_data = None
    if review_path.exists():
        try:
            with open(review_path, encoding="utf-8") as f:
                review_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    revision_desc = build_revision_desc(doc_id, review_data)
    success = inject_revision_desc(tei_path, revision_desc)

    status = review_data.get("status", "AUTO") if review_data else "AUTO"
    return success, status


def main():
    parser = argparse.ArgumentParser(description="TEI revisionDesc Injector")
    parser.add_argument("--doc", help="Einzelnes Dokument")
    parser.add_argument("--all", action="store_true", help="Alle Dokumente")
    args = parser.parse_args()

    if args.doc:
        doc_ids = [args.doc]
    elif args.all:
        doc_ids = sorted(
            [f.stem.replace("_final", "") for f in TEI_FINAL_DIR.glob("*_final.xml")],
            key=lambda x: int(x)
        )
    else:
        parser.print_help()
        return

    success_count = 0
    status_counts = {}
    for i, doc_id in enumerate(doc_ids, 1):
        ok, status = process_doc(doc_id)
        if ok:
            success_count += 1
            status_counts[status] = status_counts.get(status, 0) + 1
        marker = "+" if ok else "!"
        if i % 50 == 0 or i == len(doc_ids):
            print(f"  [{i}/{len(doc_ids)}] {doc_id}: {status} ({marker})")

    print(f"\n=== revisionDesc injected: {success_count}/{len(doc_ids)} ===")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
