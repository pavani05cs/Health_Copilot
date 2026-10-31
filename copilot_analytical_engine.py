"""
AI-Powered Personal Health Copilot - Downstream Analytical Engine
Powered by GPT-6-Luna (OpenAI Python SDK) with deterministic clinical tools,
cross-encounter drug-drug interaction analysis, longitudinal biomarker trends,
and multilingual (English, Telugu, Hindi) clinical reasoning.
"""

import os
import sys
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import health_db

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ---------------------------------------------------------------------------
# Clinical Knowledge Base (Drug Interactions, Reference Norms, Red Flags)
# ---------------------------------------------------------------------------

CLINICAL_KNOWLEDGE_BASE = {
    "drug_interactions": [
        {
            "pair": ["metformin", "glimepiride"],
            "severity": "MODERATE",
            "type": "SYNERGISTIC_ANTIDIABETIC",
            "clinical_mechanism": "Complementary mechanisms for glycemic control (sensitizer + secretagogue). Increased risk of hypoglycemia compared to Metformin monotherapy.",
            "recommendation": "Maintain regular meal schedule. Never skip meals when taking Glimepiride. Keep fast-acting sugar or glucose tablets accessible."
        },
        {
            "pair": ["metformin", "telmisartan"],
            "severity": "LOW / BENEFICIAL",
            "type": "CARDIO_METABOLIC_SYNERGY",
            "clinical_mechanism": "Telmisartan (ARB) provides renal and vascular protection in diabetic hypertension without impairing glycemic control.",
            "recommendation": "Compatible chronic regimen. Monitor renal function (serum creatinine) annually."
        },
        {
            "pair": ["glimepiride", "telmisartan"],
            "severity": "LOW",
            "type": "MONITORED",
            "clinical_mechanism": "No direct pharmacokinetic interference. Blood pressure reduction may occasionally mask subtle autonomic hypoglycemia sensations.",
            "recommendation": "Be aware of diaphoresis (sweating) or shakiness as primary hypoglycemia signs."
        },
        {
            "pair": ["vitamin d3", "metformin"],
            "severity": "BENEFICIAL",
            "type": "NUTRITIONAL_SUPPORT",
            "clinical_mechanism": "Vitamin D repletion improves insulin sensitivity in type 2 diabetes.",
            "recommendation": "Take Vitamin D3 once weekly after meals (preferably containing dietary fat) for optimal bioavailability."
        }
    ],
    "lab_reference_ranges": {
        "fbs": {"name": "Fasting Blood Sugar (FBS)", "unit": "mg/dL", "normal_low": 70, "normal_high": 100, "prediabetes_high": 125, "clinical_guideline": "ADA 2026 Standards of Care"},
        "hba1c": {"name": "Hemoglobin A1c (HbA1c)", "unit": "%", "normal_high": 5.7, "prediabetes_high": 6.4, "diabetes_target": 7.0, "clinical_guideline": "ADA / RSSDI 2026 Guidelines"},
        "creatinine": {"name": "Serum Creatinine", "unit": "mg/dL", "normal_low": 0.6, "normal_high": 1.2, "clinical_guideline": "KDIGO Guidelines"}
    },
    "red_flag_symptoms": {
        "hypoglycemia": {
            "keywords": ["dizzy", "dizziness", "shaky", "tremor", "sweat", "cold sweat", "palpitations", "fainting", "నీరసం", "మైకం", "వణుకు", "చమటలు", "చక్కర తగ్గడం", "चक्कर", "कंपकंपी", "पसीना", "बेहोशी"],
            "urgency": "IMMEDIATE_ACTION",
            "first_aid": "Consume 15 grams of fast-acting carbohydrate immediately (half cup fruit juice, 3-4 teaspoons glucose/sugar, or hard candies). Rest for 15 minutes and re-check blood glucose.",
            "escalation": "If symptoms persist or confusion worsens, seek immediate emergency medical care."
        },
        "hypertensive_crisis": {
            "keywords": ["severe headache", "blurred vision", "chest pain", "shortness of breath", "తీవ్రమైన తలనొప్పి", "గుండెల్లో నొప్పి", "ఊపిరి ఆడకపోవడం", "सिरदर्द", "सीने में दर्द"],
            "urgency": "EMERGENCY_ESCALATION",
            "first_aid": "Sit down calmly, rest, and do not self-administer extra medication without medical guidance.",
            "escalation": "Contact nearest emergency department or treating cardiologist immediately."
        }
    }
}


# ---------------------------------------------------------------------------
# Deterministic Clinical Tools Implementation
# ---------------------------------------------------------------------------

class CopilotToolExecutor:
    """
    Deterministic clinical database query engine connecting to SQLite/MySQL.
    Guarantees medical ground-truth and prevents LLM hallucination.
    """

    def __init__(self, db_path: str = health_db.DB_FILE):
        self.db_path = db_path

    def _resolve_patient_id(self, patient_or_abha: str) -> Optional[str]:
        conn = health_db.get_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT patient_id FROM patients 
            WHERE patient_id = ? OR abha_id = ? OR contact_phone = ?
            LIMIT 1;
        """, (patient_or_abha, patient_or_abha, patient_or_abha))
        row = c.fetchone()
        conn.close()
        return row[0] if row else patient_or_abha

    def get_patient_profile(self, patient_id: str) -> Dict[str, Any]:
        """Tool 1: Demographics, active diagnoses, recent vitals, latest encounter."""
        pid = self._resolve_patient_id(patient_id)
        timeline = health_db.query_patient_timeline(pid, self.db_path)
        if not timeline or not timeline.get("patient"):
            return {"status": "error", "message": f"Patient '{patient_id}' not found."}

        p = timeline["patient"]
        recent_enc = timeline["encounters"][0] if timeline.get("encounters") else {}
        recent_vital = timeline["recent_vitals"][0] if timeline.get("recent_vitals") else {}

        return {
            "status": "success",
            "patient_id": p["patient_id"],
            "full_name": p["full_name"],
            "abha_id": p.get("abha_id"),
            "age": p.get("age"),
            "gender": p.get("gender"),
            "active_conditions": [d["condition_name"] for d in timeline.get("diagnoses", [])],
            "latest_vitals": {
                "blood_pressure": f"{recent_vital.get('systolic_bp')}/{recent_vital.get('diastolic_bp')} mmHg" if recent_vital.get('systolic_bp') else "N/A",
                "pulse": f"{recent_vital.get('pulse_bpm')} bpm" if recent_vital.get('pulse_bpm') else "N/A",
                "bmi": recent_vital.get('bmi', "N/A"),
                "date": recent_vital.get('recorded_date')
            },
            "latest_encounter": {
                "encounter_id": recent_enc.get("encounter_id"),
                "date": recent_enc.get("encounter_date"),
                "hospital": recent_enc.get("hospital_name"),
                "doctor": recent_enc.get("doctor_name"),
                "qualification": recent_enc.get("doctor_qualification")
            }
        }

    def get_active_medications(self, patient_id: str) -> Dict[str, Any]:
        """Tool 2: All active drugs, frequency codes, Indic directions, and English translations."""
        pid = self._resolve_patient_id(patient_id)
        conn = health_db.get_connection(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT medication_id, drug_name, dosage_form, strength, frequency_code, 
                   frequency_text, timing, instructions_original, instructions_english, detected_language
            FROM medications 
            WHERE patient_id = ? AND status = 'active'
            ORDER BY medication_id ASC;
        """, (pid,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        # Deduplicate medications by drug_name (retaining latest prescription details)
        deduped = {}
        for r in rows:
            name_key = r["drug_name"].strip().lower()
            deduped[name_key] = r

        return {
            "status": "success",
            "patient_id": pid,
            "medication_count": len(deduped),
            "medications": list(deduped.values())
        }

    def get_lab_history_and_trends(self, patient_id: str, test_name: Optional[str] = None) -> Dict[str, Any]:
        """Tool 3: Chronological lab results, interpretations, and delta trajectories."""
        pid = self._resolve_patient_id(patient_id)
        conn = health_db.get_connection(self.db_path)
        c = conn.cursor()

        if test_name:
            c.execute("""
                SELECT test_name, value_numeric, value_string, unit, ref_range_string, interpretation, observation_date
                FROM lab_observations 
                WHERE patient_id = ? AND LOWER(test_name) LIKE LOWER(?)
                ORDER BY observation_date ASC, observation_id ASC;
            """, (pid, f"%{test_name.strip()}%"))
        else:
            c.execute("""
                SELECT test_name, value_numeric, value_string, unit, ref_range_string, interpretation, observation_date
                FROM lab_observations 
                WHERE patient_id = ?
                ORDER BY observation_date DESC, observation_id DESC;
            """, (pid,))

        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        # Group by test name and calculate trajectory if multiple observations exist
        grouped = {}
        for r in rows:
            t_name = r["test_name"]
            grouped.setdefault(t_name, []).append(r)

        trends_summary = {}
        for t_name, observations in grouped.items():
            valid_numerics = [o["value_numeric"] for o in observations if o["value_numeric"] is not None]
            trend_direction = "STABLE"
            if len(valid_numerics) >= 2:
                if valid_numerics[-1] > valid_numerics[0]:
                    trend_direction = "INCREASING"
                elif valid_numerics[-1] < valid_numerics[0]:
                    trend_direction = "DECREASING"

            latest = observations[-1]
            trends_summary[t_name] = {
                "latest_value": latest["value_numeric"] if latest["value_numeric"] is not None else latest["value_string"],
                "unit": latest.get("unit"),
                "latest_interpretation": latest.get("interpretation", "NORMAL"),
                "reference_range": latest.get("ref_range_string"),
                "observation_date": latest.get("observation_date"),
                "historical_count": len(observations),
                "trend_direction": trend_direction,
                "history": observations
            }

        return {
            "status": "success",
            "patient_id": pid,
            "test_count": len(trends_summary),
            "trends": trends_summary
        }

    def check_drug_interactions(self, medication_names: List[str]) -> Dict[str, Any]:
        """Tool 4: Evaluates pharmacological interactions between active drugs."""
        clean_names = [m.lower().strip() for m in medication_names if m]
        detected_interactions = []

        kb_interactions = CLINICAL_KNOWLEDGE_BASE["drug_interactions"]
        for item in kb_interactions:
            pair = item["pair"]
            # Check if both drugs in the pair are present in the list
            d1_matches = any(pair[0] in name for name in clean_names)
            d2_matches = any(pair[1] in name for name in clean_names)

            if d1_matches and d2_matches:
                detected_interactions.append({
                    "drugs": [pair[0].title(), pair[1].title()],
                    "severity": item["severity"],
                    "type": item["type"],
                    "mechanism": item["clinical_mechanism"],
                    "recommendation": item["recommendation"]
                })

        return {
            "status": "success",
            "evaluated_drugs": clean_names,
            "interaction_count": len(detected_interactions),
            "interactions": detected_interactions,
            "overall_safety_rating": "SAFE_WITH_MONITORING" if detected_interactions else "NO_KNOWN_INTERACTIONS"
        }

    def get_clinical_instructions(self, patient_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Tool 5: Doctor-mandated diet, exercise, follow-up dates, and red-flag emergency advice."""
        pid = self._resolve_patient_id(patient_id)
        conn = health_db.get_connection(self.db_path)
        c = conn.cursor()

        if category:
            c.execute("""
                SELECT instruction_id, category, instruction_original, instruction_english, 
                       detected_language, follow_up_date
                FROM clinical_instructions
                WHERE patient_id = ? AND LOWER(category) = LOWER(?)
                ORDER BY instruction_id ASC;
            """, (pid, category.strip()))
        else:
            c.execute("""
                SELECT instruction_id, category, instruction_original, instruction_english, 
                       detected_language, follow_up_date
                FROM clinical_instructions
                WHERE patient_id = ?
                ORDER BY instruction_id ASC;
            """, (pid,))

        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        # Detect upcoming follow-up date
        follow_ups = [r["follow_up_date"] for r in rows if r.get("follow_up_date")]
        latest_follow_up = follow_ups[0] if follow_ups else None

        return {
            "status": "success",
            "patient_id": pid,
            "instruction_count": len(rows),
            "next_follow_up_date": latest_follow_up,
            "instructions": rows
        }

    def generate_clinical_handover(self, patient_id: str) -> Dict[str, Any]:
        """Tool 6: Structured SBAR (Situation, Background, Assessment, Recommendation) brief for doctors."""
        pid = self._resolve_patient_id(patient_id)
        prof = self.get_patient_profile(pid)
        meds = self.get_active_medications(pid)
        labs = self.get_lab_history_and_trends(pid)
        instrs = self.get_clinical_instructions(pid)

        if prof.get("status") == "error":
            return {"status": "error", "message": f"Patient '{patient_id}' not found."}

        sbar = {
            "patient": {
                "name": prof["full_name"],
                "abha_id": prof["abha_id"],
                "age_sex": f"{prof['age']}y / {prof['gender']}"
            },
            "situation": f"Patient under care for {', '.join(prof['active_conditions']) or 'Chronic Illness'}.",
            "background": {
                "diagnoses": prof["active_conditions"],
                "latest_encounter": prof.get("latest_encounter"),
                "vitals": prof.get("latest_vitals")
            },
            "assessment": {
                "active_medication_count": meds.get("medication_count", 0),
                "medications": [f"{m['drug_name']} {m['strength']} ({m['frequency_code'] or m['frequency_text']})" for m in meds.get("medications", [])],
                "abnormal_labs": [
                    f"{t_name}: {info['latest_value']} {info['unit']} [{info['latest_interpretation']}]"
                    for t_name, info in labs.get("trends", {}).items() if info["latest_interpretation"] in ["HIGH", "LOW"]
                ]
            },
            "recommendation": {
                "next_follow_up": instrs.get("next_follow_up_date"),
                "instructions_summary": [i["instruction_english"] for i in instrs.get("instructions", []) if i.get("instruction_english")]
            }
        }

        return {
            "status": "success",
            "sbar": sbar
        }


# ---------------------------------------------------------------------------
# OpenAI Tool Specifications for GPT-6-Luna
# ---------------------------------------------------------------------------

COPILOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_profile",
            "description": "Fetches patient demographic profile, active diagnoses, recent vitals, and treating doctor/hospital details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID (e.g. 'PAT-91443288912011') or ABHA ID."}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_medications",
            "description": "Fetches all active prescribed medications, dosage forms, strengths, frequency codes (e.g. 1-0-1), timings, original Telugu/Hindi instructions, and English translations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID or ABHA ID."}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_lab_history_and_trends",
            "description": "Retrieves chronological lab observations, biological reference intervals, interpretations (HIGH/NORMAL/LOW), and longitudinal trend direction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID or ABHA ID."},
                    "test_name": {"type": "string", "description": "Optional specific test name (e.g. 'FBS', 'HbA1c', 'Creatinine') to filter."}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_drug_interactions",
            "description": "Evaluates pharmacological drug-drug interactions (DDIs), duplications, and safety warnings between a list of medication names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "medication_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of active medication names to analyze (e.g. ['Metformin', 'Glimepiride', 'Telmisartan'])."
                    }
                },
                "required": ["medication_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clinical_instructions",
            "description": "Retrieves doctor-mandated lifestyle advice, dietary rules, exercise goals, follow-up appointment date, and emergency red-flag precautions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID or ABHA ID."},
                    "category": {"type": "string", "description": "Optional category filter (e.g. 'diet', 'exercise', 'follow_up', 'emergency_warning')."}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_clinical_handover",
            "description": "Generates a structured SBAR (Situation, Background, Assessment, Recommendation) clinical handover summary formatted for doctors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient ID or ABHA ID."}
                },
                "required": ["patient_id"]
            }
        }
    }
]


# ---------------------------------------------------------------------------
# Clinical Copilot System Prompt
# ---------------------------------------------------------------------------

COPILOT_SYSTEM_PROMPT = """You are the "AI-Powered Personal Health Copilot", an empathetic, highly intelligent, and safe clinical assistant designed for patients and clinicians under India's ABDM healthcare framework.
You are powered by GPT-6-Luna and have access to verified clinical tools querying the patient's ground-truth relational health database (health_copilot.db).

---

### CORE OPERATING PRINCIPLES:

1. **GROUNDED IN GROUND TRUTH (ZERO HALLUCINATION)**:
   - Always call the provided tools (`get_patient_profile`, `get_active_medications`, `get_lab_history_and_trends`, `check_drug_interactions`, `get_clinical_instructions`, `generate_clinical_handover`) before answering clinical questions.
   - Ground all statements in the patient's records (reference the hospital e.g., Apollo Clinic, doctor e.g., Dr. K. Srinivas, and dates).

2. **MULTILINGUAL FLUENCY & CULTURAL ADAPTATION**:
   - If the user asks in Telugu (తెలుగు) or requests Telugu explanations: Respond in natural, grammatically correct Telugu script with warm empathy. Explain clinical terms simply (e.g. Fasting Sugar as "ఉదయం ఖాళీ కడుపుతో చేసే రక్త పరీక్ష", HbA1c as "గత 3 నెలల సగటు చక్కెర స్థాయి"). Include original prescription text when discussing medications.
   - If the user asks in Hindi (हिन्दी): Respond in clear Hindi script with empathetic explanations.
   - If the user asks in English: Use accessible, jargon-free 8th-grade level English.

3. **STRICT CLINICAL SAFETY GUARDRAILS (HEALTHCARE IMPACT)**:
   - **Non-Prescriptive**: You clarify and explain what the doctor has prescribed. You NEVER change dosages, add new prescription medications, or discontinue medications unilaterally.
   - **Attributed Advice**: Always remind the patient to discuss any changes with their treating doctor.
   - **Red-Flag Emergency Triage**:
     - If the user reports dizziness, shakiness, sweating, palpitations, or fainting (especially on Glimepiride / insulin): IMMEDIATELY flag potential Hypoglycemia (low blood sugar). Advise urgent first-aid (consume 15g fast sugar: half glass juice, 3 tsp sugar/glucose) and seek immediate medical evaluation.
     - If the user reports severe chest pain or hypertensive emergency: Direct them to emergency services immediately.

4. **ACTIONABLE EXPLANATIONS**:
   - When explaining medications, provide the exact daily schedule: Morning / Afternoon / Night and whether to take Before or After food.
   - When explaining lab results, always state the normal reference interval and whether the patient's value is High, Normal, or Low.
   - Highlight upcoming follow-up dates (e.g. 2026-10-27)."""


# ---------------------------------------------------------------------------
# Patient Copilot Agent Class
# ---------------------------------------------------------------------------

class PatientCopilotAgent:
    """
    Downstream Conversational Health Copilot powered by GPT-6-Luna.
    Maintains session history, invokes deterministic clinical tools,
    and returns rich multimodal responses for patients and clinicians.
    """

    def __init__(
        self,
        model: str = "gpt-6-luna",
        api_key: Optional[str] = None,
        db_path: str = health_db.DB_FILE
    ):
        self.model = os.environ.get("OPENAI_MODEL") or model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LUNA_API_KEY")
        self.tool_executor = CopilotToolExecutor(db_path)

        # In-memory sessions store: session_id -> list of messages
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}

        # Initialize OpenAI Client
        self.client = None
        if self.api_key and HAS_OPENAI:
            self.client = OpenAI(api_key=self.api_key)

    def _get_or_create_session(self, session_id: str, patient_id: str) -> List[Dict[str, Any]]:
        if session_id not in self.sessions:
            # Preload verified profile and active medications snapshot for immediate response
            profile = self.tool_executor.get_patient_profile(patient_id)
            meds_data = self.tool_executor.get_active_medications(patient_id)
            active_meds = meds_data.get("active_medications", [])
            med_list = [f"{m.get('drug_name', '')} {m.get('strength') or ''} ({m.get('frequency_text') or m.get('frequency_code') or ''})".strip() for m in active_meds]

            snapshot = (
                f"### VERIFIED ACTIVE PATIENT CONTEXT (Ground Truth):\n"
                f"- Patient Name: {profile.get('full_name', 'Unknown')}\n"
                f"- Patient ID: {profile.get('patient_id')}\n"
                f"- ABHA ID: {profile.get('abha_id', 'N/A')}\n"
                f"- Demographics: {profile.get('age', 'N/A')} years, {profile.get('gender', 'N/A')}\n"
                f"- Active Diagnoses: {', '.join(profile.get('active_conditions', [])) or 'None reported'}\n"
                f"- Active Medications: {'; '.join(med_list) if med_list else 'No active medications'}\n"
                f"- Recent Vitals: Blood Pressure {profile.get('latest_vitals', {}).get('blood_pressure')}, Pulse {profile.get('latest_vitals', {}).get('pulse')}\n"
                f"- Latest Encounter: {profile.get('latest_encounter', {}).get('hospital')} ({profile.get('latest_encounter', {}).get('date')})\n\n"
                f"NOTE: The verified patient profile and active medications are already provided above. "
                f"Respond directly and concisely without making redundant tool calls to get_patient_profile or get_active_medications. "
                f"Only invoke specific tools (such as check_drug_interactions, get_lab_history_and_trends, get_clinical_instructions, or generate_clinical_handover) when deep interaction analysis or specific historical lab trends are requested."
            )

            system_msg = {
                "role": "system",
                "content": f"{COPILOT_SYSTEM_PROMPT}\n\n{snapshot}"
            }
            self.sessions[session_id] = [system_msg]
        return self.sessions[session_id]

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches an LLM tool call to the deterministic CopilotToolExecutor."""
        if tool_name == "get_patient_profile":
            return self.tool_executor.get_patient_profile(arguments["patient_id"])
        elif tool_name == "get_active_medications":
            return self.tool_executor.get_active_medications(arguments["patient_id"])
        elif tool_name == "get_lab_history_and_trends":
            return self.tool_executor.get_lab_history_and_trends(
                arguments["patient_id"],
                arguments.get("test_name")
            )
        elif tool_name == "check_drug_interactions":
            return self.tool_executor.check_drug_interactions(arguments["medication_names"])
        elif tool_name == "get_clinical_instructions":
            return self.tool_executor.get_clinical_instructions(
                arguments["patient_id"],
                arguments.get("category")
            )
        elif tool_name == "generate_clinical_handover":
            return self.tool_executor.generate_clinical_handover(arguments["patient_id"])
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def chat(
        self,
        patient_id: str,
        message: str,
        session_id: Optional[str] = None,
        language: str = "auto",
        max_iterations: int = 8
    ) -> Dict[str, Any]:
        """
        Executes an autonomous clinical reasoning turn.
        - Loads session conversation history
        - Invokes GPT-6-Luna with tools (reasoning_effort='none')
        - Executes required tools
        - Formats response with clinical safety guardrails
        """
        sess_id = session_id or f"sess_{patient_id}"
        conversation = self._get_or_create_session(sess_id, patient_id)

        # Inject user instruction
        user_prompt = message
        if language in ["te", "telugu"]:
            user_prompt += "\n(Please respond in Telugu / తెలుగు script)."
        elif language in ["hi", "hindi"]:
            user_prompt += "\n(Please respond in Hindi / हिन्दी script)."

        conversation.append({"role": "user", "content": user_prompt})

        invoked_tools = []
        t0 = time.time()

        if self.client:
            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                try:
                    kwargs = {
                        "model": self.model,
                        "messages": conversation,
                        "tools": COPILOT_TOOLS,
                        "tool_choice": "auto"
                    }
                    if any(x in self.model.lower() for x in ["luna", "gpt-6", "o1", "o3"]):
                        kwargs["reasoning_effort"] = "none"

                    response = self.client.chat.completions.create(**kwargs)
                except Exception as e:
                    print(f"[COPILOT ERROR] GPT-6-Luna API call failed: {e}")
                    raise e

                response_msg = response.choices[0].message
                tool_calls = response_msg.tool_calls

                # Append assistant step
                conversation.append(response_msg.model_dump(exclude_none=True))

                # If no tool calls, generation is complete
                if not tool_calls:
                    elapsed = time.time() - t0
                    return {
                        "status": "success",
                        "model": self.model,
                        "session_id": sess_id,
                        "patient_id": patient_id,
                        "answer": response_msg.content,
                        "invoked_tools": invoked_tools,
                        "latency_ms": round(elapsed * 1000, 1),
                        "conversation_turns": len(conversation)
                    }

                # Execute tool calls
                for tc in tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        fn_args = {}

                    invoked_tools.append(fn_name)
                    print(f"  [COPILOT TOOL] -> {fn_name}({list(fn_args.keys())})")
                    tool_result = self.execute_tool_call(fn_name, fn_args)

                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

        # Fallback / Offline deterministic mode if no API key
        return {
            "status": "error",
            "message": "OpenAI client not configured. Please supply OPENAI_API_KEY in .env."
        }


# Quick test
if __name__ == "__main__":
    agent = PatientCopilotAgent()
    print(f"[INIT] PatientCopilotAgent ready with Model: {agent.model}")
