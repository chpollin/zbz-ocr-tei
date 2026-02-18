#!/usr/bin/env python3
"""
TEI-Transformation: OCR-Output → TEI-XML

Transformiert Markdown-OCR-Ausgabe in TEI-XML nach DTA-Basisformat
mit projektspezifischen Anpassungen für die Jeanne Hersch Edition.

Ansatz: Nachgelagerte GND-Verknüpfung (TEI-Struktur zuerst, NER separat)

Usage:
    python scripts/transform_to_tei.py --input output/ocr_results/2310_p2.md --type review
    python scripts/transform_to_tei.py --doc 2310 --type review
"""

import argparse
import re
from pathlib import Path

from scripts.config import OCR_RESULTS_DIR, TEI_DIR, DOC_TYPES, KNOWN_ENTITIES


def normalize_text(text: str) -> str:
    """
    Normalisiert Text nach TEI-Mapping.md Regeln.
    """
    # Typografische Anführungszeichen (vorerst deaktiviert - komplexere Logik nötig)
    # text = re.sub(r'"([^"]*)"', '"\g<1>"', text)
    # text = re.sub(r"'([^']*)'", ''\g<1>'', text)

    # Gedankenstriche (Bindestrich-Minus zu Halbgeviertstrich wenn von Leerzeichen umgeben)
    text = re.sub(r' - ', ' – ', text)

    # Französische Apostrophe
    text = re.sub(r"(\w)'(\w)", r"\1'\2", text)

    return text


def detect_structure(text: str) -> dict:
    """
    Erkennt Strukturelemente im Text.

    Returns:
        dict mit erkannten Strukturen (paragraphs, italics, etc.)
    """
    lines = text.strip().split('\n')

    structure = {
        "paragraphs": [],
        "head": None,
        "has_bibliographic_head": False,
    }

    current_para = []

    for line in lines:
        line = line.strip()

        if not line:
            # Leere Zeile = Absatzende
            if current_para:
                para_text = ' '.join(current_para)
                structure["paragraphs"].append(para_text)
                current_para = []
        else:
            current_para.append(line)

    # Letzter Absatz
    if current_para:
        structure["paragraphs"].append(' '.join(current_para))

    # Erster Absatz als Head erkennen (bei Rezensionen: bibliografische Angabe)
    if structure["paragraphs"]:
        first = structure["paragraphs"][0]
        # Typische Rezensions-Header: "Autor, Titel, Verlag, Jahr, Seiten"
        if re.search(r'\d{4}.*\d+\s*p\.?', first) or re.search(r'trad\. de|Paris|Verlag', first):
            structure["head"] = first
            structure["has_bibliographic_head"] = True
            structure["paragraphs"] = structure["paragraphs"][1:]

    return structure


def detect_italics(text: str) -> str:
    """
    Erkennt potenzielle Kursivierung basierend auf Kontext.

    Heuristik:
    - Werktitel in Klammern: (Orientation dans le monde)
    - Fremdwörter: hic et nunc, quer zur Zeit
    - Hervorhebungen nach Doppelpunkt
    """
    # Werktitel in Klammern (französisch)
    text = re.sub(
        r'\(([A-Z][^)]{3,})\)',
        r'(<hi rendition="#i">\1</hi>)',
        text
    )

    # Bekannte fremdsprachige Ausdrücke
    foreign_phrases = [
        r'hic et nunc',
        r'quer zur Zeit',
        r'a priori',
        r'a posteriori',
    ]
    for phrase in foreign_phrases:
        text = re.sub(
            rf'\b({phrase})\b',
            r'<hi rendition="#i">\1</hi>',
            text,
            flags=re.IGNORECASE
        )

    return text


def mark_entities(text: str, add_gnd: bool = False) -> str:
    """
    Markiert bekannte Entitäten im Text.

    Args:
        text: Eingabetext
        add_gnd: Wenn True, werden GND-IDs hinzugefügt (aus Seed-Liste)
    """
    # Sortiere nach Länge (längere Namen zuerst, um "Karl Jaspers" vor "Jaspers" zu matchen)
    sorted_entities = sorted(KNOWN_ENTITIES.items(), key=lambda x: len(x[0]), reverse=True)

    # Bereits markierte Positionen tracken
    marked_positions = set()

    for name, gnd_id in sorted_entities:
        if add_gnd:
            replacement = f'<persName ref="{gnd_id}">{name}</persName>'
        else:
            replacement = f'<persName>{name}</persName>'

        # Einfaches Wortgrenzen-Matching
        pattern = rf'\b{re.escape(name)}\b'

        # Finde alle Matches und ersetze nur wenn nicht bereits in einem Tag
        def replace_if_not_tagged(match):
            # Prüfe ob Position bereits markiert wurde (Teil eines längeren Namens)
            start, end = match.start(), match.end()
            for pos in marked_positions:
                if pos[0] <= start < pos[1] or pos[0] < end <= pos[1]:
                    return match.group(0)  # Keine Ersetzung

            # Prüfe ob bereits in einem XML-Tag
            before = text[:start]
            if '<persName' in before and '</persName>' not in before[before.rfind('<persName'):]:
                return match.group(0)  # Bereits innerhalb eines Tags

            marked_positions.add((start, end))
            return replacement

        text = re.sub(pattern, replace_if_not_tagged, text)

    return text


def create_tei_xml(
    doc_id: str,
    page_num: int,
    page_label: str,
    structure: dict,
    doc_type: str = "essay",
    add_gnd: bool = False,
) -> str:
    """
    Erstellt TEI-XML aus erkannter Struktur.
    """
    div_type = DOC_TYPES.get(doc_type, 'div n="1"')

    # XML-Header
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">',
        '  <teiHeader>',
        '    <fileDesc>',
        '      <titleStmt>',
        f'        <title type="main">{doc_id}</title>',
        '      </titleStmt>',
        '      <publicationStmt>',
        '        <publisher>tranScriptorium</publisher>',
        '      </publicationStmt>',
        '      <sourceDesc>',
        '        <bibl><publisher>Generated by transform_to_tei.py</publisher></bibl>',
        '      </sourceDesc>',
        '    </fileDesc>',
        '  </teiHeader>',
        '',
        '  <text>',
        '    <body>',
        f'      <{div_type}>',
        f'        <pb facs="#facs_{page_num}" n="{page_label}"/>',
    ]

    # Head (falls vorhanden)
    if structure.get("head"):
        head_text = normalize_text(structure["head"])
        head_text = mark_entities(head_text, add_gnd)

        if structure.get("has_bibliographic_head"):
            xml_parts.append('        <head>')
            xml_parts.append(f'          <bibl corresp="GND:???">')
            xml_parts.append(f'            {head_text}')
            xml_parts.append('          </bibl>')
            xml_parts.append('        </head>')
        else:
            xml_parts.append(f'        <head>{head_text}</head>')

    # Absätze
    for i, para in enumerate(structure["paragraphs"], 1):
        para_text = normalize_text(para)
        para_text = detect_italics(para_text)
        para_text = mark_entities(para_text, add_gnd)

        xml_parts.append(f'        <p facs="#facs_{page_num}_r_{i}">')
        xml_parts.append(f'          {para_text}')
        xml_parts.append('        </p>')

    # XML-Footer
    xml_parts.extend([
        f'      </div>',
        '    </body>',
        '  </text>',
        '</TEI>',
    ])

    return '\n'.join(xml_parts)


def transform_file(
    input_path: Path,
    output_path: Path,
    doc_type: str = "essay",
    add_gnd: bool = False,
) -> dict:
    """
    Transformiert eine OCR-Markdown-Datei zu TEI-XML.

    Returns:
        dict mit Statistiken
    """
    # Dokument-ID und Seitennummer aus Dateiname
    # Format: 2310_p2.md
    match = re.match(r'(\d+)_p(\d+)\.md', input_path.name)
    if match:
        doc_id = match.group(1)
        page_num = int(match.group(2))
    else:
        doc_id = input_path.stem
        page_num = 1

    # Text laden
    text = input_path.read_text(encoding='utf-8')

    # Struktur erkennen
    structure = detect_structure(text)

    # TEI erzeugen
    tei_xml = create_tei_xml(
        doc_id=doc_id,
        page_num=page_num,
        page_label=str(page_num),  # Könnte auch aus Metadaten kommen
        structure=structure,
        doc_type=doc_type,
        add_gnd=add_gnd,
    )

    # Speichern
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tei_xml, encoding='utf-8')

    # Statistiken
    entity_count = len(re.findall(r'<persName', tei_xml))

    return {
        "doc_id": doc_id,
        "page_num": page_num,
        "paragraphs": len(structure["paragraphs"]),
        "has_head": structure.get("head") is not None,
        "entities_marked": entity_count,
        "output_path": str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Transformiert OCR-Output zu TEI-XML"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        help="Pfad zur OCR-Markdown-Datei"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Ausgabepfad für TEI-XML (optional)"
    )
    parser.add_argument(
        "--doc",
        help="Dokument-ID (z.B. 2310) - verarbeitet alle Seiten"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["review", "interview", "essay", "lexicon"],
        default="essay",
        help="Dokumenttyp (default: essay)"
    )
    parser.add_argument(
        "--add-gnd",
        action="store_true",
        help="GND-IDs aus Seed-Liste hinzufügen"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe"
    )

    args = parser.parse_args()

    ocr_dir = OCR_RESULTS_DIR
    tei_dir = TEI_DIR

    results = []

    if args.input:
        # Einzelne Datei
        input_path = args.input
        if args.output:
            output_path = args.output
        else:
            output_path = tei_dir / input_path.with_suffix('.xml').name

        result = transform_file(
            input_path, output_path,
            doc_type=args.type,
            add_gnd=args.add_gnd
        )
        results.append(result)

    elif args.doc:
        # Alle Seiten eines Dokuments
        pattern = f"{args.doc}_p*.md"
        files = sorted(ocr_dir.glob(pattern))

        if not files:
            print(f"Keine Dateien gefunden: {ocr_dir / pattern}")
            return

        for input_path in files:
            output_path = tei_dir / input_path.with_suffix('.xml').name
            result = transform_file(
                input_path, output_path,
                doc_type=args.type,
                add_gnd=args.add_gnd
            )
            results.append(result)

    else:
        parser.print_help()
        return

    # Ausgabe
    print(f"\n{'='*60}")
    print(f"TEI-Transformation abgeschlossen")
    print(f"{'='*60}")
    print(f"Dateien:     {len(results)}")
    print(f"Dokumenttyp: {args.type}")
    print(f"GND-Modus:   {'Mit GND-IDs' if args.add_gnd else 'Ohne GND (nachgelagert)'}")
    print()

    total_paras = sum(r["paragraphs"] for r in results)
    total_entities = sum(r["entities_marked"] for r in results)

    print(f"Absätze:     {total_paras}")
    print(f"Entitäten:   {total_entities}")
    print()

    if args.verbose:
        for r in results:
            print(f"  {r['doc_id']}_p{r['page_num']}: {r['paragraphs']} Absätze, {r['entities_marked']} Entitäten")

    print(f"\nAusgabe: {tei_dir}")


if __name__ == "__main__":
    main()
