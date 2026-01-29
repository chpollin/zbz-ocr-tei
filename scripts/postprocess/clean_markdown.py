"""
Markdown-Formatierung entfernen.

OCR-Modelle wie DeepSeek geben oft Markdown aus.
Für die TEI-Konvertierung muss dieses entfernt werden.
"""

import re


def clean_markdown(text: str, preserve_structure: bool = True) -> str:
    """
    Entfernt Markdown-Formatierung.

    Args:
        text: Text mit Markdown-Formatierung
        preserve_structure: Wenn True, werden Überschriften als separate
                           Zeilen beibehalten (nur # entfernt)

    Returns:
        Text ohne Markdown
    """
    # 1. Überschriften: ## Text → Text
    if preserve_structure:
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    else:
        text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)

    # 2. Fett: **text** oder __text__ → text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # 3. Kursiv: *text* oder _text_ → text
    # Vorsicht: Nicht am Zeilenanfang (könnte Liste sein)
    text = re.sub(r'(?<![*_\n])\*([^*\n]+?)\*(?![*])', r'\1', text)
    text = re.sub(r'(?<![*_\n])_([^_\n]+?)_(?![_])', r'\1', text)

    # 4. Code: `code` → code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 5. Links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 6. Bilder: ![alt](url) → (entfernen)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # 7. Listen: - item oder * item oder 1. item → item
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 8. Blockquotes: > text → text
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # 9. Horizontale Linien: --- oder *** → (entfernen)
    text = re.sub(r'^[-*]{3,}\s*$', '', text, flags=re.MULTILINE)

    return text


def extract_structure(text: str) -> dict:
    """
    Extrahiert strukturelle Elemente aus Markdown.

    Nützlich für die spätere TEI-Transformation.

    Returns:
        Dictionary mit gefundenen Strukturelementen
    """
    structure = {
        'headings': [],
        'bold': [],
        'italic': [],
        'lists': [],
        'quotes': []
    }

    # Überschriften
    for match in re.finditer(r'^(#{1,6})\s+(.+)$', text, flags=re.MULTILINE):
        level = len(match.group(1))
        structure['headings'].append({
            'level': level,
            'text': match.group(2),
            'position': match.start()
        })

    # Fett
    for match in re.finditer(r'\*\*(.+?)\*\*', text):
        structure['bold'].append({
            'text': match.group(1),
            'position': match.start()
        })

    # Kursiv
    for match in re.finditer(r'(?<![*])\*([^*]+?)\*(?![*])', text):
        structure['italic'].append({
            'text': match.group(1),
            'position': match.start()
        })

    return structure


if __name__ == '__main__':
    test_text = '''
## L'ŒUVRE DE KARL JASPERS

On ne trouve pas dans la pensée de **Karl Jaspers** d'évolution au sens d'un *itinéraire intellectuel*.

### Caractéristiques

- Point 1
- Point 2

> Une citation importante

Le texte continue avec `code inline` et un [lien](http://example.com).
'''

    print("Original:")
    print(test_text)
    print("\nStruktur:")
    structure = extract_structure(test_text)
    for key, items in structure.items():
        if items:
            print(f"  {key}: {len(items)} gefunden")
            for item in items[:3]:
                print(f"    - {item}")

    print("\nBereinigt:")
    print(clean_markdown(test_text))
