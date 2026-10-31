import os
import sys
import json
import time

# oneDNN / CPU environment flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
sys.stdout.reconfigure(encoding='utf-8')

from paddleocr import PaddleOCR
from PIL import Image

print("=" * 70)
print("  LIGHTWEIGHT INDIC SANITY TEST (PP-OCRv6 Det + Indic Rec)")
print("=" * 70)

TEST_DIR = "/home/ubuntu/multilingual_test"
telugu_img_path = os.path.join(TEST_DIR, "dummy_telugu_rx.png")
hindi_img_path = os.path.join(TEST_DIR, "dummy_hindi_rx.png")

# 1. Test Telugu Engine
print("\n[1/2] Initializing Telugu Engine (PP-OCRv6_small_det + te_PP-OCRv5_mobile_rec)...")
t0 = time.time()
ocr_te = PaddleOCR(
    text_detection_model_name="PP-OCRv6_small_det",
    text_recognition_model_name="te_PP-OCRv5_mobile_rec",
    use_textline_orientation=True
)
print(f"      Initialized in {(time.time() - t0)*1000:.1f}ms")

print(f"      Running inference on {os.path.basename(telugu_img_path)}...")
t1 = time.time()
res_te = ocr_te.predict(telugu_img_path)
elapsed_te = (time.time() - t1) * 1000

lines_te = []
for res in res_te:
    texts = res.get("rec_texts", [])
    scores = res.get("rec_scores", [])
    for t, s in zip(texts, scores):
        lines_te.append({"text": str(t).strip(), "confidence": round(float(s), 4)})

print(f"      Completed in {elapsed_te:.1f}ms | Lines Extracted: {len(lines_te)}")
print("      Sample Telugu Extractions:")
for item in lines_te[:10]:
    print(f"        [{item['confidence']:.2f}] {item['text']}")

# Free memory before next test
del ocr_te
del res_te
import gc; gc.collect()

# 2. Test Hindi Engine
print("\n[2/2] Initializing Hindi Engine (PP-OCRv6_small_det + devanagari_PP-OCRv5_mobile_rec)...")
t0 = time.time()
ocr_hi = PaddleOCR(
    text_detection_model_name="PP-OCRv6_small_det",
    text_recognition_model_name="devanagari_PP-OCRv5_mobile_rec",
    use_textline_orientation=True
)
print(f"      Initialized in {(time.time() - t0)*1000:.1f}ms")

print(f"      Running inference on {os.path.basename(hindi_img_path)}...")
t1 = time.time()
res_hi = ocr_hi.predict(hindi_img_path)
elapsed_hi = (time.time() - t1) * 1000

lines_hi = []
for res in res_hi:
    texts = res.get("rec_texts", [])
    scores = res.get("rec_scores", [])
    for t, s in zip(texts, scores):
        lines_hi.append({"text": str(t).strip(), "confidence": round(float(s), 4)})

print(f"      Completed in {elapsed_hi:.1f}ms | Lines Extracted: {len(lines_hi)}")
print("      Sample Hindi Extractions:")
for item in lines_hi[:10]:
    print(f"        [{item['confidence']:.2f}] {item['text']}")

# Save sanity results
output_file = os.path.join(TEST_DIR, "indic_sanity_success.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "telugu": {"lines": lines_te, "latency_ms": elapsed_te},
        "hindi": {"lines": lines_hi, "latency_ms": elapsed_hi}
    }, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print(f"SANITY TEST SUCCESSFUL! Output saved to: {output_file}")
print("=" * 70)
