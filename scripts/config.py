"""
Zentrale Konfiguration fuer das zbz-ocr-tei Projekt.

Alle Pfade, Modellnamen und Konstanten an einem Ort.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Projekt-Root (2 Ebenen ueber scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Verzeichnisse
DATA_DIR = PROJECT_ROOT / "data"

# Quelldaten (ZB-Lieferung, immutabler Input): alles unter data/source/
SOURCE_DIR = DATA_DIR / "source"
SCANS_DIR = SOURCE_DIR / "pdf"                                 # PDF-Scans (ZB-Digitalisate)
REFERENCE_TEI_DIR = SOURCE_DIR / "reference_tei"               # Transkribus-erstellte Referenz-/Gold-TEI
TRANSKRIBUS_PAGE_XML_DIR = SOURCE_DIR / "transkribus_page_xml"  # PAGE-XML-Exporte aus Transkribus
GUIDELINES_DIR = SOURCE_DIR / "guidelines"                     # Editionsrichtlinien (ZBZ)
MASTERFILE_DIR = SOURCE_DIR / "masterfile"                     # Masterfile.xlsx (Katalog + Steuerung)
MASTERFILE_PATH = MASTERFILE_DIR / "Masterfile.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "output"
OCR_RESULTS_DIR = OUTPUT_DIR / "ocr_results"
MISTRAL_RESULTS_DIR = OUTPUT_DIR / "mistral_results"
OCR_CURATED_DIR = OUTPUT_DIR / "ocr_curated"                   # vom Viewer kuratiertes OCR (hoechste Prioritaet)
EVALUATION_DIR = OUTPUT_DIR / "evaluation"
LAYOUT_DIR = OUTPUT_DIR / "layout"
CLASSIFICATION_DIR = OUTPUT_DIR / "classification"
TEI_DIR = OUTPUT_DIR / "tei"
TEI_UNIFIED_DIR = OUTPUT_DIR / "tei_unified"
TEI_CURATED_DIR = DATA_DIR / "curated_tei"
TEI_FINAL_DIR = OUTPUT_DIR / "tei_final"
TEI_PREVIEW_DIR = OUTPUT_DIR / "tei_preview"        # reversible M3-Vorschau, beruehrt tei_final nie

# TEI-Konstanten
TEI_NS = "http://www.tei-c.org/ns/1.0"

# Div-Typen aus Editionsrichtlinien ZBZ (verbindlich)
_RICHTLINIEN_DIV_TYPES = {
    "review", "interview", "conversation", "entry",
    "bibliography", "editorial", "translation",
    "reprint", "otherEdition", "dedication", "foreign",
}
# Erweiterte Div-Typen aus Pipeline-Genre-Inferenz (nicht in Richtlinien,
# aber real im Korpus und in 285 generierten TEIs vorhanden)
_PIPELINE_DIV_TYPES = {
    "text", "redactional", "speech", "conference",
    "letter", "preface", "sub-section",
    "source-metadata",  # kuratiert: e-periodica-Metadatenseite (z.B. Doc 1170)
}
VALID_DIV_TYPES = _RICHTLINIEN_DIV_TYPES | _PIPELINE_DIV_TYPES

# Schema-Validierung (zbz_hersch.rng: projektspezifisch, aus ODD generiert)
TEI_SCHEMA_DIR = DATA_DIR / "schema"
TEI_SCHEMA_PATH = TEI_SCHEMA_DIR / "zbz_hersch.rng"
LLM_CORRECTED_C_DIR = OUTPUT_DIR / "llm_corrected_c"
GEMINI_CORRECTED_A_DIR = OUTPUT_DIR / "gemini_corrected_a"
GEMINI_CORRECTED_B_DIR = OUTPUT_DIR / "gemini_corrected_b"
PAGE_XML_DIR = OUTPUT_DIR / "page_xml"
DOC_METADATA_PATH = DATA_DIR / "doc_metadata.json"  # generierte Gemini-Klassifikation (committeter Cache)

DOCS_DIR = PROJECT_ROOT / "docs"
IMAGES_DIR = DOCS_DIR / "images"

# OCR-Modelle
MISTRAL_MODEL = "mistral-document-ai-2512"

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

# Gemini vision OCR model; engine "auto" resolves to it since the Mistral endpoint went away,
# the Mistral path stays selectable as the reproducibility record of the delivered corpus.
GEMINI_OCR_MODEL = "gemini-3.1-flash-lite"


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

# ZBZ Structural Tag -> PAGE-XML Region Type
ZBZ_TO_PAGE_TYPE = {
    "zb_heading":    "heading",
    "zb_paragraph":  "paragraph",
    "footnote":      "footnote",
    "caption":       "caption",
    "_filter":       None,
    "_skip":         None,
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

def get_test_metadata(doc_id: str) -> dict | None:
    """Gibt TESTPLAN-Metadaten fuer eine doc_id zurueck."""
    for phase_data in TESTPLAN.values():
        for test in phase_data["tests"]:
            if test["pdf"].replace(".pdf", "") == doc_id:
                return test
    return None
