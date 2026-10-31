import paddleocr._pipelines.ocr as m
from paddleocr import PaddleOCR

print("PP-OCRv6 Supported Languages Count:", len(m._PPOCRV6_LANGS))
print("Sample PP-OCRv6 Languages:", sorted(list(m._PPOCRV6_LANGS))[:20])

ocr_dummy = PaddleOCR()
print("\nLanguage model mappings in PaddleOCR:")
for lang in ["en", "ch", "te", "devanagari", "hi", "ta"]:
    det, rec = ocr_dummy._get_ocr_model_names(lang, None)
    print(f" - {lang:<12} -> Det: {det}, Rec: {rec}")
