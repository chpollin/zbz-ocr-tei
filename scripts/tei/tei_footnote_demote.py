"""Referenz-verifizierte Fussnoten-Demotion (idempotent, mit Backup).

Manche `<note place="foot">` in `tei_final` tragen in Wahrheit Fliesstext, den der
KI-TEI-Schritt (Gemini, Stufe 6) faelschlich als Fussnote ausgezeichnet hat. Da der
CER-Vergleich Fussnoten ausschliesst (E5), faellt dieser Text aus dem Vergleich
(zaehlt als Loeschung) und ist zugleich falsch ausgeliefertes TEI.

Diskriminator -- Evidenz, kein Raten: steht ein zusammenhaengender >= MIN_MATCH Zeichen
langer Ausschnitt des Notentextes im BODY der ZBZ-Referenz (`extract_text_for_comparison`
liefert ihn OHNE Fussnoten), ist der Block beweisbar Fliesstext -> Demotion nach `<p>`.
Kurze Quellenangaben `(Philosophie, I, p. 27)` bleiben unangetastet (zu kurz fuer MIN_MATCH).

Idempotent: bereits demotete Bloecke sind `<p>` und werden nicht mehr gefunden. Da die
Korrektur direkt in `output/tei_final/` schreibt (Pipeline-Output, nicht versioniert), wird
sie von einem Re-Run (`tei_unified --reassemble`) ueberschrieben -- ein erneuter `--apply`-Lauf
stellt sie deterministisch wieder her.

HOLD: 40 und 1520 sind referenz-verifiziert, aber editorisch heikel (Doc 1520 ist eine
Jaspers-Anthologie mit plausibel echten langen Zitat-Fussnoten). Sie werden nur mit
`--include-hold` angefasst -- der Body/Fussnote-Entscheid liegt bei ZBZ.

Worklist + Methodik: knowledge/decisions.md (E85); Ergebnis in knowledge/arbeitsbericht-v3.md.

  python -m scripts.tei.tei_footnote_demote --dry-run                 # alle Kandidaten zeigen
  python -m scripts.tei.tei_footnote_demote --dry-run --doc 290       # ein Doc
  python -m scripts.tei.tei_footnote_demote --apply                   # bestaetigte demoten (40/1520 ausgenommen)
  python -m scripts.tei.tei_footnote_demote --apply --include-hold    # auch 40/1520 (nach ZBZ-Freigabe)
"""
import argparse
import re
import shutil
import xml.etree.ElementTree as ET

from scripts.config import REFERENCE_TEI_DIR, TEI_FINAL_DIR
from scripts.edition.generate_edition_data import PAGES_DIR, _extract_pages_from_final
from scripts.eval.evaluate_ocr import extract_text_for_comparison

MIN_MATCH = 150          # zusammenhaengender Referenz-Treffer = Beweis fuer Fliesstext
HOLD = {"40", "1520"}    # referenz-verifiziert, aber ZBZ-Editorentscheid noetig
BACKUP_DIR = TEI_FINAL_DIR.parent / "_backup_pre_footnote_demote"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _ref_body(doc_id):
    """Body-Text der ZBZ-Referenz OHNE Fussnoten (E5), normalisiert. None wenn keine Referenz."""
    rp = REFERENCE_TEI_DIR / f"{doc_id}.xml"
    if not rp.exists():
        return None
    return _norm(extract_text_for_comparison(rp))


def _verified(note_text, ref_body):
    """True, wenn ein zusammenhaengender >= MIN_MATCH Ausschnitt im Ref-Body steht."""
    t = _norm(note_text)
    if len(t) < MIN_MATCH or not ref_body:
        return False
    for w in (300, 250, 200, MIN_MATCH):
        if w > len(t):
            continue
        for i in range(0, len(t) - w + 1, 20):
            if t[i:i + w] in ref_body:
                return True
    return False


def _candidates(doc_id):
    """Liste (xml_id, laenge, head) der referenz-verifizierten Fussnoten eines Docs."""
    pp = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    if not pp.exists():
        return []
    ref_body = _ref_body(doc_id)
    if ref_body is None:
        return []
    root = ET.fromstring(pp.read_text(encoding="utf-8"))
    out = []
    for note in root.iter():
        tag = note.tag.split("}")[-1]
        if tag != "note" or note.get("place") != "foot":
            continue
        nid = note.get(XML_ID)
        if not nid:
            continue
        text = _norm("".join(note.itertext()))
        if _verified(text, ref_body):
            out.append((nid, len(text), text[:55]))
    return out


def _demote(doc_id, ids):
    """Ersetzt <note place=foot xml:id=ID>...</note> durch <p xml:id=ID ...>...</p>.
    Backup vorher. Gibt die Zahl real geaenderter Bloecke zurueck."""
    pp = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    content = pp.read_text(encoding="utf-8")
    changed = 0
    for nid in ids:
        pat = r'(<note\b[^>]*\bxml:id="%s"[^>]*>)(.*?)(</note>)' % re.escape(nid)
        m = re.search(pat, content, re.DOTALL)
        if not m:
            continue  # schon <p> (idempotent) oder nicht gefunden
        open_tag, inner, _ = m.groups()
        new_open = re.sub(r'\s+place="[^"]*"', "", open_tag)
        new_open = re.sub(r'\s+n="[^"]*"', "", new_open)
        new_open = new_open.replace("<note", "<p", 1)
        content = content[:m.start()] + new_open + inner + "</p>" + content[m.end():]
        changed += 1
    if changed:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pp, BACKUP_DIR / f"{doc_id}_final.xml")
        pp.write_text(content, encoding="utf-8")
    return changed


def _mirror(doc_id):
    """Per-Seiten-Mirror + finales TEI fuer EIN Doc neu schreiben (Viewer ohne Server)."""
    final = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    ddir = PAGES_DIR / doc_id
    ddir.mkdir(parents=True, exist_ok=True)
    for pn, xml in _extract_pages_from_final(final).items():
        (ddir / f"{doc_id}_p{pn}.xml").write_text(xml, encoding="utf-8")
    shutil.copy2(final, ddir / f"{doc_id}_final.xml")


def main():
    ap = argparse.ArgumentParser(description="Referenz-verifizierte Fussnoten-Demotion (note place=foot -> p)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="nur zeigen, was demoted wuerde (Default)")
    g.add_argument("--apply", action="store_true", help="Demotion schreiben (mit Backup) + Mirror regenerieren")
    ap.add_argument("--doc", action="append", help="auf bestimmte Doc-IDs beschraenken (mehrfach moeglich)")
    ap.add_argument("--include-hold", action="store_true", help="auch die editorisch zurueckgehaltenen Docs (40, 1520)")
    args = ap.parse_args()

    if args.doc:
        docs = sorted(set(args.doc))
    else:
        docs = sorted({p.stem for p in REFERENCE_TEI_DIR.glob("*.xml")})

    total_cand = total_done = held = 0
    for doc_id in docs:
        cands = _candidates(doc_id)
        if not cands:
            continue
        if doc_id in HOLD and not args.include_hold and not args.doc:
            held += len(cands)
            print(f"[HOLD] {doc_id}: {len(cands)} referenz-verifiziert, aber ZBZ-Entscheid noetig (--include-hold).")
            for nid, ln, head in cands:
                print(f"         {nid:<10} len={ln:<5} {head!r}")
            continue
        total_cand += len(cands)
        print(f"{doc_id}: {len(cands)} referenz-verifizierte Fussnote(n)")
        for nid, ln, head in cands:
            print(f"   {nid:<10} len={ln:<5} {head!r}")
        if args.apply:
            ids = [c[0] for c in cands]
            n = _demote(doc_id, ids)
            if n:
                _mirror(doc_id)
            total_done += n
            print(f"   -> {n} demoted, Mirror aktualisiert" if n else "   -> bereits <p> (idempotent, nichts zu tun)")

    print()
    mode = "ANGEWANDT" if args.apply else "VORSCHAU"
    print(f"[{mode}] Kandidaten: {total_cand}"
          + (f", demoted: {total_done}" if args.apply else "")
          + (f", zurueckgehalten (HOLD): {held}" if held else ""))
    if not args.apply:
        print("       Schreiben mit --apply. HOLD-Docs (40,1520) nur mit --include-hold.")


if __name__ == "__main__":
    main()
