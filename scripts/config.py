"""
Zentrale Konfiguration fuer das zbz-ocr-tei Projekt.

Alle Pfade, Modellnamen und Konstanten an einem Ort.
"""

import os
from pathlib import Path

# Projekt-Root (2 Ebenen ueber scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Verzeichnisse
DATA_DIR = PROJECT_ROOT / "data"
SCANS_DIR = DATA_DIR / "scans"
REFERENZ_TEI_DIR = DATA_DIR / "referenz-tei"

OUTPUT_DIR = PROJECT_ROOT / "output"
OCR_RESULTS_DIR = OUTPUT_DIR / "ocr_results"
MISTRAL_RESULTS_DIR = OUTPUT_DIR / "mistral_results"
EVALUATION_DIR = OUTPUT_DIR / "evaluation"
LAYOUT_DIR = OUTPUT_DIR / "layout"
CLASSIFICATION_DIR = OUTPUT_DIR / "classification"
TEI_DIR = OUTPUT_DIR / "tei"
LLM_CORRECTED_C_DIR = OUTPUT_DIR / "llm_corrected_c"
GEMINI_CORRECTED_A_DIR = OUTPUT_DIR / "gemini_corrected_a"
GEMINI_CORRECTED_B_DIR = OUTPUT_DIR / "gemini_corrected_b"
DOC_METADATA_PATH = DATA_DIR / "doc_metadata.json"

DOCS_DIR = PROJECT_ROOT / "docs"
IMAGES_DIR = DOCS_DIR / "images"

# OCR-Modelle
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-OCR-2"
MISTRAL_MODEL = "mistral-document-ai-2512"

# OCR-Prompts
DEEPSEEK_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."

# PDF-Rendering
DEFAULT_DPI = 300
WEB_DPI = 150

# Mistral API
MISTRAL_MAX_PAGES_PER_REQUEST = 30
MISTRAL_TIMEOUT_SECONDS = 120

# LLM Post-Processing (Anthropic)
LLM_CORRECTED_DIR = OUTPUT_DIR / "llm_corrected"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_MAX_RETRIES = 3
ANTHROPIC_TIMEOUT_SECONDS = 60

# Docling-Serve API
DOCLING_SERVE_URL = os.environ.get("DOCLING_SERVE_URL", "http://localhost:5001")

# Gemini API (Layout QA + Detect)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_DETECT_MODEL = GEMINI_MODEL  # gleich; bei Bedarf separat ueberschreiben

# Docling BlockType -> ZBZ Structural Tag
DOCLING_TO_ZBZ = {
    "title":          "zb_heading",
    "section_header": "zb_heading",
    "text":           "zb_paragraph",
    "paragraph":      "zb_paragraph",
    "list_item":      "zb_paragraph",
    "footnote":       "footnote",
    "caption":        "caption",
    "page_header":    "_filter",
    "page_footer":    "_filter",
    "picture":        "_skip",
    "figure":         "_skip",
    "table":          "zb_paragraph",
    "formula":        "zb_paragraph",
}

# Farben pro Label (RGB) fuer Overlay-Bilder
LABEL_COLORS = {
    "section_header": (255, 0, 0),       # Rot
    "title":          (255, 0, 0),       # Rot
    "text":           (0, 128, 0),       # Gruen
    "paragraph":      (0, 128, 0),       # Gruen
    "list_item":      (0, 128, 0),       # Gruen
    "footnote":       (0, 0, 255),       # Blau
    "caption":        (255, 165, 0),     # Orange
    "picture":        (128, 0, 128),     # Lila
    "figure":         (128, 0, 128),     # Lila
    "table":          (0, 128, 128),     # Teal
    "page_header":    (128, 128, 128),   # Grau
    "page_footer":    (128, 128, 128),   # Grau
    "formula":        (255, 0, 255),     # Magenta
}

# Dokument-Klassifikation (Typ B = zweispaltig)
TWO_COLUMN_DOCS = ["2530", "890", "3040"]

# Testplan
TESTPLAN = {
    "phase1": {
        "name": "Baseline (einspaltig)",
        "tests": [
            {"pdf": "2310.pdf", "pages": [1, 2], "type": "A", "lang": "FR", "desc": "JSTOR Rezension"},
            {"pdf": "1180.pdf", "pages": [1, 2], "type": "A", "lang": "DE/FR", "desc": "Jahresbericht"},
            {"pdf": "290.pdf", "pages": [0, 1], "type": "A", "lang": "FR", "desc": "Comptes Rendus"},
        ]
    },
    "phase2": {
        "name": "Zweispaltig",
        "tests": [
            {"pdf": "2530.pdf", "pages": [0, 1], "type": "B", "lang": "FR", "desc": "Zeitschrift zweispaltig"},
            {"pdf": "890.pdf", "pages": [1, 2], "type": "B", "lang": "DE", "desc": "Lehrerzeitung"},
            {"pdf": "3040.pdf", "pages": [0, 1], "type": "B", "lang": "FR", "desc": "Lexikon mit Fussnoten"},
        ]
    },
    "phase3": {
        "name": "Spezialformate",
        "tests": [
            {"pdf": "90.pdf", "pages": [1, 2], "type": "D", "lang": "DE", "desc": "Historisch 1944"},
            {"pdf": "1440.pdf", "pages": [0, 1], "type": "D", "lang": "DE", "desc": "Interview/Dialog"},
            {"pdf": "830.pdf", "pages": [0, 1], "type": "D", "lang": "FR", "desc": "Bildband"},
            {"pdf": "1330.pdf", "pages": [0, 1], "type": "D", "lang": "FR", "desc": "Sammelband"},
        ]
    },
    "phase4": {
        "name": "Monografien",
        "tests": [
            {"pdf": "40.pdf", "pages": [4, 5], "type": "C", "lang": "FR", "desc": "Roman"},
            {"pdf": "1520.pdf", "pages": [2, 3], "type": "C", "lang": "?", "desc": "Monografie"},
        ]
    },
}

# Phase-1-Tests (Kurzform fuer Mistral-Benchmark)
PHASE1_TESTS = TESTPLAN["phase1"]["tests"]

# Bekannte GND-Entitaeten (Seed fuer NER, genutzt von Downstream-Tools)
KNOWN_ENTITIES = {
    "Karl Jaspers": "GND:118557106",
    "Jaspers": "GND:118557106",
    "Jeanne Hersch": "GND:118815679",
    "Hersch": "GND:118815679",
    "Bergson": "GND:118509578",
    "Kierkegaard": "GND:118562002",
    "Heidegger": "GND:118547798",
    "Kant": "GND:118559796",
    "Platon": "GND:118594893",
    "Sartre": "GND:118605895",
    "Hannah Arendt": "GND:118502751",
}


def get_test_metadata(doc_id: str) -> dict | None:
    """Gibt TESTPLAN-Metadaten fuer eine doc_id zurueck."""
    for phase_data in TESTPLAN.values():
        for test in phase_data["tests"]:
            if test["pdf"].replace(".pdf", "") == doc_id:
                return test
    return None
