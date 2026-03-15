"""
TEI Validator: RelaxNG-Schema + projektspezifische Pruefungen.

Zwei Ebenen:
  - Errors (blockierend):  RelaxNG-Schema + Projekt-Regeln (valid=false)
  - Warnings (informativ):  Quality-Checks fuer Editoren (valid bleibt true)

Aufruf:
    python -m scripts.tei.tei_validator --doc 2310
    python -m scripts.tei.tei_validator --all --report
    python -m scripts.tei.tei_validator --all --html-report
"""

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import (
    SCHEMA_DOWNLOAD_TIMEOUT,
    TEI_ALL_URL,
    TEI_NS,
    TEI_SCHEMA_DIR,
    TEI_SCHEMA_PATH,
    TEI_UNIFIED_DIR,
    VALID_DIV_TYPES,
)

try:
    from lxml import etree as lxml_etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False
    lxml_etree = None


# ---------------------------------------------------------------------------
# Schema Download
# ---------------------------------------------------------------------------

def ensure_schema() -> Path:
    """Stellt sicher, dass das RelaxNG-Schema vorhanden ist."""
    if TEI_SCHEMA_PATH.exists():
        return TEI_SCHEMA_PATH

    TEI_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Lade TEI-All RelaxNG Schema von {TEI_ALL_URL} ...")
    import urllib.request
    try:
        with urllib.request.urlopen(TEI_ALL_URL, timeout=SCHEMA_DOWNLOAD_TIMEOUT) as resp:
            TEI_SCHEMA_PATH.write_bytes(resp.read())
        print(f"  Schema gespeichert: {TEI_SCHEMA_PATH}")
    except Exception as e:
        print(f"  WARNUNG: Download fehlgeschlagen: {e}")
        print("  Validierung nur mit Projekt-Regeln moeglich.")
        return None

    return TEI_SCHEMA_PATH


# ---------------------------------------------------------------------------
# RelaxNG Validation
# ---------------------------------------------------------------------------

def validate_relaxng(tei_path: Path, schema_path: Path) -> list[dict]:
    """Validiert TEI gegen RelaxNG-Schema via lxml.

    Returns:
        Liste von Fehlern: [{"line": int, "message": str}]
    """
    if not HAS_LXML:
        return [{"line": 0, "message": "lxml nicht installiert -- pip install lxml"}]

    try:
        schema_doc = lxml_etree.parse(str(schema_path))
        relaxng = lxml_etree.RelaxNG(schema_doc)
    except Exception as e:
        return [{"line": 0, "message": f"Schema-Fehler: {e}"}]

    try:
        doc = lxml_etree.parse(str(tei_path))
    except lxml_etree.XMLSyntaxError as e:
        return [{"line": getattr(e, "lineno", 0),
                 "message": f"XML-Syntax: {e}"}]

    if relaxng.validate(doc):
        return []

    return [
        {"line": error.line, "message": str(error.message)}
        for error in relaxng.error_log
    ]


# ---------------------------------------------------------------------------
# Projekt-Pruefungen (auf bereits geparstem Tree)
# ---------------------------------------------------------------------------

def _check_project_rules(root) -> tuple[list[dict], list[dict]]:
    """Prueft alle Projekt-Regeln auf einem lxml-Root.

    Returns:
        (errors, warnings) -- errors sind blockierend, warnings informativ.
    """
    errors = []
    warnings = []

    # -----------------------------------------------------------------------
    # ERRORS -- blockierend (valid=false)
    # -----------------------------------------------------------------------

    # R1: TEI type="naegeli"
    tei_type = root.get("type")
    if tei_type != "naegeli":
        errors.append({
            "line": root.sourceline or 0,
            "message": f'TEI root: type="{tei_type}", erwartet "naegeli"',
            "rule": "R1",
        })

    # R2: teiHeader vorhanden
    header = root.find(f"{{{TEI_NS}}}teiHeader")
    if header is None:
        errors.append({"line": 0, "message": "teiHeader fehlt", "rule": "R2"})

    # R3: text/body vorhanden
    body = root.find(f".//{{{TEI_NS}}}body")
    if body is None:
        errors.append({"line": 0, "message": "text/body fehlt", "rule": "R3"})

    # R4: Mindestens ein div
    divs = root.findall(f".//{{{TEI_NS}}}div")
    if not divs:
        errors.append({"line": 0, "message": "Kein <div> gefunden", "rule": "R4"})

    # R5: div-Typen gueltig
    for div in divs:
        div_type = div.get("type")
        div_n = div.get("n")
        if div_type and div_type not in VALID_DIV_TYPES:
            errors.append({
                "line": div.sourceline or 0,
                "message": f'Unbekannter div type="{div_type}"',
                "rule": "R5",
            })
        if not div_type and not div_n:
            errors.append({
                "line": div.sourceline or 0,
                "message": "div ohne type oder n Attribut",
                "rule": "R5",
            })

    # R6: note muss place haben
    for note in root.findall(f".//{{{TEI_NS}}}note"):
        if not note.get("place"):
            errors.append({
                "line": note.sourceline or 0,
                "message": "note ohne place Attribut",
                "rule": "R6",
            })

    # -----------------------------------------------------------------------
    # WARNINGS -- informativ fuer Editoren
    # -----------------------------------------------------------------------

    # W9: Entity-Elemente ohne ref (wird erst nach NER-Injection aufgeloest)
    missing_refs = 0
    total_entities = 0
    for elem_name in ("persName", "orgName", "placeName"):
        for elem in root.findall(f".//{{{TEI_NS}}}{elem_name}"):
            total_entities += 1
            if not elem.get("ref"):
                missing_refs += 1
    if missing_refs > 0:
        warnings.append({
            "line": 0,
            "message": f'{missing_refs}/{total_entities} Entity-Tags ohne ref (NER-Injection ausstehend)',
            "rule": "W9",
        })

    # W1: Sprach-Code "und" (undetermined)
    for lang in root.findall(f".//{{{TEI_NS}}}language"):
        if lang.get("ident", "") == "und":
            warnings.append({
                "line": lang.sourceline or 0,
                "message": 'Sprach-Code "und" (undetermined) -- sollte spezifisch sein (fra/deu/...)',
                "rule": "W1",
            })

    # W2: teiHeader Vollstaendigkeit -- title, author, date nicht leer
    if header is not None:
        title_el = header.find(f".//{{{TEI_NS}}}title")
        title_text = "".join(title_el.itertext()).strip() if title_el is not None else ""
        if not title_text:
            warnings.append({
                "line": (title_el.sourceline if title_el is not None else 0) or 0,
                "message": "teiHeader: <title> fehlt oder ist leer",
                "rule": "W2",
            })

        author_el = header.find(f".//{{{TEI_NS}}}author")
        author_text = "".join(author_el.itertext()).strip() if author_el is not None else ""
        if not author_text:
            warnings.append({
                "line": (author_el.sourceline if author_el is not None else 0) or 0,
                "message": "teiHeader: <author> fehlt oder ist leer",
                "rule": "W2",
            })

    # W3: facsimile-pb-Konsistenz -- Anzahl surface == Anzahl pb
    surfaces = root.findall(f".//{{{TEI_NS}}}surface")
    pbs = root.findall(f".//{{{TEI_NS}}}pb")
    if surfaces and pbs and len(surfaces) != len(pbs):
        warnings.append({
            "line": 0,
            "message": f'facsimile/pb Mismatch: {len(surfaces)} surfaces, {len(pbs)} pb-Elemente',
            "rule": "W3",
        })

    # W4: Leere <div> Elemente (kein Text-Content)
    for div in divs:
        text_content = "".join(div.itertext()).strip()
        if not text_content:
            warnings.append({
                "line": div.sourceline or 0,
                "message": f'Leeres <div> (type="{div.get("type", "")}" n="{div.get("n", "")}")',
                "rule": "W4",
            })

    # W5: Text-Volumen -- Seiten mit weniger als 50 Zeichen sind verdaechtig
    if body is not None and pbs:
        _check_thin_pages(body, pbs, warnings)

    # W6: lb-Dichte -- Seiten ohne <lb/> sind verdaechtig
    if body is not None:
        lbs = body.findall(f".//{{{TEI_NS}}}lb")
        if pbs and not lbs:
            warnings.append({
                "line": 0,
                "message": f'Keine <lb/> Elemente im body ({len(pbs)} Seiten)',
                "rule": "W6",
            })

    # W7: graphic ohne sinnvolles url-Attribut
    for graphic in root.findall(f".//{{{TEI_NS}}}graphic"):
        url = graphic.get("url", "")
        if not url or url == "unknown":
            warnings.append({
                "line": graphic.sourceline or 0,
                "message": f'<graphic> ohne sinnvolles url (url="{url}")',
                "rule": "W7",
            })

    # W8: Entity-Coverage -- Docs ohne jegliche Entity-Tags
    entity_count = sum(
        len(root.findall(f".//{{{TEI_NS}}}{tag}"))
        for tag in ("persName", "orgName", "placeName", "bibl")
    )
    if body is not None and entity_count == 0:
        body_text = "".join(body.itertext())
        if len(body_text) > 500:
            warnings.append({
                "line": 0,
                "message": f'Keine Entity-Tags (persName/orgName/placeName/bibl) bei {len(body_text)} Zeichen Text',
                "rule": "W8",
            })

    return errors, warnings


def _check_thin_pages(body, pbs, warnings):
    """Prueft ob Seiten ungewoehnlich wenig Text haben."""
    # Sammle Text-Laenge pro Seite (approximiert ueber pb-Positionen)
    # Einfache Heuristik: Gesamttext / Seitenanzahl < 50 Zeichen
    total_text = "".join(body.itertext())
    n_pages = len(pbs)
    if n_pages > 0:
        avg_chars = len(total_text) / n_pages
        if avg_chars < 50:
            warnings.append({
                "line": 0,
                "message": f'Sehr wenig Text: {len(total_text)} Zeichen auf {n_pages} Seiten (avg {avg_chars:.0f} chars/Seite)',
                "rule": "W5",
            })


# ---------------------------------------------------------------------------
# Haupt-Validierung
# ---------------------------------------------------------------------------

def validate_tei_file(tei_path: Path) -> dict:
    """Validiert eine TEI-Datei (Schema + Projekt-Regeln + Warnings).

    Returns:
        {"valid": bool, "errors": [...], "warnings": [...],
         "schema_errors": int, "project_errors": int, "warning_count": int}
    """
    result = {
        "file": str(tei_path.name),
        "valid": True,
        "errors": [],
        "warnings": [],
        "schema_errors": 0,
        "project_errors": 0,
        "warning_count": 0,
    }

    # 1. XML parsen (einmal, fuer alle Checks)
    if not HAS_LXML:
        try:
            import xml.etree.ElementTree as ET
            ET.parse(str(tei_path))
        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append({"line": 0, "message": f"XML Parse Error: {e}"})
            return result
        # Ohne lxml: nur Wellformedness, keine weiteren Checks
        return result

    try:
        tree = lxml_etree.parse(str(tei_path))
    except lxml_etree.XMLSyntaxError as e:
        result["valid"] = False
        result["errors"].append({
            "line": getattr(e, "lineno", 0),
            "message": f"XML-Syntax: {e}",
        })
        return result

    root = tree.getroot()

    # 2. RelaxNG-Schema
    schema_path = ensure_schema()
    if schema_path and schema_path.exists():
        schema_errors = validate_relaxng(tei_path, schema_path)
        result["schema_errors"] = len(schema_errors)
        result["errors"].extend(schema_errors)
        if schema_errors:
            result["valid"] = False

    # 3. Projekt-Regeln + Warnings (auf bereits geparstem Tree)
    project_errors, quality_warnings = _check_project_rules(root)
    result["project_errors"] = len(project_errors)
    result["errors"].extend(project_errors)
    if project_errors:
        result["valid"] = False

    result["warnings"] = quality_warnings
    result["warning_count"] = len(quality_warnings)

    return result


def validate_all(tei_dir: Path = None) -> dict:
    """Validiert alle TEI-Dateien in einem Verzeichnis."""
    if tei_dir is None:
        tei_dir = TEI_UNIFIED_DIR

    summary = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "with_warnings": 0,
        "per_doc": {},
    }

    if not tei_dir.exists():
        print(f"Verzeichnis nicht gefunden: {tei_dir}")
        return summary

    for doc_dir in sorted(tei_dir.iterdir()):
        if not doc_dir.is_dir():
            continue
        final = doc_dir / f"{doc_dir.name}_final.xml"
        if not final.exists():
            continue

        summary["total"] += 1
        result = validate_tei_file(final)
        summary["per_doc"][doc_dir.name] = result

        if result["valid"]:
            summary["valid"] += 1
        else:
            summary["invalid"] += 1

        if result["warnings"]:
            summary["with_warnings"] += 1

    return summary


# ---------------------------------------------------------------------------
# HTML-Report
# ---------------------------------------------------------------------------

def generate_html_report(summary: dict, output_path: Path) -> None:
    """Erzeugt einen kompakten HTML-Validierungsbericht."""
    total = summary["total"]
    valid = summary["valid"]
    invalid = summary["invalid"]
    with_warnings = summary["with_warnings"]
    valid_pct = (valid / total * 100) if total else 0

    # Fehler/Warning-Haeufigkeit aggregieren
    error_counter = Counter()
    warning_counter = Counter()

    for doc_id, result in summary["per_doc"].items():
        for err in result.get("errors", []):
            msg = re.sub(r'line \d+', 'line N', err.get("message", ""))
            rule = err.get("rule", "schema")
            error_counter[f'[{rule}] {msg[:80]}'] += 1
        for warn in result.get("warnings", []):
            rule = warn.get("rule", "?")
            warning_counter[rule] += 1

    # Warning-Rule Beschreibungen
    warning_labels = {
        "W1": "Sprach-Code undetermined ('und')",
        "W2": "teiHeader unvollstaendig (title/author leer)",
        "W3": "facsimile/pb Mismatch (surface vs. pb Anzahl)",
        "W4": "Leere div-Elemente",
        "W5": "Sehr wenig Text (avg <50 chars/Seite)",
        "W6": "Keine lb-Elemente",
        "W7": "graphic ohne url-Attribut",
        "W8": "Keine Entity-Tags bei substanziellem Text",
        "W9": "Entity-Tags ohne ref (NER-Injection ausstehend)",
    }

    # Error-Frequency HTML
    error_freq_rows = ""
    for msg, count in error_counter.most_common(20):
        error_freq_rows += (
            f'<tr><td class="msg">{_html_escape(msg)}</td>'
            f'<td class="num">{count}</td></tr>\n'
        )

    # Warning-Frequency HTML
    warning_freq_rows = ""
    for rule, count in warning_counter.most_common():
        label = warning_labels.get(rule, rule)
        warning_freq_rows += (
            f'<tr><td>{rule}</td><td>{_html_escape(label)}</td>'
            f'<td class="num">{count}</td></tr>\n'
        )

    # Per-Document Detail Table
    doc_rows = ""
    for doc_id in sorted(summary["per_doc"].keys(), key=lambda x: int(x) if x.isdigit() else x):
        result = summary["per_doc"][doc_id]
        is_valid = result["valid"]
        n_errors = result.get("schema_errors", 0) + result.get("project_errors", 0)
        n_warnings = result.get("warning_count", 0)

        status_class = "valid" if is_valid else "invalid"
        status_text = "VALID" if is_valid else "INVALID"

        # Warning Rules auflisten
        warn_rules = ", ".join(
            w.get("rule", "?") for w in result.get("warnings", [])
        ) or "-"

        # Fehler-Details (erste 3)
        error_detail = ""
        for err in result.get("errors", [])[:3]:
            line = err.get("line", "?")
            rule = err.get("rule", "schema")
            msg = _html_escape(err.get("message", "")[:80])
            error_detail += f'<div class="err-detail">[{rule}] L{line}: {msg}</div>'

        doc_rows += (
            f'<tr class="{status_class}">'
            f'<td>{doc_id}</td>'
            f'<td><span class="badge {status_class}">{status_text}</span></td>'
            f'<td class="num">{n_errors}</td>'
            f'<td class="num">{n_warnings}</td>'
            f'<td>{warn_rules}</td>'
            f'<td>{error_detail}</td>'
            f'</tr>\n'
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>TEI Validation Report</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 1100px; margin: 2em auto; padding: 0 1.5em; color: #1a2744; background: #fafbfd; }}
h1 {{ color: #1a2744; margin-bottom: 0.3em; }}
h2 {{ color: #4a6fa5; border-bottom: 2px solid #e0e6ed; padding-bottom: 6px; margin-top: 2em; }}
.subtitle {{ color: #666; margin-top: 0; }}
.metrics {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 1.5em 0; }}
.metric {{ padding: 16px 24px; background: #fff; border-radius: 10px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.08); min-width: 100px; }}
.metric .value {{ font-size: 2em; font-weight: bold; color: #1a2744; }}
.metric .label {{ font-size: 0.8em; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
.metric.ok .value {{ color: #2e7d32; }}
.metric.warn .value {{ color: #e65100; }}
.metric.err .value {{ color: #c62828; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }}
th, td {{ padding: 7px 10px; border: 1px solid #e0e6ed; text-align: left; }}
th {{ background: #f0f4f8; font-weight: 600; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
td.msg {{ font-family: 'JetBrains Mono', monospace; font-size: 0.85em; word-break: break-all; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
.badge.valid {{ background: #e8f5e9; color: #2e7d32; }}
.badge.invalid {{ background: #ffebee; color: #c62828; }}
tr.invalid {{ background: #fff8f8; }}
.err-detail {{ font-family: 'JetBrains Mono', monospace; font-size: 0.8em; color: #c62828; margin: 2px 0; }}
.rule-desc {{ margin: 0.5em 0; padding: 8px 12px; background: #f0f4f8; border-radius: 6px; font-size: 0.9em; }}
footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid #e0e6ed; color: #888; font-size: 0.85em; }}
</style>
</head>
<body>

<h1>TEI Validation Report</h1>
<p class="subtitle">ZBZ-OCR-TEI Pipeline | {timestamp}</p>

<div class="metrics">
<div class="metric"><div class="value">{total}</div><div class="label">Dokumente</div></div>
<div class="metric ok"><div class="value">{valid}</div><div class="label">Valid</div></div>
<div class="metric err"><div class="value">{invalid}</div><div class="label">Invalid</div></div>
<div class="metric warn"><div class="value">{with_warnings}</div><div class="label">Mit Warnings</div></div>
<div class="metric ok"><div class="value">{valid_pct:.1f}%</div><div class="label">Valid Rate</div></div>
</div>

<h2>Errors (blockierend)</h2>
<div class="rule-desc">
  Schema-Fehler (RelaxNG TEI-All) und Projekt-Regeln (R1-R7).
  Dokumente mit Errors gelten als INVALID.
</div>
{"<p>Keine Errors gefunden.</p>" if not error_freq_rows else f'''
<table>
<tr><th>Fehler</th><th>Docs</th></tr>
{error_freq_rows}
</table>'''}

<h2>Warnings (informativ fuer Editoren)</h2>
<div class="rule-desc">
  Quality-Checks (W1-W8). Nicht blockierend -- zeigen Probleme,
  die bei der Kuration geprueft werden sollten.
</div>
{"<p>Keine Warnings.</p>" if not warning_freq_rows else f'''
<table>
<tr><th>Regel</th><th>Beschreibung</th><th>Docs</th></tr>
{warning_freq_rows}
</table>'''}

<h2>Per-Dokument Detail</h2>
<table>
<tr><th>Doc</th><th>Status</th><th>Errors</th><th>Warnings</th><th>Warning-Regeln</th><th>Details</th></tr>
{doc_rows}
</table>

<footer>
  <p>Errors: RelaxNG TEI-All + R1 (type=naegeli), R2 (teiHeader), R3 (body), R4 (div), R5 (div-types), R6 (note place)</p>
  <p>Warnings: W1 (Sprache), W2 (Header-Felder), W3 (facsimile/pb), W4 (leere div), W5 (Text-Volumen), W6 (lb-Dichte), W7 (graphic url), W8 (Entity-Coverage), W9 (Entity-Refs)</p>
</footer>

</body>
</html>"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML-Report geschrieben: {output_path}")


def _html_escape(text: str) -> str:
    """Minimales HTML-Escaping."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TEI Validator: RelaxNG + Projekt-Regeln + Quality Warnings"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument validieren")
    parser.add_argument("--all", action="store_true",
                        help="Alle unified TEI validieren")
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis")
    parser.add_argument("--report", action="store_true",
                        help="Validierungsbericht als JSON speichern")
    parser.add_argument("--html-report", action="store_true",
                        help="HTML-Validierungsbericht erzeugen")
    args = parser.parse_args()

    tei_dir = Path(args.dir) if args.dir else TEI_UNIFIED_DIR

    if args.doc:
        doc_dir = tei_dir / args.doc
        final = doc_dir / f"{args.doc}_final.xml"
        if not final.exists():
            print(f"Datei nicht gefunden: {final}")
            return
        result = validate_tei_file(final)
        status = "VALID" if result["valid"] else "INVALID"
        print(f"{args.doc}: {status}")
        print(f"  Schema-Fehler:    {result['schema_errors']}")
        print(f"  Projekt-Fehler:   {result['project_errors']}")
        print(f"  Warnings:         {result['warning_count']}")
        for err in result["errors"][:10]:
            rule = err.get("rule", "schema")
            print(f"    ERROR [{rule}] L{err.get('line', '?')}: {err['message']}")
        for warn in result["warnings"][:10]:
            print(f"    WARN  [{warn.get('rule', '?')}] {warn['message']}")

    elif args.all:
        start = time.time()
        print(f"Validiere alle TEI in {tei_dir} ...")
        summary = validate_all(tei_dir)
        elapsed = time.time() - start

        print(f"\n  Gesamt:        {summary['total']}")
        print(f"  Valide:        {summary['valid']}")
        print(f"  Invalide:      {summary['invalid']}")
        print(f"  Mit Warnings:  {summary['with_warnings']}")
        print(f"  Dauer:         {elapsed:.1f}s")

        # Fehler-Details
        for doc_id, result in summary["per_doc"].items():
            if not result["valid"]:
                n_err = len(result["errors"])
                print(f"  {doc_id}: {n_err} Fehler")
                for err in result["errors"][:3]:
                    rule = err.get("rule", "schema")
                    print(f"    [{rule}] L{err.get('line', '?')}: {err['message'][:80]}")

        if args.report:
            report_path = tei_dir / "validation_report.json"
            report_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"\n  JSON-Bericht: {report_path}")

        if args.html_report:
            html_path = tei_dir / "validation_report.html"
            generate_html_report(summary, html_path)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
