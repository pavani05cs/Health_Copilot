import sys
import subprocess

print("Python version:", sys.version)

try:
    from PIL import Image, ImageDraw, ImageFont, features
    print("Pillow version:", Image.__version__)
    print("libraqm available:", features.check('raqm'))
except Exception as e:
    print("Pillow error:", e)

try:
    import reportlab
    print("ReportLab version:", reportlab.__version__)
except Exception as e:
    print("ReportLab not found:", e)

try:
    import pypdfium2
    print("pypdfium2 version:", pypdfium2.__version__)
except Exception as e:
    print("pypdfium2 error:", e)

# Check available fonts
res = subprocess.run(["fc-list", ":", "file"], capture_output=True, text=True)
fonts = res.stdout.splitlines()
telugu_fonts = [f for f in fonts if any(k in f.lower() for k in ["telu", "ponnala", "nats", "gidugu"])]
hindi_fonts = [f for f in fonts if any(k in f.lower() for k in ["deva", "gargi", "samyak"])]

print(f"Total fonts: {len(fonts)}")
print(f"Telugu fonts found: {len(telugu_fonts)}")
for f in telugu_fonts[:5]:
    print("  Telugu font:", f)
print(f"Devanagari fonts found: {len(hindi_fonts)}")
for f in hindi_fonts[:5]:
    print("  Devanagari font:", f)
