"""
OCR-Evaluationsskript: Vergleicht OCR-Output mit Referenz-TEI.
Berechnet Character Error Rate (CER) und Word Error Rate (WER).
Generiert visuellen HTML-Report mit Diff-Ansicht.
"""

import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET

from scripts.config import (
    REFERENZ_TEI_DIR, OCR_RESULTS_DIR, EVALUATION_DIR, TESTPLAN,
    TEI_FINAL_DIR,
)
from scripts.utils import get_phase_doc_ids


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


def extract_pages_from_tei(tei_path: Path) -> dict[int, str]:
    """Extrahiert Text pro Seite aus TEI-XML anhand <pb facs='#facs_N'> Tags.

    Gibt ein Dict {page_num: normalized_text} zurueck.
    page_num entspricht der physischen PDF-Seite (= OCR-Datei {doc}_p{page_num}.md).
    """
    with open(tei_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return {}

    # Namespace entfernen
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}')[1]

    body = root.find('.//body')
    if body is None:
        return {}

    # Alle pb-Elemente mit facs-Attribut finden und Seitennummer extrahieren
    pages = {}
    current_page = None
    current_parts = []

    def _flush():
        nonlocal current_page, current_parts
        if current_page is not None and current_parts:
            text = normalize_text(''.join(current_parts))
            if text:
                pages[current_page] = text
        current_parts = []

    def _extract_page_num(elem):
        """Extrahiert Seitennummer aus facs='#facs_N' oder facs='#facs_N_r'."""
        facs = elem.get('facs', '')
        m = re.match(r'#facs_(\d+)', facs)
        return int(m.group(1)) if m else None

    def collect_text(elem):
        nonlocal current_page, current_parts
        if elem.tag == 'pb':
            page_num = _extract_page_num(elem)
            if page_num is not None:
                _flush()
                current_page = page_num
        elif elem.tag == 'lb':
            if elem.get('break') != 'no':
                current_parts.append(' ')
        else:
            if elem.text:
                current_parts.append(elem.text)
            for child in elem:
                collect_text(child)
            # Nicht-pb/lb Elemente: tail gehoert zur aktuellen Seite
        if elem.tail and elem.tag not in ('body',):
            current_parts.append(elem.tail)

    # Body-Kinder traversieren
    if body.text:
        current_parts.append(body.text)
    for child in body:
        collect_text(child)
    _flush()

    return pages


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


def extract_text_for_comparison(tei_path: Path, include_footnotes: bool = False) -> str:
    """Extrahiert Text aus TEI-XML fuer CER-Benchmarking.

    Gegenueber extract_text_from_tei mit drei Korrekturen:
    1. <choice>: Nur <corr> extrahieren (nicht sic+corr konkateniert)
    2. <note place="foot">: Optional ausschliessen (Default: exkludiert)
    3. Unicode NFC-Normalisierung fuer konsistenten Diakritika-Vergleich
    """
    with open(tei_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        text = re.sub(r'<[^>]+>', '', content)
        return unicodedata.normalize('NFC', normalize_text(text))

    # Namespace entfernen
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}')[1]
        for attr_key in list(elem.attrib.keys()):
            if '}' in attr_key:
                elem.attrib[attr_key.split('}')[1]] = elem.attrib.pop(attr_key)

    body = root.find('.//body')
    if body is None:
        return ""

    def get_text(elem):
        """Rekursive Textextraktion. Tail wird vom PARENT gehandhabt."""
        parts = []

        # <choice>: Nur corr extrahieren, sic ignorieren
        if elem.tag == 'choice':
            corr = elem.find('corr')
            target = corr if corr is not None else elem.find('sic')
            if target is not None:
                parts.append(get_text(target))
            return ''.join(parts)

        # <note place="foot"> optional exkludieren
        if elem.tag == 'note' and elem.get('place') == 'foot' and not include_footnotes:
            return ''

        if elem.text:
            parts.append(elem.text)

        for child in elem:
            if child.tag == 'lb':
                if child.get('break') != 'no':
                    parts.append(' ')
            elif child.tag == 'pb':
                parts.append('\n\n')
            else:
                parts.append(get_text(child))
            # Tail: immer vom Parent gehandhabt
            if child.tail:
                parts.append(child.tail)

        return ''.join(parts)

    text = get_text(body)
    text = normalize_text(text)
    return unicodedata.normalize('NFC', text)


def load_ocr_result(ocr_path: Path) -> str:
    """Laedt OCR-Ergebnis aus Markdown-Datei."""
    if not ocr_path.exists():
        return ""
    text = ocr_path.read_text(encoding='utf-8')
    return normalize_text(text)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Berechnet Levenshtein-Distanz (Fallback ohne rapidfuzz)."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    return dp[m][n]


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Berechnet Character Error Rate (CER) mit Levenshtein-Distanz."""
    if len(reference) == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0

    try:
        from rapidfuzz.distance import Levenshtein
        distance = Levenshtein.distance(reference, hypothesis)
    except ImportError:
        distance = _levenshtein_distance(reference, hypothesis)

    return distance / len(reference)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Berechnet Word Error Rate (WER)."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0

    try:
        from rapidfuzz.distance import Levenshtein
        distance = Levenshtein.distance(ref_words, hyp_words)
    except ImportError:
        distance = _levenshtein_distance(ref_words, hyp_words)

    return distance / len(ref_words)


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


def _has_diacritic_diff(ref: str, hyp: str) -> bool:
    """Prueft ob sich ref und hyp nur in Diakritika/Akzenten unterscheiden."""
    ref_base = unicodedata.normalize('NFD', ref)
    hyp_base = unicodedata.normalize('NFD', hyp)
    ref_stripped = ''.join(c for c in ref_base if unicodedata.category(c) != 'Mn')
    hyp_stripped = ''.join(c for c in hyp_base if unicodedata.category(c) != 'Mn')
    return ref_stripped == hyp_stripped and ref != hyp


def _is_punctuation_only(text: str) -> bool:
    """Prueft ob Text nur aus Interpunktion/Symbolen besteht."""
    return all(
        unicodedata.category(c).startswith(('P', 'S')) or c in ' \t'
        for c in text
    ) if text else False


def _has_repeated_ngrams(text: str, n: int = 3, threshold: int = 3) -> bool:
    """Erkennt wiederholte n-gramme (OCR-Halluzination)."""
    if len(text) < n * threshold:
        return False
    ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
    from collections import Counter
    counts = Counter(ngrams)
    return any(c >= threshold for c in counts.values())


def categorize_errors(differences: list, ref_length: int) -> dict:
    """Klassifiziert Fehler aus find_differences() in Kategorien.

    Kategorien: diacritics, punctuation, hyphenation, whitespace,
    ocr_artifact, layout, other.
    Gibt pro Kategorie count, cer_contribution und examples zurueck.
    """
    categories = {
        'diacritics': {'count': 0, 'char_distance': 0, 'examples': []},
        'punctuation': {'count': 0, 'char_distance': 0, 'examples': []},
        'hyphenation': {'count': 0, 'char_distance': 0, 'examples': []},
        'whitespace': {'count': 0, 'char_distance': 0, 'examples': []},
        'ocr_artifact': {'count': 0, 'char_distance': 0, 'examples': []},
        'layout': {'count': 0, 'char_distance': 0, 'examples': []},
        'other': {'count': 0, 'char_distance': 0, 'examples': []},
    }

    for diff in differences:
        ref = diff.get('reference', '')
        hyp = diff.get('hypothesis', '')
        diff_type = diff.get('type', '')
        edit_dist = max(len(ref), len(hyp))

        # Klassifikation (erste zutreffende Regel gewinnt)
        if ref.strip() == '' and hyp.strip() == '':
            cat = 'whitespace'
        elif ref.strip() == hyp.strip():
            cat = 'whitespace'
        elif _has_diacritic_diff(ref, hyp):
            cat = 'diacritics'
        elif _is_punctuation_only(ref) and _is_punctuation_only(hyp):
            cat = 'punctuation'
        elif _is_punctuation_only(ref) and hyp == '':
            cat = 'punctuation'
        elif ref == '' and _is_punctuation_only(hyp):
            cat = 'punctuation'
        elif any(c in ref + hyp for c in ['-', '\u00AD', '\u2010', '\u2011']):
            # Bindestrich/Trennstrich involviert
            if len(ref) < 5 and len(hyp) < 5:
                cat = 'hyphenation'
            else:
                cat = 'other'
        elif diff_type == 'insert' and len(hyp) > 50 and _has_repeated_ngrams(hyp):
            cat = 'ocr_artifact'
        elif diff_type == 'insert' and len(hyp) > 80:
            cat = 'layout'
        elif diff_type == 'delete' and len(ref) > 80:
            cat = 'layout'
        elif diff_type in ('insert', 'delete') and len(ref) + len(hyp) > 40:
            # Groessere Inserts/Deletes: eher Layout/Struktur
            cat = 'layout'
        else:
            cat = 'other'

        categories[cat]['count'] += 1
        categories[cat]['char_distance'] += edit_dist

        if len(categories[cat]['examples']) < 3:
            categories[cat]['examples'].append({
                'ref': ref[:80],
                'hyp': hyp[:80],
                'type': diff_type,
            })

    # CER-Beitrag pro Kategorie berechnen
    for cat_data in categories.values():
        cat_data['cer_contribution'] = (
            cat_data['char_distance'] / ref_length if ref_length > 0 else 0.0
        )

    return categories


def generate_html_report(results: dict, output_path: Path):
    """Generiert HTML-Report mit visueller Diff-Ansicht."""
    engine_label = results.get('engine', 'OCR').capitalize()
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Evaluation Report - {engine_label}</title>
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
        <h1>OCR Evaluation Report - {engine_label}</h1>
        <p>Vergleich von {engine_label}-Output mit Referenz-TEI-Dateien</p>

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


def _strip_markdown(text: str) -> str:
    """Entfernt Markdown-Formatierung fuer Alignment-Suche."""
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)  # *bold* / **bold**
    text = re.sub(r'_+([^_]+)_+', r'\1', text)    # _italic_
    text = re.sub(r'#+\s*', '', text)               # ## headers
    return text


def _find_phrase_in_text(phrase: str, text: str) -> int:
    """Sucht Phrase im Text, auch mit Markdown-Unterschieden."""
    pos = text.find(phrase)
    if pos != -1:
        return pos
    # Fallback: Ohne Markdown suchen
    clean_text = _strip_markdown(text)
    clean_phrase = _strip_markdown(phrase)
    pos = clean_text.find(clean_phrase)
    return pos


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

    # Wenn Laengen sehr aehnlich sind (Faktor < 1.05), vergleiche direkt
    len_ratio = max(len(reference), len(ocr_text)) / max(min(len(reference), len(ocr_text)), 1)
    if len_ratio < 1.05:
        return (0, len(reference), 0, len(ocr_text), reference, ocr_text)

    # Strategie: Suche markante Phrasen, mit abnehmender Laenge

    # 1. Anfang der Referenz im OCR finden (probiere 8, 5, 3 Woerter)
    ocr_start_pos = -1
    for n_words in [8, 5, 3]:
        ref_start_phrase = ' '.join(ref_words[:n_words])
        ocr_start_pos = _find_phrase_in_text(ref_start_phrase, ocr_text)
        if ocr_start_pos != -1:
            break

    # 2. Ende der Referenz im OCR finden
    ocr_end_pos = -1
    for n_words in [8, 5, 3]:
        ref_end_phrase = ' '.join(ref_words[-n_words:])
        ocr_end_pos = _find_phrase_in_text(ref_end_phrase, ocr_text)
        if ocr_end_pos != -1:
            ocr_end_pos = ocr_end_pos + len(ref_end_phrase)
            break

    if ocr_start_pos != -1 and ocr_end_pos != -1 and ocr_end_pos > ocr_start_pos:
        matched_ocr = ocr_text[ocr_start_pos:ocr_end_pos]
        return (0, len(reference), ocr_start_pos, ocr_end_pos, reference, matched_ocr)

    if ocr_start_pos != -1:
        # Anfang gefunden, Ende schaetzen
        estimated_end = min(ocr_start_pos + len(reference) + 200, len(ocr_text))
        matched_ocr = ocr_text[ocr_start_pos:estimated_end]
        return (0, len(reference), ocr_start_pos, estimated_end, reference, matched_ocr)

    # 3. Alternativ: Anfang des OCR in der Referenz finden
    ref_start_pos = -1
    for n_words in [8, 5, 3]:
        ocr_start_phrase = ' '.join(ocr_words[:n_words])
        ref_start_pos = _find_phrase_in_text(ocr_start_phrase, reference)
        if ref_start_pos != -1:
            break

    if ref_start_pos != -1:
        ref_end_pos = -1
        for n_words in [8, 5, 3]:
            ocr_end_phrase = ' '.join(ocr_words[-n_words:])
            ref_end_pos = _find_phrase_in_text(ocr_end_phrase, reference)
            if ref_end_pos != -1:
                ref_end_pos = ref_end_pos + len(ocr_end_phrase)
                break

        if ref_end_pos == -1 or ref_end_pos <= ref_start_pos:
            ref_end_pos = min(ref_start_pos + len(ocr_text) + 200, len(reference))

        matched_ref = reference[ref_start_pos:ref_end_pos]
        return (ref_start_pos, ref_end_pos, 0, len(ocr_text), matched_ref, ocr_text)

    # Fallback: Einzelne lange Woerter suchen
    for words, text, is_ref in [(ref_words, ocr_text, True), (ocr_words, reference, False)]:
        for i in range(min(30, len(words))):
            word = words[i]
            if len(word) > 8:  # Nur markante Woerter
                pos = text.find(word)
                if pos != -1:
                    if is_ref:
                        estimated_end = min(pos + len(reference) + 200, len(ocr_text))
                        matched_ocr = ocr_text[pos:estimated_end]
                        return (0, len(reference), pos, estimated_end, reference, matched_ocr)
                    else:
                        estimated_end = min(pos + len(ocr_text) + 200, len(reference))
                        matched_ref = reference[pos:estimated_end]
                        return (pos, estimated_end, 0, len(ocr_text), matched_ref, ocr_text)

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

    # TEI-Datei finden (mit Fuzzy-Lookup fuer Sondernamen wie "1520 - in Arbeit.xml")
    tei_path = tei_dir / f"{doc_id}.xml"
    if not tei_path.exists():
        tei_path = tei_dir / "Pilot" / f"{doc_id}.xml"
    if not tei_path.exists():
        # Glob-Fallback: Suche nach Dateien die mit doc_id beginnen
        candidates = list(tei_dir.glob(f"**/{doc_id}*.xml"))
        if candidates:
            tei_path = candidates[0]

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


def _find_tei_path(doc_id: str, tei_dir: Path) -> Path | None:
    """Findet TEI-Datei fuer ein Dokument (mit Fuzzy-Lookup)."""
    tei_path = tei_dir / f"{doc_id}.xml"
    if tei_path.exists():
        return tei_path
    tei_path = tei_dir / "Pilot" / f"{doc_id}.xml"
    if tei_path.exists():
        return tei_path
    candidates = list(tei_dir.glob(f"**/{doc_id}*.xml"))
    if candidates:
        return candidates[0]
    return None


def _match_tei_to_ocr(tei_pages: dict[int, str], ocr_by_page: dict[int, Path]) -> dict[int, int]:
    """Matcht TEI-Seiten auf OCR-Seiten per Content-Matching.

    Erkennt zunaechst einen initialen Offset anhand der ersten TEI-Seite,
    dann validiert und passt den Offset seitenweise an (fuer Dokumente
    mit Leerseiten/Illustrationen die den Offset verschieben).

    Gibt ein Dict {tei_page_num: ocr_page_num} zurueck.
    """
    # Preload OCR texts
    ocr_texts = {}
    for num, path in ocr_by_page.items():
        ocr_texts[num] = load_ocr_result(path)

    def _score(ref_text, ocr_text):
        """Zaehlt uebereinstimmende Woerter (>5 Zeichen) als Matching-Score."""
        words = [w for w in ref_text.split() if len(w) > 5][:8]
        if not words:
            return 0
        return sum(1 for w in words if w.lower() in ocr_text.lower())

    def _find_best_ocr(ref_text, search_range):
        """Findet die beste OCR-Seite fuer einen TEI-Text im gegebenen Bereich."""
        best_num = None
        best_score = 0
        for ocr_num in search_range:
            if ocr_num not in ocr_texts:
                continue
            score = _score(ref_text, ocr_texts[ocr_num])
            if score > best_score:
                best_score = score
                best_num = ocr_num
        return best_num, best_score

    mapping = {}
    current_offset = 0
    offset_found = False

    for tei_num in sorted(tei_pages.keys()):
        ref_text = tei_pages[tei_num]
        if len(ref_text) < 50:
            continue

        if not offset_found:
            # Initialen Offset ueber breiten Bereich suchen
            best_num, best_score = _find_best_ocr(ref_text, range(1, max(ocr_by_page.keys()) + 1))
            if best_num is not None and best_score >= 2:
                current_offset = best_num - tei_num
                offset_found = True
                mapping[tei_num] = best_num
                continue

        # Erwartete OCR-Seite plus Suchfenster fuer Drift
        expected = tei_num + current_offset
        search = range(max(1, expected - 2), expected + 4)
        best_num, best_score = _find_best_ocr(ref_text, search)

        if best_num is not None and best_score >= 2:
            mapping[tei_num] = best_num
            current_offset = best_num - tei_num
        elif expected in ocr_texts:
            # Fallback: Erwartete Seite nehmen, auch ohne starken Score
            mapping[tei_num] = expected

    return mapping


def evaluate_document_pagewise(doc_id: str, tei_dir: Path, ocr_dir: Path) -> dict:
    """Seitenweiser CER/WER-Vergleich fuer lange Dokumente (Monografien).

    Matcht jede TEI-Seite (<pb facs='#facs_N'>) per Content-Matching auf die
    passende OCR-Seite und berechnet CER/WER pro Seite. Behandelt automatisch
    Seitenversatz und Drift durch Leerseiten/Illustrationen im PDF.
    """
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
        'alignment_info': '',
        'pagewise': True,
        'page_results': []
    }

    # TEI-Datei finden
    tei_path = _find_tei_path(doc_id, tei_dir)
    if tei_path is None:
        result['status'] = 'SKIP'
        result['error'] = f"TEI nicht gefunden: {doc_id}.xml"
        return result

    # OCR-Dateien finden
    ocr_files = sorted(ocr_dir.glob(f"{doc_id}_p*.md"))
    if not ocr_files:
        result['status'] = 'SKIP'
        result['error'] = f"OCR nicht gefunden: {doc_id}_p*.md"
        return result

    # TEI seitenweise extrahieren
    tei_pages = extract_pages_from_tei(tei_path)
    if not tei_pages:
        result['status'] = 'SKIP'
        result['error'] = f"Keine <pb>-Tags in TEI gefunden: {tei_path.name}"
        return result

    # OCR-Dateien nach Seitennummer indexieren
    ocr_by_page = {}
    for ocr_file in ocr_files:
        m = re.match(rf'{re.escape(doc_id)}_p(\d+)\.md$', ocr_file.name)
        if m:
            ocr_by_page[int(m.group(1))] = ocr_file

    # Content-basiertes Seiten-Matching
    page_mapping = _match_tei_to_ocr(tei_pages, ocr_by_page)

    # Seitenweise vergleichen
    total_cer_weighted = 0.0
    total_wer_weighted = 0.0
    total_ref_chars = 0
    total_ocr_chars = 0
    matched_pages = 0
    all_diffs = []

    for tei_num in sorted(page_mapping.keys()):
        ref_text = tei_pages[tei_num]
        if not ref_text.strip():
            continue

        ocr_num = page_mapping[tei_num]
        ocr_text = load_ocr_result(ocr_by_page[ocr_num])
        if not ocr_text.strip():
            continue

        cer = calculate_cer(ref_text, ocr_text)
        wer = calculate_wer(ref_text, ocr_text)
        weight = len(ref_text)

        total_cer_weighted += cer * weight
        total_wer_weighted += wer * weight
        total_ref_chars += len(ref_text)
        total_ocr_chars += len(ocr_text)
        matched_pages += 1

        result['page_results'].append({
            'page': tei_num,
            'ocr_page': ocr_num,
            'cer': cer,
            'wer': wer,
            'ref_chars': len(ref_text),
            'ocr_chars': len(ocr_text)
        })

        if cer > 0.05 and len(all_diffs) < 30:
            diffs = find_differences(ref_text, ocr_text)
            for d in diffs[:5]:
                d['page'] = tei_num
            all_diffs.extend(diffs[:5])

    if total_ref_chars == 0:
        result['status'] = 'SKIP'
        result['error'] = "Keine uebereinstimmenden Seiten gefunden"
        return result

    result['cer'] = total_cer_weighted / total_ref_chars
    result['wer'] = total_wer_weighted / total_ref_chars
    result['ref_chars'] = total_ref_chars
    result['ocr_chars'] = total_ocr_chars
    result['differences'] = all_diffs[:20]
    result['alignment_info'] = (
        f"Seitenweise: {matched_pages}/{len(tei_pages)} TEI-Seiten matched, "
        f"{len(tei_pages) - matched_pages} ohne Match, "
        f"{len(ocr_by_page)} OCR-Seiten"
    )

    return result


def compute_proxy_quality(doc_id: str) -> dict:
    """Berechnet Proxy-Qualitaetsmetriken fuer Docs ohne Ground Truth.

    Basiert auf Screening-Daten (Review-JSONs) und strukturellen Signalen.
    """
    result = {
        'doc_id': doc_id,
        'proxy_score': None,
        'confidence': 'low',
        'signals': {},
        'estimated_cer_bucket': 'unknown',
    }

    # Review-JSON laden
    review_path = TEI_FINAL_DIR / f"{doc_id}_review.json"
    if not review_path.exists():
        return result

    review = json.loads(review_path.read_text(encoding='utf-8'))
    layers = review.get('layers', {})

    # Signal-Extraktion
    score_map = {'ok': 1.0, 'warning': 0.5, 'n/a': None}

    # v2-Format (mit layers)
    l2_score = score_map.get(layers.get('L2_ocr', {}).get('score'), None)
    l7_score = score_map.get(layers.get('L7_coherence', {}).get('score'), None)
    l4_score = score_map.get(layers.get('L4_tei', {}).get('score'), None)

    # v1-Fallback (ohne layers): aus Findings und Validator-Status ableiten
    if not layers:
        status = review.get('status', '')
        if status in ('APPROVED', 'APPROVED_WITH_NOTES'):
            # v1 APPROVED: moderate Vertrauenswuerdigkeit
            validator_str = review.get('validator', '')
            if 'VALID' in validator_str and '0 errors' in validator_str:
                l4_score = 1.0
            elif 'VALID' in validator_str:
                l4_score = 0.8
            # Aus Findings OCR-Probleme erkennen
            findings_v1 = review.get('findings', [])
            ocr_findings = [f for f in findings_v1 if f.get('code', '').startswith(('E', 'L2'))]
            if not ocr_findings:
                l2_score = 0.85  # Kein OCR-Problem gemeldet
            else:
                l2_score = 0.5

    # Validator-Warnungen zaehlen
    raw_warnings = layers.get('L4_tei', {}).get('validator_warnings', [])
    l4_warnings = len(raw_warnings) if isinstance(raw_warnings, list) else int(raw_warnings or 0)
    if l4_score == 1.0 and l4_warnings > 0:
        l4_score = 0.8

    # Findings zaehlen
    findings = review.get('findings', [])
    warning_count = len([f for f in findings
                         if isinstance(f, dict) and
                         f.get('severity') in ('warning', 'error')])

    # OCR-Keywords in Notes (v2: L2-Notes, v1: alle findings)
    ocr_keywords = ['Halluzination', 'halluzin', 'repetitiv', 'OCR-Fehler',
                    'Artefakt', 'unleserlich', 'verstummelt', 'Zeichensalat']
    notes_text = layers.get('L2_ocr', {}).get('notes', '')
    if not notes_text:
        notes_text = ' '.join(f.get('msg', '') for f in findings)
    found_keywords = [kw for kw in ocr_keywords if kw.lower() in notes_text.lower()]

    result['signals'] = {
        'l2_ocr': layers.get('L2_ocr', {}).get('score', '?'),
        'l7_coherence': layers.get('L7_coherence', {}).get('score', '?'),
        'l4_tei': layers.get('L4_tei', {}).get('score', '?'),
        'l4_warning_count': l4_warnings,
        'finding_count': warning_count,
        'ocr_keywords_found': found_keywords,
        'review_status': review.get('status', '?'),
        'review_version': 'v2' if layers else 'v1',
    }

    # Proxy-Score berechnen (gewichteter Durchschnitt der verfuegbaren Signale)
    scores = []
    weights = []
    if l2_score is not None:
        scores.append(l2_score)
        weights.append(3.0)  # OCR-Score am wichtigsten
    if l7_score is not None:
        scores.append(l7_score)
        weights.append(2.0)
    if l4_score is not None:
        scores.append(l4_score)
        weights.append(1.0)

    # Malus fuer OCR-Keywords
    keyword_penalty = min(len(found_keywords) * 0.15, 0.5)
    # Malus fuer Findings
    finding_penalty = min(warning_count * 0.05, 0.3)

    if scores:
        weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        result['proxy_score'] = max(0.0, weighted_avg - keyword_penalty - finding_penalty)
        result['confidence'] = 'high' if len(scores) >= 2 else 'medium'

        # CER-Bucket schaetzen
        ps = result['proxy_score']
        if ps >= 0.9:
            result['estimated_cer_bucket'] = 'excellent'
        elif ps >= 0.7:
            result['estimated_cer_bucket'] = 'good'
        elif ps >= 0.4:
            result['estimated_cer_bucket'] = 'fair'
        else:
            result['estimated_cer_bucket'] = 'poor'

    return result


def evaluate_tei_vs_tei(doc_id: str, ref_dir: Path, pipeline_dir: Path) -> dict:
    """End-to-End CER/WER: Vergleicht Referenz-TEI mit Pipeline-TEI.

    Extrahiert Text aus beiden TEI-XMLs mit extract_text_for_comparison(),
    verwendet Alignment bei Laengendifferenz, und kategorisiert Fehlermuster.
    """
    result = {
        'doc_id': doc_id,
        'status': 'OK',
        'comparison_type': 'tei_vs_tei',
        'cer': 0.0,
        'wer': 0.0,
        'ref_chars': 0,
        'hyp_chars': 0,
        'footnote_cer': None,
        'error_categories': {},
        'differences': [],
        'alignment_info': '',
    }

    # Referenz-TEI finden
    ref_path = _find_tei_path(doc_id, ref_dir)
    if ref_path is None:
        result['status'] = 'SKIP'
        result['error'] = f"Referenz-TEI nicht gefunden: {doc_id}"
        return result

    # Pipeline-TEI finden
    pipe_path = pipeline_dir / f"{doc_id}_final.xml"
    if not pipe_path.exists():
        # Fallback ohne _final Suffix
        pipe_path = pipeline_dir / f"{doc_id}.xml"
    if not pipe_path.exists():
        result['status'] = 'SKIP'
        result['error'] = f"Pipeline-TEI nicht gefunden: {doc_id}"
        return result

    # Text extrahieren (ohne Fussnoten fuer Hauptvergleich)
    ref_text = extract_text_for_comparison(ref_path, include_footnotes=False)
    pipe_text = extract_text_for_comparison(pipe_path, include_footnotes=False)

    if not ref_text:
        result['status'] = 'SKIP'
        result['error'] = f"Referenz-TEI leer: {ref_path.name}"
        return result

    # Alignment bei Laengendifferenz (>5%)
    len_ratio = max(len(ref_text), len(pipe_text)) / max(min(len(ref_text), len(pipe_text)), 1)
    if len_ratio > 1.05:
        _, _, _, _, aligned_ref, aligned_pipe = find_best_alignment(ref_text, pipe_text)
        result['alignment_info'] = (
            f"Aligned: ref {len(ref_text)}->{len(aligned_ref)}, "
            f"pipe {len(pipe_text)}->{len(aligned_pipe)} "
            f"(ratio {len_ratio:.2f})"
        )
        ref_text = aligned_ref
        pipe_text = aligned_pipe
    else:
        result['alignment_info'] = f"Direkt: ref={len(ref_text)}, pipe={len(pipe_text)}"

    # CER / WER
    result['cer'] = calculate_cer(ref_text, pipe_text)
    result['wer'] = calculate_wer(ref_text, pipe_text)
    result['ref_chars'] = len(ref_text)
    result['hyp_chars'] = len(pipe_text)

    # Alignment-Mismatch erkennen (CER > 50% = vermutlich anderer Text)
    if result['cer'] > 0.50:
        result['status'] = 'MISMATCH'
        result['alignment_info'] += ' [MISMATCH: CER > 50%, vermutlich Textabweichung]'

    # Fussnoten-CER separat (inkl. vs. exkl. Fussnoten)
    ref_with_fn = extract_text_for_comparison(ref_path, include_footnotes=True)
    pipe_with_fn = extract_text_for_comparison(pipe_path, include_footnotes=True)
    if len(ref_with_fn) > len(ref_text) + 20:
        result['footnote_cer'] = calculate_cer(ref_with_fn, pipe_with_fn)
        result['cer_incl_footnotes'] = result['footnote_cer']

    # Fehlerkategorien
    diffs = find_differences(ref_text, pipe_text)
    result['differences'] = diffs[:30]
    result['error_categories'] = categorize_errors(diffs, len(ref_text))

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OCR-Evaluation: Vergleicht OCR mit Referenz-TEI")
    parser.add_argument("--docs", nargs='+', help="Spezifische Dokument-IDs (z.B. 2310 1180)")
    parser.add_argument("--all", action="store_true", help="Alle verfuegbaren Dokumente evaluieren")
    parser.add_argument("--ocr-dir", type=Path, help="OCR-Ergebnis-Verzeichnis (default: output/ocr_results)")
    parser.add_argument("--engine", default="deepseek", help="Engine-Name fuer Report (default: deepseek)")
    parser.add_argument("--phase", help="Testplan-Phase: phase1, phase2, phase3, phase4, all")
    parser.add_argument("--output", default="evaluation_report.html", help="Name der HTML-Report-Datei")
    parser.add_argument("--json-output", default="evaluation_results.json", help="Name der JSON-Ergebnis-Datei")
    parser.add_argument("--pagewise", action="store_true",
                        help="Seitenweiser Vergleich erzwingen (Standard: auto wenn TEI <pb>-Tags hat)")
    parser.add_argument("--no-pagewise", action="store_true",
                        help="Seitenweisen Vergleich deaktivieren (globales Alignment erzwingen)")
    args = parser.parse_args()

    # Pfade
    tei_dir = REFERENZ_TEI_DIR
    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else OCR_RESULTS_DIR
    output_dir = EVALUATION_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dokumente bestimmen
    if args.docs:
        doc_ids = args.docs
    elif args.phase:
        doc_ids = get_phase_doc_ids(args.phase)
        if not doc_ids:
            print(f"Unbekannte Phase: {args.phase}")
            print(f"Verfuegbar: {', '.join(TESTPLAN.keys())}, all")
            return 1
    elif args.all:
        ocr_files = list(ocr_dir.glob("*_p*.md"))
        doc_ids = sorted(set(f.stem.rsplit('_p', 1)[0] for f in ocr_files))
    else:
        # Default: Nur 2310 als Beispiel
        doc_ids = ['2310']

    engine_label = args.engine.capitalize()
    print(f"OCR-Evaluation ({engine_label})")
    print(f"==============")
    print(f"OCR-Verzeichnis: {ocr_dir}")
    print(f"Dokumente: {', '.join(doc_ids)}")
    print()

    # Evaluieren
    results = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'engine': args.engine,
        'ocr_dir': str(ocr_dir),
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

        # Auto-Erkennung: seitenweiser Vergleich bei genug Seiten
        # Schwelle: >10 TEI-Seiten (kurze Dokumente profitieren vom globalen Alignment)
        use_pagewise = not args.no_pagewise
        if use_pagewise and not args.pagewise:
            tei_path = _find_tei_path(doc_id, tei_dir)
            if tei_path is not None:
                test_pages = extract_pages_from_tei(tei_path)
                use_pagewise = len(test_pages) > 10
            else:
                use_pagewise = False

        if use_pagewise:
            doc_result = evaluate_document_pagewise(doc_id, tei_dir, ocr_dir)
        else:
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
    json_path = output_dir / args.json_output
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
