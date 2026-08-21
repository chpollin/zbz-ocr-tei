"""Single construction point for the Gemini client.

Three entry points build the same client: layout QA (scripts.layout.layout_qa_gemini),
document classification (scripts.ocr.classify_docs) and OCR correction
(scripts.ocr.gemini_ocr_correct). The key resolution and the fail-fast on a missing key
live here once, so a change to either reaches all three.

The environment wins over the value scripts.config reads from .env, so a shell export
overrides the stored key for a single run. The SDK import stays inside the function: the
audits and the test suite import these modules without google-genai installed.
"""

import os
import sys

from scripts.config import GEMINI_API_KEY


def api_key() -> str:
    """Resolved Gemini key; empty string when neither environment nor .env carries one."""
    return os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY


def get_client():
    """Gemini client. Missing key is a trust-boundary failure and exits with code 1."""
    from google import genai

    key = api_key()
    if not key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt. Bitte in .env eintragen.")
        sys.exit(1)
    return genai.Client(api_key=key)
