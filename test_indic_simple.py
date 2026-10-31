import os
import sys
import traceback

os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
sys.stdout.reconfigure(encoding='utf-8')

print("--- Testing Telugu & Hindi Models ---")

print("\n1. Initializing lang='te'...")
try:
    from paddleocr import PaddleOCR
    ocr_te = PaddleOCR(lang="te", use_textline_orientation=True)
    print("   Successfully initialized ocr_te!")
except Exception as e:
    print("   Failed initializing ocr_te:")
    traceback.print_exc()

print("\n2. Initializing lang='hi'...")
try:
    ocr_hi = PaddleOCR(lang="hi", use_textline_orientation=True)
    print("   Successfully initialized ocr_hi!")
except Exception as e:
    print("   Failed initializing ocr_hi:")
    traceback.print_exc()
