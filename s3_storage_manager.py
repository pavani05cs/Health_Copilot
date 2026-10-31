"""
AWS S3 Storage Manager for AI-Powered Personal Health Copilot
Implements ABDM / FHIR-ready storage across 3 dedicated S3 buckets:
  1. RAW_BUCKET: health-copilot-raw-records-938095766262
  2. ARTIFACTS_BUCKET: health-copilot-processed-artifacts-938095766262
  3. FHIR_BUCKET: health-copilot-fhir-records-938095766262
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError


def load_env_file(filepath=".env"):
    """Loads key=value pairs from .env into os.environ."""
    env_path = Path(filepath)
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v


# Load credentials
load_env_file()

AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2")
ACCOUNT_ID = "938095766262"

RAW_BUCKET = f"health-copilot-raw-records-{ACCOUNT_ID}"
ARTIFACTS_BUCKET = f"health-copilot-processed-artifacts-{ACCOUNT_ID}"
FHIR_BUCKET = f"health-copilot-fhir-records-{ACCOUNT_ID}"

s3_client = boto3.client("s3", region_name=AWS_REGION)


def upload_raw_medical_record(
    local_file_path: str,
    user_id: str,
    record_id: str,
    record_type: str = "prescription",
) -> Dict[str, str]:
    """
    Uploads original medical document (PDF/JPG/PNG) into the encrypted Raw Records Vault.
    """
    file_path = Path(local_file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {local_file_path}")

    filename = file_path.name
    s3_key = f"users/{user_id}/records/{record_id}/original_{filename}"

    metadata = {
        "user_id": user_id,
        "record_id": record_id,
        "record_type": record_type,
        "original_name": filename,
    }

    s3_client.upload_file(
        Filename=str(file_path),
        Bucket=RAW_BUCKET,
        Key=s3_key,
        ExtraArgs={
            "ServerSideEncryption": "AES256",
            "Metadata": metadata,
        },
    )

    print(f"[S3 RAW] Uploaded: s3://{RAW_BUCKET}/{s3_key}")
    return {"bucket": RAW_BUCKET, "key": s3_key, "filename": filename}


def upload_ocr_artifacts(
    user_id: str,
    record_id: str,
    ocr_json_data: dict,
    page_image_paths: Optional[List[str]] = None,
) -> Dict[str, any]:
    """
    Uploads rendered page images and PP-OCRv6 token extractions to the Processed Artifacts Bucket.
    """
    base_prefix = f"users/{user_id}/records/{record_id}"
    uploaded_pages = []

    # Upload rendered high-res pages
    if page_image_paths:
        for idx, img_path in enumerate(page_image_paths):
            p = Path(img_path)
            if p.exists():
                page_key = f"{base_prefix}/pages/{p.name}"
                s3_client.upload_file(
                    Filename=str(p),
                    Bucket=ARTIFACTS_BUCKET,
                    Key=page_key,
                    ExtraArgs={"ServerSideEncryption": "AES256", "ContentType": "image/png"},
                )
                uploaded_pages.append(page_key)
                print(f"[S3 ARTIFACT] Uploaded page: s3://{ARTIFACTS_BUCKET}/{page_key}")

    # Upload OCR JSON tokens & bounding boxes
    json_key = f"{base_prefix}/ocr/ppocrv6_tokens.json"
    s3_client.put_object(
        Bucket=ARTIFACTS_BUCKET,
        Key=json_key,
        Body=json.dumps(ocr_json_data, indent=2, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    print(f"[S3 ARTIFACT] Uploaded OCR tokens: s3://{ARTIFACTS_BUCKET}/{json_key}")

    return {
        "bucket": ARTIFACTS_BUCKET,
        "ocr_json_key": json_key,
        "pages": uploaded_pages,
    }


def upload_fhir_and_summaries(
    patient_id: str,
    record_id: str,
    fhir_bundle: dict,
    summaries: Dict[str, str],
) -> Dict[str, str]:
    """
    Uploads ABDM/FHIR-compliant structured medical record bundle and
    multilingual plain-language explanations (English, Telugu, Hindi).
    """
    base_prefix = f"patients/{patient_id}"

    # 1. Save FHIR R4 Bundle
    fhir_key = f"{base_prefix}/fhir/bundle_{record_id}.json"
    s3_client.put_object(
        Bucket=FHIR_BUCKET,
        Key=fhir_key,
        Body=json.dumps(fhir_bundle, indent=2, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    print(f"[S3 FHIR] Uploaded FHIR Bundle: s3://{FHIR_BUCKET}/{fhir_key}")

    # 2. Save Multilingual Summaries
    saved_summaries = {}
    for lang, summary_text in summaries.items():
        summary_key = f"{base_prefix}/summaries/summary_{lang}_{record_id}.json"
        summary_payload = {
            "patient_id": patient_id,
            "record_id": record_id,
            "language": lang,
            "summary": summary_text,
        }
        s3_client.put_object(
            Bucket=FHIR_BUCKET,
            Key=summary_key,
            Body=json.dumps(summary_payload, indent=2, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        saved_summaries[lang] = summary_key
        print(f"[S3 SUMMARY] Uploaded {lang.upper()} summary: s3://{FHIR_BUCKET}/{summary_key}")

    return {
        "bucket": FHIR_BUCKET,
        "fhir_key": fhir_key,
        "summaries": saved_summaries,
    }


def generate_presigned_url(bucket_name: str, object_key: str, expiration: int = 3600) -> str:
    """
    Generates a secure temporary download URL for patient UI viewing.
    """
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_key},
        ExpiresIn=expiration,
    )


def test_storage_pipeline():
    """Runs a test validation across all 3 buckets."""
    print("=" * 65)
    print(" TESTING 3-BUCKET STORAGE PIPELINE")
    print("=" * 65)

    test_user = "ABHA-91-7989983221"
    test_record_id = "rec_20261013_001"

    # 1. Raw upload test
    test_file = Path("test_upload.txt")
    test_file.write_text("Test raw medical document content.", encoding="utf-8")
    raw_res = upload_raw_medical_record(str(test_file), test_user, test_record_id, record_type="lab_report")
    test_file.unlink()

    # 2. Artifacts upload test
    mock_ocr = {
        "page_count": 1,
        "lines": [{"text": "Blood Glucose: 110 mg/dL", "confidence": 0.99}],
    }
    art_res = upload_ocr_artifacts(test_user, test_record_id, mock_ocr)

    # 3. FHIR and Multilingual summary test
    mock_fhir_bundle = {
        "resourceType": "Bundle",
        "type": "document",
        "entry": [
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"text": "Fasting Blood Sugar"},
                    "valueQuantity": {"value": 110, "unit": "mg/dL"},
                    "interpretation": {"text": "Normal"},
                }
            }
        ],
    }
    mock_summaries = {
        "en": "Your Fasting Blood Sugar is 110 mg/dL, which is within the normal range.",
        "te": "మీ ఉపవాస రక్త చక్కెర స్థాయి 110 mg/dL ఉంది, ఇది సాధారణ పరిధిలోనే ఉంది.",
        "hi": "आपका फास्टिंग ब्लड शुगर 110 mg/dL है, जो सामान्य सीमा के भीतर है।",
    }
    fhir_res = upload_fhir_and_summaries(test_user, test_record_id, mock_fhir_bundle, mock_summaries)

    print("\n" + "=" * 65)
    print(" GENERATING PRESIGNED ACCESS URLS")
    print("=" * 65)
    url = generate_presigned_url(RAW_BUCKET, raw_res["key"])
    print(f"Temporary Secure Download URL (Expires in 1hr):\n{url[:100]}...")
    print("=" * 65)
    print("[SUCCESS] All 3 Buckets verified and operational!")


if __name__ == "__main__":
    test_storage_pipeline()
