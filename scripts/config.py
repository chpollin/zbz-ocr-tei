"""
Zentrale Konfiguration fuer das zbz-ocr-tei Projekt.

Alle Pfade, Modellnamen und Konstanten an einem Ort.
"""

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
TEI_DIR = OUTPUT_DIR / "tei"
LAYOUT_DIR = OUTPUT_DIR / "layout"

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

# TEI Dokumenttypen
DOC_TYPES = {
    "review": 'div type="review"',
    "interview": 'div type="interview"',
    "essay": 'div n="1"',
    "lexicon": 'div type="entry"',
}

# Bekannte GND-Entitaeten (Seed fuer NER)
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
