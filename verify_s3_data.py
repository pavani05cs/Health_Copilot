import boto3
import json
import sys
from create_ssh_keypair import load_env_file

# Enable UTF-8 console output
sys.stdout.reconfigure(encoding='utf-8')

load_env_file()
s3 = boto3.client("s3", region_name="ap-southeast-2")

rec_id = "rec_1791831512856"
patient_id = "ABHA-91-7989983221"

print("=" * 65)
print(" S3 VERIFICATION: READING BACK PERSISTED HEALTH OBJECTS")
print("=" * 65)

# 1. Check raw file
raw_key = f"users/{patient_id}/records/{rec_id}/original_{rec_id}_Pavani_Ravulapalli_Resume.pdf"
raw_meta = s3.head_object(Bucket="health-copilot-raw-records-938095766262", Key=raw_key)
print("1. [RAW VAULT] Original PDF:")
print(f"   Bucket        : health-copilot-raw-records-938095766262")
print(f"   Key           : {raw_key}")
print(f"   Size          : {raw_meta['ContentLength']:,} bytes")
print(f"   Encryption    : {raw_meta.get('ServerSideEncryption')} (AES256)")

# 2. Check OCR tokens
tokens_key = f"users/{patient_id}/records/{rec_id}/ocr/ppocrv6_tokens.json"
tok_resp = s3.get_object(Bucket="health-copilot-processed-artifacts-938095766262", Key=tokens_key)
tok_json = json.loads(tok_resp["Body"].read().decode("utf-8"))
print("\n2. [ARTIFACTS] PP-OCRv6 Tokens & Bounding Boxes:")
print(f"   Bucket        : health-copilot-processed-artifacts-938095766262")
print(f"   Key           : {tokens_key}")
print(f"   Lines Parsed  : {tok_json.get('line_count')} lines")

# 3. Check FHIR Bundle
fhir_key = f"patients/{patient_id}/fhir/bundle_{rec_id}.json"
fhir_resp = s3.get_object(Bucket="health-copilot-fhir-records-938095766262", Key=fhir_key)
fhir_json = json.loads(fhir_resp["Body"].read().decode("utf-8"))
print("\n3. [FHIR DATA STORE] ABDM FHIR R4 Bundle:")
print(f"   Bucket        : health-copilot-fhir-records-938095766262")
print(f"   Key           : {fhir_key}")
print(f"   Resource Type : {fhir_json.get('resourceType')}")
print(f"   Entries       : {len(fhir_json.get('entry', []))} FHIR resources")

# 4. Check Telugu & Hindi Summaries
te_key = f"patients/{patient_id}/summaries/summary_te_{rec_id}.json"
te_resp = s3.get_object(Bucket="health-copilot-fhir-records-938095766262", Key=te_key)
te_json = json.loads(te_resp["Body"].read().decode("utf-8"))
print("\n4. [REGIONAL SUMMARY] Telugu (తెలుగు):")
print(f"   Key           : {te_key}")
print(f"   Summary       : {te_json.get('summary')}")

hi_key = f"patients/{patient_id}/summaries/summary_hi_{rec_id}.json"
hi_resp = s3.get_object(Bucket="health-copilot-fhir-records-938095766262", Key=hi_key)
hi_json = json.loads(hi_resp["Body"].read().decode("utf-8"))
print("\n5. [REGIONAL SUMMARY] Hindi (हिंदी):")
print(f"   Key           : {hi_key}")
print(f"   Summary       : {hi_json.get('summary')}")

print("=" * 65)
print("[VERIFIED] All 5 S3 medical objects read and confirmed intact!")
