"""
PP-OCRv6 Comprehensive Evaluation & Inference Suite based on official documentation.
Tests PP-OCRv6 across:
  1. PP-OCRv6_tiny (1.5M params - IoT / Edge)
  2. PP-OCRv6_small (7.7M params - Mobile / Desktop)
  3. PP-OCRv6_medium (34.5M params - Server Grade Flagship)
Evaluates multi-language text (English, Chinese, Numbers, Symbols) and benchmarks latency.
"""

import os
# oneDNN CPU execution compatibility flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import time
from PIL import Image, ImageDraw, ImageFont
import paddleocr
from paddleocr import PaddleOCR


def create_multilingual_benchmark_image(filepath="benchmark_ppocrv6.png"):
    """Creates a multi-scenario, multi-lingual test image."""
    width, height = 850, 220
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Outer decorative frame
    draw.rectangle([(8, 8), (width - 8, height - 8)], outline=(20, 80, 180), width=3)

    # Test text lines covering English, Chinese, Numbers, and symbols
    lines = [
        "PP-OCRv6 Universal Text Recognition Benchmark",
        "Multi-Language: English, 简体中文, 1234567890, Special: @#$%",
        "Industrial Layout: PART-NO: SN-88392-ZX | QC: PASS",
        "High Efficiency & Accuracy Lightweight Deep Learning",
    ]

    y_pos = 25
    for line in lines:
        draw.text((25, y_pos), line, fill=(15, 15, 15))
        y_pos += 45

    img.save(filepath)
    print(f"[INFO] Created multi-scenario test image: {filepath}")
    return filepath


def evaluate_tier(tier_name: str, det_model: str, rec_model: str, image_path: str):
    print("\n" + "=" * 65)
    print(f" EVALUATING PP-OCRv6 TIER: {tier_name.upper()}")
    print(f" Detection Model  : {det_model}")
    print(f" Recognition Model: {rec_model}")
    print("=" * 65)

    start_init = time.time()
    ocr = PaddleOCR(
        text_detection_model_name=det_model,
        text_recognition_model_name=rec_model,
        use_textline_orientation=True,
    )
    init_time = (time.time() - start_init) * 1000
    print(f"[INFO] Pipeline Initialized in {init_time:.1f} ms")

    # Warmup + Inference Timing
    start_infer = time.time()
    results = ocr.predict(image_path)
    infer_time = (time.time() - start_infer) * 1000

    print("\n[EXTRACTED TEXT LINES]")
    line_count = 0
    total_conf = 0.0

    for res in results:
        rec_texts = res.get("rec_texts", [])
        rec_scores = res.get("rec_scores", [])
        for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
            line_count += 1
            total_conf += float(score)
            print(f"  Line {line_count}: \"{text}\" (conf: {float(score):.4f})")

    avg_conf = (total_conf / line_count) if line_count > 0 else 0.0
    print("-" * 65)
    print(f"  Latency       : {infer_time:.2f} ms")
    print(f"  Lines Found   : {line_count}")
    print(f"  Avg Confidence: {avg_conf:.4f}")
    print("=" * 65)

    return {
        "tier": tier_name,
        "det_model": det_model,
        "rec_model": rec_model,
        "latency_ms": infer_time,
        "lines": line_count,
        "confidence": avg_conf,
    }


def main():
    print("*" * 65)
    print(" PP-OCRv6 OFFICIAL ARCHITECTURE BENCHMARK (AWS EC2)")
    print("*" * 65)

    test_image = create_multilingual_benchmark_image()

    tiers = [
        ("Small", "PP-OCRv6_small_det", "PP-OCRv6_small_rec"),
        ("Tiny", "PP-OCRv6_tiny_det", "PP-OCRv6_tiny_rec"),
        ("Medium", "PP-OCRv6_medium_det", "PP-OCRv6_medium_rec"),
    ]

    summary = []
    for tier_name, det, rec in tiers:
        try:
            stats = evaluate_tier(tier_name, det, rec, test_image)
            summary.append(stats)
        except Exception as e:
            print(f"[ERROR in {tier_name}]: {e}")

    print("\n" + "#" * 65)
    print(" PP-OCRv6 TIERS COMPARISON SUMMARY")
    print("#" * 65)
    print(f"{'Tier':<10} | {'Latency (ms)':<14} | {'Lines Detected':<16} | {'Avg Confidence':<14}")
    print("-" * 65)
    for s in summary:
        print(f"{s['tier']:<10} | {s['latency_ms']:<14.2f} | {s['lines']:<16} | {s['confidence']:<14.4f}")
    print("#" * 65)


if __name__ == "__main__":
    main()
