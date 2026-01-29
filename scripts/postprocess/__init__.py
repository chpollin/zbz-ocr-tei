"""
Post-Processing Pipeline für OCR-Texte.

Transformiert rohen OCR-Output in bereinigten Text:
- Zeichennormalisierung
- Silbentrennung auflösen
- Markdown entfernen
- Whitespace normalisieren
"""

from .normalize import normalize_text
from .dehyphenate import dehyphenate
from .clean_markdown import clean_markdown
from .pipeline import postprocess

__all__ = ['normalize_text', 'dehyphenate', 'clean_markdown', 'postprocess']
