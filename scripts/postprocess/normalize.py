"""
Zeichennormalisierung für OCR-Texte.

Ersetzt typografische Varianten durch einheitliche Zeichen:
- Anführungszeichen: „" » « → ""
- Apostrophe: '' → '
- Gedankenstriche: – — → -
"""

# Ersetzungsregeln
NORMALIZE_MAP = {
    # Anführungszeichen (deutsch/französisch → neutral)
    '„': '"',
    '\u201c': '"',  # Left double quotation mark
    '\u201d': '"',  # Right double quotation mark
    '»': '"',
    '«': '"',
    '‹': "'",
    '›': "'",

    # Apostrophe
    ''': "'",
    ''': "'",
    '`': "'",
    '´': "'",

    # Gedankenstriche
    '–': '-',  # En-dash (U+2013)
    '—': '-',  # Em-dash (U+2014)
    '‐': '-',  # Hyphen (U+2010)
    '‑': '-',  # Non-breaking hyphen (U+2011)

    # Leerzeichen
    '\u00A0': ' ',  # Non-breaking space
    '\u2009': ' ',  # Thin space
    '\u200A': ' ',  # Hair space
    '\u202F': ' ',  # Narrow no-break space

    # Ellipsis
    '…': '...',

    # Multiplication sign (oft in Größenangaben)
    '×': 'x',
}


def normalize_text(text: str, custom_rules: dict = None) -> str:
    """
    Normalisiert Zeichen im Text.

    Args:
        text: Eingabetext
        custom_rules: Zusätzliche Ersetzungsregeln (optional)

    Returns:
        Normalisierter Text
    """
    rules = NORMALIZE_MAP.copy()
    if custom_rules:
        rules.update(custom_rules)

    for old, new in rules.items():
        text = text.replace(old, new)

    return text


def get_normalize_stats(text: str) -> dict:
    """
    Zählt wie oft jedes zu normalisierende Zeichen vorkommt.

    Nützlich für Debugging und Qualitätskontrolle.
    """
    stats = {}
    for char in NORMALIZE_MAP.keys():
        count = text.count(char)
        if count > 0:
            stats[char] = {
                'count': count,
                'replacement': NORMALIZE_MAP[char],
                'unicode': f'U+{ord(char):04X}'
            }
    return stats


if __name__ == '__main__':
    # Testbeispiel
    test_text = '''
    „Dies ist ein Test" mit französischen «Guillemets».
    Der Gedankenstrich – hier – wird normalisiert.
    Apostrophe wie in l'homme oder it's werden vereinheitlicht.
    Größe: 17×25 cm.
    '''

    print("Original:")
    print(test_text)
    print("\nStatistik:")
    for char, info in get_normalize_stats(test_text).items():
        print(f"  '{char}' ({info['unicode']}): {info['count']}x → '{info['replacement']}'")
    print("\nNormalisiert:")
    print(normalize_text(test_text))
