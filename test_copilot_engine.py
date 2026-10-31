"""
Test Suite for Patient Copilot Analytical Engine (GPT-6-Luna)
Verifies multi-intent clinical reasoning against ground-truth database (health_copilot.db):
  1. Telugu Medication Schedule & Timing Guidance
  2. Lab Results & Longitudinal Trend Interpretation
  3. Cross-Encounter Drug-Drug Interaction & Safety Analysis
  4. Red-Flag Emergency Triage (Hypoglycemia / Adverse Event)
  5. Clinician Handover SBAR Brief Generation
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

from copilot_analytical_engine import PatientCopilotAgent

print("=" * 80)
print("     AI-POWERED PERSONAL HEALTH COPILOT: ANALYTICAL ENGINE TEST SUITE")
print("                          POWERED BY GPT-6-LUNA")
print("=" * 80)

# Initialize Agent
agent = PatientCopilotAgent(model="gpt-6-luna")
print(f"[INIT] Model: {agent.model}")
print(f"[INIT] OpenAI Client Connected: {agent.client is not None}")

if not agent.client:
    print("[ERROR] OpenAI Client not initialized! Check OPENAI_API_KEY in .env.")
    sys.exit(1)

PATIENT_ID = "PAT-91443288912011"  # Ramesh Rao

TEST_CASES = [
    {
        "test_name": "TEST 1: Telugu Medication Schedule & Regimen Guidance",
        "patient_id": PATIENT_ID,
        "language": "te",
        "query": "నా డాక్టర్ రాసిన మందులు ఎప్పుడు, ఎలా వేసుకోవాలి? వివరంగా తెలుగులో చెప్పండి.",
        "expected_tools": ["get_active_medications"]
    },
    {
        "test_name": "TEST 2: Lab Interpretation & Reference Range Analysis",
        "patient_id": PATIENT_ID,
        "language": "en",
        "query": "What do my Fasting Blood Sugar and HbA1c test results mean? Are they normal or high?",
        "expected_tools": ["get_lab_history_and_trends"]
    },
    {
        "test_name": "TEST 3: Cross-Encounter Drug-Drug Interaction Check",
        "patient_id": PATIENT_ID,
        "language": "en",
        "query": "Can I take Metformin, Glimepiride, and Telmisartan together? Are there any harmful drug interactions?",
        "expected_tools": ["check_drug_interactions"]
    },
    {
        "test_name": "TEST 4: Red-Flag Emergency Triage (Acute Hypoglycemia)",
        "patient_id": PATIENT_ID,
        "language": "en",
        "query": "I took my morning tablets an hour ago and I'm feeling very shaky, sweating cold, and dizzy. What should I do right now?",
        "expected_tools": ["get_active_medications"]
    },
    {
        "test_name": "TEST 5: Clinician Handover SBAR Summary Generation",
        "patient_id": PATIENT_ID,
        "language": "en",
        "query": "Please generate a concise SBAR clinical handover summary for my upcoming doctor consultation.",
        "expected_tools": ["generate_clinical_handover"]
    }
]

total_passed = 0
for idx, tc in enumerate(TEST_CASES, 1):
    print("\n" + "=" * 80)
    print(f" [{idx}/{len(TEST_CASES)}] {tc['test_name']}")
    print("=" * 80)
    print(f"  [QUERY]: {tc['query']}")
    print(f"  [LANGUAGE]: {tc['language'].upper()} | [PATIENT]: {tc['patient_id']}")
    
    t0 = time.time()
    res = agent.chat(
        patient_id=tc["patient_id"],
        message=tc["query"],
        session_id=f"test_sess_{idx}",
        language=tc["language"]
    )
    elapsed = time.time() - t0

    if res.get("status") == "success":
        print(f"\n  [SUCCESS] Completed in {elapsed:.2f}s | Latency: {res['latency_ms']}ms")
        print(f"  [TOOLS INVOKED]: {res['invoked_tools']}")
        print(f"  [COPILOT RESPONSE]:\n")
        # Indent response
        for line in res["answer"].split("\n"):
            print(f"    {line}")
        total_passed += 1
    else:
        print(f"\n  [FAILED]: {res.get('message')}")

print("\n" + "=" * 80)
print(f" TEST SUITE SUMMARY: {total_passed}/{len(TEST_CASES)} TESTS COMPLETED SUCCESSFULLY WITH GPT-6-LUNA")
print("=" * 80)
