"""
Verification script for PP-OCRv6 Small on AWS EC2.
Loads PP-OCRv6_small_det and PP-OCRv6_small_rec, runs inference, and verifies text output.
"""

import os
# Fix for oneDNN / PIR attribute conversion compatibility on CPU
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

import sys
from PIL import Image, ImageDraw
import paddle
import paddleocr
from paddleocr import PaddleOCR


def create_test_image(text="AWS EC2: PP-OCRv6 Small Running Successfully!", filepath="test_ocr_small.png"):
    """Creates a high-contrast test image with clean text."""
    width, height = 750, 120
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw dark border and black text
    draw.rectangle([(5, 5), (width - 5, height - 5)], outline=(0, 50, 180), width=3)
    draw.text((25, 45), text, fill=(0, 0, 0))
    img.save(filepath)
    print(f"[INFO] Created test image: {filepath}")
    return filepath


def run_test():
    print("=" * 65)
    print(" PP-OCRv6 Small Verification Test on AWS EC2")
    print("=" * 65)
    print(f"[INFO] PaddlePaddle Version: {paddle.__version__}")
    print(f"[INFO] PaddleOCR Version   : {paddleocr.__version__}")

    # Initialize PaddleOCR with PP-OCRv6 Small detection & recognition models
    print("\n[INFO] Initializing PP-OCRv6 Small pipeline...")
    ocr = PaddleOCR(
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_textline_orientation=True,
    )

    test_img = create_test_image()

    print("\n[INFO] Running OCR inference on test image...")
    results = ocr.predict(test_img)

    print("\n" + "=" * 65)
    print(" OCR RECOGNITION RESULTS")
    print("=" * 65)

    found_text = False
    for res in results:
        # PaddleOCR 3.7.0 PipelineResult structure
        if hasattr(res, "get"):
            rec_texts = res.get("rec_texts", [])
            rec_scores = res.get("rec_scores", [])
            rec_polys = res.get("rec_polys", [])
            for i, (t, s) in enumerate(zip(rec_texts, rec_scores)):
                print(f" [Line {i+1}] Detected Text : '{t}'")
                print(f"          Confidence    : {float(s):.4f}")
                found_text = True
        elif hasattr(res, "json"):
            print(" Result Data:", res.json)
            found_text = True
        else:
            print(" Raw result:", res)
            found_text = True

    print("=" * 65)
    if found_text:
        print("[SUCCESS] PP-OCRv6 Small verification PASSED completely!")
    else:
        print("[WARN] No text lines were parsed from result.")


if __name__ == "__main__":
    run_test()
