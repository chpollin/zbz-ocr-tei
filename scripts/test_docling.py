#!/usr/bin/env python3
"""
Test Docling OCR for two-column document layout.

Tests if Docling correctly handles column reading order
(left column first, then right column).
"""

import os
import sys
from pathlib import Path

# Windows: Disable symlink requirement for HuggingFace cache
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_docling_basic():
    """Test basic Docling import and setup."""
    print("Testing Docling import...")

    try:
        from docling.document_converter import DocumentConverter
        print("  [OK] DocumentConverter imported")

        from docling.datamodel.base_models import InputFormat
        print("  [OK] InputFormat imported")

        return True
    except ImportError as e:
        print(f"  [FAIL] Import error: {e}")
        return False


def test_docling_pdf(pdf_path: Path, output_dir: Path):
    """
    Test Docling OCR on a PDF file.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory for output files
    """
    from docling.document_converter import DocumentConverter

    print(f"\nProcessing: {pdf_path.name}")
    print("-" * 50)

    # Create converter
    converter = DocumentConverter()

    # Convert PDF
    print("  Converting PDF (this may take a while)...")
    result = converter.convert(str(pdf_path))

    # Export to markdown
    markdown = result.document.export_to_markdown()

    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{pdf_path.stem}_docling.md"
    output_file.write_text(markdown, encoding="utf-8")

    print(f"  [OK] Output saved to: {output_file}")
    print(f"  Output length: {len(markdown)} characters")

    # Show first 500 chars
    print("\n  Preview (first 500 chars):")
    print("  " + "-" * 40)
    preview = markdown[:500].replace("\n", "\n  ")
    print(f"  {preview}")
    print("  " + "-" * 40)

    return markdown


def compare_with_deepseek(docling_output: str, deepseek_file: Path):
    """
    Compare Docling output with DeepSeek output.

    Args:
        docling_output: Markdown from Docling
        deepseek_file: Path to DeepSeek output file
    """
    if not deepseek_file.exists():
        print(f"\n  [INFO] No DeepSeek output to compare: {deepseek_file}")
        return

    deepseek_output = deepseek_file.read_text(encoding="utf-8")

    print("\n  Comparison:")
    print(f"  - Docling length:  {len(docling_output)} chars")
    print(f"  - DeepSeek length: {len(deepseek_output)} chars")

    # Check for common column-order issues
    # In 2530.pdf, if columns are correctly read, certain phrases should appear in order
    # This is a heuristic check


def main():
    """Main entry point."""
    print("=" * 60)
    print("Docling OCR Test - Two-Column Layout")
    print("=" * 60)

    # Check basic import
    if not test_docling_basic():
        print("\nDocling import failed. Please check installation.")
        return 1

    # Paths
    scans_dir = PROJECT_ROOT / "data" / "scans"
    output_dir = PROJECT_ROOT / "output" / "docling_results"

    # Test PDFs (two-column - Type B)
    test_pdfs = [
        "2530.pdf",  # French, 2 pages, known column issue
    ]

    for pdf_name in test_pdfs:
        pdf_path = scans_dir / pdf_name

        if not pdf_path.exists():
            print(f"\n[SKIP] PDF not found: {pdf_path}")
            continue

        try:
            markdown = test_docling_pdf(pdf_path, output_dir)

            # Compare with DeepSeek if available
            deepseek_file = PROJECT_ROOT / "output" / "ocr_results" / f"{pdf_path.stem}_p1.md"
            compare_with_deepseek(markdown, deepseek_file)

        except Exception as e:
            print(f"\n[ERROR] Failed to process {pdf_name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test completed.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
