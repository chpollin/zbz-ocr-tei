"""
Post-Processing Pipeline - Orchestrierung aller Transformationen.

Führt alle Post-Processing-Schritte in der richtigen Reihenfolge aus.
"""

import re
from pathlib import Path
from typing import Optional

from .normalize import normalize_text, get_normalize_stats
from .dehyphenate import dehyphenate, find_potential_hyphenations
from .clean_markdown import clean_markdown, extract_structure


def postprocess(
    text: str,
    remove_markdown: bool = True,
    normalize: bool = True,
    fix_hyphenation: bool = True,
    fix_whitespace: bool = True,
    verbose: bool = False
) -> str:
    """
    Führt alle Post-Processing-Schritte aus.

    Reihenfolge:
    1. Markdown entfernen (vor Normalisierung, da Markdown eigene Zeichen hat)
    2. Zeichennormalisierung
    3. Silbentrennung auflösen
    4. Whitespace normalisieren

    Args:
        text: Roher OCR-Text
        remove_markdown: Markdown-Formatierung entfernen
        normalize: Zeichen normalisieren
        fix_hyphenation: Silbentrennungen auflösen
        fix_whitespace: Whitespace normalisieren
        verbose: Debug-Ausgaben

    Returns:
        Bereinigter Text
    """
    original_length = len(text)

    # 1. Markdown entfernen
    if remove_markdown:
        text = clean_markdown(text)
        if verbose:
            print(f"  [1] Markdown entfernt: {original_length} -> {len(text)} Zeichen")

    # 2. Zeichen normalisieren
    if normalize:
        before = len(text)
        text = normalize_text(text)
        if verbose:
            stats = get_normalize_stats(text)
            if stats:
                print(f"  [2] Zeichen normalisiert: {sum(s['count'] for s in stats.values())} Ersetzungen")

    # 3. Silbentrennung
    if fix_hyphenation:
        before = text
        text = dehyphenate(text)
        if verbose and text != before:
            changes = len(before) - len(text)
            print(f"  [3] Silbentrennung: {changes} Zeichen entfernt")

    # 4. Whitespace
    if fix_whitespace:
        # Mehrfache Leerzeilen → maximal 2
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Trailing whitespace entfernen
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

        # Leading whitespace normalisieren (aber Einrückung beibehalten)
        text = re.sub(r'^[ \t]+(?=\S)', '', text, flags=re.MULTILINE)

        # Mehrfache Leerzeichen → ein Leerzeichen
        text = re.sub(r' {2,}', ' ', text)

        if verbose:
            print(f"  [4] Whitespace normalisiert")

    return text.strip()


def process_file(
    input_path: Path,
    output_path: Optional[Path] = None,
    verbose: bool = False
) -> str:
    """
    Verarbeitet eine einzelne Datei.

    Args:
        input_path: Pfad zur Eingabedatei
        output_path: Pfad zur Ausgabedatei (optional)
        verbose: Debug-Ausgaben

    Returns:
        Bereinigter Text
    """
    if verbose:
        print(f"Verarbeite: {input_path}")

    text = input_path.read_text(encoding='utf-8')
    result = postprocess(text, verbose=verbose)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding='utf-8')
        if verbose:
            print(f"Gespeichert: {output_path}")

    return result


def process_directory(
    input_dir: Path,
    output_dir: Path,
    pattern: str = "*.md",
    verbose: bool = False
) -> dict:
    """
    Verarbeitet alle Dateien in einem Verzeichnis.

    Args:
        input_dir: Eingabeverzeichnis
        output_dir: Ausgabeverzeichnis
        pattern: Glob-Pattern für Dateien
        verbose: Debug-Ausgaben

    Returns:
        Dictionary mit Statistiken
    """
    input_files = list(input_dir.glob(pattern))
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'processed': 0,
        'failed': 0,
        'total_chars_before': 0,
        'total_chars_after': 0
    }

    for input_file in input_files:
        output_file = output_dir / input_file.name

        try:
            original = input_file.read_text(encoding='utf-8')
            result = postprocess(original, verbose=verbose)

            output_file.write_text(result, encoding='utf-8')

            stats['processed'] += 1
            stats['total_chars_before'] += len(original)
            stats['total_chars_after'] += len(result)

            if verbose:
                print(f"  [OK] {input_file.name}: {len(original)} -> {len(result)} Zeichen")

        except Exception as e:
            stats['failed'] += 1
            if verbose:
                print(f"  [FAIL] {input_file.name}: {e}")

    return stats


def get_processing_report(text: str) -> dict:
    """
    Erstellt einen Bericht über potentielle Probleme im Text.

    Nützlich für Qualitätskontrolle vor der TEI-Transformation.
    """
    report = {
        'length': len(text),
        'lines': text.count('\n') + 1,
        'paragraphs': len(re.findall(r'\n\n+', text)) + 1,
        'issues': []
    }

    # Nicht-normalisierte Zeichen
    normalize_stats = get_normalize_stats(text)
    if normalize_stats:
        report['issues'].append({
            'type': 'unnormalized_chars',
            'count': sum(s['count'] for s in normalize_stats.values()),
            'details': normalize_stats
        })

    # Potentielle Silbentrennungen
    hyphenations = find_potential_hyphenations(text)
    if hyphenations:
        report['issues'].append({
            'type': 'potential_hyphenations',
            'count': len(hyphenations),
            'details': hyphenations[:10]  # Nur erste 10
        })

    # Markdown-Reste
    md_structure = extract_structure(text)
    md_count = sum(len(v) for v in md_structure.values())
    if md_count > 0:
        report['issues'].append({
            'type': 'markdown_elements',
            'count': md_count,
            'details': md_structure
        })

    return report


if __name__ == '__main__':
    import sys

    # CLI für schnelle Tests
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if input_file.exists():
            result = process_file(input_file, verbose=True)
            print("\n" + "=" * 50)
            print("Ergebnis (erste 1000 Zeichen):")
            print("=" * 50)
            print(result[:1000])
        else:
            print(f"Datei nicht gefunden: {input_file}")
    else:
        # Demo
        demo_text = '''
## Tâches et limites des „Sciences humaines"

Les problèmes que je vais essayer de poser devant vous con-
cernent des dis- ciplines que vous connaissez **beaucoup mieux** que moi.

La traduction de „Geisteswissenschaften" pose des problèmes en français.
'''

        print("Demo: Post-Processing Pipeline")
        print("=" * 50)
        print("\nOriginal:")
        print(demo_text)

        print("\nReport:")
        report = get_processing_report(demo_text)
        print(f"  Länge: {report['length']} Zeichen")
        print(f"  Zeilen: {report['lines']}")
        print(f"  Issues: {len(report['issues'])}")
        for issue in report['issues']:
            print(f"    - {issue['type']}: {issue['count']}")

        print("\nBereinigt:")
        print(postprocess(demo_text, verbose=True))
