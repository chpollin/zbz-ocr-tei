"""
Silbentrennung auflösen.

OCR erkennt oft Zeilenumbrüche mit Trennstrichen, die zusammengefügt werden müssen:
- "Wis- senschaft" → "Wissenschaft"
- "philo- sophie" → "philosophie"
"""

import re


def dehyphenate(text: str, min_word_length: int = 3) -> str:
    """
    Löst Silbentrennungen auf.

    Args:
        text: Eingabetext mit potentiellen Silbentrennungen
        min_word_length: Minimale Länge der Wortteile (Default: 3)

    Returns:
        Text mit aufgelösten Silbentrennungen

    Beispiele:
        >>> dehyphenate("Wis- senschaft")
        'Wissenschaft'
        >>> dehyphenate("Karl- Marx")  # Eigenname, bleibt
        'Karl- Marx'
    """
    # Pattern: Wortteil + Bindestrich + optionales Newline + Whitespace + Wortteil
    # Nur auflösen wenn zweiter Teil klein beginnt (keine Eigennamen)
    pattern = rf'(\b\w{{{min_word_length},}})-\s*\n?\s*(\w{{{min_word_length},}}\b)'

    def should_join(match):
        part1, part2 = match.groups()

        # Nicht zusammenfügen wenn:
        # 1. Zweiter Teil mit Großbuchstabe beginnt (Eigenname/Satzanfang)
        if part2[0].isupper():
            return match.group(0)

        # 2. Erster Teil nur Großbuchstaben (Akronym)
        if part1.isupper():
            return match.group(0)

        # Zusammenfügen
        return part1 + part2

    return re.sub(pattern, should_join, text)


def dehyphenate_aggressive(text: str) -> str:
    """
    Aggressivere Variante: Löst auch Trennungen am Zeilenende auf,
    selbst wenn kein expliziter Bindestrich vorhanden ist.

    Vorsicht: Kann zu falschen Zusammenfügungen führen!
    """
    # Bindestrich am Zeilenende + Whitespace/Newline + Kleinbuchstabe
    pattern = r'(\w+)-\s*\n\s*([a-zäöüàâéèêëïîôùûç])'

    def join_parts(match):
        return match.group(1) + match.group(2)

    return re.sub(pattern, join_parts, text)


def find_potential_hyphenations(text: str) -> list:
    """
    Findet potentielle Silbentrennungen zur manuellen Überprüfung.

    Returns:
        Liste von Dictionaries mit Fundstellen
    """
    pattern = r'(\w+)-\s*\n?\s*(\w+)'
    matches = []

    for match in re.finditer(pattern, text):
        part1, part2 = match.groups()
        context_start = max(0, match.start() - 20)
        context_end = min(len(text), match.end() + 20)

        matches.append({
            'full_match': match.group(0),
            'part1': part1,
            'part2': part2,
            'position': match.start(),
            'context': text[context_start:context_end],
            'would_join': part2[0].islower() if part2 else False
        })

    return matches


if __name__ == '__main__':
    # Testbeispiele
    test_cases = [
        "Die Wis- senschaft ist wichtig.",
        "Die philo- sophie des Geistes.",
        "Karl- Marx war ein Denker.",  # Sollte NICHT zusammengefügt werden
        "Das UN- Abkommen",  # Akronym, sollte NICHT zusammengefügt werden
        "Die Transzendenz- erfahrung",
        "con- cernent des dis- ciplines",  # Französisch
    ]

    print("Dehyphenation Tests:")
    print("=" * 50)

    for test in test_cases:
        result = dehyphenate(test)
        changed = test != result
        print(f"  Input:  {test}")
        print(f"  Output: {result}")
        print(f"  Changed: {changed}")
        print()
