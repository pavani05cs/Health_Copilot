import paddlex

# Let's inspect paddlex official model names
import glob, os

paddlex_dir = os.path.dirname(paddlex.__file__)
configs = glob.glob(os.path.join(paddlex_dir, "**", "*.yaml"), recursive=True)
print(f"Found {len(configs)} yaml configs in paddlex.")

ocrv6_models = []
for c in configs:
    basename = os.path.basename(c)
    if "ocrv6" in basename.lower() or "pp-ocrv6" in basename.lower():
        ocrv6_models.append(basename)

print("PP-OCRv6 configs in paddlex:")
for m in sorted(set(ocrv6_models)):
    print(" -", m)
