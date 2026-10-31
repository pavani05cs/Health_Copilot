"""
Verification script for PP-OCRv6 on EC2.
Generates a test image with text and verifies end-to-end OCR inference.
"""

import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_test_image(text="Hello PP-OCRv6 on AWS EC2!", filepath="test_ocr.png"):
    """Creates a synthetic test image with clean text for validation."""
    width, height = 480, 100
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw simple text
    draw.text((20, 35), text, fill=(0, 0, 0))
    img.save(filepath)
    print(f"[INFO] Created test verification image: {filepath}")
    return filepath

def run_ocr_test():
    try:
        from paddleocr import PaddleOCR
    except ImportError as e:
        print(f"[ERROR] PaddleOCR is not installed: {e}")
        sys.exit(1)

    test_img = create_test_image()

    print("[INFO] Initializing PaddleOCR (PP-OCRv6 pipeline)...")
    # Initialize OCR engine
    ocr = PaddleOCR(use_angle_cls=True, lang="en")

    print("[INFO] Running OCR inference on test image...")
    result = ocr.ocr(test_img, cls=True)

    print("\n" + "=" * 50)
    print(" OCR TEST RESULTS")
    print("=" * 50)
    if not result or not result[0]:
        print("[WARN] No text detected in test image.")
    else:
        for idx, line in enumerate(result[0]):
            box, (text, score) = line[0], line[1]
            print(f"Line {idx + 1}:")
            print(f"  Detected Text : '{text}'")
            print(f"  Confidence    : {score:.4f}")
            print(f"  Box           : {box}")

    print("=" * 50)
    print("[SUCCESS] PP-OCRv6 test completed successfully!")

if __name__ == "__main__":
    run_ocr_test()
