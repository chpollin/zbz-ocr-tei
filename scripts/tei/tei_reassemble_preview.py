"""
M3-Reassemble-Vorschau: reversibler Trockenlauf der Lesereihenfolge-Korrektur.

Reassembliert die W19-betroffenen Dokumente (Step 1+3 neu, mit dem M1-Lesereihenfolge-Fix
aus tei_step1.match_paragraphs_to_regions) nach ``output/tei_preview`` und stellt die
W19-Treffer vorher (``output/tei_final``, ausgeliefert) gegen nachher (Vorschau) gegenueber.

``output/tei_final`` wird NIE beruehrt: ``process_document(reassemble=True)`` schreibt in den
Arbeitsbereich ``tei_unified/{id}/`` und wird von dort flach nach
``tei_preview/{id}_final.xml`` kopiert. Damit ist die Vorschau die reversible Lane-Technik vor
der operator-gated M3-Auslieferung (E84/E90), die die Source of Truth neu schriebe.

W19 wird mit derselben geteilten Logik gezaehlt wie Validator (W19) und Audit
(iter_page_zone_bboxes + reading_order_permutation), damit die drei nie auseinanderlaufen.

Die Vorschau laeuft offline und kostenfrei (``dry_run=True``, kein Gemini-Call): sie beweist
die Lesereihenfolge-Korrektur, nicht die Text-Verfeinerung. Letztere ist von der Reihenfolge
unabhaengig und bleibt der gated Auslieferung vorbehalten.

Aufruf:
    python -m scripts.tei.tei_reassemble_preview --all
    python -m scripts.tei.tei_reassemble_preview --docs 2530 890 3040
    python -m scripts.tei.tei_reassemble_preview --all --limit 20
"""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.config import TEI_FINAL_DIR, TEI_PREVIEW_DIR, TEI_UNIFIED_DIR
from scripts.tei.tei_xml_utils import iter_page_zone_bboxes, reading_order_permutation

REPORT_PATH = Path(__file__).resolve().parents[2] / "reports" / "m3-reassemble-preview.md"


def w19_pages(path: Path) -> list[str] | None:
    """Seiten mit nicht-kanonischer Lesereihenfolge (W19); None bei Parse-/Lesefehler.

    Gleiche Definition wie tei_validator._check_reading_order und reading_order_audit.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError):
        return None
    pages = []
    for page, zids, bboxes, _line in iter_page_zone_bboxes(root):
        if reading_order_permutation(bboxes) != list(range(len(bboxes))):
            pages.append(page)
    return pages


def affected_docs(tei_dir: Path | None = None) -> list[tuple[str, list[str]]]:
    """(doc_id, w19-Seiten) fuer jedes ausgelieferte Dokument mit mindestens einer W19-Seite."""
    tei_dir = tei_dir or TEI_FINAL_DIR
    out = []
    for f in sorted(tei_dir.glob("*_final.xml")):
        doc_id = f.name[: -len("_final.xml")]
        pages = w19_pages(f)
        if pages:
            out.append((doc_id, pages))
    return out


def preview_document(doc_id: str) -> dict:
    """Reassembliert doc_id nach tei_preview und liefert die W19-Zahl vorher/nachher.

    tei_final bleibt unberuehrt. Offline und kostenfrei: ``dry_run=True`` unterbindet jeden
    Gemini-Call. Step 1 wird neu gerechnet (M1-Lesereihenfolge), Step 2 nutzt den vorhandenen
    Refinement-Cache wo warm und faellt sonst auf das Step-1-Scaffold zurueck. Die W19-Aussage
    ist davon unberuehrt, da die Lesereihenfolge in Step 1 entsteht, nicht in der
    Text-Verfeinerung; eine echte M3-Auslieferung wuerde die Verfeinerung neu rechnen (gated).
    """
    from scripts.tei.tei_unified import process_document

    final_src = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    before = w19_pages(final_src) or []
    manifest = process_document(doc_id, max_step=3, reassemble=True, dry_run=True, validate=False)
    reasm = TEI_UNIFIED_DIR / doc_id / f"{doc_id}_final.xml"
    if not reasm.exists():
        return {"doc_id": doc_id, "before": len(before), "after": None,
                "status": manifest.get("status", "no_final")}
    TEI_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    dst = TEI_PREVIEW_DIR / f"{doc_id}_final.xml"
    shutil.copyfile(reasm, dst)
    after = w19_pages(dst) or []
    return {"doc_id": doc_id, "before": len(before), "after": len(after),
            "before_pages": before, "after_pages": after, "status": "ok"}


def run_preview(doc_ids: list[str], limit: int | None = None) -> dict:
    """Vorschau ueber doc_ids; liefert Ergebnisliste plus Summen. Loggt eine etwaige Begrenzung."""
    dropped = 0
    if limit is not None and limit < len(doc_ids):
        dropped = len(doc_ids) - limit
        doc_ids = doc_ids[:limit]
    results = []
    for i, doc_id in enumerate(doc_ids, 1):
        res = preview_document(doc_id)
        results.append(res)
        a = res["after"]
        print(f"  [{i}/{len(doc_ids)}] {doc_id}: W19 {res['before']} -> "
              f"{'?' if a is None else a}  ({res['status']})")
    ok = [r for r in results if r["after"] is not None]
    return {
        "results": results,
        "docs": len(results),
        "before_total": sum(r["before"] for r in ok),
        "after_total": sum(r["after"] for r in ok),
        "failed": [r["doc_id"] for r in results if r["after"] is None],
        "dropped": dropped,
    }


def build_report(summary: dict) -> str:
    """Deterministischer Markdown-Bericht (sortiert, ohne Uhrzeit; gleiche Eingabe -> gleiche Bytes)."""
    results = sorted(summary["results"], key=lambda r: int(r["doc_id"]) if r["doc_id"].isdigit() else 0)
    lines = [
        "# M3 Reassemble-Vorschau: Lesereihenfolge (W19) vorher gegen nachher",
        "",
        "Reversibler Trockenlauf der Lesereihenfolge-Korrektur (M1) ueber die W19-betroffenen",
        "Dokumente. Die Reassemblierung (Step 1+3 neu) schreibt nach `output/tei_preview`;",
        "`output/tei_final` (Source of Truth) bleibt unberuehrt. Die eigentliche M3-Auslieferung,",
        "die `tei_final` neu schriebe, ist operator-gated (E84/E90). Erzeugt von",
        "`scripts/tei/tei_reassemble_preview.py`. W19 nach derselben Definition wie Validator und",
        "Audit. Bericht deterministisch (sortiert, ohne Zeitstempel).",
        "",
        "## Zusammenfassung",
        "",
        f"- Betroffene Dokumente in der Vorschau: {summary['docs']}",
        f"- W19-Seiten vorher (tei_final): {summary['before_total']}",
        f"- W19-Seiten nachher (Vorschau): {summary['after_total']}",
    ]
    if summary["failed"]:
        lines.append(f"- Nicht reassemblierbar (kein Cache/keine Seiten): {', '.join(summary['failed'])}")
    if summary["dropped"]:
        lines.append(f"- Per --limit ausgelassen (nicht in dieser Vorschau): {summary['dropped']} Dokumente")
    lines += [
        "",
        "## Pro Dokument",
        "",
        "| Dokument | W19 vorher | W19 nachher | Delta |",
        "|---|---|---|---|",
    ]
    for r in results:
        a = "n/a" if r["after"] is None else str(r["after"])
        delta = "n/a" if r["after"] is None else str(r["after"] - r["before"])
        lines.append(f"| {r['doc_id']} | {r['before']} | {a} | {delta} |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="M3-Reassemble-Vorschau (reversibel, tei_final unberuehrt)")
    ap.add_argument("--all", action="store_true", help="Alle W19-betroffenen Dokumente (Default-Auswahl)")
    ap.add_argument("--docs", nargs="+", help="Nur diese Dokument-IDs")
    ap.add_argument("--limit", type=int, default=None, help="Auf die ersten N Dokumente begrenzen (wird geloggt)")
    ap.add_argument("--report", type=Path, default=REPORT_PATH, help="Pfad des Markdown-Berichts")
    ap.add_argument("--no-report", action="store_true", help="Bericht nicht schreiben, nur Konsole")
    args = ap.parse_args()

    if args.docs:
        doc_ids = list(args.docs)
    else:
        doc_ids = [d for d, _ in affected_docs()]
    print(f"M3-Vorschau ueber {len(doc_ids)} Dokument(e); tei_final wird nicht beruehrt.")

    summary = run_preview(doc_ids, limit=args.limit)
    print(f"\n  W19 gesamt: vorher {summary['before_total']} -> nachher {summary['after_total']} "
          f"(ueber {summary['docs']} Dokumente)")
    if summary["failed"]:
        print(f"  Nicht reassemblierbar: {', '.join(summary['failed'])}")

    if not args.no_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(build_report(summary), encoding="utf-8")
        print(f"  Bericht: {args.report}")


if __name__ == "__main__":
    main()
