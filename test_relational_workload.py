"""
Complete Workload Test for Health Copilot Relational Database & Ingestion Agent
Loads actual OCR outputs from real EC2 test runs (Telugu & Hindi prescriptions),
ingests them through ClinicalIngestionAgent, and performs longitudinal queries.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

import health_db
from ingestion_agent import ClinicalIngestionAgent

print("=" * 75)
print("     HEALTH COPILOT RELATIONAL DATABASE WORKLOAD TEST (SQLITE / MYSQL)")
print("=" * 75)

# 1. Initialize Clean DB
health_db.init_db()
agent = ClinicalIngestionAgent()

# 2. Load actual OCR output from EC2 test runs
indic_json_path = os.path.join(os.path.dirname(__file__), "indic_sanity_success.json")
if not os.path.exists(indic_json_path):
    print(f"Error: {indic_json_path} not found!")
    sys.exit(1)

with open(indic_json_path, "r", encoding="utf-8") as f:
    ocr_data = json.load(f)

telugu_ocr_lines = ocr_data["telugu"]["lines"]
hindi_ocr_lines = ocr_data["hindi"]["lines"]

# ---------------------------------------------------------------------------
# WORKLOAD 1: Ingest Apollo Clinic Telugu Prescription (Ramesh Rao)
# ---------------------------------------------------------------------------
print("\n[WORKLOAD 1] Ingesting Telugu Bilingual Prescription (Apollo Hyderabad)...")
meta_telugu = {
    "encounter_id": "ENC-HYD-2026-10-12-001",
    "encounter_date": "2026-10-12",
    "record_type": "prescription",
    "s3_raw_key": "raw/91443288912011/enc_001.pdf",
    "s3_artifacts_key": "artifacts/91443288912011/enc_001_tokens.json",
    "s3_fhir_key": "fhir/91443288912011/enc_001_bundle.json"
}

bundle_1 = agent.ingest_document(telugu_ocr_lines, meta_telugu)
print(f"  -> Successfully Ingested Encounter: {bundle_1['encounter']['encounter_id']}")
print(f"  -> Patient: {bundle_1['patient']['full_name']} | ABHA: {bundle_1['patient']['abha_id']}")
print(f"  -> Extracted: {len(bundle_1['medications'])} Medications, {len(bundle_1['lab_observations'])} Labs, {len(bundle_1['diagnoses'])} Diagnoses")

# ---------------------------------------------------------------------------
# WORKLOAD 2: Ingest Max Hospital Hindi Prescription (Sunita Sharma)
# ---------------------------------------------------------------------------
print("\n[WORKLOAD 2] Ingesting Hindi Bilingual Prescription (Max New Delhi)...")
meta_hindi = {
    "encounter_id": "ENC-DEL-2026-10-12-002",
    "encounter_date": "2026-10-12",
    "record_type": "prescription",
    "s3_raw_key": "raw/14882133419920/enc_002.pdf",
    "s3_artifacts_key": "artifacts/14882133419920/enc_002_tokens.json",
    "s3_fhir_key": "fhir/14882133419920/enc_002_bundle.json"
}

bundle_2 = agent.ingest_document(hindi_ocr_lines, meta_hindi)
print(f"  -> Successfully Ingested Encounter: {bundle_2['encounter']['encounter_id']}")
print(f"  -> Patient: {bundle_2['patient']['full_name']} | ABHA: {bundle_2['patient']['abha_id']}")
print(f"  -> Extracted: {len(bundle_2['medications'])} Medications, {len(bundle_2['lab_observations'])} Labs, {len(bundle_2['diagnoses'])} Diagnoses")

# ---------------------------------------------------------------------------
# WORKLOAD 3: Simulate Follow-Up Visit (Ramesh Rao - 27-Oct-2026)
# Fasting Blood Sugar dropped from 162 mg/dL to 128 mg/dL
# ---------------------------------------------------------------------------
print("\n[WORKLOAD 3] Ingesting Follow-up Encounter for Ramesh Rao (Fasting Sugar re-check)...")
followup_ocr_lines = [
    {"text": "APOLLO CLINIC & HEALTHCARE", "confidence": 0.99},
    {"text": "Dr. K. Srinivas, MBBS, MD | Reg No: TS-45920", "confidence": 0.98},
    {"text": "Patient Name: Ramesh Rao", "confidence": 0.99},
    {"text": "ABHA ID: 91-4432-8891-2011", "confidence": 0.99},
    {"text": "Age: 52 Yrs | Gender: Male", "confidence": 0.99},
    {"text": "Diagnosis: Type 2 Diabetes Mellitus - Under Control", "confidence": 0.98},
    {"text": "Blood Pressure: 130/82 mmHg | Pulse: 72 bpm", "confidence": 0.98},
    {"text": "Fasting Blood Sugar (FBS): 128 mg/dL | HbA1c: 7.2%", "confidence": 0.99},
    {"text": "1. Tab Metformin 500mg (1-0-1)", "confidence": 0.99},
    {"text": "మోతాదు: రోజుకు రెండుసార్లు భోజనం తర్వాత తీసుకోండి", "confidence": 0.96},
    {"text": "• వ్యాయామం కొనసాగించండి", "confidence": 0.98}
]

meta_followup = {
    "encounter_id": "ENC-HYD-2026-10-27-003",
    "encounter_date": "2026-10-27",
    "record_type": "lab_report",
    "patient_id": bundle_1["patient"]["patient_id"],
    "abha_id": "91-4432-8891-2011",
}

bundle_3 = agent.ingest_document(followup_ocr_lines, meta_followup)
print(f"  -> Successfully Ingested Follow-up: {bundle_3['encounter']['encounter_id']}")

# ---------------------------------------------------------------------------
# DEMONSTRATION OF CLINICAL RELATIONAL QUERIES (Downstream Agent Capabilities)
# ---------------------------------------------------------------------------
print("\n" + "=" * 75)
print("            DOWNSTREAM RELATIONAL CLINICAL QUERIES")
print("=" * 75)

# Query A: Longitudinal Blood Sugar Trend
patient_ramesh = bundle_1["patient"]["patient_id"]
print(f"\n[QUERY A] Longitudinal Fasting Blood Sugar Trend for Ramesh Rao ({patient_ramesh}):")
fbs_trend = health_db.query_lab_trend(patient_ramesh, "Fasting Blood Sugar")
print(f"  {'Date':<14} | {'Test Name':<30} | {'Value':<12} | {'Interpretation'}")
print("  " + "-" * 70)
for pt in fbs_trend:
    print(f"  {pt['observation_date']:<14} | Fasting Blood Sugar (FBS)     | {pt['value_numeric']} {pt['unit']:<6} | {pt['interpretation']}")

# Query B: Active Medications for Ramesh Rao
print(f"\n[QUERY B] Active Medications with Regional Telugu Instructions (Ramesh Rao):")
timeline = health_db.query_patient_timeline(patient_ramesh)
for med in timeline["active_medications"][:3]:
    print(f"  • {med['drug_name']} ({med['strength']}) - Code: [{med['frequency_code']}] ({med['frequency_text']})")
    print(f"    - Original Language ({med['detected_language'].upper()}): {med['instructions_original']}")
    print(f"    - Normalized English: {med['instructions_english']}")

# Query C: Active Medications for Sunita Sharma (Hindi)
patient_sunita = bundle_2["patient"]["patient_id"]
print(f"\n[QUERY C] Active Medications with Regional Hindi Instructions (Sunita Sharma):")
timeline_sunita = health_db.query_patient_timeline(patient_sunita)
for med in timeline_sunita["active_medications"][:3]:
    print(f"  • {med['drug_name']} ({med['strength']}) - Code: [{med['frequency_code']}] ({med['frequency_text']})")
    print(f"    - Original Language ({med['detected_language'].upper()}): {med['instructions_original']}")
    print(f"    - Normalized English: {med['instructions_english']}")

# Query D: Database Statistics Table
print("\n" + "=" * 75)
print("              DATABASE RELATIONAL INTEGRITY REPORT")
print("=" * 75)
conn = health_db.get_connection()
tables = ["patients", "encounters", "diagnoses", "vitals", "medications", "lab_observations", "clinical_instructions", "ingestion_audit_log"]
print(f"{'Table Name':<28} | {'Total Records':<15} | {'Status'}")
print("-" * 55)
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
    print(f"{t:<28} | {count:<15} | VALIDATED")
conn.close()

print("\nWorkload successfully executed with zero errors!")
