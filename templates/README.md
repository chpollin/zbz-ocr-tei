# TEI-Templates

Templates für die LLM-gestützte TEI-Transformation.

## Übersicht

| Template | Dokumenttyp | Beispiel-PDF |
|----------|-------------|--------------|
| `tei_base.xml` | Grundgerüst | - |
| `tei_essay.xml` | Essay/Artikel | 2310, 290, 1180 |
| `tei_review.xml` | Rezension | 2310 |
| `tei_interview.xml` | Interview | 1440 |
| `tei_lexicon.xml` | Lexikonartikel | 3040 |

## Platzhalter

Die Templates verwenden `{{PLATZHALTER}}` für variable Inhalte:

| Platzhalter | Beschreibung |
|-------------|--------------|
| `{{DOCUMENT_ID}}` | Projekt-ID (z.B. 2310) |
| `{{CREATOR_EMAIL}}` | E-Mail des Erstellers |
| `{{PAGE_NUM}}` | Seitennummer für facs-Attribut |
| `{{PAGE_LABEL}}` | Gedruckte Seitenzahl |
| `{{PERSON_GND}}` | GND-ID einer Person |
| `{{WORK_GND}}` | GND-ID eines Werks |

## Dokumenttyp-Erkennung

Der Dokumenttyp wird erkannt durch:

1. **Rezension**: Beginnt mit bibliografischer Angabe (Autor, Titel, Verlag)
2. **Interview**: Frage-Antwort-Struktur, oft mit Einleitung/Epigraph
3. **Lexikon**: Lemma mit Lebensdaten, strukturierte Abschnitte
4. **Essay**: Fließtext ohne spezielle Struktur

## Verwendung in Pipeline

```python
def select_template(ocr_text: str, metadata: dict) -> str:
    """Wählt Template basierend auf Dokumentanalyse."""
    if has_qa_structure(ocr_text):
        return "tei_interview.xml"
    elif starts_with_bibliographic(ocr_text):
        return "tei_review.xml"
    elif has_lemma_structure(ocr_text):
        return "tei_lexicon.xml"
    else:
        return "tei_essay.xml"
```

## Validierung

Generierte TEI-Dateien müssen validiert werden gegen:
- XML-Wohlgeformtheit (lxml)
- TEI P5 Schema (RelaxNG)

---

*Erstellt: 29.01.2026*
