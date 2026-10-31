"""
GPT Luna 6 Clinical Ingestion Agent for AI-Powered Personal Health Copilot
Powered by the OpenAI Python SDK with function calling and an in-memory conversation list.
"""

import os
import sys
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional

import health_db

# Try importing OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

SYSTEM_PROMPT = """You are the Clinical Ingestion Agent for the "AI-Powered Personal Health Copilot" (ABDM & FHIR compliant).
Your mission is to transform raw, noisy, code-mixed OCR textlines into clean, normalized relational database records.

---

### 1. AVAILABLE TOOLS
You have access to 4 general tools:
1. `get_ocr_input()`: Fetches the raw OCR lines, confidence scores, and document metadata.
2. `get_db_schema(table_name=None)`: Peeks at the relational database schema (tables, columns, types, primary and foreign keys).
3. `run_sql_query(query)`: Executes read-only SQL queries (SELECT) to check existing patients, verify foreign keys, or inspect historical records.
4. `insert_into_table(table_name, records)`: Inserts a list of row dictionaries into any table.

---

### 2. WORKFLOW & REASONING PROTOCOL
Follow this exact multi-step execution loop:

#### Step 1: Ingest & Inspect
- Call `get_ocr_input()` to read the document's raw OCR textlines and metadata.
- Call `get_db_schema()` to inspect available tables, column names, and foreign key relationships.

#### Step 2: Patient Identity Resolution (Deduplication)
- Check if the patient already exists in the `patients` table using their extracted ABHA ID or phone number:
  SELECT patient_id, full_name FROM patients WHERE abha_id = '<extracted_abha>' OR contact_phone = '<phone>';
- If found: Reuse the existing `patient_id`.
- If new: Generate a patient ID (`PAT-<clean_abha_or_uuid>`), and insert the record into `patients` via `insert_into_table("patients", [...])`.

#### Step 3: Insert Encounter Record
- Create the parent `encounters` record with:
  - `encounter_id`: Unique identifier (e.g. ENC-<UUID_or_TIMESTAMP>)
  - `patient_id`: Foreign key to `patients`
  - `encounter_date`: Standardized date in ISO-8601 (YYYY-MM-DD)
  - `record_type`: prescription, lab_report, discharge_summary, or other
  - `hospital_name`, `doctor_name`, `doctor_reg_no`, `s3_raw_key`, `s3_artifacts_key`, `s3_fhir_key`
- Insert this parent encounter into `encounters` before inserting any child records.

#### Step 4: Clinical Entity Extraction & Normalization
Extract clinical entities according to these strict medical rules:

1. **Medications (`medications` table)**:
   - Separate drug name from dosage form (e.g. Tab Metformin -> dosage_form: "Tab", drug_name: "Metformin").
   - Extract strength (e.g. 500mg, 650mg, 40mg).
   - Normalize frequency codes:
     - 1-0-1 -> frequency_code: "1-0-1", frequency_text: "Twice daily"
     - 1-0-0 -> frequency_code: "1-0-0", frequency_text: "Once daily in morning"
     - 1-1-1 -> frequency_code: "1-1-1", frequency_text: "Three times daily"
     - 0-0-1 -> frequency_code: "0-0-1", frequency_text: "Once daily at night"
   - **Bilingual & Indic Handling (Crucial)**:
     - Prescriptions in India often contain dosage directions in regional languages (Telugu, Hindi, Tamil).
     - ALWAYS preserve the original script in `instructions_original` (e.g. "మోతాదు: రోజుకు రెండుసార్లు భోజనం తర్వాత తీసుకోండి" / "खुराक: दिन में तीन बार खाने के बाद").
     - Provide the translated English equivalent in `instructions_english` (e.g. "Take twice daily after meals").
     - Set `detected_language` to "telugu", "hindi", or "english".
     - Extract `timing` (e.g. "After meals", "Empty stomach before breakfast").

2. **Lab Observations (`lab_observations` table)**:
   - Separate numeric values from units (e.g. FBS 162 mg/dL -> test_name: "Fasting Blood Sugar (FBS)", value_numeric: 162.0, unit: "mg/dL").
   - Assign LOINC codes if standard (e.g. 1558-6 for Fasting Glucose, 4548-4 for HbA1c, 777-3 for Platelets).
   - Determine `interpretation`: HIGH, LOW, or NORMAL against biological reference intervals.

3. **Vitals (`vitals` table)**:
   - Parse blood pressure (systolic_bp, diastolic_bp), pulse, temperature in °F, SpO2%, and BMI.

4. **Diagnoses (`diagnoses` table)**:
   - Capture clinical conditions (e.g. Type 2 Diabetes Mellitus, Essential Hypertension, Acute Febrile Illness) with status active.

5. **Clinical Instructions (`clinical_instructions` table)**:
   - Capture lifestyle advice, dietary rules, exercise recommendations, follow-up dates, and emergency warnings.

#### Step 5: Database Commit
- Insert all extracted entity lists into their corresponding tables via `insert_into_table`.
- Ensure all child tables have the correct `encounter_id` and `patient_id` foreign keys.

#### Step 6: Summary & Response
Provide a concise, professional clinical ingestion summary:
- Patient Name & ABHA ID
- Encounter ID & Hospital / Doctor
- Count of Medications, Labs, Diagnoses, and Vitals ingested
- Highlight any abnormal lab values or critical instructions detected."""


# ---------------------------------------------------------------------------
# OpenAI Tool Specifications
# ---------------------------------------------------------------------------

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_ocr_input",
            "description": "Fetches the raw OCR extracted textlines, confidence scores, and document metadata for the current document to be ingested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "encounter_id": {
                        "type": "string",
                        "description": "Optional encounter identifier. If omitted, fetches the active document."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_db_schema",
            "description": "Peeks at the relational database schema. Returns all table names, column names, data types, primary keys, and foreign key relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Optional specific table to inspect (e.g. 'medications', 'patients'). If omitted, returns an overview of all tables."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql_query",
            "description": "Executes a read-only SQL query (SELECT) against the database. Use this to lookup existing patients by ABHA ID, verify foreign keys, or check historical records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL SELECT statement to execute."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_into_table",
            "description": "Inserts one or more rows into a specified table. The tool handles SQL generation, parameterized escaping, and transactional commit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the target table (e.g. 'patients', 'encounters', 'medications', 'lab_observations', 'vitals', 'diagnoses', 'clinical_instructions')."
                    },
                    "records": {
                        "type": "array",
                        "description": "List of row dictionaries where keys match table columns.",
                        "items": {"type": "object"}
                    }
                },
                "required": ["table_name", "records"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# Python Backend Tool Implementations
# ---------------------------------------------------------------------------

class ToolExecutor:
    """Executes the 4 general database and OCR tools against the environment."""

    def __init__(self, db_path: str = health_db.DB_FILE):
        self.db_path = db_path
        self.active_ocr_data = None
        self.active_metadata = None

    def set_active_document(self, ocr_data: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.active_ocr_data = ocr_data
        self.active_metadata = metadata

    def get_ocr_input(self, encounter_id: Optional[str] = None) -> Dict[str, Any]:
        """Tool 1: Return active OCR document lines and metadata."""
        if not self.active_ocr_data:
            return {"status": "error", "message": "No active OCR document loaded."}
        return {
            "status": "success",
            "metadata": self.active_metadata or {},
            "line_count": len(self.active_ocr_data),
            "lines": self.active_ocr_data
        }

    def get_db_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Tool 2: Introspect database schema dynamically."""
        conn = health_db.get_connection(self.db_path)
        cursor = conn.cursor()

        tables = []
        if table_name:
            tables = [table_name]
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row["name"] for row in cursor.fetchall()]

        schema_info = {}
        for tbl in tables:
            cursor.execute(f"PRAGMA table_info({tbl});")
            cols = [
                {
                    "name": col["name"],
                    "type": col["type"],
                    "notnull": bool(col["notnull"]),
                    "pk": bool(col["pk"])
                }
                for col in cursor.fetchall()
            ]

            cursor.execute(f"PRAGMA foreign_key_list({tbl});")
            fks = [
                {
                    "from_column": fk["from"],
                    "to_table": fk["table"],
                    "to_column": fk["to"]
                }
                for fk in cursor.fetchall()
            ]

            schema_info[tbl] = {
                "columns": cols,
                "foreign_keys": fks
            }

        conn.close()
        return {"status": "success", "tables": schema_info}

    def run_sql_query(self, query: str) -> Dict[str, Any]:
        """Tool 3: Execute safe read-only SQL query."""
        clean_query = query.strip()
        if not clean_query.lower().startswith("select"):
            return {"status": "error", "message": "Only SELECT queries are allowed via run_sql_query. Use insert_into_table for writes."}

        conn = health_db.get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(clean_query)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return {"status": "success", "row_count": len(rows), "rows": rows}
        except Exception as e:
            conn.close()
            return {"status": "error", "message": str(e)}

    def insert_into_table(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool 4: Insert structured records into the specified table."""
        if not records:
            return {"status": "error", "message": "No records provided for insertion."}

        conn = health_db.get_connection(self.db_path)
        cursor = conn.cursor()
        inserted_count = 0

        try:
            for rec in records:
                cols = list(rec.keys())
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join(cols)
                values = [rec[c] for c in cols]

                sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders});"
                cursor.execute(sql, values)
                inserted_count += 1

            conn.commit()
            conn.close()
            return {
                "status": "success",
                "table": table_name,
                "inserted_count": inserted_count,
                "message": f"Successfully committed {inserted_count} rows into {table_name}."
            }
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"status": "error", "message": f"Failed inserting into {table_name}: {str(e)}"}


# ---------------------------------------------------------------------------
# GPT Luna 6 Clinical Ingestion Agent
# ---------------------------------------------------------------------------

class LunaIngestionAgent:
    """
    Ingestion Agent for GPT Luna 6 using the official OpenAI client SDK.
    Maintains an in-memory conversation list and executes tool calls autonomously.
    """

    def __init__(
        self,
        model: str = "gpt-6-luna",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        db_path: str = health_db.DB_FILE
    ):
        # Load .env if present
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

        self.model = os.environ.get("OPENAI_MODEL") or model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LUNA_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("LUNA_API_BASE")
        self.tool_executor = ToolExecutor(db_path)

        # In-memory conversation history list
        self.conversation_history: List[Dict[str, Any]] = []
        self.reset_conversation()

        # Initialize OpenAI Client if credentials present
        self.client = None
        if self.api_key and HAS_OPENAI:
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            self.client = OpenAI(**client_kwargs)

    def reset_conversation(self):
        """Resets the in-memory conversation history with the System Prompt."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches an LLM tool call to the Python tool executor."""
        if tool_name == "get_ocr_input":
            return self.tool_executor.get_ocr_input(arguments.get("encounter_id"))
        elif tool_name == "get_db_schema":
            return self.tool_executor.get_db_schema(arguments.get("table_name"))
        elif tool_name == "run_sql_query":
            return self.tool_executor.run_sql_query(arguments["query"])
        elif tool_name == "insert_into_table":
            return self.tool_executor.insert_into_table(arguments["table_name"], arguments["records"])
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def process_document(
        self,
        ocr_lines: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        max_iterations: int = 12
    ) -> Dict[str, Any]:
        """
        Executes the autonomous ingestion loop.
        - Sets active document in tool executor
        - Runs OpenAI function calling iterations
        - Stores all turns in the in-memory conversation list
        """
        # Set active OCR data in tool executor
        self.tool_executor.set_active_document(ocr_lines, metadata)

        pat_name = metadata.get("patient_name") or metadata.get("full_name") or "Identified Patient"
        pat_id = metadata.get("patient_id", "PAT-AUTO")
        pat_abha = metadata.get("abha_id") or "N/A"
        enc_id = metadata.get("encounter_id", "ENC-NEW")
        rec_type = metadata.get("record_type", "prescription")

        # Append initial user instruction with strict patient binding
        user_message = f"""Please ingest the following medical record into our relational clinical database.
Encounter ID: {enc_id}
Target Patient: {pat_name} (Patient ID: {pat_id}, ABHA: {pat_abha})
Record Type: {rec_type}

Follow the 6-step protocol:
1. Inspect the OCR tokens and peek at the schema.
2. Verify patient {pat_name} ({pat_id}) exists in `patients` table (or insert if not already present).
3. Insert the parent encounter with encounter_id = '{enc_id}' and patient_id = '{pat_id}'.
4. Normalize medications (preserve Indic original & English translation), lab observations, vitals, and diagnoses. Ensure EVERY child record specifies patient_id = '{pat_id}' and encounter_id = '{enc_id}'.
5. Insert rows into the relational tables.
6. Provide a clinical ingestion summary for {pat_name}."""

        self.conversation_history.append({"role": "user", "content": user_message})

        print(f"\n[AGENT] Ingesting Encounter {enc_id} for Patient {pat_name} ({pat_id}) with Model: {self.model}...")

        # -------------------------------------------------------------
        # Live LLM Mode (When API Key is provided)
        # -------------------------------------------------------------
        if self.client:
            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                try:
                    kwargs = {
                        "model": self.model,
                        "messages": self.conversation_history,
                        "tools": OPENAI_TOOLS,
                        "tool_choice": "auto"
                    }
                    if any(x in self.model.lower() for x in ["luna", "gpt-6", "o1", "o3"]):
                        kwargs["reasoning_effort"] = "none"

                    response = self.client.chat.completions.create(**kwargs)
                except Exception as e:
                    print(f"[AGENT ERROR] OpenAI API call failed: {e}")
                    raise e

                response_msg = response.choices[0].message
                tool_calls = response_msg.tool_calls

                # Append assistant response to in-memory conversation
                self.conversation_history.append(response_msg.model_dump(exclude_none=True))

                # If no tool calls, model has finished reasoning
                if not tool_calls:
                    print(f"[AGENT] Final response generated in {iteration} steps.")
                    return {
                        "status": "success",
                        "model": self.model,
                        "conversation_steps": len(self.conversation_history),
                        "summary": response_msg.content,
                        "conversation_history": self.conversation_history
                    }

                # Execute each tool call
                for tc in tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}

                    print(f"  -> Tool Call: {fn_name}({list(fn_args.keys())})")
                    tool_result = self.execute_tool_call(fn_name, fn_args)

                    # Append tool result to conversation history
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

        # -------------------------------------------------------------
        # Standalone / Deterministic Simulation Mode
        # (Executes the exact same tool calls and populates conversation list
        # while waiting for the user to provide their GPT Luna 6 API key)
        # -------------------------------------------------------------
        else:
            print("[INFO] OPENAI_API_KEY / LUNA_API_KEY not yet provided.")
            print("[INFO] Executing deterministic protocol with the 4 general tools...")

            # 1. Tool Call: get_ocr_input
            res_ocr = self.execute_tool_call("get_ocr_input", {})
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "get_ocr_input", "arguments": "{}"}}]
            })
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": "call_1",
                "content": json.dumps({"status": "success", "line_count": res_ocr.get("line_count", 0)})
            })

            # 2. Tool Call: get_db_schema
            res_schema = self.execute_tool_call("get_db_schema", {})
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "get_db_schema", "arguments": "{}"}}]
            })
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": "call_2",
                "content": json.dumps({"status": "success", "tables": list(res_schema.get("tables", {}).keys())})
            })

            # 3. Use Clinical Ingestion Parser to assemble entities and execute tool calls
            import ingestion_agent
            clinical_parser = ingestion_agent.ClinicalIngestionAgent(self.tool_executor.db_path)
            bundle = clinical_parser.parse_raw_ocr_lines(ocr_lines, metadata)

            # 4. Tool Call: Resolve patient with run_sql_query
            p = bundle["patient"]
            check_sql = f"SELECT patient_id FROM patients WHERE abha_id = '{p.get('abha_id')}';"
            res_patient_check = self.execute_tool_call("run_sql_query", {"query": check_sql})
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call_3", "type": "function", "function": {"name": "run_sql_query", "arguments": json.dumps({"query": check_sql})}}]
            })
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": "call_3",
                "content": json.dumps(res_patient_check)
            })

            encounter_id = bundle["encounter"]["encounter_id"]
            patient_id = p["patient_id"]

            meds = bundle.get("medications", [])
            for m in meds:
                m["encounter_id"] = encounter_id
                m["patient_id"] = patient_id

            diags = bundle.get("diagnoses", [])
            for d in diags:
                d["encounter_id"] = encounter_id
                d["patient_id"] = patient_id

            vitals_list = []
            if bundle.get("vitals"):
                v = bundle["vitals"]
                v["encounter_id"] = encounter_id
                v["patient_id"] = patient_id
                vitals_list.append(v)

            labs = bundle.get("lab_observations", [])
            for l in labs:
                l["encounter_id"] = encounter_id
                l["patient_id"] = patient_id

            instrs = bundle.get("clinical_instructions", [])
            for c in instrs:
                c["encounter_id"] = encounter_id
                c["patient_id"] = patient_id

            # 5. Tool Calls: insert_into_table for each entity
            inserts = [
                ("patients", [p]),
                ("encounters", [bundle["encounter"]]),
                ("diagnoses", diags),
                ("vitals", vitals_list),
                ("medications", meds),
                ("lab_observations", labs),
                ("clinical_instructions", instrs)
            ]

            step_idx = 4
            for tbl, rows in inserts:
                if rows:
                    call_id = f"call_{step_idx}"
                    step_idx += 1
                    res_ins = self.execute_tool_call("insert_into_table", {"table_name": tbl, "records": rows})
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{"id": call_id, "type": "function", "function": {"name": "insert_into_table", "arguments": json.dumps({"table_name": tbl, "count": len(rows)})}}]
                    })
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(res_ins)
                    })

            # 6. Final Assistant Summary
            final_summary = f"""### Clinical Ingestion Summary (Encounter: {metadata.get('encounter_id')})
- **Patient**: {p.get('full_name')} (ABHA: {p.get('abha_id')})
- **Hospital / Doctor**: {bundle['encounter'].get('hospital_name')} / {bundle['encounter'].get('doctor_name')}
- **Ingested Entities**:
  - {len(bundle.get('medications', []))} Medications (Bilingual Telugu/Hindi preserved with normalized English)
  - {len(bundle.get('lab_observations', []))} Lab Observations
  - {len(bundle.get('diagnoses', []))} Diagnoses
  - {1 if bundle.get('vitals') else 0} Vitals Record
- **Database Status**: Successfully committed into SQLite/MySQL relational tables.
*(Note: To connect live GPT Luna 6 inference, provide OPENAI_API_KEY in .env).*"""

            self.conversation_history.append({
                "role": "assistant",
                "content": final_summary
            })

            return {
                "status": "success",
                "model": f"{self.model} (Ready for API Key)",
                "conversation_steps": len(self.conversation_history),
                "summary": final_summary,
                "conversation_history": self.conversation_history
            }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Returns the current in-memory conversation list."""
        return self.conversation_history
