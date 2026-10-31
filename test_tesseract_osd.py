import os
import sys
import time
from PIL import Image
import pytesseract

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("       TESSERACT OSD (ORIENTATION & SCRIPT DETECTION) TEST")
print("=" * 70)

TEST_DIR = "/home/ubuntu/multilingual_test"
telugu_img_path = os.path.join(TEST_DIR, "dummy_telugu_rx.png")
hindi_img_path = os.path.join(TEST_DIR, "dummy_hindi_rx.png")

# Verify input files exist
for p in [telugu_img_path, hindi_img_path]:
    if not os.path.exists(p):
        print(f"Error: {p} not found!")
        sys.exit(1)

telugu_full = Image.open(telugu_img_path)
hindi_full = Image.open(hindi_img_path)

# Prepare crops:
# 1. English Header & Patient Demographics (y: 60 to 500)
# 2. Regional Prescription & Patient Instructions (y: 800 to 1950)
crops = {
    "English Header (from Telugu Doc)": telugu_full.crop((60, 60, 1594, 500)),
    "Telugu Section (Dosage & Instructions)": telugu_full.crop((80, 850, 1574, 1950)),
    "English Header (from Hindi Doc)": hindi_full.crop((60, 60, 1594, 500)),
    "Hindi Section (Dosage & Instructions)": hindi_full.crop((80, 850, 1574, 1950)),
    "Full Telugu Document": telugu_full,
    "Full Hindi Document": hindi_full,
}

print(f"\nEvaluating {len(crops)} test image targets with Tesseract OSD:\n")

results = []

for name, img in crops.items():
    print(f"---> Testing Target: [{name}] (Resolution: {img.size[0]}x{img.size[1]})")
    t0 = time.time()
    try:
        # pytesseract.image_to_osd runs tesseract with --psm 0
        osd_raw = pytesseract.image_to_osd(img)
        elapsed_ms = (time.time() - t0) * 1000

        # Parse key fields
        parsed = {}
        for line in osd_raw.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                parsed[k.strip()] = v.strip()

        script = parsed.get("Script", "Unknown")
        script_conf = parsed.get("Script confidence", "N/A")
        orientation = parsed.get("Orientation in degrees", "0")
        orient_conf = parsed.get("Orientation confidence", "N/A")

        print(f"     Detected Script    : {script}")
        print(f"     Script Confidence  : {script_conf}")
        print(f"     Orientation Angle  : {orientation}° (conf: {orient_conf})")
        print(f"     Latency            : {elapsed_ms:.1f} ms\n")

        results.append({
            "target": name,
            "script": script,
            "script_conf": script_conf,
            "orientation": orientation,
            "latency_ms": round(elapsed_ms, 1),
            "status": "PASS"
        })

    except Exception as e:
        elapsed_ms = (time.time() - t0) * 1000
        print(f"     Failed: {e}")
        print(f"     Latency: {elapsed_ms:.1f} ms\n")
        results.append({
            "target": name,
            "script": "ERROR",
            "script_conf": "0",
            "orientation": "0",
            "latency_ms": round(elapsed_ms, 1),
            "status": f"FAIL: {str(e)[:40]}"
        })

print("=" * 70)
print("                  SUMMARY BENCHMARK TABLE")
print("=" * 70)
print(f"{'Target':<42} | {'Detected Script':<15} | {'Confidence':<10} | {'Latency'}")
print("-" * 75)
for r in results:
    print(f"{r['target']:<42} | {r['script']:<15} | {r['script_conf']:<10} | {r['latency_ms']} ms")
print("=" * 75)
