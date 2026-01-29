"""
OCR-Evaluationsskript: Vergleicht OCR-Output mit Referenz-TEI.
Berechnet Character Error Rate (CER) und Word Error Rate (WER).
Generiert visuellen HTML-Report mit Diff-Ansicht.
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher, HtmlDiff
import xml.etree.ElementTree as ET

# Projekt-Root hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def extract_text_from_tei(tei_path: Path) -> str:
    """Extrahiert reinen Text aus TEI-XML (ohne Tags)."""
    with open(tei_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # XML parsen
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  Warnung: XML-Parse-Fehler in {tei_path}: {e}")
        # Fallback: Tags mit Regex entfernen
        text = re.sub(r'<[^>]+>', '', content)
        return normalize_text(text)

    # Namespace entfernen fuer einfacheren Zugriff
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}')[1]

    # Text aus body extrahieren
    body = root.find('.//body')
    if body is None:
        return ""

    # Rekursiv Text sammeln
    def get_text(elem):
        text_parts = []
        if elem.text:
            text_parts.append(elem.text)
        for child in elem:
            # Zeilenumbruch bei <lb>
            if child.tag == 'lb':
                # Silbentrennung beachten
                if child.get('break') == 'no':
                    pass  # Kein Leerzeichen bei Silbentrennung
                else:
                    text_parts.append(' ')
            # Seitenumbruch ignorieren
            elif child.tag == 'pb':
                text_parts.append('\n\n')
            else:
                text_parts.append(get_text(child))
            if child.tail:
                text_parts.append(child.tail)
        return ''.join(text_parts)

    return normalize_text(get_text(body))


def normalize_text(text: str) -> str:
    """Normalisiert Text fuer Vergleich."""
    # Mehrfache Leerzeichen/Zeilenumbrueche reduzieren
    text = re.sub(r'\s+', ' ', text)
    # Anfuehrungszeichen normalisieren
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")
    # Guillemets beibehalten (sind korrekt)
    # Whitespace am Anfang/Ende entfernen
    text = text.strip()
    return text


def load_ocr_result(ocr_path: Path) -> str:
    """Laedt OCR-Ergebnis aus Markdown-Datei."""
    if not ocr_path.exists():
        return ""
    text = ocr_path.read_text(encoding='utf-8')
    return normalize_text(text)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Berechnet Character Error Rate (CER) mit Levenshtein-Distanz."""
    if len(reference) == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0

    # Levenshtein-Distanz berechnen
    m, n = len(reference), len(hypothesis)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if reference[i-1] == hypothesis[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    distance = dp[m][n]
    cer = distance / len(reference)
    return cer


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Berechnet Word Error Rate (WER)."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0

    # Levenshtein auf Wortebene
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i-1] == hyp_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    distance = dp[m][n]
    wer = distance / len(ref_words)
    return wer


def find_differences(reference: str, hypothesis: str) -> list:
    """Findet konkrete Unterschiede zwischen Texten."""
    matcher = SequenceMatcher(None, reference, hypothesis)
    differences = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            context_start = max(0, i1 - 20)
            context_end = min(len(reference), i2 + 20)

            differences.append({
                'type': tag,
                'ref_pos': f"{i1}-{i2}",
                'hyp_pos': f"{j1}-{j2}",
                'reference': reference[i1:i2] if i1 < i2 else '',
                'hypothesis': hypothesis[j1:j2] if j1 < j2 else '',
                'context': reference[context_start:context_end]
            })

    return differences


def generate_html_report(results: dict, output_path: Path):
    """Generiert HTML-Report mit visueller Diff-Ansicht."""
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Evaluation Report</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .summary-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .summary-card.warning .value {{ color: #FF9800; }}
        .summary-card.error .value {{ color: #f44336; }}

        .document-section {{
            background: white;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .document-header {{
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .document-header.warning {{ background: #FF9800; }}
        .document-header.error {{ background: #f44336; }}
        .document-header h3 {{ margin: 0; }}
        .document-header .metrics {{
            display: flex;
            gap: 20px;
        }}
        .document-header .metric {{
            text-align: center;
        }}
        .document-header .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}

        .document-body {{
            padding: 20px;
        }}

        .diff-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .diff-panel {{
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }}
        .diff-panel-header {{
            background: #f0f0f0;
            padding: 10px 15px;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
        }}
        .diff-panel-content {{
            padding: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
            background: #fafafa;
        }}

        .errors-list {{
            margin-top: 15px;
        }}
        .error-item {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 10px 15px;
            margin: 10px 0;
        }}
        .error-item .type {{
            font-weight: bold;
            color: #856404;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .error-item .content {{
            margin-top: 5px;
            font-family: monospace;
        }}
        .error-item .ref {{ color: #d32f2f; text-decoration: line-through; }}
        .error-item .hyp {{ color: #388e3c; }}
        .error-item .context {{
            margin-top: 5px;
            font-size: 0.9em;
            color: #666;
        }}

        .toggle-btn {{
            background: #e0e0e0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }}
        .toggle-btn:hover {{ background: #d0d0d0; }}

        .collapsible {{ display: none; }}
        .collapsible.show {{ display: block; }}

        .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OCR Evaluation Report</h1>
        <p>Vergleich von OCR-Output mit Referenz-TEI-Dateien</p>

        <h2>Zusammenfassung</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{results['summary']['total_documents']}</div>
                <div class="label">Dokumente</div>
            </div>
            <div class="summary-card {'warning' if results['summary']['avg_cer'] > 0.05 else '' if results['summary']['avg_cer'] > 0.02 else ''}">
                <div class="value">{results['summary']['avg_cer']*100:.2f}%</div>
                <div class="label">Durchschn. CER</div>
            </div>
            <div class="summary-card">
                <div class="value">{results['summary']['avg_wer']*100:.2f}%</div>
                <div class="label">Durchschn. WER</div>
            </div>
            <div class="summary-card">
                <div class="value">{(1-results['summary']['avg_cer'])*100:.2f}%</div>
                <div class="label">Genauigkeit</div>
            </div>
        </div>
"""

    # Dokument-Details
    html += "<h2>Dokument-Details</h2>"

    for doc_id, doc_data in results['documents'].items():
        cer = doc_data.get('cer', 0)
        header_class = 'error' if cer > 0.1 else 'warning' if cer > 0.02 else ''

        html += f"""
        <div class="document-section">
            <div class="document-header {header_class}">
                <h3>{doc_id}</h3>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{cer*100:.2f}%</div>
                        <div>CER</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{doc_data.get('wer', 0)*100:.2f}%</div>
                        <div>WER</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{doc_data.get('ref_chars', 0)}</div>
                        <div>Zeichen (aligned)</div>
                    </div>
                </div>
            </div>
            <div class="document-body">
                <button class="toggle-btn" onclick="toggleSection('{doc_id}-diff')">Textvergleich anzeigen</button>
                <button class="toggle-btn" onclick="toggleSection('{doc_id}-errors')">Fehler anzeigen ({len(doc_data.get('differences', []))})</button>

                <div id="{doc_id}-diff" class="collapsible">
                    <div class="diff-container">
                        <div class="diff-panel">
                            <div class="diff-panel-header">Referenz (TEI)</div>
                            <div class="diff-panel-content">{doc_data.get('reference_text', '')[:2000]}{'...' if len(doc_data.get('reference_text', '')) > 2000 else ''}</div>
                        </div>
                        <div class="diff-panel">
                            <div class="diff-panel-header">OCR-Output</div>
                            <div class="diff-panel-content">{doc_data.get('ocr_text', '')[:2000]}{'...' if len(doc_data.get('ocr_text', '')) > 2000 else ''}</div>
                        </div>
                    </div>
                </div>

                <div id="{doc_id}-errors" class="collapsible errors-list">
"""

        # Fehler auflisten (max 20)
        for diff in doc_data.get('differences', [])[:20]:
            ref_text = diff.get('reference', '').replace('<', '&lt;').replace('>', '&gt;')
            hyp_text = diff.get('hypothesis', '').replace('<', '&lt;').replace('>', '&gt;')
            context = diff.get('context', '').replace('<', '&lt;').replace('>', '&gt;')

            html += f"""
                    <div class="error-item">
                        <div class="type">{diff.get('type', 'unknown')}</div>
                        <div class="content">
                            <span class="ref">{ref_text if ref_text else '(leer)'}</span>
                            &rarr;
                            <span class="hyp">{hyp_text if hyp_text else '(leer)'}</span>
                        </div>
                        <div class="context">Kontext: ...{context}...</div>
                    </div>
"""

        if len(doc_data.get('differences', [])) > 20:
            html += f'<p>... und {len(doc_data["differences"]) - 20} weitere Unterschiede</p>'

        html += """
                </div>
            </div>
        </div>
"""

    # Footer
    html += f"""
        <div class="timestamp">
            Generiert am {results['timestamp']}
        </div>
    </div>

    <script>
        function toggleSection(id) {{
            const elem = document.getElementById(id);
            elem.classList.toggle('show');
        }}
    </script>
</body>
</html>
"""

    output_path.write_text(html, encoding='utf-8')
    print(f"HTML-Report gespeichert: {output_path}")


def find_best_alignment(reference: str, ocr_text: str, window_size: int = 100) -> tuple:
    """
    Findet die beste Ausrichtung zwischen OCR-Text und Referenztext.
    Zwei Szenarien:
    1. OCR ist Teilmenge der Referenz (OCR deckt nur einige Seiten ab)
    2. Referenz ist Teilmenge der OCR (OCR enthaelt mehr als das Dokument)

    Gibt (ref_start, ref_end, ocr_start, ocr_end, matched_reference, matched_ocr) zurueck.
    """
    if len(ocr_text) < 50 or len(reference) < 50:
        return (0, len(reference), 0, len(ocr_text), reference, ocr_text)

    ref_words = reference.split()
    ocr_words = ocr_text.split()

    if len(ref_words) < 5 or len(ocr_words) < 5:
        return (0, len(reference), 0, len(ocr_text), reference, ocr_text)

    # Strategie: Suche markante Phrasen aus der Referenz im OCR und umgekehrt

    # 1. Anfang der Referenz im OCR finden
    ref_start_phrase = ' '.join(ref_words[:8])
    ocr_start_pos = ocr_text.find(ref_start_phrase)

    # 2. Ende der Referenz im OCR finden
    ref_end_phrase = ' '.join(ref_words[-8:])
    ocr_end_pos = ocr_text.find(ref_end_phrase)

    if ocr_start_pos != -1 and ocr_end_pos != -1:
        # Referenz ist im OCR enthalten - OCR zuschneiden
        ocr_end_pos = ocr_end_pos + len(ref_end_phrase)
        matched_ocr = ocr_text[ocr_start_pos:ocr_end_pos]
        return (0, len(reference), ocr_start_pos, ocr_end_pos, reference, matched_ocr)

    # 3. Alternativ: Anfang des OCR in der Referenz finden
    ocr_start_phrase = ' '.join(ocr_words[:8])
    ref_start_pos = reference.find(ocr_start_phrase)

    # 4. Ende des OCR in der Referenz finden
    ocr_end_phrase = ' '.join(ocr_words[-8:])
    ref_end_pos = reference.find(ocr_end_phrase)

    if ref_start_pos != -1:
        # OCR-Anfang gefunden - Referenz ab dort verwenden
        if ref_end_pos != -1 and ref_end_pos > ref_start_pos:
            ref_end_pos = ref_end_pos + len(ocr_end_phrase)
        else:
            ref_end_pos = min(ref_start_pos + len(ocr_text) + 200, len(reference))

        matched_ref = reference[ref_start_pos:ref_end_pos]
        return (ref_start_pos, ref_end_pos, 0, len(ocr_text), matched_ref, ocr_text)

    # Fallback: Kuerzeren Text als Basis nehmen
    if len(ocr_text) < len(reference):
        # OCR ist kuerzer - versuche Woerter einzeln zu matchen
        for i in range(min(20, len(ocr_words))):
            word = ocr_words[i]
            if len(word) > 5:
                pos = reference.find(word)
                if pos != -1:
                    # Gefunden! Von hier aus matchen
                    end_pos = min(pos + len(ocr_text) + 200, len(reference))
                    matched_ref = reference[pos:end_pos]
                    return (pos, end_pos, 0, len(ocr_text), matched_ref, ocr_text)

    # Kein gutes Alignment gefunden
    return (0, len(reference), 0, len(ocr_text), reference, ocr_text)


def evaluate_document(doc_id: str, tei_dir: Path, ocr_dir: Path) -> dict:
    """Evaluiert ein einzelnes Dokument."""
    result = {
        'doc_id': doc_id,
        'status': 'OK',
        'cer': 0.0,
        'wer': 0.0,
        'ref_chars': 0,
        'ocr_chars': 0,
        'differences': [],
        'reference_text': '',
        'ocr_text': '',
        'alignment_info': ''
    }

    # TEI-Datei finden
    tei_path = tei_dir / f"{doc_id}.xml"
    if not tei_path.exists():
        # Auch im Pilot-Ordner suchen
        tei_path = tei_dir / "Pilot" / f"{doc_id}.xml"

    if not tei_path.exists():
        result['status'] = 'SKIP'
        result['error'] = f"TEI nicht gefunden: {doc_id}.xml"
        return result

    # OCR-Dateien finden (koennen mehrere Seiten sein)
    ocr_files = sorted(ocr_dir.glob(f"{doc_id}_p*.md"))
    if not ocr_files:
        result['status'] = 'SKIP'
        result['error'] = f"OCR nicht gefunden: {doc_id}_p*.md"
        return result

    # Texte laden
    full_reference = extract_text_from_tei(tei_path)

    ocr_texts = []
    for ocr_file in ocr_files:
        ocr_texts.append(load_ocr_result(ocr_file))
    ocr_combined = ' '.join(ocr_texts)

    # Alignment finden - OCR deckt nur Teilbereich ab oder enthaelt mehr
    ref_start, ref_end, ocr_start, ocr_end, aligned_reference, aligned_ocr = find_best_alignment(full_reference, ocr_combined)

    ref_coverage = ((ref_end - ref_start) / len(full_reference) * 100) if len(full_reference) > 0 else 0
    ocr_coverage = ((ocr_end - ocr_start) / len(ocr_combined) * 100) if len(ocr_combined) > 0 else 0

    result['alignment_info'] = f"Ref[{ref_start}:{ref_end}] ({ref_coverage:.1f}%), OCR[{ocr_start}:{ocr_end}] ({ocr_coverage:.1f}%)"
    result['reference_text'] = aligned_reference
    result['ocr_text'] = aligned_ocr
    result['ref_chars'] = len(aligned_reference)
    result['ocr_chars'] = len(aligned_ocr)
    result['full_ref_chars'] = len(full_reference)
    result['full_ocr_chars'] = len(ocr_combined)

    # Metriken auf aligniertem Text berechnen
    result['cer'] = calculate_cer(aligned_reference, aligned_ocr)
    result['wer'] = calculate_wer(aligned_reference, aligned_ocr)

    # Unterschiede finden
    result['differences'] = find_differences(aligned_reference, aligned_ocr)

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OCR-Evaluation: Vergleicht OCR mit Referenz-TEI")
    parser.add_argument("--docs", nargs='+', help="Spezifische Dokument-IDs (z.B. 2310 1180)")
    parser.add_argument("--all", action="store_true", help="Alle verfuegbaren Dokumente evaluieren")
    parser.add_argument("--output", default="evaluation_report.html", help="Name der HTML-Report-Datei")
    args = parser.parse_args()

    # Pfade
    tei_dir = PROJECT_ROOT / "data" / "referenz-tei"
    ocr_dir = PROJECT_ROOT / "output" / "ocr_results"
    output_dir = PROJECT_ROOT / "output" / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dokumente bestimmen
    if args.docs:
        doc_ids = args.docs
    elif args.all:
        # Alle OCR-Ergebnisse finden
        ocr_files = list(ocr_dir.glob("*_p*.md"))
        doc_ids = sorted(set(f.stem.rsplit('_p', 1)[0] for f in ocr_files))
    else:
        # Default: Nur 2310 als Beispiel
        doc_ids = ['2310']

    print(f"OCR-Evaluation")
    print(f"==============")
    print(f"Dokumente: {', '.join(doc_ids)}")
    print()

    # Evaluieren
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'documents': {},
        'summary': {
            'total_documents': 0,
            'evaluated': 0,
            'skipped': 0,
            'avg_cer': 0.0,
            'avg_wer': 0.0
        }
    }

    cer_values = []
    wer_values = []

    for doc_id in doc_ids:
        print(f"Evaluiere: {doc_id}")
        doc_result = evaluate_document(doc_id, tei_dir, ocr_dir)
        results['documents'][doc_id] = doc_result
        results['summary']['total_documents'] += 1

        if doc_result['status'] == 'OK':
            results['summary']['evaluated'] += 1
            cer_values.append(doc_result['cer'])
            wer_values.append(doc_result['wer'])
            print(f"  CER: {doc_result['cer']*100:.2f}%, WER: {doc_result['wer']*100:.2f}%")
            print(f"  Alignment: {doc_result.get('alignment_info', 'N/A')}")
            print(f"  Referenz (aligned): {doc_result['ref_chars']} Zeichen, OCR: {doc_result['ocr_chars']} Zeichen")
            print(f"  Unterschiede: {len(doc_result['differences'])}")
        else:
            results['summary']['skipped'] += 1
            print(f"  [SKIP] {doc_result.get('error', 'Unbekannt')}")
        print()

    # Durchschnitte berechnen
    if cer_values:
        results['summary']['avg_cer'] = sum(cer_values) / len(cer_values)
        results['summary']['avg_wer'] = sum(wer_values) / len(wer_values)

    # JSON speichern
    json_path = output_dir / "evaluation_results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    print(f"JSON-Ergebnisse: {json_path}")

    # HTML-Report generieren
    html_path = output_dir / args.output
    generate_html_report(results, html_path)

    # Zusammenfassung
    print()
    print("=" * 50)
    print("ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"Dokumente: {results['summary']['total_documents']}")
    print(f"Evaluiert: {results['summary']['evaluated']}")
    print(f"Uebersprungen: {results['summary']['skipped']}")
    if cer_values:
        print(f"Durchschn. CER: {results['summary']['avg_cer']*100:.2f}%")
        print(f"Durchschn. WER: {results['summary']['avg_wer']*100:.2f}%")
        print(f"Durchschn. Genauigkeit: {(1-results['summary']['avg_cer'])*100:.2f}%")


if __name__ == "__main__":
    main()
