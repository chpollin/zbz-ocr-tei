"""
Zentraler Gemini-API-Client mit Retry-Logik und Rate-Limit-Handling.

Ersetzt duplizierte Client-Erzeugung und API-Key-Loading
in gemini_ocr_correct, layout_qa_gemini, tei_gemini, tei_unified, classify_docs.
"""

import os
import time
import warnings

# Suppress Gemini SDK thought_signature warnings (alle Gemini-Scripts betroffen)
warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")


def get_client():
    """Erstellt Gemini-Client mit API-Key aus Environment.

    Laedt .env automatisch falls noetig. Prueft os.environ und
    config.GEMINI_API_KEY als Fallback.

    Raises:
        RuntimeError: Wenn GEMINI_API_KEY nicht gesetzt ist.
    """
    from google import genai
    from scripts.utils import load_env

    load_env()
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY nicht gesetzt. "
            "Bitte in .env oder als Umgebungsvariable definieren."
        )
    return genai.Client(api_key=api_key)


def has_api_key() -> bool:
    """Prueft ob ein Gemini API-Key verfuegbar ist (ohne Client zu erstellen)."""
    from scripts.utils import load_env
    load_env()
    return bool(os.environ.get("GEMINI_API_KEY", ""))


def call_gemini(client, model, contents, config=None, retries=3, base_delay=15):
    """Gemini-API-Call mit Rate-Limit-Retry.

    Args:
        client: genai.Client-Instanz
        model: Modellname (z.B. "gemini-3.1-flash-lite-preview")
        contents: Prompt-Contents (Text, Bilder, etc.)
        config: Optionale GenerateContentConfig
        retries: Maximale Anzahl Versuche bei Rate-Limit
        base_delay: Basis-Wartezeit in Sekunden (wird pro Versuch multipliziert)

    Returns:
        GenerateContentResponse

    Raises:
        RuntimeError: Nach Erschoepfung aller Retries
        Exception: Bei nicht-Rate-Limit-Fehlern
    """
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                delay = base_delay * (attempt + 1)
                print(f"  Rate limit, warte {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Gemini-API nach {retries} Versuchen fehlgeschlagen")
