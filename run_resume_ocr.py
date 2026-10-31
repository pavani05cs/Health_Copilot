"""
Run PP-OCRv6 OCR on uploaded Resume PDF via EC2
Converts PDF pages to high-res images and executes PP-OCRv6 Small & Medium pipeline.
"""

import os
# oneDNN CPU execution compatibility flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import json
import time
from pathlib import Path
import pypdfium2 as pdfium
from paddleocr import PaddleOCR


def render_pdf_to_images(pdf_path: str, scale: float = 2.0):
    """Renders PDF pages to PNG images."""
    print(f"[INFO] Opening PDF: {pdf_path}")
    pdf = pdfium.PdfDocument(pdf_path)
    page_count = len(pdf)
    print(f"[INFO] Total pages: {page_count}")

    image_paths = []
    for i in range(page_count):
        page = pdf[i]
        # render at scale for crisp OCR (2.0 = ~144 DPI, 3.0 = ~216 DPI)
        image = page.render(scale=scale).to_pil()
        out_path = f"resume_page_{i + 1}.png"
        image.save(out_path)
        print(f"[INFO] Rendered Page {i + 1} -> {out_path} ({image.width}x{image.height})")
        image_paths.append(out_path)

    return image_paths


def run_ocr(pdf_path="resume.pdf", tier="small"):
    print("=" * 65)
    print(f" RUNNING PP-OCRv6 ({tier.upper()}) ON RESUME VIA EC2")
    print("=" * 65)

    images = render_pdf_to_images(pdf_path)

    det_model = f"PP-OCRv6_{tier}_det"
    rec_model = f"PP-OCRv6_{tier}_rec"

    print(f"\n[INFO] Loading PP-OCRv6 {tier.upper()} model ({det_model}, {rec_model})...")
    ocr = PaddleOCR(
        text_detection_model_name=det_model,
        text_recognition_model_name=rec_model,
        use_textline_orientation=True,
    )

    full_document_results = []

    for page_idx, img_path in enumerate(images):
        page_num = page_idx + 1
        print(f"\n>>> Processing Page {page_num}...")
        start_t = time.time()
        results = ocr.predict(img_path)
        latency = (time.time() - start_t) * 1000

        page_data = {
            "page": page_num,
            "image": img_path,
            "latency_ms": latency,
            "lines": [],
        }

        for res in results:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            polys = res.get("rec_polys", [])

            # Pair items
            paired = []
            for i, (t, s) in enumerate(zip(texts, scores)):
                poly = polys[i].tolist() if i < len(polys) and hasattr(polys[i], "tolist") else []
                # Compute centroid or top-left y for sorting
                top_y = min(p[1] for p in poly) if poly else 0
                left_x = min(p[0] for p in poly) if poly else 0
                paired.append({
                    "text": str(t).strip(),
                    "confidence": float(s),
                    "box": poly,
                    "top_y": top_y,
                    "left_x": left_x,
                })

            # Sort primarily by vertical position (with ~15px line grouping tolerance), then by horizontal
            paired.sort(key=lambda item: (round(item["top_y"] / 15) * 15, item["left_x"]))

            for idx, item in enumerate(paired):
                line_entry = {
                    "line_number": idx + 1,
                    "text": item["text"],
                    "confidence": item["confidence"],
                    "box": item["box"],
                }
                page_data["lines"].append(line_entry)
                print(f"  [{idx + 1:02d}] ({item['confidence']*100:.1f}%) {item['text']}")

        full_document_results.append(page_data)
        print(f"[PAGE {page_num} COMPLETE] Found {len(page_data['lines'])} lines in {latency:.1f} ms")

    # Save to JSON
    with open("resume_ocr_result.json", "w", encoding="utf-8") as f:
        json.dump(full_document_results, f, indent=2, ensure_ascii=False)

    # Save formatted text summary
    with open("resume_ocr_result.txt", "w", encoding="utf-8") as f:
        f.write("=" * 65 + "\n")
        f.write(" PP-OCRv6 RESUME OCR EXTRACTION RESULTS\n")
        f.write("=" * 65 + "\n\n")
        for p in full_document_results:
            f.write(f"--- PAGE {p['page']} ({len(p['lines'])} lines, {p['latency_ms']:.1f}ms) ---\n")
            for l in p["lines"]:
                f.write(f"{l['text']}\n")
            f.write("\n")

    print("\n" + "=" * 65)
    print("[SUCCESS] Full Document OCR Completed!")
    print("Saved output to: resume_ocr_result.json and resume_ocr_result.txt")
    print("=" * 65)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="small", choices=["tiny", "small", "medium"])
    args = parser.parse_args()
    run_ocr("resume.pdf", tier=args.tier)
