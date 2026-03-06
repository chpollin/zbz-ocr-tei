"""
TEI Validator: RelaxNG-Schema + projektspezifische Regeln.

Validiert generierte TEI-XML gegen das TEI-All RelaxNG-Schema
und prueft ZBZ-projektspezifische Regeln.

Aufruf:
    python -m scripts.tei.tei_validator --doc 2310
    python -m scripts.tei.tei_validator --all
    python -m scripts.tei.tei_validator --report
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import TEI_SCHEMA_DIR, TEI_SCHEMA_PATH, TEI_UNIFIED_DIR

TEI_NS = "http://www.tei-c.org/ns/1.0"
TEI_ALL_URL = "https://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng"


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
        urllib.request.urlretrieve(TEI_ALL_URL, str(TEI_SCHEMA_PATH))
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
    try:
        from lxml import etree
    except ImportError:
        return [{"line": 0, "message": "lxml nicht installiert -- pip install lxml"}]

    try:
        schema_doc = etree.parse(str(schema_path))
        relaxng = etree.RelaxNG(schema_doc)
    except Exception as e:
        return [{"line": 0, "message": f"Schema-Fehler: {e}"}]

    try:
        doc = etree.parse(str(tei_path))
    except etree.XMLSyntaxError as e:
        return [{"line": getattr(e, "lineno", 0),
                 "message": f"XML-Syntax: {e}"}]

    is_valid = relaxng.validate(doc)
    if is_valid:
        return []

    errors = []
    for error in relaxng.error_log:
        errors.append({
            "line": error.line,
            "message": str(error.message),
        })
    return errors


# ---------------------------------------------------------------------------
# Projekt-spezifische Regeln
# ---------------------------------------------------------------------------

def validate_project_rules(tei_path: Path) -> list[dict]:
    """Prueft ZBZ-projektspezifische Regeln.

    Returns:
        Liste von Warnungen/Fehlern
    """
    try:
        from lxml import etree
    except ImportError:
        import xml.etree.ElementTree as etree_std
        tree = etree_std.parse(str(tei_path))
        root = tree.getroot()
        ns = {"tei": TEI_NS}
        errors = []
        # Minimal-Check mit stdlib
        if "naegeli" not in (root.get("type") or ""):
            errors.append({"line": 0, "message": 'TEI root missing type="naegeli"'})
        return errors

    tree = etree.parse(str(tei_path))
    root = tree.getroot()
    ns = {"tei": TEI_NS}
    errors = []

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

    # R5: div-Typen pruefen
    valid_types = {
        "review", "interview", "conversation", "entry",
        "bibliography", "editorial", "text", "translation",
        "reprint", "redactional",
    }
    for div in divs:
        div_type = div.get("type")
        div_n = div.get("n")
        if div_type and div_type not in valid_types:
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

    # R6: note muss place="foot" haben
    for note in root.findall(f".//{{{TEI_NS}}}note"):
        if not note.get("place"):
            errors.append({
                "line": note.sourceline or 0,
                "message": "note ohne place Attribut",
                "rule": "R6",
            })

    # R7: persName/orgName muessen ref haben
    for elem_name in ("persName", "orgName"):
        for elem in root.findall(f".//{{{TEI_NS}}}{elem_name}"):
            if not elem.get("ref"):
                text = (elem.text or "")[:30]
                errors.append({
                    "line": elem.sourceline or 0,
                    "message": f'{elem_name} ohne ref: "{text}"',
                    "rule": "R7",
                })

    # R8: language ident vorhanden
    for lang in root.findall(f".//{{{TEI_NS}}}language"):
        ident = lang.get("ident")
        if not ident:
            errors.append({
                "line": lang.sourceline or 0,
                "message": "language ohne ident Attribut",
                "rule": "R8",
            })

    return errors


# ---------------------------------------------------------------------------
# Haupt-Validierung
# ---------------------------------------------------------------------------

def validate_tei_file(tei_path: Path) -> dict:
    """Validiert eine TEI-Datei (Schema + Projekt-Regeln).

    Returns:
        {"valid": bool, "errors": [...], "warnings": [...],
         "schema_errors": int, "project_errors": int}
    """
    result = {
        "file": str(tei_path.name),
        "valid": True,
        "errors": [],
        "warnings": [],
        "schema_errors": 0,
        "project_errors": 0,
    }

    # XML Well-formedness
    try:
        import xml.etree.ElementTree as ET
        ET.parse(str(tei_path))
    except ET.ParseError as e:
        result["valid"] = False
        result["errors"].append({"line": 0, "message": f"XML Parse Error: {e}"})
        return result

    # RelaxNG-Schema
    schema_path = ensure_schema()
    if schema_path and schema_path.exists():
        schema_errors = validate_relaxng(tei_path, schema_path)
        result["schema_errors"] = len(schema_errors)
        for err in schema_errors:
            result["errors"].append(err)
        if schema_errors:
            result["valid"] = False

    # Projekt-Regeln
    project_errors = validate_project_rules(tei_path)
    result["project_errors"] = len(project_errors)
    for err in project_errors:
        result["warnings"].append(err)

    return result


def validate_all(tei_dir: Path = None) -> dict:
    """Validiert alle TEI-Dateien in einem Verzeichnis.

    Returns:
        {"total": int, "valid": int, "invalid": int,
         "per_doc": {doc_id: result}}
    """
    if tei_dir is None:
        tei_dir = TEI_UNIFIED_DIR

    summary = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
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

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TEI Validator: RelaxNG + Projekt-Regeln"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument validieren")
    parser.add_argument("--all", action="store_true",
                        help="Alle unified TEI validieren")
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis")
    parser.add_argument("--report", action="store_true",
                        help="Validierungsbericht als JSON speichern")
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
        print(f"  Schema-Fehler: {result['schema_errors']}")
        print(f"  Projekt-Warnungen: {result['project_errors']}")
        for err in result["errors"][:10]:
            print(f"    L{err.get('line', '?')}: {err['message']}")
        for warn in result["warnings"][:10]:
            rule = warn.get("rule", "")
            print(f"    [{rule}] {warn['message']}")

    elif args.all:
        print(f"Validiere alle TEI in {tei_dir} ...")
        summary = validate_all(tei_dir)
        print(f"\n  Gesamt: {summary['total']}")
        print(f"  Valide: {summary['valid']}")
        print(f"  Invalide: {summary['invalid']}")

        # Fehler-Details
        for doc_id, result in summary["per_doc"].items():
            if not result["valid"]:
                n_err = len(result["errors"])
                print(f"  {doc_id}: {n_err} Fehler")
                for err in result["errors"][:3]:
                    print(f"    L{err.get('line', '?')}: {err['message'][:80]}")

        if args.report:
            report_path = tei_dir / "validation_report.json"
            report_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"\n  Bericht: {report_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
