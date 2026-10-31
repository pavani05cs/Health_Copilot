import paddlex
from paddlex.inference.models import common
import paddleocr

print("PaddleOCR official pipelines / models:")
from paddleocr._pipelines.ocr import OCR_SYSTEM_MODELS
for k, v in OCR_SYSTEM_MODELS.items():
    print(k, "->", v)
