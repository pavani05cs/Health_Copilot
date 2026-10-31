import os
import sys
import json
import time

# Set oneDNN / CPU flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
sys.stdout.reconfigure(encoding='utf-8')

from paddleocr import PaddleOCR
from PIL import Image

print("=" * 70)
print("     SANITY TEST: PADDLEOCR TELUGU & HINDI PP-OCRV5 ON EC2")
print("=" * 70)

TEST_DIR = "/home/ubuntu/multilingual_test"
telugu_img_path = os.path.join(TEST_DIR, "dummy_telugu_rx.png")
hindi_img_path = os.path.join(TEST_DIR, "dummy_hindi_rx.png")

sanity_results = {}

# -------------------------------------------------------------
# 1. Sanity Test: Telugu Model (te_PP-OCRv5)
# -------------------------------------------------------------
print("\n[TEST 1/2] Running Telugu OCR (lang='te') on dummy_telugu_rx.png...")
ocr_te = PaddleOCR(lang="te", use_textline_orientation=True)

t0 = time.time()
res_te = ocr_te.predict(telugu_img_path)
latency_te = (time.time() - t0) * 1000

lines_te = []
for res in res_te:
    texts = res.get("rec_texts", [])
    scores = res.get("rec_scores", [])
    polys = res.get("rec_polys", [])
    for idx, (t, s) in enumerate(zip(texts, scores)):
        lines_te.append({
            "line_index": idx + 1,
            "text": str(t).strip(),
            "confidence": round(float(s), 4)
        })

print(f"  -> Telugu OCR Completed in {latency_te:.1f}ms | Extracted {len(lines_te)} textlines.")
sanity_results["telugu"] = {
    "model": "te_PP-OCRv5_mobile_rec + PP-OCRv5_server_det",
    "image": os.path.basename(telugu_img_path),
    "latency_ms": round(latency_te, 1),
    "line_count": len(lines_te),
    "lines": lines_te
}

# -------------------------------------------------------------
# 2. Sanity Test: Hindi Model (devanagari_PP-OCRv5)
# -------------------------------------------------------------
print("\n[TEST 2/2] Running Hindi OCR (lang='hi') on dummy_hindi_rx.png...")
ocr_hi = PaddleOCR(lang="hi", use_textline_orientation=True)

t0 = time.time()
res_hi = ocr_hi.predict(hindi_img_path)
latency_hi = (time.time() - t0) * 1000

lines_hi = []
for res in res_hi:
    texts = res.get("rec_texts", [])
    scores = res.get("rec_scores", [])
    polys = res.get("rec_polys", [])
    for idx, (t, s) in enumerate(zip(texts, scores)):
        lines_hi.append({
            "line_index": idx + 1,
            "text": str(t).strip(),
            "confidence": round(float(s), 4)
        })

print(f"  -> Hindi OCR Completed in {latency_hi:.1f}ms | Extracted {len(lines_hi)} textlines.")
sanity_results["hindi"] = {
    "model": "devanagari_PP-OCRv5_mobile_rec + PP-OCRv5_server_det",
    "image": os.path.basename(hindi_img_path),
    "latency_ms": round(latency_hi, 1),
    "line_count": len(lines_hi),
    "lines": lines_hi
}

# Save output
out_json = os.path.join(TEST_DIR, "indic_sanity_results.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(sanity_results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print(f"Sanity test completed successfully! Results written to: {out_json}")
print("=" * 70)

# Display Extracted Lines
print("\n>>> EXTRACTED TELUGU LINES (Sample):")
for item in lines_te:
    # Print lines that contain Telugu Unicode or key lines
    print(f"  [Conf: {item['confidence']:.2f}] {item['text']}")

print("\n>>> EXTRACTED HINDI LINES (Sample):")
for item in lines_hi:
    print(f"  [Conf: {item['confidence']:.2f}] {item['text']}")
