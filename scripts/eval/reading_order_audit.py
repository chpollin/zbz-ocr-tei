"""
Lesereihenfolge-Audit: welche ausgelieferten Seiten wuerde der Reihenfolge-Fix (E90)
umsortieren, und wie schwellwert-stabil ist diese Umsortierung.

NUR DIAGNOSE -- liest output/tei_final, schreibt NICHTS an den TEI-Daten und ist KEIN
Pass/Fail-Gate. Bereitet die operator-gated Korpus-Neugenerierung (Milestone M3) vor, indem es
die W19-Menge (nicht-kanonische Lesereihenfolge) triagiert:

  robust  = die kanonische Umsortierung bleibt unter kleiner Schwellwert-Perturbation gleich
            (Spalten-/Band-Ordnung schwellwert-unabhaengig, hohe Konfidenz, dass der Fix die
            Seite korrekt umordnet)
  fragil  = die Umsortierung kippt schon bei kleiner Aenderung der Schwellwerte (geometrischer
            Grenzfall, etwa ein Block nahe der Vollbreiten-Schwelle), braucht fachliche Sicht
            am Faksimile, bevor der Editionstext umgeschrieben wird

"robust" heisst schwellwert-unabhaengig, NICHT bewiesen korrekt: eine systematisch falsche
Heuristik koennte stabil falsch sein. Eine kleine Sicht-Stichprobe ueber robuste Seiten
validiert diese Annahme; die fragile Liste ist die eigentliche Sicht-Arbeitsliste.

Deckungsgleich mit Validator-W19: beide nutzen iter_page_zone_bboxes + reading_order_permutation
aus tei_xml_utils, sehen also exakt dieselbe handlungsrelevante Seitenmenge.

Aufruf:
    python -m scripts.eval.reading_order_audit                # Summen (stdout)
    python -m scripts.eval.reading_order_audit --worklist     # zusaetzlich fragile Seiten je Dok
    python -m scripts.eval.reading_order_audit --dir PFAD     # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR).
"""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.config import TEI_FINAL_DIR
from scripts.core.tei_xml_utils import (
    COLUMN_GAP_PCT,
    WIDE_REGION_W_PCT,
    iter_page_zone_bboxes,
    reading_order_permutation,
)

# Schwellwert-Perturbation fuer die Stabilitaetspruefung. Klein gegenueber den Defaults
# (WIDE 60, GAP 12): kippt die Permutation schon hier, haengt die Umsortierung an einer
# Grenzentscheidung und ist ein Sicht-Fall.
WIDE_DELTAS = (-5.0, 0.0, 5.0)
GAP_DELTAS = (-3.0, 0.0, 3.0)


def classify_page(bboxes):
    """Triage einer Seite anhand ihrer Zonen-Bboxes.

    None, wenn der Fix die Seite unveraendert laesst (bereits kanonisch). Sonst 'robust',
    wenn die kanonische Umsortierung unter allen Schwellwert-Perturbationen gleich bleibt,
    oder 'fragil', wenn sie bei einer Perturbation kippt.
    """
    base = reading_order_permutation(bboxes)
    if base == list(range(len(bboxes))):
        return None
    for dw in WIDE_DELTAS:
        for dg in GAP_DELTAS:
            perm = reading_order_permutation(
                bboxes,
                wide_w_pct=WIDE_REGION_W_PCT + dw,
                column_gap_pct=COLUMN_GAP_PCT + dg,
            )
            if perm != base:
                return "fragil"
    return "robust"


def audit_document(path):
    """Triagiert ein TEI-Dokument. Gibt (per_page, fehlertext) zurueck.

    per_page ist eine Liste (page, label) fuer Seiten, die der Fix umsortieren wuerde
    (label robust|fragil); kanonische Seiten erscheinen nicht.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except Exception as exc:  # nicht wohlgeformtes XML etc.
        return [], str(exc)
    out = []
    for page, _zids, bboxes, _line in iter_page_zone_bboxes(root):
        label = classify_page(bboxes)
        if label is not None:
            out.append((page, label))
    return out, None


def audit_corpus(tei_dir):
    """Triagiert alle *_final.xml in tei_dir. Gibt ein Summen-Dict zurueck."""
    docs = {}            # doc_id -> [(page, label), ...] (nur Seiten mit Umsortierung)
    errors = []
    files = sorted(Path(tei_dir).glob("*_final.xml"))
    for f in files:
        doc_id = f.stem.replace("_final", "")
        per_page, err = audit_document(f)
        if err:
            errors.append((doc_id, err))
            continue
        if per_page:
            docs[doc_id] = per_page
    return {"total_files": len(files), "docs": docs, "errors": errors}


def _print_summary(summary):
    docs = summary["docs"]
    affected = [lab for pages in docs.values() for _, lab in pages]
    robust = affected.count("robust")
    fragil = affected.count("fragil")
    docs_fragil = sum(1 for pages in docs.values() if any(lab == "fragil" for _, lab in pages))
    print(
        f"Lesereihenfolge-Audit ueber {summary['total_files']} Dokumente "
        f"(WIDE={WIDE_REGION_W_PCT} +/-5, GAP={COLUMN_GAP_PCT} +/-3)\n"
    )
    print(f"  Dokumente mit Umsortierung:    {len(docs)}")
    print(f"  Seiten mit Umsortierung:       {len(affected)}")
    print(f"    davon robust (vertraubar):   {robust}")
    print(f"    davon fragil (Sicht noetig): {fragil}")
    print(f"  Dokumente mit fragilen Seiten: {docs_fragil}")
    if summary["errors"]:
        print(f"  Parse-Fehler:                  {len(summary['errors'])}")
    top = sorted(docs.items(), key=lambda kv: -len(kv[1]))[:15]
    if top:
        print("\n  Top betroffen (doc: Seiten gesamt / davon fragil):")
        for doc_id, pages in top:
            nf = sum(1 for _, lab in pages if lab == "fragil")
            print(f"    {doc_id}: {len(pages)} / {nf}")


def _print_worklist(summary):
    fragile_docs = {
        d: [pg for pg, lab in pages if lab == "fragil"]
        for d, pages in summary["docs"].items()
        if any(lab == "fragil" for _, lab in pages)
    }
    if not fragile_docs:
        print("\n  Keine fragilen Seiten -- keine Sicht-Arbeitsliste.")
        return
    print("\n  Sicht-Arbeitsliste (fragile Seiten je Dokument):")
    for doc_id in sorted(fragile_docs, key=lambda d: -len(fragile_docs[d])):
        pages = sorted(fragile_docs[doc_id], key=lambda p: int(p))
        print(f"    {doc_id}: {', '.join(pages)}")


def main():
    parser = argparse.ArgumentParser(
        description="Lesereihenfolge-Audit (Diagnose, schreibt nichts); triagiert die W19-Menge"
    )
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    parser.add_argument("--worklist", action="store_true",
                        help="fragile Seiten je Dokument auflisten")
    args = parser.parse_args()
    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    if args.worklist:
        _print_worklist(summary)


if __name__ == "__main__":
    main()
