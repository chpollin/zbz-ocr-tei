"""Bestandskorrektur der gedruckten Seitenfolio im <pb n="...">-Attribut (Operator-
Entscheidung 2026-07-07).

Die ausgelieferten TEI tragen im pb@n ueberwiegend die laufende Scan-Nummer (1..N).
Dieses Werkzeug hebt sie, wo eine gedruckte Druckfolio sicher ableitbar ist, auf die
Druckseitenzahl in eckigen Klammern (ZBZ-Referenzkonvention, z. B. n="[249]",
Punktnotation n="[7.14]"). Seiten ohne sicher ableitbare Folio behalten die
Scan-Nummer ungeklammert.

Signalquellen je Seite, deterministisch, in dieser Prioritaet:
  1. Footer   gedruckte Zahl aus den Layout-_filter/_skip-Regionen der Seite
              (detect_page_number aus scripts/tei/tei_step1, wiederverwendet, kein Duplikat).
  2. Interpolation  Luecke aus konsistenten Nachbar-Ankern forward-verankert
              (interpolate_document_pb aus scripts/tei/tei_step1).
  3. Offset   bei dokumentweit stabilem Footer-Offset (z. B. Doc 110, Offset 2) wird die
              Folio als Scan-Position minus Offset abgeleitet, aber nur bei hoher Konsistenz
              (OFFSET_CONSISTENCY_MIN) und genug Beleg-Seiten (OFFSET_MIN_FOOTER_PAGES).
Bereits druckpaginierte Dokumente (Audit-Klasse printed_folio) werden nur geklammert,
nicht verrechnet. Blank-Seiten (<pb type="blank"/>) erhalten hoechstens einen
interpolierten Wert, nie Footer/Offset; sonst bleiben sie unveraendert.

Zusatz --strip-folio-echo: Absaetze, die AUSSCHLIESSLICH aus der fuer diese Seite
ermittelten Druckzahl bestehen (z. B. <p>248</p>, <p> 7 </p>), werden als Footer-Echo
entfernt -- nur bei exakter Uebereinstimmung mit der ermittelten Folio.

Der reale Lauf schreibt mit Backup nach output/_backup_pre_pb_folio/ und ist idempotent
(erneutes Klammern erzeugt kein [[...]], zweiter Lauf ist byte-identisch). Der --dry-run
liest tei_final nur und schreibt ausschliesslich den Report output/audits/pb_folio_preview.json.

Aufruf:
    python -m scripts.tei.tei_pb_folio --dry-run                 # Report, nichts schreiben
    python -m scripts.tei.tei_pb_folio --dry-run --strip-folio-echo
    python -m scripts.tei.tei_pb_folio                           # schreiben (mit Backup)
    python -m scripts.tei.tei_pb_folio --doc 570 --dry-run       # einzelnes Dokument
"""

import argparse
import json
import re
import sys
from collections import Counter

from scripts.config import LAYOUT_DIR, OUTPUT_DIR, TEI_FINAL_DIR
from scripts.core.loaders import load_layout_gemini
from scripts.eval.pb_number_audit import classify_document, read_layout_page_numbers
from scripts.tei.marker_common import backup_and_write, iter_final_files
from scripts.tei.pb_split import BODY_INNER_RE, iter_page_spans
from scripts.tei.tei_step1 import detect_page_number, interpolate_document_pb

BACKUP_DIR = OUTPUT_DIR / "_backup_pre_pb_folio"
AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audits"
PREVIEW_PATH = AUDIT_OUTPUT_DIR / "pb_folio_preview.json"

VALIDATION_DOCS = ("570", "110", "2330", "30")

# Offset-Rekonstruktion (Prioritaet 3) extrapoliert die Folio auf Seiten OHNE eigenen
# Footer-Beleg. Das ist nur zulaessig, wenn ein einziger Offset praktisch die gesamte
# Footer-Evidenz des Dokuments erklaert -- sonst verrechnet ein gemischtes Front-/Back-
# matter-Offset-Bild die Paginierung. Darum eine hohe Konsistenzschwelle und eine
# Mindest-Belegmenge (an _MIN_NUMERIC=3 des pb_number_audit angelehnt: unter drei
# Beleg-Seiten traegt ein Offset zu wenig Signal fuer eine dokumentweite Extrapolation).
OFFSET_CONSISTENCY_MIN = 0.9
OFFSET_MIN_FOOTER_PAGES = 3

# reine Ziffernfolge oder Punkt-Notation (7.14) -- eine gueltige Folio-Ziffer
_FOLIO_RE = re.compile(r"^\d+(?:\.\d+)*$")
# pb@n-Attribut (whitespace-verankert, damit kein "n" innerhalb anderer Attribute trifft)
_N_ATTR_RE = re.compile(r'\sn="[^"]*"')
_N_VALUE_RE = re.compile(r'\sn="([^"]*)"')
# ein <p>...</p> (Echo-Kandidat); group(1) = Inhalt
_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.DOTALL)

SOURCES = ("footer", "interpolation", "offset", "existing_folio", "fallback")


def folio_content(n):
    """Klammerlose Folio-Ziffer eines n-Werts, sonst None.

    Toleriert eckige Klammern und Whitespace; akzeptiert reine Ziffern und Punkt-
    Notation (7.14). Nicht-numerische n-Werte (roemische Ziffern, leer) ergeben None.
    """
    if not n:
        return None
    s = n.strip().strip("[]").strip()
    return s if _FOLIO_RE.match(s) else None


def bracket(folio):
    """Setzt eine Folio-Ziffer in eckige Klammern (ZBZ-Referenzkonvention)."""
    return f"[{folio}]"


def is_blank_pb(pb_tag):
    """True, wenn das <pb> als Leerseite markiert ist (type='blank')."""
    return 'type="blank"' in pb_tag


def n_value(pb_tag):
    """Aktueller n-Wert eines <pb>-Tags, sonst leerer String."""
    m = _N_VALUE_RE.search(pb_tag)
    return m.group(1) if m else ""


def set_pb_n(pb_tag, new_n):
    """Ersetzt (oder ergaenzt) das n-Attribut eines <pb>-Tags. type='blank' bleibt erhalten."""
    if _N_ATTR_RE.search(pb_tag):
        return _N_ATTR_RE.sub(f' n="{new_n}"', pb_tag, count=1)
    if pb_tag.endswith("/>"):
        return pb_tag[:-2].rstrip() + f' n="{new_n}" />'
    if pb_tag.endswith(">"):
        return pb_tag[:-1].rstrip() + f' n="{new_n}">'
    return pb_tag


def compute_offset(layout_page_numbers):
    """Dominanter Footer-Offset eines Dokuments und seine Konsistenz.

    Betrachtet nur Seiten mit genau einer numerischen Footer-Zahl; Offset = Scan-Position
    minus Footer-Zahl. Returns (offset_mode, consistency, single_footer_pages);
    consistency = Anteil der Beleg-Seiten, die den Modus tragen. Ohne Beleg (None, 0.0, 0).
    """
    singles = {
        p: int(v[0])
        for p, v in (layout_page_numbers or {}).items()
        if len(v) == 1 and str(v[0]).isdigit()
    }
    if not singles:
        return None, 0.0, 0
    offsets = Counter(p - f for p, f in singles.items())
    mode, count = offsets.most_common(1)[0]
    total = sum(offsets.values())
    return mode, count / total, total


def offset_is_stable(consistency, single_pages):
    """True, wenn der Offset dokumentweit als Rekonstruktionsbasis taugt."""
    return single_pages >= OFFSET_MIN_FOOTER_PAGES and consistency >= OFFSET_CONSISTENCY_MIN


def resolve_page_folio(page, blank, footer, interp, offset, offset_ok, current_n, printed_folio_doc):
    """Bestimmt pb@n einer Seite plus Quelle und die klammerlose Folio-Ziffer.

    Returns (new_n, source, folio_numeric). Bei source='fallback' bleibt new_n == current_n
    (Scan-Nummer, ungeklammert) und folio_numeric ist None (kein Echo-Abgleich).
    """
    if printed_folio_doc:
        inner = folio_content(current_n)
        if inner is not None:
            return bracket(inner), "existing_folio", inner
        return current_n, "fallback", None

    if blank:
        if page in interp:
            f = str(interp[page])
            return bracket(f), "interpolation", f
        return current_n, "fallback", None

    if footer:
        return bracket(footer), "footer", footer
    if page in interp:
        f = str(interp[page])
        return bracket(f), "interpolation", f
    if offset_ok and offset is not None and (page - offset) >= 1:
        f = str(page - offset)
        return bracket(f), "offset", f
    return current_n, "fallback", None


def strip_echo_paragraphs(chunk, folio_numeric):
    """Entfernt <p>-Absaetze, deren sichtbarer Text EXAKT der Folio-Ziffer entspricht.

    Nur exakte Uebereinstimmung (whitespace-tolerant); '<p>248 und mehr</p>' oder
    '<p>1248</p>' bleiben unangetastet. Returns (neuer_chunk, entfernte_anzahl).
    """
    if not folio_numeric:
        return chunk, 0
    removed = 0

    def repl(m):
        nonlocal removed
        visible = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if visible == folio_numeric:
            removed += 1
            return ""
        return m.group(0)

    return _P_RE.sub(repl, chunk), removed


def rewrite_body(body_inner, detected_str, interp, offset, offset_ok, printed_folio_doc, strip_echo):
    """Reine String-Transformation des <body>-Inhalts (Kern des Schreibpfads, ohne IO).

    detected_str: Seite -> Footer-Zahl (str). interp: Seite -> interpolierte Ganzzahl.
    Returns (neuer_body_inner, report) mit source_counts, coverage, echo und changes.
    """
    spans = iter_page_spans(body_inner)
    report = {
        "source_counts": {s: 0 for s in SOURCES},
        "content_pages": 0,
        "content_folio": 0,
        "blank_pages": 0,
        "echo": 0,
        "changes": [],
    }
    if not spans:
        return body_inner, report

    out = body_inner[: spans[0].pb_start]
    for span in spans:
        blank = is_blank_pb(span.pb_tag)
        current = n_value(span.pb_tag)
        footer = detected_str.get(span.page)
        new_n, source, folio_num = resolve_page_folio(
            span.page, blank, footer, interp, offset, offset_ok, current, printed_folio_doc
        )
        report["source_counts"][source] += 1
        if blank:
            report["blank_pages"] += 1
        else:
            report["content_pages"] += 1
            if source != "fallback":
                report["content_folio"] += 1

        new_pb = set_pb_n(span.pb_tag, new_n)
        chunk = body_inner[span.content_start:span.content_end]
        if strip_echo and folio_num:
            chunk, removed = strip_echo_paragraphs(chunk, folio_num)
            report["echo"] += removed
        if new_n != current:
            report["changes"].append([span.page, current, new_n, source])
        out += new_pb + chunk

    report["coverage"] = _coverage(report["content_pages"], report["content_folio"])
    return out, report


def _coverage(content_pages, content_folio):
    if content_pages == 0:
        return "none" if content_folio == 0 else "full"
    if content_folio == 0:
        return "none"
    if content_folio == content_pages:
        return "full"
    return "partial"


def _gather_signals(doc_id, pages):
    """Footer-Zahlen je Seite, Interpolation, Offset und Audit-Klasse eines Dokuments."""
    detected_str = {}
    detected_int = {}
    for p in pages:
        layout = load_layout_gemini(doc_id, p)
        if layout and layout.get("regions"):
            printed = detect_page_number(layout["regions"])
            if printed:
                detected_str[p] = printed
                if printed.isdigit():
                    detected_int[p] = int(printed)
    interp = interpolate_document_pb(detected_int, pages)
    layout_page_numbers = read_layout_page_numbers(LAYOUT_DIR / doc_id)
    off_mode, off_cons, off_pages = compute_offset(layout_page_numbers)
    offset_ok = off_mode is not None and offset_is_stable(off_cons, off_pages)
    return detected_str, interp, off_mode, offset_ok, layout_page_numbers


def process_doc(doc_id, dry_run, strip_echo):
    """Verarbeitet ein Dokument. Liest tei_final + Layout, schreibt nur im realen Lauf."""
    final_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    report = {"doc_id": doc_id, "ok": False, "error": None, "changed": False}
    if not final_path.exists():
        report["error"] = "final.xml fehlt"
        return report

    raw = final_path.read_text(encoding="utf-8")
    body_match = BODY_INNER_RE.search(raw)
    if not body_match:
        report["error"] = "kein <body>"
        return report

    body_inner = body_match.group(1)
    spans = iter_page_spans(body_inner)
    if not spans:
        report["error"] = "kein <pb>"
        return report

    pages = [s.page for s in spans]
    current_ns = [n_value(s.pb_tag) for s in spans]
    detected_str, interp, off_mode, offset_ok, layout_page_numbers = _gather_signals(doc_id, pages)
    klass = classify_document(current_ns, layout_page_numbers)["class"]
    printed_folio_doc = klass == "printed_folio"

    new_body, body_report = rewrite_body(
        body_inner, detected_str, interp, off_mode, offset_ok, printed_folio_doc, strip_echo
    )
    new_raw = raw[: body_match.start(1)] + new_body + raw[body_match.end(1):]

    report.update(body_report)
    report["ok"] = True
    report["class"] = klass
    report["offset"] = off_mode if offset_ok else None
    report["changed"] = new_raw != raw

    if not dry_run and report["changed"]:
        backup_and_write(final_path, BACKUP_DIR, new_raw)

    return report


def _print_validation(reports):
    print("\nValidierung (angeforderte Dokumente):")
    for doc in VALIDATION_DOCS:
        r = reports.get(doc)
        if not r or not r.get("ok"):
            print(f"  {doc}: (nicht verarbeitet)")
            continue
        head = f"  {doc}: class={r['class']} offset={r['offset']} echo={r['echo']}"
        print(head)
        for page, frm, to, src in r["changes"][:6]:
            print(f"      S{page}: {frm} -> {to}  ({src})")
        if not r["changes"]:
            print("      (keine Aenderung)")


def _print_summary(reports):
    ok = [r for r in reports.values() if r.get("ok")]
    src_total = Counter()
    for r in ok:
        for s in SOURCES:
            src_total[s] += r["source_counts"][s]
    cov = Counter(r["coverage"] for r in ok)
    echo_total = sum(r["echo"] for r in ok)
    blank_total = sum(r["blank_pages"] for r in ok)
    errors = [(r["doc_id"], r["error"]) for r in reports.values() if r.get("error")]

    print("-" * 60)
    print(f"Dokumente verarbeitet:     {len(ok)}")
    print("Seiten je Folio-Quelle:")
    for s in SOURCES:
        print(f"    {s:16s}: {src_total[s]}")
    print(f"    {'blank':16s}: {blank_total}")
    print("Abdeckung (Content-Seiten je Dokument):")
    for c in ("full", "partial", "none"):
        print(f"    {c:16s}: {cov.get(c, 0)}")
    print(f"Footer-Echo-Absaetze:      {echo_total}")
    if errors:
        print(f"FEHLER in {len(errors)} Docs: {[e[0] for e in errors]}")


def _write_report(reports, strip_echo):
    AUDIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = [r for r in reports.values() if r.get("ok")]
    src_total = Counter()
    for r in ok:
        for s in SOURCES:
            src_total[s] += r["source_counts"][s]
    payload = {
        "tool": "pb_folio",
        "strip_folio_echo": strip_echo,
        "offset_consistency_min": OFFSET_CONSISTENCY_MIN,
        "offset_min_footer_pages": OFFSET_MIN_FOOTER_PAGES,
        "corpus_totals": {
            "documents": len(ok),
            "pages_per_source": dict(src_total),
            "blank_pages": sum(r["blank_pages"] for r in ok),
            "echo_paragraphs": sum(r["echo"] for r in ok),
            "coverage": dict(Counter(r["coverage"] for r in ok)),
        },
        "documents": reports,
    }
    PREVIEW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON-Report: {PREVIEW_PATH}")


def main():
    ap = argparse.ArgumentParser(description="pb@n auf gedruckte Druckfolio heben (Bestandskorrektur)")
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Report")
    ap.add_argument("--strip-folio-echo", action="store_true",
                    help="Absaetze, die exakt die ermittelte Folio wiederholen, als Echo entfernen")
    args = ap.parse_args()

    docs = [doc_id for doc_id, _ in iter_final_files(args.doc)]
    if not docs:
        print(f"[FEHLER] keine tei_final-Dokumente gefunden{' fuer ' + args.doc if args.doc else ''}",
              file=sys.stderr)
        return

    reports = {}
    for doc_id in docs:
        r = process_doc(doc_id, args.dry_run, args.strip_folio_echo)
        reports[doc_id] = r
        if r.get("error"):
            print(f"  {doc_id:>5}  [FEHLER] {r['error']}", file=sys.stderr)
            continue
        cnt = r["source_counts"]
        print(f"  {doc_id:>5}  class={r['class']:14s} folio={r['content_folio']}/{r['content_pages']}"
              f"  footer={cnt['footer']} interp={cnt['interpolation']} offset={cnt['offset']}"
              f" existing={cnt['existing_folio']} fallback={cnt['fallback']} echo={r['echo']}")

    _print_validation(reports)
    _print_summary(reports)
    _write_report(reports, args.strip_folio_echo)
    if args.dry_run:
        print("(dry-run: nur Report geschrieben, tei_final unberuehrt)")
    else:
        print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
