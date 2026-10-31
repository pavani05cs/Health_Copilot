"""
Test Runner for GPT Luna 6 Clinical Ingestion Agent
Verifies in-memory conversation list, OpenAI function calling tool definitions,
and end-to-end ingestion into the relational database.
"""

import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

from luna_ingestion_agent import LunaIngestionAgent, OPENAI_TOOLS, SYSTEM_PROMPT
import health_db

print("=" * 75)
print("     GPT LUNA 6 CLINICAL INGESTION AGENT TEST RUNNER")
print("=" * 75)

# 1. Initialize DB
health_db.init_db()

# 2. Instantiate Luna Ingestion Agent
agent = LunaIngestionAgent(model="gpt-luna-6")
print(f"[INIT] Model: {agent.model}")
print(f"[INIT] In-Memory Conversation History initialized with {len(agent.conversation_history)} message(s):")
print(f"       Role: {agent.conversation_history[0]['role']} | Prompt Length: {len(agent.conversation_history[0]['content'])} chars")

print(f"\n[INIT] OpenAI Function Tools Defined ({len(OPENAI_TOOLS)} tools):")
for t in OPENAI_TOOLS:
    fn = t["function"]
    print(f"  • Tool: {fn['name']:<24} -> {fn['description'][:60]}...")

# 3. Load Real OCR Data
indic_json_path = os.path.join(os.path.dirname(__file__), "indic_sanity_success.json")
with open(indic_json_path, "r", encoding="utf-8") as f:
    ocr_data = json.load(f)

telugu_lines = ocr_data["telugu"]["lines"]
hindi_lines = ocr_data["hindi"]["lines"]

# 4. Ingest Telugu Prescription via Agent
print("\n" + "=" * 75)
print(" [RUN 1] Processing Telugu Prescription (Apollo Hyderabad) with Luna Agent")
print("=" * 75)

meta_1 = {
    "encounter_id": "ENC-LUNA-HYD-001",
    "encounter_date": "2026-10-12",
    "record_type": "prescription",
    "s3_raw_key": "raw/91443288912011/luna_001.pdf",
    "s3_artifacts_key": "artifacts/91443288912011/luna_001_tokens.json",
    "s3_fhir_key": "fhir/91443288912011/luna_001_bundle.json"
}

res_1 = agent.process_document(telugu_lines, meta_1)
print(f"\n[AGENT RESULT] Status: {res_1['status']} | Model: {res_1['model']}")
print(f"[AGENT RESULT] In-Memory Conversation History Length: {len(agent.conversation_history)} messages")

# 5. Display In-Memory Conversation Turns
print("\n" + "-" * 75)
print(" IN-MEMORY CONVERSATION HISTORY STRUCTURE (Sample Turns):")
print("-" * 75)
for i, turn in enumerate(agent.conversation_history[:8]):
    role = turn.get("role", "unknown")
    if role == "system":
        print(f"  [Turn {i}] Role: SYSTEM (Clinical System Prompt)")
    elif role == "user":
        print(f"  [Turn {i}] Role: USER -> {turn.get('content')[:70]}...")
    elif role == "assistant":
        if turn.get("tool_calls"):
            calls = [tc['function']['name'] for tc in turn['tool_calls']]
            print(f"  [Turn {i}] Role: ASSISTANT -> Calling Tool(s): {calls}")
        else:
            print(f"  [Turn {i}] Role: ASSISTANT -> {turn.get('content')[:70]}...")
    elif role == "tool":
        content_preview = turn.get('content', '')[:60]
        print(f"  [Turn {i}] Role: TOOL (id: {turn.get('tool_call_id')}) -> {content_preview}...")

print(f"\n[Turn {len(agent.conversation_history)-1}] Final Response from Assistant:")
print(agent.conversation_history[-1].get("content"))

# 6. Verify Database Contents
print("\n" + "=" * 75)
print(" DATABASE RELATIONAL VERIFICATION")
print("=" * 75)
conn = health_db.get_connection()
for tbl in ["patients", "encounters", "medications", "lab_observations"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {tbl};").fetchone()[0]
    print(f"  Table: {tbl:<20} | Rows: {count}")

print("\nSample Meds from DB for Encounter ENC-LUNA-HYD-001:")
cursor = conn.execute("SELECT drug_name, strength, frequency_code, instructions_original, instructions_english FROM medications WHERE encounter_id = 'ENC-LUNA-HYD-001';")
for r in cursor.fetchall():
    print(f"  • {r['drug_name']} ({r['strength']}) - [{r['frequency_code']}]")
    print(f"    Original Indic : {r['instructions_original']}")
    print(f"    Normalized Eng : {r['instructions_english']}")
conn.close()

print("\nLuna Ingestion Agent test completed successfully!")
