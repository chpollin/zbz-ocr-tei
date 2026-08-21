"""Entfernt den redundanten Fussnoten-Marker aus dem Notentext (idempotent, mit Backup).

Manche `<note place="foot">` in `tei_final` oeffnen ihren Body mit dem hochgestellten
Druck-Markenzeichen als Literal, z.B. `<note place="foot" n="1"><lb/><hi rendition="#sup">1</hi> K. Jaspers ...`.
Die Editionsrichtlinie (Z.354) modelliert die Fussnotenmarke jedoch AUSSCHLIESSLICH ueber das
Attribut @n und gibt sie NICHT als Zeichen im Notentext wieder. In allen 25 ZBZ-Referenz-TEIs
oeffnet keine einzige Fussnote mit einem fuehrenden `<hi rendition="#sup">`-Marker -- der Marker
im Body ist also ein nachweisbarer Generator-Defekt (Welle-2-Rest, Fix `note-footnote-n`).

Diskriminator -- Evidenz, kein Raten: nur ein `<hi rendition="#sup">M</hi>` als ERSTES signifikantes
Kind einer `<note place="foot">` (hoechstens hinter genau einem fuehrenden `<lb/>`), mit kurzer
Marke M (<= 3 Zeichen), wird entfernt. @n wird defensiv nur gesetzt, wenn es fehlt -- ein
vorhandener kuratierter Wert wird nie ueberschrieben. Mitten-im-Text-Hochstellungen (Exponenten,
Ordinalia `9e`) und Nicht-Fussnoten werden nie beruehrt.

Idempotent: nach dem Lauf oeffnet keine Note mehr mit einem fuehrenden #sup-Marker; ein zweiter
Lauf findet nichts. Da direkt in `output/tei_final/` geschrieben wird (Pipeline-Output, nicht
versioniert), ueberschreibt ein Re-Run (`tei_unified --reassemble`) die Korrektur -- ein erneuter
`--apply`-Lauf stellt sie deterministisch wieder her. Verifiziert: 4 Docs (110, 130, 1140, 1500),
16 Notes. Aendert die CER NICHT (Fussnoten sind vom Vergleich ausgeschlossen, E5); rein konformitaet.

Befund + Methodik: knowledge/decisions.md (E85).

  python -m scripts.tei.tei_footnote_marker_strip --dry-run            # Kandidaten zeigen (Default)
  python -m scripts.tei.tei_footnote_marker_strip --dry-run --doc 110  # ein Doc
  python -m scripts.tei.tei_footnote_marker_strip --apply              # entfernen (mit Backup) + Mirror
"""
import argparse
import re
import shutil
import xml.etree.ElementTree as ET

from scripts.config import TEI_FINAL_DIR
from scripts.edition.generate_edition_data import PAGES_DIR, _extract_pages_from_final

MAX_MARK = 3             # nur kurze Druckmarken (Ziffer/Symbol), keine ganzen Saetze
BACKUP_DIR = TEI_FINAL_DIR.parent / "_backup_pre_marker_strip"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
TEI = "{http://www.tei-c.org/ns/1.0}"

# Surgischer Treffer: note-Open-Tag mit place="foot", optional genau ein fuehrendes <lb/>
# (+ Whitespace), dann der fuehrende <hi rendition="#sup">M</hi>-Marker. Alles dahinter
# (cand.tail = der eigentliche Notentext) bleibt unberuehrt.
_MARKER_RE = re.compile(
    r'(<note\b[^>]*\bplace="foot"[^>]*>)'   # 1: note-Open-Tag
    r'(\s*(?:<lb\b[^>]*/>\s*)?)'            # 2: optional fuehrendes <lb/> + Whitespace
    r'<hi\b[^>]*\brendition="#sup"[^>]*>'   # der fuehrende #sup-Marker
    rf'([^<]{{1,{MAX_MARK}}})'               # 3: die Marke (kurz)
    r'</hi>',
    re.DOTALL,
)


def strip_sup_markers(xml_text):
    """Entfernt fuehrende #sup-Marker aus allen <note place=foot>. Gibt (neuer_text, anzahl) zurueck.

    Reine String-Funktion (test- und idempotenz-freundlich, kein Disk-Zugriff). @n wird defensiv
    nur gesetzt, wenn der Open-Tag keines traegt und die Marke alphanumerisch ist.
    """
    def repl(m):
        open_tag, lead, mark = m.group(1), m.group(2), m.group(3)
        if mark.isalnum() and not re.search(r'\bn="', open_tag):
            open_tag = re.sub(r"^<note", f'<note n="{mark}"', open_tag)
        return open_tag + lead
    return _MARKER_RE.subn(repl, xml_text)


def _candidates(doc_id):
    """(xml_id, marke)-Liste der Notes mit fuehrendem #sup-Marker. ET-Detektion (Diagnose)."""
    pp = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    if not pp.exists():
        return []
    try:
        root = ET.fromstring(pp.read_text(encoding="utf-8"))
    except ET.ParseError:
        return []
    out = []
    for note in root.iter(f"{TEI}note"):
        if note.get("place") != "foot":
            continue
        kids = list(note)
        if not kids:
            continue
        idx = 0
        if kids[0].tag == f"{TEI}lb" and (note.text is None or not note.text.strip()):
            idx = 1
        if idx >= len(kids):
            continue
        cand = kids[idx]
        if cand.tag == f"{TEI}hi" and cand.get("rendition") == "#sup":
            mark = (cand.text or "").strip()
            if mark and len(mark) <= MAX_MARK:
                out.append((note.get(XML_ID) or "?", mark))
    return out


def _strip(doc_id):
    """Entfernt die Marker in EINEM Doc (Backup vorher). Gibt die Zahl geaenderter Stellen zurueck."""
    pp = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    content = pp.read_text(encoding="utf-8")
    new_content, n = strip_sup_markers(content)
    if n:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pp, BACKUP_DIR / f"{doc_id}_final.xml")
        pp.write_text(new_content, encoding="utf-8")
    return n


def _mirror(doc_id):
    """Per-Seiten-Mirror + finales TEI fuer EIN Doc neu schreiben (Viewer ohne Server)."""
    final = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    ddir = PAGES_DIR / doc_id
    ddir.mkdir(parents=True, exist_ok=True)
    for pn, xml in _extract_pages_from_final(final).items():
        (ddir / f"{doc_id}_p{pn}.xml").write_text(xml, encoding="utf-8")
    shutil.copy2(final, ddir / f"{doc_id}_final.xml")


def main():
    ap = argparse.ArgumentParser(description="Fuehrenden #sup-Fussnoten-Marker aus dem Notentext entfernen")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="nur zeigen, was entfernt wuerde (Default)")
    g.add_argument("--apply", action="store_true", help="Marker entfernen (mit Backup) + Mirror regenerieren")
    ap.add_argument("--doc", action="append", help="auf bestimmte Doc-IDs beschraenken (mehrfach moeglich)")
    args = ap.parse_args()

    if args.doc:
        docs = sorted(set(args.doc))
    else:
        docs = sorted({p.stem.replace("_final", "") for p in TEI_FINAL_DIR.glob("*_final.xml")})

    total_cand = total_done = 0
    for doc_id in docs:
        cands = _candidates(doc_id)
        if not cands:
            continue
        total_cand += len(cands)
        print(f"{doc_id}: {len(cands)} Fussnote(n) mit fuehrendem #sup-Marker")
        for nid, mark in cands:
            print(f"   {nid:<10} marke={mark!r}")
        if args.apply:
            n = _strip(doc_id)
            if n:
                _mirror(doc_id)
            total_done += n
            print(f"   -> {n} Marker entfernt, Mirror aktualisiert" if n else "   -> bereits sauber (idempotent)")

    print()
    mode = "ANGEWANDT" if args.apply else "VORSCHAU"
    print(f"[{mode}] Kandidaten: {total_cand}" + (f", entfernt: {total_done}" if args.apply else ""))
    if not args.apply:
        print("       Schreiben mit --apply.")


if __name__ == "__main__":
    main()
