"""
Relations-Integritaet: prueft die internen Verweise im Lieferbestand output/tei_final.

NUR DIAGNOSE -- liest output/tei_final, aendert nichts, ist KEIN Gate. Erzeugt einen
JSON-Report (output/audits/) und eine ASCII-Konsolen-Zusammenfassung.

Vier Klassen je Dokument:
  note_links     jedes <note @next> zeigt auf eine existierende xml:id, deren @prev
                 zurueckzeigt (und umgekehrt fuer @prev).
  anchor_pairs   anchor xml:id "*-start" hat ein passendes "*-end" (und umgekehrt).
  head_titles    hoechstens ein <title type="main"> je <head>.
  speech_context <sp>/<speaker> nur innerhalb <div type="interview"|"conversation">.

Aufruf:
    python -m scripts.eval.relation_integrity_audit             # Summen (stdout) + JSON
    python -m scripts.eval.relation_integrity_audit --dir PFAD  # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR).
"""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR, TEI_NS

AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audits"
_XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_SPEECH_DIV_TYPES = {"interview", "conversation"}


def _tag(name):
    return f"{{{TEI_NS}}}{name}"


def _ref(value):
    """Strip a leading '#' from an id reference."""
    return value[1:] if value and value.startswith("#") else value


def _check_note_links(root, id_map):
    out = []
    for note in root.iter(_tag("note")):
        nid = note.get(_XML_ID)
        nxt = note.get("next")
        if nxt:
            target = _ref(nxt)
            if target not in id_map:
                out.append({"type": "next_target_missing", "id": nid, "next": nxt})
            elif _ref(id_map[target].get("prev")) != nid:
                out.append({"type": "next_not_reciprocated", "id": nid, "next": nxt})
        prv = note.get("prev")
        if prv:
            target = _ref(prv)
            if target not in id_map:
                out.append({"type": "prev_target_missing", "id": nid, "prev": prv})
            elif _ref(id_map[target].get("next")) != nid:
                out.append({"type": "prev_not_reciprocated", "id": nid, "prev": prv})
    return out


def _check_anchor_pairs(root):
    out = []
    starts, ends = set(), set()
    for anchor in root.iter(_tag("anchor")):
        aid = anchor.get(_XML_ID)
        if not aid:
            continue
        if aid.endswith("-start"):
            starts.add(aid[:-len("-start")])
        elif aid.endswith("-end"):
            ends.add(aid[:-len("-end")])
    for base in sorted(starts - ends):
        out.append({"base": base, "have": base + "-start", "missing": base + "-end"})
    for base in sorted(ends - starts):
        out.append({"base": base, "have": base + "-end", "missing": base + "-start"})
    return out


def _check_head_titles(root):
    out = []
    for head in root.iter(_tag("head")):
        mains = [t for t in head.iter(_tag("title")) if t.get("type") == "main"]
        if len(mains) > 1:
            out.append({"count": len(mains)})
    return out


def _check_speech_context(root):
    parent = {c: p for p in root.iter() for c in p}
    out = []
    div_tag = _tag("div")
    for tag in ("sp", "speaker"):
        for el in root.iter(_tag(tag)):
            div_type = None
            node = parent.get(el)
            while node is not None:
                if node.tag == div_tag:
                    div_type = node.get("type")
                    break
                node = parent.get(node)
            if div_type not in _SPEECH_DIV_TYPES:
                out.append({"element": tag, "div_type": div_type})
    return out


def audit_root(root) -> dict:
    """Run all four relation checks on a parsed TEI root."""
    id_map = {el.get(_XML_ID): el for el in root.iter() if el.get(_XML_ID)}
    return {
        "note_links": _check_note_links(root, id_map),
        "anchor_pairs": _check_anchor_pairs(root),
        "head_titles": _check_head_titles(root),
        "speech_context": _check_speech_context(root),
    }


def audit_document(tei_path):
    try:
        root = ET.parse(str(tei_path)).getroot()
    except (ET.ParseError, OSError) as exc:
        return None, str(exc)
    return audit_root(root), None


_CATEGORIES = ("note_links", "anchor_pairs", "head_titles", "speech_context")


def audit_corpus(tei_dir) -> dict:
    files = sorted(Path(tei_dir).glob("*_final.xml"))
    docs = {}
    errors = []
    for f in files:
        doc_id = f.stem.replace("_final", "")
        findings, err = audit_document(f)
        if err:
            errors.append((doc_id, err))
            continue
        if any(findings[c] for c in _CATEGORIES):
            docs[doc_id] = findings
    return {"total_files": len(files), "docs": docs, "errors": errors}


def _print_summary(summary):
    docs = summary["docs"]
    print(f"Relations-Integritaet ueber {summary['total_files']} Dokumente\n")
    print(f"  Dokumente mit mindestens einem Befund: {len(docs)}")
    labels = {
        "note_links": "note @next/@prev inkonsistent",
        "anchor_pairs": "anchor start/end unpaarig",
        "head_titles": "mehr als ein title[main] je head",
        "speech_context": "sp/speaker ausserhalb interview/conversation",
    }
    for cat in _CATEGORIES:
        doc_hits = sum(1 for f in docs.values() if f[cat])
        occ = sum(len(f[cat]) for f in docs.values())
        print(f"    {labels[cat]:44} {doc_hits:4} / {occ}")
    if summary["errors"]:
        print(f"  Parse-Fehler: {len(summary['errors'])}")
    for cat in _CATEGORIES:
        top = sorted(((d, len(f[cat])) for d, f in docs.items() if f[cat]), key=lambda kv: -kv[1])[:8]
        if top:
            print(f"\n  Top {cat} (doc: Vorkommen):")
            for d, c in top:
                print(f"    {d}: {c}")


def _write_report(summary, tei_dir):
    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_OUTPUT_DIR / "relation_integrity_audit.json"
    docs = summary["docs"]
    payload = {
        "audit": "relation_integrity",
        "tei_dir": str(tei_dir),
        "total_files": summary["total_files"],
        "corpus_totals": {
            cat: {
                "documents": sum(1 for f in docs.values() if f[cat]),
                "occurrences": sum(len(f[cat]) for f in docs.values()),
            }
            for cat in _CATEGORIES
        },
        "documents": docs,
        "errors": summary["errors"],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON-Report: {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Relations-Integritaet (Diagnose, schreibt nichts an den TEI-Daten)"
    )
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (Default tei_final)")
    args = parser.parse_args()
    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    _write_report(summary, tei_dir)


if __name__ == "__main__":
    main()
