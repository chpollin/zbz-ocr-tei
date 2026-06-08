"""
Struktur-Audit: Pipeline-TEI (tei_final) gegen Ground Truth (reference_tei).

Zaehlt strukturelle TEI-Bausteine (pb, note, figure/graphic, div@type, front/back,
anchor ...) je Objekt und stellt Pipeline gegen ZBZ-Referenz. NUR DIAGNOSE -- schreibt
nichts an den TEI-Daten und ist KEIN Pass/Fail-Gate.

WICHTIG zur Interpretation: Die 25 Referenz-TEIs sind Teiltranskriptionen (die Pipeline
ist oft vollstaendiger). Reine Zaehl-Deltas beweisen daher KEINEN Fehler. Bekannte,
erklaerbare Abweichungen (keine Defekte):
- front/back/anchor: in der Pipeline bewusst nicht automatisch erzeugt (Kuration).
- div type="text": Pipeline-Konvention, um Regel R5 zu erfuellen (jedes div braucht
  type oder n) und lose Bloecke valide einzuwickeln; die ZBZ-Referenz nutzt blanke <div>.
- graphic vs. facs: Pipeline verknuepft Abbildungen ueber @facs (Faksimile-Zonen),
  die Referenz ueber <graphic url="*.tif">. Beides gueltiges TEI.

Aufruf:
    python -m scripts.eval.structure_audit                 # Tabelle + Summen (stdout)
    python -m scripts.eval.structure_audit --doc 760       # nur ein Objekt
    python -m scripts.eval.structure_audit --json PFAD     # zusaetzlich JSON-Report

Quelle der Wahrheit fuer Pfade: scripts/config.py (REFERENCE_TEI_DIR, TEI_FINAL_DIR).
"""
import argparse
import json
import re
from collections import Counter
import xml.etree.ElementTree as ET

from scripts.config import REFERENCE_TEI_DIR, TEI_FINAL_DIR

TEI = "{http://www.tei-c.org/ns/1.0}"

# Strukturelle Bausteine, die wir gegenueberstellen.
KEY_ELEMENTS = [
    "pb", "note", "figure", "graphic", "head", "p",
    "lg", "l", "table", "list", "front", "back", "div", "anchor",
]


def _localname(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def analyze(path):
    """Strukturzaehlung eines TEI-Dokuments. Gibt (daten, fehlertext) zurueck."""
    try:
        root = ET.parse(str(path)).getroot()
    except Exception as exc:  # nicht wohlgeformtes XML etc.
        return None, str(exc)
    elements = Counter()
    note_place = Counter()
    div_type = Counter()
    for el in root.iter():
        name = _localname(el.tag)
        elements[name] += 1
        if name == "note":
            note_place[el.get("place") or "(none)"] += 1
        elif name == "div":
            div_type[el.get("type") or "(none)"] += 1
    return {
        "elements": dict(elements),
        "note_place": dict(note_place),
        "div_type": dict(div_type),
    }, None


def _key(elements):
    return {k: elements.get(k, 0) for k in KEY_ELEMENTS}


def _reference_ids(single=None):
    ids = []
    for path in sorted(REFERENCE_TEI_DIR.glob("*.xml")):
        m = re.match(r"^(\d+)\.xml$", path.name)
        if m:
            ids.append(int(m.group(1)))
    ids.sort()
    if single is not None:
        ids = [i for i in ids if i == single]
    return ids


def run(single=None, json_path=None):
    if not REFERENCE_TEI_DIR.exists():
        print("Referenz-TEIs nicht vorhanden (%s) -- nichts zu vergleichen." % REFERENCE_TEI_DIR)
        return 0

    ids = _reference_ids(single)
    print("Objekte mit Ground Truth: %d" % len(ids))
    print("=" * 96)
    print("{:>6} | {:>9} | {:>9} | {:>11} | {:>9} | {:>9}".format(
        "DOC", "pb r/f", "note r/f", "fig+gra r/f", "front r/f", "back r/f"))
    print("-" * 96)

    rows = []
    skipped = []
    for did in ids:
        ref_path = REFERENCE_TEI_DIR / ("%d.xml" % did)
        fin_path = TEI_FINAL_DIR / ("%d_final.xml" % did)
        if not fin_path.exists():
            skipped.append((did, "kein tei_final"))
            print("{:>6} | kein tei_final".format(did))
            continue
        ref, ref_err = analyze(ref_path)
        fin, fin_err = analyze(fin_path)
        if ref_err or fin_err:
            skipped.append((did, "parse: ref=%s fin=%s" % (ref_err, fin_err)))
            print("{:>6} | parse-error ref={} fin={}".format(did, ref_err, fin_err))
            continue
        rk, fk = _key(ref["elements"]), _key(fin["elements"])
        rows.append({"doc": did, "ref": ref, "fin": fin})
        print("{:>6} | {:>3}/{:<3} | {:>3}/{:<3} | {:>4}/{:<4} | {:>3}/{:<3} | {:>3}/{:<3}".format(
            did,
            rk["pb"], fk["pb"],
            rk["note"], fk["note"],
            rk["figure"] + rk["graphic"], fk["figure"] + fk["graphic"],
            rk["front"], fk["front"],
            rk["back"], fk["back"]))

    print("=" * 96)
    print("r = reference (Ground Truth, Teiltranskription), f = final (Pipeline)")

    # Aggregate
    agg = Counter()
    for row in rows:
        for k in KEY_ELEMENTS:
            agg["ref_" + k] += row["ref"]["elements"].get(k, 0)
            agg["fin_" + k] += row["fin"]["elements"].get(k, 0)
    print("\nSUMMEN ueber %d vergleichbare Objekte:" % len(rows))
    for k in KEY_ELEMENTS:
        r, f = agg["ref_" + k], agg["fin_" + k]
        print("  %-8s ref=%5d  fin=%5d  delta=%+d" % (k, r, f, f - r))

    for label, side in [("Pipeline", "fin"), ("Ground Truth", "ref")]:
        c = Counter()
        for row in rows:
            c.update(row[side]["div_type"])
        print("\ndiv @type (%s):" % label)
        for k, v in c.most_common():
            print("  %-14s %d" % (k, v))

    if skipped:
        print("\nUebersprungen:")
        for did, why in skipped:
            print("  %6d  %s" % (did, why))

    if json_path:
        payload = {
            "compared": len(rows),
            "skipped": [{"doc": d, "reason": w} for d, w in skipped],
            "aggregate": {k: {"ref": agg["ref_" + k], "fin": agg["fin_" + k]} for k in KEY_ELEMENTS},
            "per_doc": rows,
        }
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print("\nJSON-Report: %s" % json_path)

    return 0


def main():
    ap = argparse.ArgumentParser(description="Struktur-Audit Pipeline vs Ground Truth (nur Diagnose).")
    ap.add_argument("--doc", type=int, default=None, help="nur dieses Objekt (DOC_ID)")
    ap.add_argument("--json", dest="json_path", default=None, help="JSON-Report-Pfad")
    args = ap.parse_args()
    raise SystemExit(run(single=args.doc, json_path=args.json_path))


if __name__ == "__main__":
    main()
