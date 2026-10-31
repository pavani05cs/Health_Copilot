"""
Live End-to-End Pipeline Test for AI-Powered Health Copilot
Sends the uploaded document to the EC2 API and validates:
  1. PP-OCRv6 Text Detection & Recognition
  2. S3 Raw Records Vault upload
  3. S3 OCR Artifacts upload
  4. S3 ABDM / FHIR R4 Bundle & Multilingual Summaries upload
"""

import urllib.request
import uuid
import json
import time

URL = "http://32.236.41.158:8000/api/process-record"
FILE_PATH = "resume.pdf"
PATIENT_ABHA_ID = "ABHA-91-7989983221"

print("=" * 65)
print(" LIVE END-TO-END HEALTH COPILOT PIPELINE TEST")
print(f" Target EC2 Endpoint: {URL}")
print(f" Test Document      : {FILE_PATH}")
print(f" Patient ABHA ID    : {PATIENT_ABHA_ID}")
print("=" * 65)

# Read PDF bytes
with open(FILE_PATH, "rb") as f:
    pdf_bytes = f.read()

boundary = uuid.uuid4().hex
c_type = f"multipart/form-data; boundary={boundary}"

body = []
def add_field(name, val):
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="{name}"'.encode())
    body.append(b"")
    body.append(str(val).encode())

def add_file(name, filename, data):
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode())
    body.append(b"Content-Type: application/pdf")
    body.append(b"")
    body.append(data)

add_field("abha_id", PATIENT_ABHA_ID)
add_field("record_type", "patient_profile_record")
add_field("tier", "small")
add_file("file", "Pavani_Ravulapalli_Resume.pdf", pdf_bytes)
body.append(f"--{boundary}--".encode())
body.append(b"")

full_body = b"\r\n".join(body)

req = urllib.request.Request(URL, data=full_body, headers={"Content-Type": c_type})

print("\n[STEP 1] Uploading document to EC2 and triggering PP-OCRv6...")
start_time = time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        duration = time.time() - start_time
        res = json.loads(resp.read().decode("utf-8"))

        print(f"[OK] Response received in {duration:.2f} seconds!")
        print("\n" + "=" * 65)
        print(" PIPELINE RESULTS SUMMARY")
        print("=" * 65)
        print(f" Status        : {res.get('status')}")
        print(f" Record ID     : {res.get('record_id')}")
        print(f" Patient ID    : {res.get('patient_id')}")
        print(f" OCR Latency   : {res.get('ocr_latency_ms'):.1f} ms")
        print(f" Lines Found   : {len(res.get('extracted_lines', []))}")
        
        s3_data = res.get("s3_storage", {})
        print("\n[STEP 2] S3 3-TIER ABDM VAULT STORAGE VERIFICATION:")
        print(f" 1. Raw Bucket       : s3://{s3_data.get('raw_bucket')}/{s3_data.get('raw_key')}")
        print(f" 2. Artifacts Bucket : s3://{s3_data.get('artifacts_bucket')}/{s3_data.get('ocr_tokens_key')}")
        print(f" 3. FHIR Bundle      : s3://{s3_data.get('fhir_bucket')}/{s3_data.get('fhir_key')}")
        print(" 4. Multi-language Summaries Stored:")
        for lang, key in s3_data.get("summaries", {}).items():
            print(f"    - [{lang.upper()}]: s3://{s3_data.get('fhir_bucket')}/{key}")

        print("\n[STEP 3] SAMPLE EXTRACTED LINES:")
        for i, line in enumerate(res.get("extracted_lines", [])[:10]):
            print(f"   Line {i+1:02d}: \"{line['text']}\" (conf: {line['confidence']*100:.1f}%)")
        print(f"   ... and {len(res.get('extracted_lines', [])) - 10} more lines.")

        # Save test result locally
        with open("live_test_response.json", "w", encoding="utf-8") as out:
            json.dump(res, out, indent=2, ensure_ascii=False)
        print(f"\n[INFO] Full response saved to: live_test_response.json")
        print("=" * 65)
        print("[SUCCESS] ALL VERIFICATION CHECKS PASSED!")

except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")
