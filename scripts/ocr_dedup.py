"""OCR Deduplizierung: Entfernt Halluzinationen aus OCR-Ergebnissen.

Erkennt und bereinigt:
- Token-Repetitions-Loops (z.B. "les filles, les filles, les filles...")
- Zeilen-Repetitions-Loops (z.B. identische Absaetze hintereinander)
- Barcode-/Garbage-Artefakte (z.B. "KdSvoSsBtGcWIS...")
- URL-Artefakte
- Einzel-Buchstaben-Loops (z.B. "J\nJ\nJ\n...")
"""

import re
import sys
from pathlib import Path


def remove_token_repetitions(text: str, min_repeat: int = 4) -> str:
    """Entfernt Wiederholungen von Wortgruppen (2-8 Tokens).

    Erkennt Muster wie: "les filles, les filles, les filles, les filles"
    und reduziert auf maximal 2 Vorkommen.
    """
    for group_len in range(8, 1, -1):
        # Muster: Wortgruppe wiederholt sich min_repeat+ mal
        pattern = r'((?:\S+[\s,;]+){' + str(group_len) + r'})\1{' + str(min_repeat - 1) + r',}'
        text = re.sub(pattern, r'\1\1', text)
    return text


def remove_single_char_loops(text: str) -> str:
    """Entfernt Loops aus einzelnen Buchstaben (z.B. J\\nJ\\nJ\\n...)."""
    # Einzelner Buchstabe auf eigener Zeile, 5+ mal wiederholt
    text = re.sub(r'(\n[A-Z]\n){5,}', '\n', text)
    # Am Ende: J" wiederholt
    text = re.sub(r'(\n[A-Z]"?\n){5,}', '\n', text)
    return text


def remove_line_repetitions(text: str, min_repeat: int = 3) -> str:
    """Entfernt identische aufeinanderfolgende Absaetze/Zeilen."""
    lines = text.split('\n')
    result = []
    prev_line = None
    repeat_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped == prev_line and stripped and len(stripped) > 20:
            repeat_count += 1
            if repeat_count < min_repeat:
                result.append(line)
        else:
            repeat_count = 0
            result.append(line)
            prev_line = stripped

    return '\n'.join(result)


def remove_garbage_strings(text: str) -> str:
    """Entfernt Barcode-/Garbage-Artefakte (lange Zeichenketten ohne Woerter)."""
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        # Zeile mit >30 Zeichen, aber <20% Leerzeichen = Garbage
        if len(stripped) > 30:
            space_ratio = stripped.count(' ') / len(stripped)
            alpha_ratio = sum(1 for c in stripped if c.isalpha()) / len(stripped)
            # Wenig Spaces + hoher Anteil Grossbuchstaben/Ziffern = Garbage
            if space_ratio < 0.05 and alpha_ratio > 0.5:
                # Pruefe ob es ein normales langes Wort oder URL ist
                if not stripped.startswith('http') and not stripped.startswith('#'):
                    continue  # Skip garbage line
        # URL-Artefakte
        if re.match(r'^https?://.*\d{4}/\d{2}/\d{2}/\d{2}', stripped):
            continue
        result.append(line)
    return '\n'.join(result)


def remove_year_loops(text: str) -> str:
    """Entfernt Jahrzahl-Wiederholungen (z.B. 1969, 1969, 1969...)."""
    text = re.sub(r'(\d{4})(,?\s*\1){4,}', r'\1', text)
    return text


def deduplicate_ocr(text: str) -> str:
    """Wendet alle Bereinigungen an."""
    text = remove_garbage_strings(text)
    text = remove_year_loops(text)
    text = remove_token_repetitions(text)
    text = remove_single_char_loops(text)
    text = remove_line_repetitions(text)
    # Mehrfache Leerzeilen reduzieren
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text


def process_doc(doc_id: str, dry_run: bool = False) -> dict:
    """Bereinigt alle OCR-Seiten eines Dokuments."""
    ocr_dir = Path("output/ocr_results")
    pages = sorted(ocr_dir.glob(f"{doc_id}_p*.md"))

    if not pages:
        print(f"  {doc_id}: Keine OCR-Dateien gefunden")
        return {"doc_id": doc_id, "pages": 0, "changes": 0}

    changes = 0
    for page_path in pages:
        original = page_path.read_text(encoding="utf-8")
        cleaned = deduplicate_ocr(original)

        if cleaned != original:
            changes += 1
            removed_chars = len(original) - len(cleaned)
            pct = removed_chars / len(original) * 100 if original else 0
            print(f"  {page_path.name}: {removed_chars:,} Zeichen entfernt ({pct:.0f}%)")
            if not dry_run:
                page_path.write_text(cleaned, encoding="utf-8")

    print(f"  {doc_id}: {len(pages)} Seiten, {changes} geaendert")
    return {"doc_id": doc_id, "pages": len(pages), "changes": changes}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="OCR-Halluzinationen bereinigen")
    parser.add_argument("--doc", nargs="+", required=True, help="Dokument-IDs")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen")
    args = parser.parse_args()

    total_changes = 0
    for doc_id in args.doc:
        result = process_doc(doc_id, dry_run=args.dry_run)
        total_changes += result["changes"]

    print(f"\nGesamt: {total_changes} Dateien geaendert"
          + (" (dry-run)" if args.dry_run else ""))
