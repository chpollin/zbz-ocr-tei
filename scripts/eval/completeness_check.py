"""
Vollstaendigkeits-Check: Vergleicht erwartete Seitenzahl (PDF/Metadaten)
mit tatsaechlichen <pb>-Elementen in den finalen TEI-Dateien.

Identifiziert Dokumente mit fehlenden Seiten oder unerwarteten Abweichungen.

Usage:
    python -m scripts.eval.completeness_check              # alle 285 Docs
    python -m scripts.eval.completeness_check --doc 1910   # einzelnes Doc
    python -m scripts.eval.completeness_check --html       # mit HTML-Report
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from scripts.config import (
    DOC_METADATA_PATH,
    EVALUATION_DIR,
    SCANS_DIR,
    TEI_FINAL_DIR,
)
from scripts.eval.audit_common import doc_id_from_path


def extract_pb_facs(content: str) -> tuple[int, list[int], bool]:
    """Parse <pb> elements and their facs indices.

    Returns (pb_count, facs_indices, all_have_facs). facs_indices holds the
    integer N from facs="#facs_N" in document order; all_have_facs is False
    if any <pb> lacks a facs reference (then facs-based reconciliation is
    unsafe and the caller falls back to the raw pb count).
    """
    pbs = re.findall(r"<pb\b[^>]*>", content)
    facs_indices: list[int] = []
    all_have_facs = True
    for pb in pbs:
        m = re.search(r'facs="#facs_(\d+)"', pb)
        if m:
            facs_indices.append(int(m.group(1)))
        else:
            all_have_facs = False
    return len(pbs), facs_indices, all_have_facs


def reconcile_page_count(
    expected_pages: int,
    pb_count: int,
    facs_indices: list[int],
    all_have_facs: bool,
    pdf_pages: int,
) -> dict:
    """Reconcile the pb structure against the expected physical scan count.

    Two deterministic counting artifacts are neutralized:
      (a) split double page -- two <pb> share one facs scan; inflates pb_count.
      (b) leading cover -- facs numbering starts above 1 (library / e-periodica
          cover scan carries no content pb); deflates pb_count.

    Each adjustment is capped to only close the gap toward expected, never to
    overshoot it. A split can shave off at most the pb excess above expected; a
    leading cover can add at most the shortfall below expected. This keeps the
    check on its own dimension (page count): a document whose pb already equals
    expected stays OK even when facs labels are swapped (a facs-integrity issue
    for other audits), while genuine content loss beyond the artifacts still
    surfaces as MINOR/MISMATCH.
    """
    if facs_indices and all_have_facs:
        distinct_facs = len(set(facs_indices))
        leading_cover = min(facs_indices) - 1
        split_pages = pb_count - distinct_facs
    else:
        # No usable facs mapping: fall back to the raw pb count.
        distinct_facs = pb_count
        leading_cover = 0
        split_pages = 0

    reference = expected_pages if expected_pages > 0 else pdf_pages
    effective = pb_count
    if reference > 0:
        if pb_count > reference and split_pages > 0:
            effective = pb_count - min(split_pages, pb_count - reference)
        elif pb_count < reference and leading_cover > 0:
            effective = pb_count + min(leading_cover, reference - pb_count)

    count_status = "OK"
    if expected_pages > 0 and effective > 0:
        diff = abs(effective - expected_pages)
        if diff > 0:
            ratio = effective / expected_pages
            if ratio < 0.8 or ratio > 1.3:
                count_status = "MISMATCH"
            else:
                count_status = "MINOR"

    return {
        "effective_pages": effective,
        "distinct_facs": distinct_facs,
        "split_pages": split_pages,
        "leading_cover": leading_cover,
        "count_status": count_status,
    }


def count_pdf_pages(pdf_path: Path) -> int:
    """Zaehlt Seiten einer PDF-Datei (ohne externe Dependencies)."""
    try:
        content = pdf_path.read_bytes()
        # Einfacher Regex-Ansatz: /Type /Page zaehlen (nicht /Pages)
        # Funktioniert fuer die meisten PDFs
        count = len(re.findall(rb"/Type\s*/Page(?!\s*s)", content))
        return count if count > 0 else -1
    except Exception:
        return -1


def check_text_per_page(tei_path: Path) -> list[dict]:
    """Extrahiert Textlaenge pro Seite aus TEI."""
    try:
        content = tei_path.read_text(encoding="utf-8")
    except Exception:
        return []

    # Text zwischen <pb>-Elementen aufteilen
    parts = re.split(r"<pb\s[^>]*>", content)
    pages = []
    for i, part in enumerate(parts[1:], 1):  # Skip Header vor erstem <pb>
        # Tags entfernen, nur Text zaehlen
        text = re.sub(r"<[^>]+>", "", part)
        text = text.strip()
        pages.append({
            "page": i,
            "char_count": len(text),
            "word_count": len(text.split()),
        })
    return pages


def run(doc_ids: list[str] | None = None, generate_html: bool = False) -> dict:
    """Fuehrt Vollstaendigkeits-Check durch."""

    # Metadaten laden
    with open(DOC_METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    docs_meta = metadata.get("documents", {})

    # Dokumente bestimmen
    if doc_ids:
        target_ids = doc_ids
    else:
        target_ids = sorted(
            doc_id_from_path(p)
            for p in TEI_FINAL_DIR.glob("*_final.xml")
        )

    print(f"Vollstaendigkeits-Check: {len(target_ids)} Dokumente")
    print()

    documents = {}
    issues = []

    for doc_id in target_ids:
        tei_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
        if not tei_path.exists():
            continue

        # Erwartete Seitenzahl aus Metadaten
        expected_pages = docs_meta.get(doc_id, {}).get("page_count", 0)

        # Tatsaechliche <pb>-Elemente + facs-Struktur
        content = tei_path.read_text(encoding="utf-8")
        actual_pb, facs_indices, all_have_facs = extract_pb_facs(content)

        # PDF-Seitenzahl als dritte Quelle
        pdf_path = SCANS_DIR / f"{doc_id}.pdf"
        pdf_pages = count_pdf_pages(pdf_path) if pdf_path.exists() else -1

        # Reconcile pb structure against physical scans (splits + leading cover)
        recon = reconcile_page_count(
            expected_pages, actual_pb, facs_indices, all_have_facs, pdf_pages
        )

        # Textlaenge pro Seite
        page_stats = check_text_per_page(tei_path)

        # Leere Seiten identifizieren (weniger als 50 Zeichen)
        empty_pages = [p for p in page_stats if p["char_count"] < 50]

        # Sehr kurze Seiten (weniger als 200 Zeichen, aber nicht leer)
        short_pages = [p for p in page_stats if 50 <= p["char_count"] < 200]

        # Durchschnittliche Textlaenge pro Seite
        char_counts = [p["char_count"] for p in page_stats if p["char_count"] > 50]
        avg_chars = sum(char_counts) / len(char_counts) if char_counts else 0

        # Ausreisser: Seiten mit weniger als 30% des Durchschnitts
        thin_pages = []
        if avg_chars > 0:
            thin_pages = [
                p for p in page_stats
                if p["char_count"] > 50 and p["char_count"] < avg_chars * 0.3
            ]

        # Bewertung
        status = "OK"
        issue_notes = []

        # Seiten-Mismatch (auf reconciled effective count, nicht roher pb-Zahl)
        effective = recon["effective_pages"]
        if recon["count_status"] in ("MISMATCH", "MINOR"):
            status = recon["count_status"]
            issue_notes.append(
                f"Seiten-{'Mismatch' if status == 'MISMATCH' else 'Differenz'}: "
                f"erwartet {expected_pages}, TEI effektiv {effective} "
                f"(pb={actual_pb}, Splits={recon['split_pages']}, "
                f"Deckblatt={recon['leading_cover']})"
            )

        # Leere Seiten
        if empty_pages:
            if status == "OK":
                status = "WARNING"
            issue_notes.append(
                f"{len(empty_pages)} leere Seite(n): {[p['page'] for p in empty_pages[:5]]}"
            )

        # Sehr duenne Seiten
        if thin_pages:
            if status == "OK":
                status = "WARNING"
            issue_notes.append(
                f"{len(thin_pages)} duenne Seite(n) (<30% Durchschnitt)"
            )

        doc_result = {
            "expected_pages": expected_pages,
            "actual_pb": actual_pb,
            "effective_pages": effective,
            "split_pages": recon["split_pages"],
            "leading_cover": recon["leading_cover"],
            "pdf_pages": pdf_pages,
            "status": status,
            "issues": issue_notes,
            "empty_pages": len(empty_pages),
            "short_pages": len(short_pages),
            "thin_pages": len(thin_pages),
            "avg_chars_per_page": round(avg_chars),
            "total_chars": sum(p["char_count"] for p in page_stats),
            "layout_type": docs_meta.get(doc_id, {}).get("layout_type", "?"),
            "language": docs_meta.get(doc_id, {}).get("language", "?"),
        }

        documents[doc_id] = doc_result

        if status != "OK":
            issues.append((doc_id, doc_result))

        # Output
        marker = f"  [{status}]" if status != "OK" else ""
        notes = "; ".join(issue_notes) if issue_notes else ""
        print(
            f"  {doc_id:>5}: pages={expected_pages:>3} pb={actual_pb:>3} "
            f"avg={avg_chars:>5.0f}ch/p  empty={len(empty_pages)} thin={len(thin_pages)}"
            f"{marker}  {notes}"
        )

    # Zusammenfassung
    statuses = [d["status"] for d in documents.values()]
    summary = {
        "total_documents": len(documents),
        "ok": statuses.count("OK"),
        "minor": statuses.count("MINOR"),
        "warning": statuses.count("WARNING"),
        "mismatch": statuses.count("MISMATCH"),
    }

    print()
    print(f"=== Zusammenfassung ===")
    print(f"  OK:       {summary['ok']}")
    print(f"  Minor:    {summary['minor']}")
    print(f"  Warning:  {summary['warning']}")
    print(f"  Mismatch: {summary['mismatch']}")

    results = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "scripts/eval/completeness_check.py",
        "summary": summary,
        "documents": documents,
    }

    # JSON speichern
    output_json = EVALUATION_DIR / "completeness_check.json"
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON: {output_json}")

    if generate_html:
        _generate_html(results, EVALUATION_DIR / "completeness_check.html")

    return results


def _generate_html(results: dict, output_path: Path) -> None:
    """Erzeugt HTML-Report fuer Vollstaendigkeits-Check."""
    docs = results["documents"]
    summary = results["summary"]

    rows = []
    for doc_id, doc in sorted(docs.items(), key=lambda x: x[1]["status"], reverse=True):
        status = doc["status"]
        color = {
            "OK": "#27ae60", "MINOR": "#f39c12",
            "WARNING": "#e67e22", "MISMATCH": "#e74c3c"
        }.get(status, "#95a5a6")

        issues_html = "<br>".join(doc["issues"]) if doc["issues"] else "-"
        rows.append(f"""
        <tr>
            <td>{doc_id}</td>
            <td>{doc['layout_type']}</td>
            <td>{doc['language']}</td>
            <td>{doc['expected_pages']}</td>
            <td>{doc['actual_pb']}</td>
            <td>{doc['avg_chars_per_page']:,}</td>
            <td>{doc['empty_pages']}</td>
            <td>{doc['thin_pages']}</td>
            <td style="color:{color};font-weight:bold">{status}</td>
            <td style="font-size:0.85em">{issues_html}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Vollstaendigkeits-Check</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
        h1 {{ color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9em; }}
        th, td {{ padding: 6px 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; position: sticky; top: 0; }}
        tr:hover {{ background: #f5f5f5; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 1rem 0; }}
        .stat {{ background: #ecf0f1; padding: 12px; border-radius: 6px; text-align: center; }}
        .stat .value {{ font-size: 1.6em; font-weight: bold; color: #2c3e50; }}
        .stat .label {{ font-size: 0.85em; color: #7f8c8d; }}
    </style>
</head>
<body>
    <h1>Vollstaendigkeits-Check</h1>
    <p>Generiert: {results['generated']}</p>
    <div class="summary">
        <div class="stat"><div class="value">{summary['total_documents']}</div><div class="label">Dokumente</div></div>
        <div class="stat"><div class="value" style="color:#27ae60">{summary['ok']}</div><div class="label">OK</div></div>
        <div class="stat"><div class="value" style="color:#f39c12">{summary['minor']}</div><div class="label">Minor</div></div>
        <div class="stat"><div class="value" style="color:#e67e22">{summary['warning']}</div><div class="label">Warning</div></div>
        <div class="stat"><div class="value" style="color:#e74c3c">{summary['mismatch']}</div><div class="label">Mismatch</div></div>
    </div>
    <table>
        <thead><tr><th>Doc</th><th>Typ</th><th>Lang</th><th>Erwartet</th><th>pb</th><th>Avg ch/p</th><th>Leer</th><th>Duenn</th><th>Status</th><th>Details</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    print(f"  HTML-Report: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vollstaendigkeits-Check (Seiten)")
    parser.add_argument("--doc", help="Einzelnes Dokument (ID)")
    parser.add_argument("--html", action="store_true", help="HTML-Report")
    args = parser.parse_args()

    doc_ids = [args.doc] if args.doc else None
    run(doc_ids=doc_ids, generate_html=args.html)
