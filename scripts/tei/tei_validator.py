"""
TEI Validator: RelaxNG-Schema + projektspezifische Pruefungen.

Zwei Ebenen:
  - Errors (blockierend):  RelaxNG-Schema + Projekt-Regeln (valid=false)
  - Warnings (informativ):  Quality-Checks fuer Editoren (valid bleibt true)

Aufruf (Default-Verzeichnis ist die ausgelieferte SoT tei_final, --dir ueberschreibt):
    python -m scripts.tei.tei_validator --doc 2310
    python -m scripts.tei.tei_validator --all --report
    python -m scripts.tei.tei_validator --all --html-report
    python -m scripts.tei.tei_validator --all --dir output/tei_unified  # Zwischenstand
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
    REFERENCE_TEI_DIR,
    TEI_FINAL_DIR,
    TEI_NS,
    TEI_SCHEMA_PATH,
    TEI_UNIFIED_DIR,
    VALID_DIV_TYPES,
)
from scripts.tei.tei_xml_utils import (
    iter_page_zone_bboxes,
    normalize_lang_code,
    reading_order_permutation,
)
from scripts.tei.zbz_conformity import RULE_LABELS as ZBZ_RULE_LABELS, check_conformity

try:
    from lxml import etree as lxml_etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False
    lxml_etree = None


# ---------------------------------------------------------------------------
# Schema-Pfad (lokal, projektspezifisch: zbz_hersch.rng)
# ---------------------------------------------------------------------------

def ensure_schema() -> Path:
    """Prueft, ob das projektspezifische RelaxNG-Schema vorhanden ist."""
    if TEI_SCHEMA_PATH.exists():
        return TEI_SCHEMA_PATH

    print(f"WARNUNG: Schema nicht gefunden: {TEI_SCHEMA_PATH}")
    print("  Erwartet: data/schema/zbz_hersch.rng (projektspezifisch, aus ODD generiert)")
    print("  Validierung nur mit Projekt-Regeln moeglich.")
    return None


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

    # R7: figure darf nicht in p stehen (Richtlinie: eigenstaendige Bloecke)
    for p in root.findall(f".//{{{TEI_NS}}}p"):
        for fig in p.findall(f"{{{TEI_NS}}}figure"):
            errors.append({
                "line": fig.sourceline or 0,
                "message": "<figure> innerhalb von <p> -- muss eigenstaendiger Block sein",
                "rule": "R7",
            })

    # -----------------------------------------------------------------------
    # WARNINGS -- informativ fuer Editoren
    # -----------------------------------------------------------------------

    # W1: Sprach-Code "und" (undetermined) -- nur wenn langUsage vorhanden
    # (zbz_hersch.rng Schema hat kein langUsage, daher optional)
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

    # W11: div-Struktur -- zu viele top-level divs mit gleichem n
    if body is not None:
        top_divs = body.findall(f"{{{TEI_NS}}}div")
        if len(top_divs) > 3:
            # Zaehle wie viele den gleichen n-Wert haben
            n_vals = [d.get("n", "") for d in top_divs]
            from collections import Counter as _Counter
            most_common_n, count = _Counter(n_vals).most_common(1)[0]
            if count > 3:
                warnings.append({
                    "line": 0,
                    "message": f'{count} top-level divs mit n="{most_common_n}" -- div-Merge nicht gegriffen?',
                    "rule": "W11",
                })

    # W12: note place="foot" sollte n-Attribut haben (Richtlinie: Fussnotennummer)
    for note in root.findall(f".//{{{TEI_NS}}}note"):
        if note.get("place") == "foot" and not note.get("n"):
            warnings.append({
                "line": note.sourceline or 0,
                "message": '<note place="foot"> ohne n-Attribut (Fussnotennummer fehlt)',
                "rule": "W12",
            })

    # W13: note place="foot" sollte xml:id mit Pattern fn{Seite}-{Nr} haben
    fn_id_pattern = re.compile(r"^fn\d+[a-z]?-\d+$")
    for note in root.findall(f".//{{{TEI_NS}}}note"):
        if note.get("place") == "foot":
            xml_id = note.get("{http://www.w3.org/XML/1998/namespace}id", "")
            if xml_id and not fn_id_pattern.match(xml_id):
                warnings.append({
                    "line": note.sourceline or 0,
                    "message": f'Fussnoten xml:id="{xml_id}" entspricht nicht Pattern fn{{Seite}}-{{Nr}}',
                    "rule": "W13",
                })

    # W14: back/div sollte type in {translation, reprint, otherEdition} haben
    _BACK_DIV_TYPES = {"translation", "reprint", "otherEdition"}
    back = root.find(f".//{{{TEI_NS}}}back")
    if back is not None:
        for div in back.findall(f"{{{TEI_NS}}}div"):
            div_type = div.get("type", "")
            if div_type and div_type not in _BACK_DIV_TYPES:
                warnings.append({
                    "line": div.sourceline or 0,
                    "message": f'<back>/<div type="{div_type}"> -- erwartet: {_BACK_DIV_TYPES}',
                    "rule": "W14",
                })

    # W15: div mit @type UND @n -- Editionsrichtlinie: Struktur-n vs. Spezial-type exklusiv
    for div in root.findall(f".//{{{TEI_NS}}}div"):
        if div.get("type") and div.get("n") is not None:
            warnings.append({
                "line": div.sourceline or 0,
                "message": f'<div type="{div.get("type")}"> traegt zugleich n="{div.get("n")}" (type/n exklusiv)',
                "rule": "W15",
            })

    # W16: figure ohne xml:id -- Editionsrichtlinie: fortlaufende figN
    for fig in root.findall(f".//{{{TEI_NS}}}figure"):
        if not fig.get("{http://www.w3.org/XML/1998/namespace}id"):
            warnings.append({
                "line": fig.sourceline or 0,
                "message": "<figure> ohne xml:id (Richtlinie: fortlaufende figN)",
                "rule": "W16",
            })

    # W17: leeres <speaker> -- Sprechername fehlt. Kurations-Slot: Benennung/GND-Verknuepfung
    # ist stromabwaerts (ZBZ-Edition, E71), nicht in der Pipeline. Hier nur sichtbar machen.
    for sp in root.findall(f".//{{{TEI_NS}}}sp"):
        speaker = sp.find(f"{{{TEI_NS}}}speaker")
        if speaker is not None:
            has_content = (speaker.text or "").strip() or len(list(speaker)) > 0
            if not has_content:
                warnings.append({
                    "line": speaker.sourceline or 0,
                    "message": "<speaker> ohne Inhalt (Sprechername fehlt -- Kurations-Slot, E71)",
                    "rule": "W17",
                })

    # W18: <foreign> mit nicht-normalisiertem Sprachcode (Richtlinie: einheitlich ISO-639-2/T
    # 3-Letter). Deckungsgleich mit dem Pipeline-Pass: gemeldet wird genau das, was
    # _normalize_foreign_lang aendern wuerde (gemeinsame normalize_lang_code, keine
    # un-raeumbaren Dauer-Warnungen, kein duplizierter Varianten-Satz).
    for fo in root.findall(f".//{{{TEI_NS}}}foreign"):
        lang = fo.get("{http://www.w3.org/XML/1998/namespace}lang")
        if lang and normalize_lang_code(lang) != lang:
            warnings.append({
                "line": fo.sourceline or 0,
                "message": f'<foreign xml:lang="{lang}"> nicht normalisiert (erwartet 639-2/T 3-Letter)',
                "rule": "W18",
            })

    # W19: Lesereihenfolge der Body-Bloecke je Seite (Spalten-/Band-Ordnung, Defekt 30/760)
    _check_reading_order(root, warnings)

    return errors, warnings


def _check_reading_order(root, warnings):
    """W19: ausgelieferte Block-Reihenfolge je Seite gegen die kanonische Lese-Ordnung.

    Vergleicht, in welcher Reihenfolge die Body-Bloecke ihre Facsimile-Zonen referenzieren,
    mit der spalten-/bandbewussten Lesereihenfolge derselben Zonen (reading_order_permutation,
    geteilt mit dem Generator). Der Befund ist ein VERDACHTSSIGNAL mit zwei moeglichen
    Ursachen: tatsaechlich verschraenkter Text (Defekt der frueheren y-Sortierung) ODER eine
    korrupte Block-zu-Zonen-Zuordnung bei korrektem Text. Die CER-Probe ueber alle
    Referenzdokumente ergab, dass im Altbestand die zweite Ursache dominiert (E99); ein
    maschinelles Umordnen ist deshalb ausgeschlossen und die Aufloesung Kurationsarbeit am
    Faksimile. Greift nur, wo Zonen-Koordinaten vorliegen; neu generierte Dokumente
    (Generator-Fix) sind kanonisch und loesen nicht aus.
    """
    for page, zids, bboxes, line in iter_page_zone_bboxes(root):
        if reading_order_permutation(bboxes) != list(range(len(bboxes))):
            warnings.append({
                "line": line,
                "message": (
                    f"Lesereihenfolge Seite {page}: {len(zids)} Bloecke nicht in kanonischer "
                    f"Spalten-/Lese-Ordnung (Text- ODER Zonen-Defekt, Faksimile-Kuration; E99)"
                ),
                "rule": "W19",
            })


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


def _collect_finals(tei_dir: Path) -> list[tuple[str, Path]]:
    """Sammelt (doc_id, final_path) aus zwei Ablage-Layouts.

    Flach (``{dir}/*_final.xml``) wie die ausgelieferte SoT ``tei_final`` ODER verschachtelt
    (``{dir}/{id}/{id}_final.xml``) wie ``tei_unified``. Die flache Schicht fiel zuvor durch
    (``validate_all`` prueffte nur ``is_dir``-Eintraege), wurde also nie mit Projektregeln und
    Warnungen validiert -- genau die Luecke aus E68 (``tei_final`` ist flach abgelegt).
    """
    flat = sorted(tei_dir.glob("*_final.xml"))
    if flat:
        return [(f.name[: -len("_final.xml")], f) for f in flat]
    finals = []
    for doc_dir in sorted(tei_dir.iterdir()):
        if not doc_dir.is_dir():
            continue
        final = doc_dir / f"{doc_dir.name}_final.xml"
        if final.exists():
            finals.append((doc_dir.name, final))
    return finals


def validate_all(tei_dir: Path | None = None) -> dict:
    """Validiert alle TEI-Dateien in einem Verzeichnis (flache oder verschachtelte Ablage).

    Default ist die ausgelieferte SoT ``tei_final`` (E43): das No-Argument-Gate prueft den
    Lieferbestand, nicht den Zwischenstand. ``tei_unified`` (Pipeline-Selbstcheck) wird von
    ``tei_unified.py`` explizit uebergeben; ``--dir`` erlaubt jedes andere Verzeichnis.
    """
    if tei_dir is None:
        tei_dir = TEI_FINAL_DIR

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

    for doc_id, final in _collect_finals(tei_dir):
        summary["total"] += 1
        result = validate_tei_file(final)
        summary["per_doc"][doc_id] = result

        if result["valid"]:
            summary["valid"] += 1
        else:
            summary["invalid"] += 1

        if result["warnings"]:
            summary["with_warnings"] += 1

    return summary


def conformity_all(tei_dir: Path | None = None) -> dict:
    """ZBZ-Konformitaetspruefung (Inline-GND-Modell, E88) ueber alle ausgelieferten TEI.

    Ergaenzt die Schema-/Projektregel-Validierung um die Editionsrichtlinien-Regeln, die ein
    RelaxNG nicht ausdruecken kann (Normdaten nur GND, kein Register, nur Person/Org/Werk,
    Rendering-Vokabular, ``pb facs/n``). Siehe scripts/tei/zbz_conformity.py.
    """
    if tei_dir is None:
        tei_dir = TEI_FINAL_DIR

    summary = {"total": 0, "conformant": 0, "with_violation": 0,
               "violations": Counter(), "advisories": Counter(), "per_doc": {}}

    if not HAS_LXML or not tei_dir.exists():
        return summary

    for doc_id, final in _collect_finals(tei_dir):
        summary["total"] += 1
        root = lxml_etree.parse(str(final)).getroot()
        findings = check_conformity(root)
        viol = [f for f in findings if f["severity"] == "violation"]
        adv = [f for f in findings if f["severity"] == "advisory"]
        for f in viol:
            summary["violations"][f["rule"]] += 1
        for f in adv:
            summary["advisories"][f["rule"]] += 1
        if viol:
            summary["with_violation"] += 1
        else:
            summary["conformant"] += 1
        summary["per_doc"][doc_id] = {"violations": viol, "advisories": adv}

    return summary


# ---------------------------------------------------------------------------
# Referenz-Vergleich
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Normalisiert Text fuer CER-Vergleich."""
    import unicodedata
    # Unicode normalisieren
    text = unicodedata.normalize("NFC", text)
    # Whitespace normalisieren
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _compute_cer(ref_text: str, hyp_text: str) -> float:
    """Berechnet die CER in Prozent (Levenshtein-basiert) aus bereits extrahiertem Text.

    Die Extraktion erfolgt im Aufrufer (compare_with_reference) ueber die KANONISCHE
    extract_text_for_comparison(), damit --compare-ref dieselbe Zahl liefert wie der
    Benchmark. Prozent, da HTML/CLI in % rechnen (O24).
    """
    if not ref_text:
        return 0.0
    try:
        from scripts.eval.evaluate_ocr import calculate_cer
        return round(calculate_cer(ref_text, hyp_text) * 100, 2)
    except ImportError:
        # Fallback nur, wenn das Eval-Modul fehlt: grobe Laengen-Approximation (Prozent)
        diff = abs(len(ref_text) - len(hyp_text))
        return round(diff / max(len(ref_text), 1) * 100, 2)


def compare_with_reference(tei_dir: Path | None = None, ref_dir: Path | None = None) -> dict:
    """Vergleicht Pipeline-TEI mit ZBZ-Referenz-TEI.

    Returns:
        {"total": int, "docs": [{"doc_id": ..., "cer": ..., "structure": ..., "entities": ...}]}
    """
    if tei_dir is None:
        tei_dir = TEI_UNIFIED_DIR
    if ref_dir is None:
        ref_dir = REFERENCE_TEI_DIR

    if not HAS_LXML or not ref_dir.exists():
        return {"total": 0, "docs": [], "error": "lxml oder Referenz-Verzeichnis fehlt"}

    results = []

    for ref_file in sorted(ref_dir.glob("*.xml")):
        doc_id = ref_file.stem
        # Ausgelieferte Schicht ist tei_final/ (Single Source of Truth, CLAUDE.md).
        # Fallback auf die alte per-Doc-Struktur in tei_unified/{id}/.
        our_file = TEI_FINAL_DIR / f"{doc_id}_final.xml"
        if not our_file.exists():
            our_file = tei_dir / doc_id / f"{doc_id}_final.xml"
        if not our_file.exists():
            continue

        try:
            ref_tree = lxml_etree.parse(str(ref_file))
            our_tree = lxml_etree.parse(str(our_file))
        except Exception as e:
            results.append({"doc_id": doc_id, "error": str(e)})
            continue

        ref_root = ref_tree.getroot()
        our_root = our_tree.getroot()

        # CER: canonical extraction (extract_text_for_comparison), identical to the
        # benchmark/statistics path; any other extraction yields a diverging figure.
        try:
            from scripts.eval.evaluate_ocr import (
                extract_text_for_comparison as _extract,
            )
            ref_text = _extract(ref_file)
            our_text = _extract(our_file)
        except ImportError:
            ref_body = ref_root.find(f".//{{{TEI_NS}}}body")
            our_body = our_root.find(f".//{{{TEI_NS}}}body")
            ref_text = _normalize_text("".join(ref_body.itertext())) if ref_body is not None else ""
            our_text = _normalize_text("".join(our_body.itertext())) if our_body is not None else ""
        cer = _compute_cer(ref_text, our_text)

        # Struktur-Vergleich
        structure = {}
        for tag in ("div", "p", "pb", "note", "head"):
            ref_count = len(ref_root.findall(f".//{{{TEI_NS}}}{tag}"))
            our_count = len(our_root.findall(f".//{{{TEI_NS}}}{tag}"))
            structure[tag] = {"ref": ref_count, "pipeline": our_count}

        # Top-level div count
        ref_body = ref_root.find(f".//{{{TEI_NS}}}body")
        our_body = our_root.find(f".//{{{TEI_NS}}}body")
        ref_top_divs = len(ref_body.findall(f"{{{TEI_NS}}}div")) if ref_body is not None else 0
        our_top_divs = len(our_body.findall(f"{{{TEI_NS}}}div")) if our_body is not None else 0
        structure["top_divs"] = {"ref": ref_top_divs, "pipeline": our_top_divs}

        results.append({
            "doc_id": doc_id,
            "cer": cer,
            "ref_chars": len(ref_text),
            "pipeline_chars": len(our_text),
            "structure": structure,
        })

    return {"total": len(results), "docs": results}


def generate_reference_report(comparison: dict, output_path: Path) -> None:
    """Erzeugt HTML-Report fuer Referenz-Vergleich."""
    docs = comparison.get("docs", [])
    if not docs:
        print("Keine Vergleichsdaten vorhanden.")
        return

    # Aggregierte Metriken
    cers = [d["cer"] for d in docs if "cer" in d and "error" not in d]
    avg_cer = sum(cers) / len(cers) if cers else 0

    # Per-Doc Tabelle
    doc_rows = ""
    for d in docs:
        if "error" in d:
            doc_rows += f'<tr><td>{d["doc_id"]}</td><td colspan="4">ERROR: {_html_escape(d["error"])}</td></tr>\n'
            continue

        s = d["structure"]

        doc_rows += (
            f'<tr>'
            f'<td>{d["doc_id"]}</td>'
            f'<td class="num">{d["cer"]:.1f}%</td>'
            f'<td class="num">{s["top_divs"]["ref"]}/{s["top_divs"]["pipeline"]}</td>'
            f'<td class="num">{s["p"]["ref"]}/{s["p"]["pipeline"]}</td>'
            f'<td class="num">{s["pb"]["ref"]}/{s["pb"]["pipeline"]}</td>'
            f'</tr>\n'
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>TEI Reference Comparison</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1000px; margin: 2em auto; padding: 0 1.5em; color: #1a2744; background: #fafbfd; }}
h1 {{ color: #1a2744; margin-bottom: 0.3em; }}
h2 {{ color: #4a6fa5; border-bottom: 2px solid #e0e6ed; padding-bottom: 6px; margin-top: 2em; }}
.subtitle {{ color: #666; margin-top: 0; }}
.metrics {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 1.5em 0; }}
.metric {{ padding: 16px 24px; background: #fff; border-radius: 10px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.08); min-width: 100px; }}
.metric .value {{ font-size: 2em; font-weight: bold; color: #1a2744; }}
.metric .label {{ font-size: 0.8em; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }}
th, td {{ padding: 7px 10px; border: 1px solid #e0e6ed; text-align: left; }}
th {{ background: #f0f4f8; font-weight: 600; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid #e0e6ed; color: #888; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>TEI Reference Comparison</h1>
<p class="subtitle">Pipeline vs. ZBZ-Referenz | {timestamp}</p>

<div class="metrics">
<div class="metric"><div class="value">{len(docs)}</div><div class="label">Docs verglichen</div></div>
<div class="metric"><div class="value">{avg_cer:.1f}%</div><div class="label">Avg CER</div></div>
</div>

<h2>Per-Dokument Vergleich</h2>
<p>Spalten Ref/Pipeline zeigen Counts (Referenz / Pipeline).</p>
<table>
<tr><th>Doc</th><th>CER</th><th>top-divs (R/P)</th><th>p (R/P)</th><th>pb (R/P)</th></tr>
{doc_rows}
</table>

<footer>
<p>CER = Character Error Rate (Pipeline vs. Referenz Body-Text). Strukturzahlen: Referenz / Pipeline.</p>
</footer>
</body>
</html>"""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Referenz-Report geschrieben: {output_path}")


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

    for result in summary["per_doc"].values():
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
        "W11": "Zu viele top-level divs mit gleichem n (div-Merge fehlt)",
        "W12": "note place=foot ohne n-Attribut",
        "W13": "Fussnoten xml:id entspricht nicht fn{Seite}-{Nr}",
        "W14": "back/div mit unerwartetem type",
        "W15": "div mit type UND n (exklusiv)",
        "W16": "figure ohne xml:id (figN)",
        "W17": "speaker ohne Inhalt (Kurations-Slot, E71)",
        "W18": "foreign xml:lang nicht normalisiert (639-2/B)",
        "W19": "Lesereihenfolge Seite nicht kanonisch (Spalten-/Band-Ordnung)",
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
  Schema-Fehler (RelaxNG zbz_hersch.rng) und Projekt-Regeln (R1-R7).
  Dokumente mit Errors gelten als INVALID.
</div>
{"<p>Keine Errors gefunden.</p>" if not error_freq_rows else f'''
<table>
<tr><th>Fehler</th><th>Docs</th></tr>
{error_freq_rows}
</table>'''}

<h2>Warnings (informativ fuer Editoren)</h2>
<div class="rule-desc">
  Quality-Checks (W1-W19). Nicht blockierend -- zeigen Probleme,
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
  <p>Errors: RelaxNG zbz_hersch.rng + R1 (type=naegeli), R2 (teiHeader), R3 (body), R4 (div), R5 (div-types), R6 (note place), R7 (figure in p)</p>
  <p>Warnings: W1 (Sprache), W2 (Header-Felder), W3 (facsimile/pb), W4 (leere div), W5 (Text-Volumen), W6 (lb-Dichte), W7 (graphic url), W11 (div-Merge), W12 (Fussnoten-n), W13 (Fussnoten-xml:id), W14 (back/div-Typ), W15 (div type+n), W16 (figure xml:id), W17 (leerer speaker), W18 (foreign lang), W19 (Lesereihenfolge)</p>
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
                        help="Alle ausgelieferten TEI (tei_final) validieren")
    parser.add_argument("--dir", help="Alternatives TEI-Verzeichnis (z.B. tei_unified)")
    parser.add_argument("--report", action="store_true",
                        help="Validierungsbericht als JSON speichern")
    parser.add_argument("--html-report", action="store_true",
                        help="HTML-Validierungsbericht erzeugen")
    parser.add_argument("--compare-ref", action="store_true",
                        help="Vergleich mit ZBZ-Referenz-TEI")
    parser.add_argument("--conformity", action="store_true",
                        help="ZBZ-Konformitaetspruefung (Inline-GND-Modell, E88) ueber tei_final")
    args = parser.parse_args()

    tei_dir = Path(args.dir) if args.dir else TEI_FINAL_DIR

    if args.doc:
        # Flache Ablage (tei_final/{id}_final.xml) zuerst, dann verschachtelt
        # (tei_unified/{id}/{id}_final.xml) -- analog _collect_finals.
        final = tei_dir / f"{args.doc}_final.xml"
        if not final.exists():
            final = tei_dir / args.doc / f"{args.doc}_final.xml"
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

    elif args.compare_ref:
        print(f"Vergleiche Pipeline-TEI mit Referenz ({REFERENCE_TEI_DIR}) ...")
        comparison = compare_with_reference(tei_dir)
        print(f"\n  Verglichen: {comparison['total']} Docs")
        for d in comparison.get("docs", []):
            if "error" in d:
                print(f"  {d['doc_id']}: ERROR - {d['error']}")
            else:
                s = d["structure"]
                print(f"  {d['doc_id']}: CER={d['cer']:.1f}%  divs={s['top_divs']['ref']}/{s['top_divs']['pipeline']}  "
                      f"p={s['p']['ref']}/{s['p']['pipeline']}  pb={s['pb']['ref']}/{s['pb']['pipeline']}")

        # HTML-Report
        html_path = tei_dir / "reference_comparison.html"
        generate_reference_report(comparison, html_path)

        # JSON
        json_path = tei_dir / "reference_comparison.json"
        json_path.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  JSON: {json_path}")

    elif args.conformity:
        cdir = Path(args.dir) if args.dir else TEI_FINAL_DIR
        print(f"ZBZ-Konformitaetspruefung (Inline-GND, E88) ueber {cdir} ...")
        summary = conformity_all(cdir)
        print(f"\n  Gesamt:           {summary['total']}")
        print(f"  Konform:          {summary['conformant']}")
        print(f"  Mit Verletzung:   {summary['with_violation']}")
        if summary["violations"]:
            print("\n  Verletzungen je Regel:")
            for rule, count in summary["violations"].most_common():
                print(f"    {rule}: {count}  ({ZBZ_RULE_LABELS.get(rule, rule)})")
        else:
            print("\n  Keine Konformitaets-Verletzungen.")
        if summary["advisories"]:
            print("\n  Advisories je Regel:")
            for rule, count in summary["advisories"].most_common():
                print(f"    {rule}: {count}  ({ZBZ_RULE_LABELS.get(rule, rule)})")
        # Dokumente mit Verletzung auflisten
        for doc_id, res in summary["per_doc"].items():
            if res["violations"]:
                print(f"  {doc_id}: {len(res['violations'])} Verletzung(en)")
                for v in res["violations"][:3]:
                    print(f"    [{v['rule']}] L{v['line']}: {v['message'][:80]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
