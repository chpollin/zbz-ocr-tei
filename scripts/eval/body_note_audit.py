"""
Body-als-Note-Audit: findet lange <note place="foot">-Bloecke im Lieferbestand
output/tei_final, die in Wahrheit Haupttext oder abgesetzte Blockzitate sind
(Ueberdetektion, Defekt E82). Die referenzverifizierte Demotion E85 hat nur
referenzgedeckte Dokumente repariert; dieses Audit priorisiert referenzlose.

NUR DIAGNOSE -- liest output/tei_final (und die Referenz-IDs aus
data/source/reference_tei), aendert NIE eine TEI-Datei, ist KEIN Pass/Fail-Gate.
Erzeugt einen JSON-Report (output/audits/body_note_audit.json) und eine
ASCII-Konsolen-Zusammenfassung. Keine LLM-/API-Aufrufe.

Gewichtete Signale je <note place="foot"> (deterministisch, jeweils in [0,1]):
  marker    (0.5)  kein Fussnoten-Marker (Ziffer, *, Kreuz) am Notenanfang -> 1.0;
                   Marker vorhanden und korrespondierend im Body derselben Seite -> 0.0
                   (echte Fussnote); Marker vorhanden ohne Body-Korrespondenz -> 0.35.
  length    (0.3)  Notenlaenge ueber der Schwelle, skaliert bis zur Saettigung.
  position  (0.2)  y_pct der Quellregion (aus der facsimile-Zone, auf die die Note
                   zeigt): unteres Drittel -> 0.0 (dort stehen Fussnoten), oberes
                   Drittel -> 1.0, Mitte/unbekannt -> 0.5.

Referenzabdeckung ist Ranking-Metadatum, kein Score-Bestandteil: Dokumente ohne
ZBZ-Referenz werden in Summary und Report zuerst gelistet.

Kandidat = Notenlaenge >= MIN_LEN UND Score >= CANDIDATE_THRESHOLD.

Aufruf:
    python -m scripts.eval.body_note_audit               # Summen (stdout) + JSON
    python -m scripts.eval.body_note_audit --dir PFAD    # alternatives TEI-Verzeichnis

Quelle der Wahrheit fuer Pfade: scripts/config.py (TEI_FINAL_DIR, REFERENCE_TEI_DIR).
"""
import re
from pathlib import Path

from scripts.config import REFERENCE_TEI_DIR, TEI_NS
from scripts.eval.audit_common import (
    doc_id_from_path,
    iter_final_tei,
    parse_tei,
    resolve_tei_dir,
    write_audit_report,
)

XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# --- calibration constants (tuned on the E82 facsimile-calibrated examples) ---
MIN_LEN = 400            # candidate length gate (chars of normalized note text)
LEN_SATURATION = 2000    # length signal reaches 1.0 here
TOP_THIRD = 100.0 / 3    # y_pct boundary top/middle
BOTTOM_THIRD = 200.0 / 3  # y_pct boundary middle/bottom
CANDIDATE_THRESHOLD = 0.4

W_MARKER = 0.5
W_LENGTH = 0.3
W_POSITION = 0.2

# leading footnote marker at the very start of a note (asterisks/daggers or a small number)
_LEADING_ASTERISK_RE = re.compile(r"^\s*[*†‡]+")
_LEADING_DIGIT_RE = re.compile(r"^\s*\d{1,3}[.)]?\s")
_SUPERSCRIPT_RE = re.compile(r"[¹²³⁰-⁹]")


def _ascii(s: str) -> str:
    """Fold to ASCII for the Windows console (JSON report keeps full Unicode)."""
    return s.encode("ascii", "replace").decode("ascii")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def leading_marker_class(note_text: str):
    """Classify a leading footnote marker at the note start.

    Returns (class, matched) where class in {"asterisk", "digit", None}.
    """
    t = note_text or ""
    m = _LEADING_ASTERISK_RE.match(t)
    if m:
        return "asterisk", m.group(0).strip()
    m = _LEADING_DIGIT_RE.match(t)
    if m:
        return "digit", m.group(0).strip()
    return None, ""


def body_has_corresponding_marker(marker_cls, body_text: str) -> bool:
    """Whether the page body carries a marker matching a note's leading marker.

    Conservative: only asterisk/dagger symbols or any superscript digit count. A plain
    inline digit is too ambiguous to treat as a footnote reference, so a digit-led note
    without a superscript in the body is left as an orphan (mild suspicion).
    """
    b = body_text or ""
    if marker_cls == "asterisk":
        return bool(re.search(r"[*†‡]", b))
    if marker_cls == "digit":
        return bool(_SUPERSCRIPT_RE.search(b))
    return False


def length_signal(length: int) -> float:
    span = LEN_SATURATION - MIN_LEN
    return max(0.0, min(1.0, (length - MIN_LEN) / span))


def position_signal(y_pct) -> float:
    if y_pct is None:
        return 0.5
    if y_pct < TOP_THIRD:
        return 1.0
    if y_pct > BOTTOM_THIRD:
        return 0.0
    return 0.5


def marker_signal(marker_cls, body_corresp: bool) -> float:
    if marker_cls is None:
        return 1.0
    return 0.0 if body_corresp else 0.35


def score_note(length: int, y_pct, marker_cls, body_corresp: bool):
    """Weighted body-as-note suspicion score in [0,1] plus its component signals."""
    s_marker = marker_signal(marker_cls, body_corresp)
    s_length = length_signal(length)
    s_position = position_signal(y_pct)
    score = W_MARKER * s_marker + W_LENGTH * s_length + W_POSITION * s_position
    signals = {
        "marker": round(s_marker, 3),
        "length": round(s_length, 3),
        "position": round(s_position, 3),
    }
    return round(score, 3), signals


def _facs_page(ref: str):
    """Scan page number from a facs reference like 'facs_147_r_3' or 'facs_147'."""
    m = re.match(r"facs_(\d+)", (ref or "").lstrip("#"))
    return int(m.group(1)) if m else None


def parse_facsimile(root) -> dict:
    """Map zone/surface xml:id -> {'y_pct': float|None, 'page': int}.

    y_pct is uly / surface height for zones; surfaces themselves carry no vertical
    anchor (y_pct None). These zone coordinates are the layout regions projected into
    the TEI facsimile, so the note's own facs id yields its source-region position.
    """
    out = {}
    for surf in root.iter(f"{{{TEI_NS}}}surface"):
        sid = surf.get(XML_ID) or ""
        page = _facs_page(sid)
        lry = float(surf.get("lry") or 0) or None
        out[sid] = {"y_pct": None, "page": page}
        for z in surf.findall(f"{{{TEI_NS}}}zone"):
            zid = z.get(XML_ID)
            uly = float(z.get("uly") or 0)
            # some source surfaces store zone coords in a different scale than lry;
            # a value outside [0, lry] is inconsistent -> position unknown, not garbage
            y_pct = round(uly / lry * 100, 1) if lry and 0 <= uly <= lry else None
            out[zid] = {"y_pct": y_pct, "page": page}
    return out


def collect_body(root):
    """Walk <body> in document order, grouping content by scan page.

    Returns (page_body_text: {page: str}, foot_notes: [dict]). Foot notes carry their
    page (from the note's facs, else the current <pb> page), normalized text and length.
    Note subtrees are excluded from page body text so a note's own marker never counts
    as its own body correspondence.
    """
    body = root.find(f".//{{{TEI_NS}}}body")
    page_body = {}
    notes = []
    pb_tag = f"{{{TEI_NS}}}pb"
    note_tag = f"{{{TEI_NS}}}note"
    state = {"page": 0}

    def add_body(page, text):
        if text:
            page_body.setdefault(page, []).append(text)

    def walk(el, in_note):
        for ch in el:
            if ch.tag == pb_tag:
                p = _facs_page(ch.get("facs") or "")
                if p is not None:
                    state["page"] = p
                # a pb tail belongs to the (new) current page
                if not in_note:
                    add_body(state["page"], ch.tail)
                continue
            is_note = ch.tag == note_tag and ch.get("place") == "foot"
            if is_note:
                text = _norm("".join(ch.itertext()))
                page = _facs_page(ch.get("facs") or "")
                notes.append(
                    {
                        "facs": (ch.get("facs") or "").lstrip("#"),
                        "page_hint": page if page is not None else state["page"],
                        "text": text,
                        "length": len(text),
                    }
                )
                # descend not needed for body text; a note's tail is body of current page
                if not in_note:
                    add_body(state["page"], ch.tail)
                continue
            if not in_note:
                add_body(state["page"], ch.text)
            walk(ch, in_note)
            if not in_note:
                add_body(state["page"], ch.tail)

    if body is not None:
        add_body(state["page"], body.text)
        walk(body, False)
    return {p: " ".join(t) for p, t in page_body.items()}, notes


def analyze_document(root, doc_id: str) -> dict:
    """Score every foot note of a parsed TEI document; return candidates and stats."""
    facs = parse_facsimile(root)
    page_body, notes = collect_body(root)
    candidates = []
    for n in notes:
        length = n["length"]
        info = facs.get(n["facs"], {})
        page = info.get("page") or n["page_hint"]
        y_pct = info.get("y_pct")
        marker_cls, marker_txt = leading_marker_class(n["text"])
        body_corresp = body_has_corresponding_marker(marker_cls, page_body.get(page, ""))
        score, signals = score_note(length, y_pct, marker_cls, body_corresp)
        if length >= MIN_LEN and score >= CANDIDATE_THRESHOLD:
            candidates.append(
                {
                    "doc": doc_id,
                    "page": page,
                    "length": length,
                    "y_pct": y_pct,
                    "leading_marker": marker_txt or None,
                    "body_marker_corresp": body_corresp,
                    "signals": signals,
                    "score": score,
                    "snippet": n["text"][:120],
                }
            )
    candidates.sort(key=lambda c: -c["score"])
    return {"note_count": len(notes), "candidates": candidates}


def audit_document(tei_path, reference_ids=frozenset()):
    """Diagnose one document. Returns (findings, error_text)."""
    doc_id = doc_id_from_path(tei_path)
    root, err = parse_tei(tei_path)
    if err:
        return None, err
    res = analyze_document(root, doc_id)
    res["doc"] = doc_id
    res["has_reference"] = doc_id in reference_ids
    return res, None


def _reference_ids(reference_dir) -> set:
    d = Path(reference_dir)
    if not d.is_dir():
        return set()
    return {f.stem for f in d.glob("*.xml")}


def audit_corpus(tei_dir, reference_ids=None) -> dict:
    if reference_ids is None:
        reference_ids = _reference_ids(REFERENCE_TEI_DIR)
    documents = []
    errors = []
    total = 0
    for doc_id, f in iter_final_tei(tei_dir):
        total += 1
        res, err = audit_document(f, reference_ids=reference_ids)
        if err:
            errors.append((doc_id, err))
            continue
        if res["candidates"]:
            documents.append(res)
    documents.sort(key=lambda d: (d["has_reference"], -max(c["score"] for c in d["candidates"])))
    total_cand = sum(len(d["candidates"]) for d in documents)
    total_cand_nr = sum(len(d["candidates"]) for d in documents if not d["has_reference"])
    return {
        "total_files": total,
        "documents": documents,
        "errors": errors,
        "corpus_totals": {
            "candidate_notes": total_cand,
            "candidate_notes_no_reference": total_cand_nr,
            "candidate_docs": len(documents),
            "candidate_docs_no_reference": sum(1 for d in documents if not d["has_reference"]),
        },
    }


def _print_summary(summary):
    tot = summary["corpus_totals"]
    print(f"Body-als-Note-Audit ueber {summary['total_files']} Dokumente (Diagnose E82)\n")
    print(f"  Kandidaten-Noten gesamt:            {tot['candidate_notes']}")
    print(f"  davon in referenzlosen Dokumenten:  {tot['candidate_notes_no_reference']}")
    print(f"  betroffene Dokumente:               {tot['candidate_docs']}"
          f"  (referenzlos: {tot['candidate_docs_no_reference']})")
    if summary["errors"]:
        print(f"  Parse-Fehler: {len(summary['errors'])}")
    top = summary["documents"][:15]
    if top:
        print("\n  Top-Kandidaten (referenzlose zuerst; doc, ref, seite, laenge, y_pct, score):")
        for d in top:
            ref = "ref " if d["has_reference"] else "    "
            for c in d["candidates"][:3]:
                y = "??" if c["y_pct"] is None else f"{c['y_pct']:.0f}"
                print(f"    {ref}{d['doc']:>5}  S{str(c['page']):<4} len={c['length']:>4}"
                      f"  y={y:>3}%  score={c['score']:.2f}  {_ascii(c['snippet'][:48])}")


def _write_report(summary, tei_dir):
    payload = {
        "audit": "body_note",
        "tei_dir": str(tei_dir),
        "total_files": summary["total_files"],
        "thresholds": {
            "min_len": MIN_LEN,
            "len_saturation": LEN_SATURATION,
            "candidate_threshold": CANDIDATE_THRESHOLD,
            "weights": {"marker": W_MARKER, "length": W_LENGTH, "position": W_POSITION},
        },
        "corpus_totals": summary["corpus_totals"],
        "documents": summary["documents"],
        "errors": summary["errors"],
    }
    write_audit_report("body_note_audit", payload)


def main():
    tei_dir = resolve_tei_dir("Body-als-Note-Audit (Diagnose, schreibt nichts an den TEI-Daten)")
    summary = audit_corpus(tei_dir)
    _print_summary(summary)
    _write_report(summary, tei_dir)


if __name__ == "__main__":
    main()
