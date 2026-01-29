#!/usr/bin/env python3
"""
Test DeepSeek-OCR-2 with column-aware prompt for two-column documents.

Tests if different prompts can improve column reading order.
"""

import sys
import torch
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_gpu():
    """Check GPU availability."""
    if not torch.cuda.is_available():
        print("[WARN] CUDA not available, using CPU (slow)")
        return False
    print(f"[OK] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[OK] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    return True


def load_model():
    """Load DeepSeek-OCR-2 model."""
    from transformers import AutoModel, AutoTokenizer

    print("Loading DeepSeek-OCR-2 model...")
    model = AutoModel.from_pretrained(
        'deepseek-ai/DeepSeek-OCR-2',
        trust_remote_code=True
    )
    model = model.eval().cuda().to(torch.bfloat16)

    tokenizer = AutoTokenizer.from_pretrained(
        'deepseek-ai/DeepSeek-OCR-2',
        trust_remote_code=True
    )

    print("[OK] Model loaded")
    return model, tokenizer


def pdf_to_images(pdf_path: Path, dpi: int = 300) -> list:
    """Convert PDF pages to images."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    images = []

    for i, page in enumerate(pdf):
        bitmap = page.render(scale=dpi/72)
        pil_image = bitmap.to_pil()
        images.append((i + 1, pil_image))

    return images


def run_ocr(model, tokenizer, image_path: Path, output_dir: Path, prompt: str) -> str:
    """
    Run OCR with specific prompt using DeepSeek's infer method.

    Returns the extracted text.
    """
    # Run OCR
    model.infer(
        tokenizer,
        prompt=prompt,
        image_file=str(image_path),
        output_path=str(output_dir),
        base_size=1024,
        image_size=768,
        crop_mode=True,
        save_results=True
    )

    # Read result from result.mmd
    result_file = output_dir / "result.mmd"
    if result_file.exists():
        text = result_file.read_text(encoding='utf-8')
        return text
    return ""


def test_prompts(model, tokenizer, image_path: Path, output_dir: Path):
    """
    Test different prompts for column handling.
    """
    prompts = {
        "standard": "<image>\n<|grounding|>Convert the document to markdown.",

        "column_v1": "<image>\n<|grounding|>This is a two-column document. Read the LEFT column completely first from top to bottom, then read the RIGHT column from top to bottom. Convert to markdown.",

        "column_v2": "<image>\n<|grounding|>Document with two columns. Important: First extract ALL text from the left column (top to bottom), then ALL text from the right column (top to bottom). Output as markdown.",

        "no_grounding": "<image>\nConvert this two-column document to markdown. Read left column first, then right column.",
    }

    results = {}
    temp_dir = output_dir / "temp_ocr"

    for name, prompt in prompts.items():
        print(f"\n  Testing prompt: {name}")
        print("-" * 40)

        # Clean temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)

        try:
            text = run_ocr(model, tokenizer, image_path, temp_dir, prompt)

            if text:
                # Save output
                output_file = output_dir / f"{image_path.stem}_{name}.md"
                output_file.write_text(text, encoding="utf-8")

                results[name] = text
                print(f"  [OK] Output: {len(text)} chars")
                print(f"  Saved to: {output_file.name}")

                # Show first 300 chars
                preview = text[:300].replace("\n", " ")
                print(f"  Preview: {preview}...")
            else:
                print("  [WARN] No output")
                results[name] = None

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            results[name] = None

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("DeepSeek-OCR-2 Column-Aware Prompt Test")
    print("=" * 60)

    # Check GPU
    if not check_gpu():
        print("\nGPU required for reasonable performance.")
        return 1

    # Paths
    scans_dir = PROJECT_ROOT / "data" / "scans"
    output_dir = PROJECT_ROOT / "output" / "column_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test PDF
    pdf_path = scans_dir / "2530.pdf"

    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return 1

    # Convert first page to image
    print(f"\nConverting {pdf_path.name} to images...")
    images = pdf_to_images(pdf_path)
    print(f"[OK] {len(images)} pages")

    # Save first page as image for testing
    page_num, img = images[0]
    img_path = output_dir / f"{pdf_path.stem}_p{page_num}.png"
    img.save(str(img_path))
    print(f"[OK] Saved: {img_path}")

    # Load model
    model, tokenizer = load_model()

    # Test prompts
    print("\n" + "=" * 60)
    print("Testing different prompts...")
    print("=" * 60)

    results = test_prompts(model, tokenizer, img_path, output_dir)

    # Summary
    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)

    for name, text in results.items():
        if text:
            print(f"\n{name}:")
            print(f"  Length: {len(text)} chars")
            # Show first words as order indicator
            words = text.split()[:20]
            print(f"  First 20 words: {' '.join(words)}...")
        else:
            print(f"\n{name}: FAILED")

    print("\n" + "=" * 60)
    print("Output files saved to: " + str(output_dir))
    print("Compare outputs manually to determine best prompt.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
