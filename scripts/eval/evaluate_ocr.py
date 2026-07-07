"""
OCR-Evaluationsskript: Vergleicht OCR-Output mit Referenz-TEI.
Berechnet Character Error Rate (CER) und Word Error Rate (WER).
Generiert visuellen HTML-Report mit Diff-Ansicht.

=====================================================================
CER-VERTRAG (kanonische Definition, gilt fuer das ganze Projekt)
=====================================================================
Verbindlich verifiziert gegen OCR-D, dinglehopper, Transkribus, jiwer
(siehe knowledge/final-report.md, Abschnitt Externe Verifikation).

- Formel:        CER = Levenshtein(ref, hyp) / len(ref)   (Transkribus-Konvention,
                 Denominator = Referenzlaenge). Kann >1.0 werden; das wird NICHT
                 versteckt. Optional zusaetzlich OCR-D-normiert (gedeckelt).
- Alignment:     GLOBALES Levenshtein ueber den VOLLTEXT. Kein Zuschneiden der
                 Hypothese auf die Referenz -- das wuerde Insertions/Extra-Text
                 verstecken (frueheres find_best_alignment-Trimming, abgeschafft).
- Case:          PRIMAER case-sensitiv (konsistent mit der Transkribus-Ground-Truth
                 und OCR-D/dinglehopper, wo Case ein Fehler ist). Case-insensitiv
                 (Unicode casefold) wird SEKUNDAER zusaetzlich berichtet.
- Unicode:       NFC (Standard). Symmetrische Norm. von Quotes/Guillemets/Apostroph/
                 Bindestrich -> ASCII, auf BEIDE Seiten angewandt (keine konventions-
                 bedingten Pseudo-Fehler).
- Footnotes:     fuer den Hauptvergleich exkludiert; cer_incl_footnotes separat.
- <choice>:      nur <corr> wird verglichen (nicht sic+corr konkateniert).
- Aggregation:   Doc-Ebene (1 char-gewichtete CER pro Dok), Bootstrap ueber Docs.
- Ausschluss:    NUR strukturell (Seitenzahl-Ratio), ergebnisUNABHAENGIG. Ein hoher
                 CER bei gleicher Seitenzahl ist ein echtes Ergebnis, kein Artefakt.

EINE kanonische Funktion -- extract_text_for_comparison() + calculate_cer() --
wird von benchmark_cer, cer_statistics_runner UND tei_validator verwendet.
"""

import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET

from scripts.config import (
    REFERENCE_TEI_DIR, OCR_RESULTS_DIR, EVALUATION_DIR, TESTPLAN,
    TEI_FINAL_DIR,
)
from scripts.utils import get_phase_doc_ids
from scripts.eval.eval_report import generate_html_report


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
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    # Guillemets beibehalten (sind korrekt)
    # Whitespace am Anfang/Ende entfernen
    text = text.strip()
    return text


def normalize_for_comparison(text: str, casefold: bool = False) -> str:
    """Symmetrische Normalisierung fuer CER-Vergleich.

    Wendet alle konventionsbedingten Zeichenersetzungen an, damit
    Unterschiede zwischen Pipeline-TEI (durchlief normalize_for_tei)
    und Referenz-TEI (Transkribus) nicht als CER gezaehlt werden.

    Angewendet auf BEIDE Seiten des Vergleichs.

    Args:
        casefold: Wenn True, Unicode-Casefolding (case-INSENSITIVE Sekundaer-Metrik).
                  Standard False = case-SENSITIV -- korrekte Default-Konvention: die
                  Transkribus-Ground-Truth ist case-sensitiv, OCR-D/dinglehopper zaehlen
                  Case als Fehler, jiwer macht ToLowerCase opt-in. Ein pauschales lower()
                  wuerde alle Majuskel/Minuskel-Fehler verstecken.
    """
    # 1. Guillemets + deutsche Anfuehrungszeichen -> ASCII
    text = text.replace('\u00AB', '"').replace('\u00BB', '"')   # « »
    text = text.replace('\u201E', '"')                          # „
    text = text.replace('\u2039', "'").replace('\u203A', "'")   # ‹ ›
    # 2. Apostrophe -> ASCII
    text = text.replace('\u0060', "'").replace('\u00B4', "'")   # ` ´
    # 3. Alle Strichvarianten -> ASCII Hyphen-minus (U+002D)
    text = text.replace('\u2010', '-')   # Hyphen
    text = text.replace('\u2011', '-')   # Non-breaking hyphen
    text = text.replace('\u2013', '-')   # En-dash
    text = text.replace('\u2014', '-')   # Em-dash
    text = text.replace('\u2012', '-')   # Figure dash
    text = text.replace('\u00AD', '')    # Soft hyphen entfernen
    # 4. Leerzeichen vor franzoesischer Interpunktion entfernen
    text = re.sub(r' +([;:?!])', r'\1', text)
    # 5. Optionales Casefolding -- NUR fuer die case-insensitive Sekundaer-Metrik.
    #    Standard ist case-sensitiv. casefold() ist Unicode-korrekt (ss = ß) und
    #    konsistent mit dem Regime nfc_hyphen_case in cer_statistics.
    if casefold:
        text = text.casefold()
    # 6. Basis-Normalisierung (Whitespace, Smart Quotes, Strip)
    text = normalize_text(text)
    # 7. Unicode NFC
    text = unicodedata.normalize('NFC', text)
    return text


def extract_text_for_comparison(tei_path: Path, include_footnotes: bool = False,
                                casefold: bool = False) -> str:
    """Extrahiert Text aus TEI-XML fuer CER-Benchmarking.

    Gegenueber extract_text_from_tei mit drei Korrekturen:
    1. <choice>: Nur <corr> extrahieren (nicht sic+corr konkateniert)
    2. <note place="foot">: Optional ausschliessen (Default: exkludiert)
    3. Unicode NFC-Normalisierung fuer konsistenten Diakritika-Vergleich

    casefold=True liefert den case-insensitiven Text (Sekundaer-Metrik).
    """
    with open(tei_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        text = re.sub(r'<[^>]+>', '', content)
        return normalize_for_comparison(text, casefold=casefold)

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
    return normalize_for_comparison(text, casefold=casefold)


def extract_pages_for_comparison(tei_path: Path,
                                 include_footnotes: bool = False,
                                 casefold: bool = False,
                                 ) -> dict[int, str]:
    """Extrahiert Text pro Seite aus TEI-XML fuer CER-Benchmarking.

    Aehnlich wie extract_pages_from_tei(), aber mit CER-spezifischer
    Normalisierung (normalize_for_comparison) und <choice>/<note>-Behandlung
    analog zu extract_text_for_comparison(). Die Duplizierung ist bewusst:
    extract_pages_from_tei() liefert Rohtext, diese Funktion liefert
    benchmark-normalisierten Text pro Seite.
    """
    with open(tei_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return {}

    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}')[1]
        for attr_key in list(elem.attrib.keys()):
            if '}' in attr_key:
                elem.attrib[attr_key.split('}')[1]] = elem.attrib.pop(attr_key)

    body = root.find('.//body')
    if body is None:
        return {}

    pages = {}
    current_page = None
    current_parts = []

    def _flush():
        nonlocal current_page, current_parts
        if current_page is not None and current_parts:
            raw = ''.join(current_parts)
            text = normalize_for_comparison(raw, casefold=casefold)
            if text.strip():
                pages[current_page] = text
        current_parts = []

    def _extract_page_num(elem):
        facs = elem.get('facs', '')
        m = re.match(r'#facs_(\d+)', facs)
        return int(m.group(1)) if m else None

    def collect(elem):
        nonlocal current_page, current_parts
        if elem.tag == 'pb':
            page_num = _extract_page_num(elem)
            if page_num is not None:
                _flush()
                current_page = page_num
        elif elem.tag == 'choice':
            corr = elem.find('corr')
            target = corr if corr is not None else elem.find('sic')
            if target is not None:
                collect(target)
        elif elem.tag == 'note' and elem.get('place') == 'foot' and not include_footnotes:
            pass
        elif elem.tag == 'lb':
            if elem.get('break') != 'no':
                current_parts.append(' ')
        else:
            if elem.text:
                current_parts.append(elem.text)
            for child in elem:
                collect(child)
        if elem.tail and elem.tag not in ('body',):
            current_parts.append(elem.tail)

    if body.text:
        current_parts.append(body.text)
    for child in body:
        collect(child)
    _flush()

    return pages


def load_ocr_result(ocr_path: Path, casefold: bool = False) -> str:
    """Laedt OCR-Ergebnis aus Markdown-Datei."""
    if not ocr_path.exists():
        return ""
    text = ocr_path.read_text(encoding='utf-8')
    return normalize_for_comparison(text, casefold=casefold)


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


def _get_opcodes(reference: str, hypothesis: str):
    """Liefert (tag, i1, i2, j1, j2)-Opcodes aus dem ECHTEN Levenshtein-Alignment.

    Wichtig: rapidfuzz.Levenshtein.opcodes nutzt dieselbe minimale Editierdistanz
    wie calculate_cer(). difflib.SequenceMatcher (frueher hier) liefert ein anderes,
    lesbarkeits-optimiertes Alignment (Autojunk-Heuristik), dessen Block-Distanzen
    NICHT zur CER aufsummieren. editops/opcodes garantieren Konsistenz mit der Headline.
    Fallback auf difflib nur, wenn rapidfuzz fehlt.
    """
    try:
        from rapidfuzz.distance import Levenshtein as _RFLev
        return [(op.tag, op.src_start, op.src_end, op.dest_start, op.dest_end)
                for op in _RFLev.opcodes(reference, hypothesis)]
    except ImportError:
        return list(SequenceMatcher(None, reference, hypothesis).get_opcodes())


def find_differences(reference: str, hypothesis: str) -> list:
    """Findet konkrete Unterschiede zwischen Texten (echtes Levenshtein-Alignment)."""
    differences = []

    for tag, i1, i2, j1, j2 in _get_opcodes(reference, hypothesis):
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


# Eine zusammenhaengende Einfuegung >= SCOPE_BLOCK_MIN Zeichen gilt als
# struktureller Mehrtext der Pipeline ggue. der (oft selektiven) Referenz
# -- z.B. Journal-Masthead, Nachbar-Rezension, Inhaltsverzeichnis. Solche
# Bloecke sind KEIN OCR-Fehler. Tunbar; dokumentiert im CER-Vertrag oben.
SCOPE_BLOCK_MIN = 50


def classify_edit_operations(reference: str, hypothesis: str,
                             scope_block_min: int = SCOPE_BLOCK_MIN) -> dict:
    """Zerlegt die Levenshtein-Editieroperationen in zwei Toepfe.

    fidelity (echte Fehler):
        - Substitutionen (replace-Bloecke)         -> Text falsch erkannt
        - ALLE Loeschungen (delete)                -> Pipeline VERPASST Referenztext
        - kleine Einfuegungen (< scope_block_min)  -> spurioses Zeichen/Wort
    scope (kein OCR-Fehler):
        - grosse Einfuegungen (>= scope_block_min) -> Pipeline-Mehrtext ggue. Referenz
                                                      (Masthead, 2. Rezension, Inhaltsverz.)

    fidelity_distance + scope_insertion_distance == Levenshtein(ref, hyp), d.h.
    cer (=total/N) ist identisch zu calculate_cer; cer_fidelity + scope_insertion_rate == cer.
    Asymmetrie ist beabsichtigt: vollstaendiger sein als die Referenz ist kein Fehler,
    unvollstaendiger sein schon (siehe knowledge/specification.md, Quality measurement).
    """
    fid = 0
    scope_ins = 0
    for tag, i1, i2, j1, j2 in _get_opcodes(reference, hypothesis):
        r, h = i2 - i1, j2 - j1
        if tag == 'equal':
            continue
        if tag == 'replace':
            fid += max(r, h)
        elif tag == 'delete':
            fid += r
        elif tag == 'insert':
            if h >= scope_block_min:
                scope_ins += h
            else:
                fid += h
    n = len(reference)
    total = fid + scope_ins
    if n == 0:
        base = 0.0 if not hypothesis else 1.0
        return {'total_distance': total, 'fidelity_distance': fid,
                'scope_insertion_distance': scope_ins, 'cer': base,
                'cer_fidelity': base, 'scope_insertion_rate': 0.0,
                'scope_block_min': scope_block_min}
    return {
        'total_distance': total,
        'fidelity_distance': fid,
        'scope_insertion_distance': scope_ins,
        'cer': total / n,
        'cer_fidelity': fid / n,
        'scope_insertion_rate': scope_ins / n,
        'scope_block_min': scope_block_min,
    }


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


def build_confusion_matrix(differences: list) -> dict:
    """Baut zeichenweise Konfusionsmatrix aus find_differences()-Output.

    Gibt dict mit:
      - substitutions: Liste von {ref_char, hyp_char, ref_cp, hyp_cp, count}
      - insertions: Liste von {char, codepoint, count}
      - deletions: Liste von {char, codepoint, count}
    Alle sortiert nach Haeufigkeit (absteigend).
    """
    from collections import Counter

    sub_counter = Counter()   # (ref_char, hyp_char) -> count
    ins_counter = Counter()   # char -> count
    del_counter = Counter()   # char -> count

    for diff in differences:
        ref = diff.get('reference', '')
        hyp = diff.get('hypothesis', '')
        diff_type = diff.get('type', '')

        if diff_type == 'replace':
            # Zeichenweises Alignment innerhalb des Blocks
            for i in range(max(len(ref), len(hyp))):
                r = ref[i] if i < len(ref) else ''
                h = hyp[i] if i < len(hyp) else ''
                if r and h and r != h:
                    sub_counter[(r, h)] += 1
                elif r and not h:
                    del_counter[r] += 1
                elif h and not r:
                    ins_counter[h] += 1
        elif diff_type == 'insert':
            for c in hyp:
                ins_counter[c] += 1
        elif diff_type == 'delete':
            for c in ref:
                del_counter[c] += 1

    def _cp(c):
        return f"U+{ord(c):04X}" if c else ""

    substitutions = [
        {
            'ref_char': r, 'hyp_char': h,
            'ref_codepoint': _cp(r), 'hyp_codepoint': _cp(h),
            'ref_name': unicodedata.name(r, '?'), 'hyp_name': unicodedata.name(h, '?'),
            'count': cnt,
        }
        for (r, h), cnt in sub_counter.most_common()
    ]

    insertions = [
        {'char': c, 'codepoint': _cp(c), 'name': unicodedata.name(c, '?'), 'count': cnt}
        for c, cnt in ins_counter.most_common()
    ]

    deletions = [
        {'char': c, 'codepoint': _cp(c), 'name': unicodedata.name(c, '?'), 'count': cnt}
        for c, cnt in del_counter.most_common()
    ]

    return {
        'substitutions': substitutions,
        'insertions': insertions,
        'deletions': deletions,
        'total_substitutions': sum(sub_counter.values()),
        'total_insertions': sum(ins_counter.values()),
        'total_deletions': sum(del_counter.values()),
    }


def _strip_markdown(text: str) -> str:
    """Entfernt Markdown-Formatierung fuer Alignment-Suche."""
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)  # *bold* / **bold**
    text = re.sub(r'_+([^_]+)_+', r'\1', text)    # _italic_
    text = re.sub(r'#+\s*', '', text)               # ## headers
    return text


def _find_phrase_in_text(phrase: str, text: str, case_insensitive: bool = False) -> int:
    """Sucht Phrase im Text, auch mit Markdown-Unterschieden."""
    pos = text.find(phrase)
    if pos != -1:
        return pos
    # Fallback 1: Ohne Markdown suchen
    clean_text = _strip_markdown(text)
    clean_phrase = _strip_markdown(phrase)
    pos = clean_text.find(clean_phrase)
    if pos != -1:
        return pos
    # Fallback 2: Case-insensitive (nur wenn explizit angefordert)
    if case_insensitive:
        pos = clean_text.lower().find(clean_phrase.lower())
        return pos
    return -1


def find_best_alignment(reference: str, ocr_text: str, window_size: int = 100) -> tuple:
    """
    DIAGNOSE-WERKZEUG (nicht mehr Headline-Pfad). Findet die beste Ausrichtung
    zwischen OCR-Text und Referenztext fuer den Vergleich cer vs cer_aligned_legacy.
    Die Headline-CER nutzt KEIN Alignment mehr (Volltext-Vergleich), weil das
    Zuschneiden der Hypothese Insertions/Extra-Text versteckt. Padding-Fallbacks
    (frueher +200 auf Referenzlaenge) wurden entfernt -- Nicht-Treffer dehnen jetzt
    bis zum Textende statt auf Referenzlaenge aufzufuellen.

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
        # Anfang gefunden, Ende nicht: bis zum ENDE der Hypothese nehmen.
        # KEIN Padding auf Referenzlaenge (+200) -- das wuerde Insertions verstecken.
        matched_ocr = ocr_text[ocr_start_pos:]
        return (0, len(reference), ocr_start_pos, len(ocr_text), reference, matched_ocr)

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
            ref_end_pos = len(reference)  # bis zum Ende, kein +200-Padding

        matched_ref = reference[ref_start_pos:ref_end_pos]
        return (ref_start_pos, ref_end_pos, 0, len(ocr_text), matched_ref, ocr_text)

    # 4. Case-insensitive Phrasensuche (fuer UPPERCASE-Titel etc.)
    #    Nur mit langen Phrasen (5+ Woerter), VOR Single-Word-Fallback
    ci_start = -1
    ci_end_pos = -1
    for n_words in [8, 5]:
        ref_start_phrase = ' '.join(ref_words[:n_words])
        ci_start = _find_phrase_in_text(ref_start_phrase, ocr_text, case_insensitive=True)
        if ci_start != -1:
            for n_end in [8, 5]:
                ref_end_phrase = ' '.join(ref_words[-n_end:])
                ci_end_pos = _find_phrase_in_text(ref_end_phrase, ocr_text, case_insensitive=True)
                if ci_end_pos != -1 and ci_end_pos > ci_start:
                    ci_end_pos = ci_end_pos + len(ref_end_phrase)
                    break
            break

    if ci_start != -1 and ci_end_pos != -1 and ci_end_pos > ci_start:
        matched_ocr = ocr_text[ci_start:ci_end_pos]
        return (0, len(reference), ci_start, ci_end_pos, reference, matched_ocr)

    if ci_start != -1:
        matched_ocr = ocr_text[ci_start:]  # bis zum Ende, kein +200-Padding
        return (0, len(reference), ci_start, len(ocr_text), reference, matched_ocr)

    # 5. Fallback: Einzelne lange Woerter suchen
    for words, text, is_ref in [(ref_words, ocr_text, True), (ocr_words, reference, False)]:
        for i in range(min(30, len(words))):
            word = words[i]
            if len(word) > 8:  # Nur markante Woerter
                pos = text.find(word)
                if pos != -1:
                    if is_ref:
                        matched_ocr = ocr_text[pos:]  # bis zum Ende, kein +200-Padding
                        return (0, len(reference), pos, len(ocr_text), reference, matched_ocr)
                    else:
                        matched_ref = reference[pos:]
                        return (pos, len(reference), 0, len(ocr_text), matched_ref, ocr_text)

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

    # Seitenzahl (strukturelles Scope-Signal). Blank-Seiten (<pb type="blank"/>,
    # von tei_blank_marker nur in tei_final injiziert) werden NICHT mitgezaehlt,
    # sonst entsteht bei kurzen Docs ein kuenstlicher Seiten-Mismatch.
    def _count_pb(path):
        try:
            content = path.read_text(encoding='utf-8')
            return sum(1 for tag in re.findall(r'<pb\b[^>]*>', content)
                       if 'type="blank"' not in tag)
        except Exception:
            return 0

    ref_pages = _count_pb(ref_path)
    pipe_pages = _count_pb(pipe_path)
    result['ref_pages'] = ref_pages
    result['pipe_pages'] = pipe_pages
    if ref_pages > 0 and pipe_pages > 0:
        page_ratio = max(ref_pages, pipe_pages) / max(min(ref_pages, pipe_pages), 1)
        if page_ratio >= 1.5:
            result['scope_mismatch'] = True
            result['scope_info'] = (
                f"Seiten-Mismatch: Ref={ref_pages}, Pipeline={pipe_pages} "
                f"(Ratio {page_ratio:.1f}x). Struktureller Scope-Unterschied."
            )

    # Text extrahieren (ohne Fussnoten fuer Hauptvergleich), case-sensitiv = primaer.
    ref_text = extract_text_for_comparison(ref_path, include_footnotes=False)
    pipe_text = extract_text_for_comparison(pipe_path, include_footnotes=False)

    if not ref_text:
        result['status'] = 'SKIP'
        result['error'] = f"Referenz-TEI leer: {ref_path.name}"
        return result

    # PRIMAER: Volltext-CER OHNE Trimming (dinglehopper/jiwer-Konvention).
    # calculate_cer rechnet globales Levenshtein ueber den ganzen Text. Wir
    # schneiden die Hypothese NICHT auf die Referenz zu -- das wuerde Insertions
    # und Extra-Text der Pipeline verstecken (frueheres find_best_alignment-Trimming).
    result['cer'] = calculate_cer(ref_text, pipe_text)
    result['wer'] = calculate_wer(ref_text, pipe_text)
    result['ref_chars'] = len(ref_text)
    result['hyp_chars'] = len(pipe_text)
    len_ratio = max(len(ref_text), len(pipe_text)) / max(min(len(ref_text), len(pipe_text)), 1)

    # Drei-Zahlen-Zerlegung (siehe classify_edit_operations):
    #   cer            = volle Divergenz von der Referenz (= calculate_cer)
    #   cer_fidelity   = echte OCR-/Transkriptionsfehler (Subst. + kleine Indels + Loeschungen)
    #   scope_insertion_rate = Pipeline-Mehrtext ggue. (oft selektiver) Referenz, kein Fehler
    ops_class = classify_edit_operations(ref_text, pipe_text)
    result['cer_fidelity'] = ops_class['cer_fidelity']
    result['scope_insertion_rate'] = ops_class['scope_insertion_rate']

    # SEKUNDAER: case-insensitive (Unicode casefold) -- selber Volltext-Vergleich.
    ref_cf = extract_text_for_comparison(ref_path, include_footnotes=False, casefold=True)
    pipe_cf = extract_text_for_comparison(pipe_path, include_footnotes=False, casefold=True)
    result['cer_casefold'] = calculate_cer(ref_cf, pipe_cf)

    # DIAGNOSE (nicht Headline): die frueher verwendete alignment-getrimmte CER.
    # Macht den Deflations-Effekt sichtbar (cer vs cer_aligned_legacy). find_best_alignment
    # ohne Padding-Fallbacks (siehe dortige Korrektur).
    if len_ratio > 1.05:
        _, _, _, _, aref, apipe = find_best_alignment(ref_text, pipe_text)
        result['cer_aligned_legacy'] = calculate_cer(aref, apipe)
    else:
        result['cer_aligned_legacy'] = result['cer']

    result['alignment_info'] = (
        f"Volltext case-sensitiv={result['cer']*100:.2f}%, "
        f"case-insensitiv={result['cer_casefold']*100:.2f}%, "
        f"legacy-aligned={result['cer_aligned_legacy']*100:.2f}% (ratio {len_ratio:.2f})"
    )

    # Hoher CER ist ein informatives Flag, KEIN Status-Wechsel und KEIN Ausschluss.
    # Ein hoher CER bei gleicher Seitenzahl ist ein echtes Ergebnis; nur strukturelle
    # Seiten-Mismatches (scope_mismatch oben) sind Benchmark-Artefakte.
    result['high_cer'] = result['cer'] > 0.50

    # Fussnoten-CER separat (Volltext, konsistent zur Primaer-CER)
    ref_with_fn = extract_text_for_comparison(ref_path, include_footnotes=True)
    pipe_with_fn = extract_text_for_comparison(pipe_path, include_footnotes=True)
    if len(ref_with_fn) > len(ref_text) + 20:
        result['cer_incl_footnotes'] = calculate_cer(ref_with_fn, pipe_with_fn)
        result['footnote_cer'] = result['cer_incl_footnotes']

    # Fehlerkategorien (editops-basiert, summiert zur tatsaechlichen Editierdistanz)
    diffs = find_differences(ref_text, pipe_text)
    result['differences'] = diffs[:30]
    result['error_categories'] = categorize_errors(diffs, len(ref_text))

    return result


def evaluate_tei_vs_tei_pagewise(doc_id: str, ref_dir: Path,
                                  pipeline_dir: Path) -> dict:
    """Seitenweiser CER-Vergleich: Referenz-TEI vs. Pipeline-TEI.

    Extrahiert Text pro Seite aus beiden TEIs, berechnet CER/WER pro Seite,
    und identifiziert Outlier-Seiten (CER > threshold).
    """
    result = {
        'doc_id': doc_id,
        'status': 'OK',
        'cer': 0.0,
        'wer': 0.0,
        'page_count': 0,
        'page_results': [],
        'outlier_pages': [],
    }

    ref_path = _find_tei_path(doc_id, ref_dir)
    if ref_path is None:
        result['status'] = 'SKIP'
        result['error'] = f"Referenz-TEI nicht gefunden: {doc_id}"
        return result

    pipe_path = pipeline_dir / f"{doc_id}_final.xml"
    if not pipe_path.exists():
        pipe_path = pipeline_dir / f"{doc_id}.xml"
    if not pipe_path.exists():
        result['status'] = 'SKIP'
        result['error'] = f"Pipeline-TEI nicht gefunden: {doc_id}"
        return result

    ref_pages = extract_pages_for_comparison(ref_path)
    pipe_pages = extract_pages_for_comparison(pipe_path)

    if not ref_pages:
        result['status'] = 'SKIP'
        result['error'] = "Keine Seiten in Referenz-TEI"
        return result

    # Seiten matchen (gleiche Seitennummern)
    matched_pages = sorted(set(ref_pages.keys()) & set(pipe_pages.keys()))
    if not matched_pages:
        # Fallback: Sequentielles Matching (1:1)
        ref_sorted = sorted(ref_pages.keys())
        pipe_sorted = sorted(pipe_pages.keys())
        n = min(len(ref_sorted), len(pipe_sorted))
        matched_pairs = list(zip(ref_sorted[:n], pipe_sorted[:n]))
    else:
        matched_pairs = [(p, p) for p in matched_pages]

    total_ref_chars = 0
    total_distance = 0
    total_ref_words = 0
    total_word_distance = 0

    for ref_page, pipe_page in matched_pairs:
        ref_text = ref_pages[ref_page]
        pipe_text = pipe_pages.get(pipe_page, "")

        page_cer = calculate_cer(ref_text, pipe_text)
        page_wer = calculate_wer(ref_text, pipe_text)

        page_result = {
            'page': ref_page,
            'ref_page': ref_page,
            'pipe_page': pipe_page,
            'cer': round(page_cer, 4),
            'wer': round(page_wer, 4),
            'ref_chars': len(ref_text),
            'hyp_chars': len(pipe_text),
        }
        result['page_results'].append(page_result)

        # Gewichtete Aggregation (CER * ref_chars fuer gewichteten Durchschnitt)
        total_ref_chars += len(ref_text)
        total_distance += round(page_cer * len(ref_text))

        total_ref_words += len(ref_text.split())
        total_word_distance += round(page_wer * len(ref_text.split()))

    # Gewichtete Gesamt-CER
    result['cer'] = round(total_distance / max(total_ref_chars, 1), 4)
    result['wer'] = round(total_word_distance / max(total_ref_words, 1), 4)
    result['page_count'] = len(result['page_results'])
    result['ref_pages_total'] = len(ref_pages)
    result['pipe_pages_total'] = len(pipe_pages)
    result['matched_pages'] = len(matched_pairs)

    # Outlier-Seiten (CER > 10%)
    result['outlier_pages'] = [
        pr for pr in result['page_results'] if pr['cer'] > 0.10
    ]

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OCR-Evaluation: Vergleicht OCR mit Referenz-TEI")
    parser.add_argument("--docs", nargs='+', help="Spezifische Dokument-IDs (z.B. 2310 1180)")
    parser.add_argument("--all", action="store_true", help="Alle verfuegbaren Dokumente evaluieren")
    parser.add_argument("--ocr-dir", type=Path, help="OCR-Ergebnis-Verzeichnis (default: output/ocr_results)")
    parser.add_argument("--engine", default="mistral", help="Engine-Name fuer Report (default: mistral)")
    parser.add_argument("--phase", help="Testplan-Phase: phase1, phase2, phase3, phase4, all")
    parser.add_argument("--output", default="evaluation_report.html", help="Name der HTML-Report-Datei")
    parser.add_argument("--json-output", default="evaluation_results.json", help="Name der JSON-Ergebnis-Datei")
    parser.add_argument("--pagewise", action="store_true",
                        help="Seitenweiser Vergleich erzwingen (Standard: auto wenn TEI <pb>-Tags hat)")
    parser.add_argument("--no-pagewise", action="store_true",
                        help="Seitenweisen Vergleich deaktivieren (globales Alignment erzwingen)")
    args = parser.parse_args()

    # Pfade
    tei_dir = REFERENCE_TEI_DIR
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
