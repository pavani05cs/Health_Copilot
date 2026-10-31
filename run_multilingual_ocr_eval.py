import os
import sys
import json
import time

# Set oneDNN & Paddle environment flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
sys.stdout.reconfigure(encoding='utf-8')

from paddleocr import PaddleOCR

print("=" * 70)
print("     MULTILINGUAL PP-OCR BENCHMARK & EVALUATION ON AWS EC2")
print("=" * 70)

TEST_DIR = "/home/ubuntu/multilingual_test"
telugu_img = os.path.join(TEST_DIR, "dummy_telugu_rx.png")
hindi_img = os.path.join(TEST_DIR, "dummy_hindi_rx.png")

results = {}

def evaluate_engine(name, engine, img_path):
    print(f"\n---> Evaluating [{name}] on {os.path.basename(img_path)}...")
    t0 = time.time()
    res_list = engine.predict(img_path)
    elapsed_ms = (time.time() - t0) * 1000

    extracted_lines = []
    for res in res_list:
        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])
        for t, s in zip(texts, scores):
            extracted_lines.append({
                "text": str(t).strip(),
                "confidence": round(float(s), 4)
            })

    avg_conf = (
        sum(item["confidence"] for item in extracted_lines) / len(extracted_lines)
        if extracted_lines else 0.0
    )

    print(f"     Status: Success | Lines Extracted: {len(extracted_lines)} | Avg Confidence: {avg_conf:.4f} | Latency: {elapsed_ms:.1f}ms")
    return {
        "engine": name,
        "image": os.path.basename(img_path),
        "line_count": len(extracted_lines),
        "avg_confidence": round(avg_conf, 4),
        "latency_ms": round(elapsed_ms, 1),
        "lines": extracted_lines
    }

# 1. Initialize PP-OCRv6 Small (Default English/Latin)
print("\n[1/4] Initializing PP-OCRv6 Small (Default Latin/English)...")
engine_ppocrv6_small = PaddleOCR(
    text_detection_model_name="PP-OCRv6_small_det",
    text_recognition_model_name="PP-OCRv6_small_rec",
    use_textline_orientation=True
)

# Test PP-OCRv6 on Telugu Rx
results["ppocrv6_telugu"] = evaluate_engine("PP-OCRv6_small (lang=en)", engine_ppocrv6_small, telugu_img)

# Test PP-OCRv6 on Hindi Rx
results["ppocrv6_hindi"] = evaluate_engine("PP-OCRv6_small (lang=en)", engine_ppocrv6_small, hindi_img)

# 2. Initialize Telugu Engine (lang="te")
print("\n[2/4] Initializing PaddleOCR Telugu Engine (lang='te')...")
engine_te = PaddleOCR(lang="te", use_textline_orientation=True)

# Test Telugu Engine on Telugu Rx
results["te_engine_telugu"] = evaluate_engine("PaddleOCR_Telugu (lang=te)", engine_te, telugu_img)

# 3. Initialize Hindi Engine (lang="hi")
print("\n[3/4] Initializing PaddleOCR Hindi Engine (lang='hi')...")
engine_hi = PaddleOCR(lang="hi", use_textline_orientation=True)

# Test Hindi Engine on Hindi Rx
results["hi_engine_hindi"] = evaluate_engine("PaddleOCR_Hindi (lang=hi)", engine_hi, hindi_img)

# 4. Save detailed benchmark results
output_json = os.path.join(TEST_DIR, "multilingual_benchmark_results.json")
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print(f"Benchmark results successfully saved to {output_json}")
print("=" * 70)

# Print Summary Comparison Table
print("\n=== SUMMARY COMPARISON ===")
print(f"{'Engine':<28} | {'Document':<18} | {'Lines':<6} | {'Avg Conf':<9} | {'Latency'}")
print("-" * 75)
for key, r in results.items():
    print(f"{r['engine']:<28} | {r['image']:<18} | {r['line_count']:<6} | {r['avg_confidence']:<9.4f} | {r['latency_ms']} ms")

# Print Detailed Side-by-Side Sample Lines for Telugu
print("\n=== TELUGU SAMPLE LINES COMPARISON ===")
print("--- [PP-OCRv6 (Latin)] Sample Detections ---")
for line in results["ppocrv6_telugu"]["lines"][:12]:
    print(f"  [{line['confidence']:.2f}] {line['text']}")

print("\n--- [PaddleOCR Telugu (lang=te)] Sample Detections ---")
for line in results["te_engine_telugu"]["lines"][:12]:
    print(f"  [{line['confidence']:.2f}] {line['text']}")

# Print Detailed Side-by-Side Sample Lines for Hindi
print("\n=== HINDI SAMPLE LINES COMPARISON ===")
print("--- [PP-OCRv6 (Latin)] Sample Detections ---")
for line in results["ppocrv6_hindi"]["lines"][:12]:
    print(f"  [{line['confidence']:.2f}] {line['text']}")

print("\n--- [PaddleOCR Hindi (lang=hi)] Sample Detections ---")
for line in results["hi_engine_hindi"]["lines"][:12]:
    print(f"  [{line['confidence']:.2f}] {line['text']}")
