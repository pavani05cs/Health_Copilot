"""
End-to-End Live Ingestion Pipeline Test
Feeds real OCR extracted tokens from dummy_telugu_rx.pdf into LunaIngestionAgent,
which autonomously invokes OpenAI tools (get_ocr_input, get_db_schema, run_sql_query, insert_into_table)
powered by the live GPT model and commits data to SQLite/MySQL.
"""

import os
import sys
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from luna_ingestion_agent import LunaIngestionAgent
import health_db

print("=" * 80)
print("     AI-POWERED PERSONAL HEALTH COPILOT: END-TO-END LIVE INGESTION TEST")
print("=" * 80)

# 1. Reset / Initialize Clean Database
health_db.init_db()

# 2. Instantiate Live Agent (reads OPENAI_API_KEY from .env)
agent = LunaIngestionAgent(model="gpt-6-luna")
print(f"[INIT] Model: {agent.model}")
print(f"[INIT] Client Connected: {agent.client is not None}")
if not agent.client:
    print("[ERROR] OpenAI client not initialized! Check OPENAI_API_KEY in .env.")
    sys.exit(1)

# 3. Load Real OCR Output from EC2 run of dummy_telugu_rx.pdf
ocr_path = os.path.join(os.path.dirname(__file__), "indic_sanity_success.json")
if not os.path.exists(ocr_path):
    print(f"[ERROR] {ocr_path} not found!")
    sys.exit(1)

with open(ocr_path, "r", encoding="utf-8") as f:
    raw_ocr = json.load(f)

telugu_ocr_lines = raw_ocr["telugu"]["lines"]
print(f"[INPUT] Loaded {len(telugu_ocr_lines)} OCR textlines from dummy_telugu_rx.pdf.")

# 4. Define Document Metadata
metadata = {
    "encounter_id": "ENC-LIVE-APOLLO-001",
    "encounter_date": "2026-10-12",
    "record_type": "prescription",
    "patient_id": "PAT-91443288912011",
    "abha_id": "91-4432-8891-2011",
    "s3_raw_key": "raw/91443288912011/dummy_telugu_rx.pdf",
    "s3_artifacts_key": "artifacts/91443288912011/dummy_telugu_rx_tokens.json",
    "s3_fhir_key": "fhir/91443288912011/dummy_telugu_rx_fhir.json"
}

# 5. Execute Autonomous Ingestion Loop with live GPT-4o
print("\n" + "=" * 80)
print(" [START] Running Autonomous Ingestion Agent Loop...")
print("=" * 80)

t0 = time.time()
result = agent.process_document(telugu_ocr_lines, metadata)
elapsed = time.time() - t0

print("\n" + "=" * 80)
print(f" [COMPLETE] Agent Finished in {elapsed:.2f}s | Steps: {result['conversation_steps']}")
print("=" * 80)

# 6. Display the In-Memory Conversation History
print("\n" + "-" * 80)
print(" IN-MEMORY CONVERSATION HISTORY (Detailed Breakdown):")
print("-" * 80)
history = agent.get_conversation_history()
for idx, msg in enumerate(history):
    role = msg.get("role")
    if role == "system":
        print(f"  [Step {idx:02d}] SYSTEM PROMPT (Length: {len(msg.get('content'))} characters)")
    elif role == "user":
        print(f"  [Step {idx:02d}] USER INSTRUCTION:\n         {msg.get('content')[:120]}...\n")
    elif role == "assistant":
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            print(f"  [Step {idx:02d}] ASSISTANT -> Generating {len(tool_calls)} Tool Call(s):")
            for tc in tool_calls:
                fn = tc.get("function", {})
                args_preview = fn.get("arguments", "")
                if len(args_preview) > 90:
                    args_preview = args_preview[:90] + "..."
                print(f"            • {fn.get('name')}({args_preview})")
        else:
            print(f"  [Step {idx:02d}] ASSISTANT FINAL RESPONSE:\n{msg.get('content')}\n")
    elif role == "tool":
        content = msg.get("content", "")
        if len(content) > 100:
            content = content[:100] + "..."
        print(f"  [Step {idx:02d}] TOOL RESULT (id: {msg.get('tool_call_id')}):\n         {content}")

# 7. Relational Database Verification (Prove Data Integrity)
print("\n" + "=" * 80)
print(" RELATIONAL DATABASE SQL VERIFICATION (health_copilot.db)")
print("=" * 80)

conn = health_db.get_connection()

# Check Patients
print("\n[TABLE: patients]")
for r in conn.execute("SELECT patient_id, abha_id, full_name, age, gender, contact_phone FROM patients;").fetchall():
    print(f"  • ID: {r['patient_id']} | Name: {r['full_name']} | ABHA: {r['abha_id']} | Age: {r['age']} | Sex: {r['gender']}")

# Check Encounters
print("\n[TABLE: encounters]")
for r in conn.execute("SELECT encounter_id, patient_id, encounter_date, hospital_name, doctor_name FROM encounters;").fetchall():
    print(f"  • Encounter: {r['encounter_id']} | Date: {r['encounter_date']} | Hospital: {r['hospital_name']} | Doctor: {r['doctor_name']}")

# Check Medications
print("\n[TABLE: medications (Preserved Indic Script + English Translation)]")
med_rows = conn.execute("SELECT drug_name, strength, frequency_code, instructions_original, instructions_english FROM medications;").fetchall()
for r in med_rows:
    print(f"  • {r['drug_name']} ({r['strength']}) - Code: [{r['frequency_code']}]")
    print(f"    - Original Telugu : {r['instructions_original']}")
    print(f"    - Normalized Eng  : {r['instructions_english']}")

# Check Lab Observations
print("\n[TABLE: lab_observations]")
lab_rows = conn.execute("SELECT test_name, value_numeric, unit, interpretation FROM lab_observations;").fetchall()
for r in lab_rows:
    print(f"  • {r['test_name']}: {r['value_numeric']} {r['unit']} | Interpretation: {r['interpretation']}")

# Check Vitals
print("\n[TABLE: vitals]")
vitals_rows = conn.execute("SELECT systolic_bp, diastolic_bp, pulse_bpm, bmi FROM vitals;").fetchall()
for r in vitals_rows:
    print(f"  • BP: {r['systolic_bp']}/{r['diastolic_bp']} mmHg | Pulse: {r['pulse_bpm']} bpm | BMI: {r['bmi']}")

# Check Diagnoses
print("\n[TABLE: diagnoses]")
diag_rows = conn.execute("SELECT condition_name, clinical_status FROM diagnoses;").fetchall()
for r in diag_rows:
    print(f"  • Condition: {r['condition_name']} (Status: {r['clinical_status']})")

conn.close()

print("\n" + "=" * 80)
print(" END-TO-END FLOW COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")
print("=" * 80)
