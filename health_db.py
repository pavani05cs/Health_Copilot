"""
Health Copilot Relational Database Engine (SQLite / MySQL-compatible)
Normalized clinical schema conforming to ABDM entities and FHIR R4 resources.
Supports transactional ingestion, longitudinal querying, and entity relationships.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "health_copilot.db")


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys and WAL mode enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: str = DB_FILE):
    """Creates the complete normalized relational schema."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Master Patients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        abha_id TEXT UNIQUE,
        full_name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        contact_phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Encounters / Documents Table (One row per ingested document/visit)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS encounters (
        encounter_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        encounter_date TEXT NOT NULL,
        record_type TEXT NOT NULL, -- prescription, lab_report, discharge_summary, other
        hospital_name TEXT,
        department TEXT,
        doctor_name TEXT,
        doctor_reg_no TEXT,
        doctor_qualification TEXT,
        s3_raw_key TEXT,
        s3_artifacts_key TEXT,
        s3_fhir_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 3. Diagnoses / Conditions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diagnoses (
        diagnosis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        condition_name TEXT NOT NULL,
        icd10_code TEXT,
        clinical_status TEXT DEFAULT 'active', -- active, resolved, provisional
        severity TEXT,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 4. Clinical Vitals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vitals (
        vital_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        systolic_bp REAL,
        diastolic_bp REAL,
        pulse_bpm INTEGER,
        temperature_f REAL,
        spo2_percent REAL,
        bmi REAL,
        recorded_date TEXT,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 5. Medications / Prescriptions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        medication_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        drug_name TEXT NOT NULL,
        brand_name TEXT,
        dosage_form TEXT, -- Tab, Cap, Syrup, Inj
        strength TEXT, -- 500mg, 40mg, etc.
        frequency_code TEXT, -- 1-0-1, 1-0-0, OD, BD, PRN
        frequency_text TEXT, -- Twice daily, Once daily
        timing TEXT, -- After meals, Empty stomach
        duration TEXT, -- 15 days, 1 month, etc.
        instructions_original TEXT, -- Original Indic or Latin text
        instructions_english TEXT, -- Standardized English translation
        detected_language TEXT, -- telugu, hindi, english
        status TEXT DEFAULT 'active', -- active, completed, discontinued
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 6. Lab Observations / Test Results Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lab_observations (
        observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        panel_name TEXT, -- Diabetic Profile, Hemogram, etc.
        test_name TEXT NOT NULL, -- Fasting Blood Sugar, HbA1c, Platelets
        test_code_loinc TEXT,
        value_numeric REAL,
        value_string TEXT,
        unit TEXT, -- mg/dL, %, /mcL
        ref_range_low REAL,
        ref_range_high REAL,
        ref_range_string TEXT, -- "70 - 100"
        interpretation TEXT, -- NORMAL, HIGH, LOW, CRITICAL
        observation_date TEXT NOT NULL,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 7. Clinical Instructions & Lifestyle Advice Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinical_instructions (
        instruction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        category TEXT, -- diet, exercise, warning, follow_up, general
        instruction_original TEXT,
        instruction_english TEXT,
        detected_language TEXT,
        follow_up_date TEXT,
        FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id) ON DELETE CASCADE,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
    );
    """)

    # 8. Ingestion Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        encounter_id TEXT,
        patient_id TEXT,
        ocr_line_count INTEGER,
        entities_extracted INTEGER,
        status TEXT, -- SUCCESS, FAILED, PARTIAL
        agent_model TEXT,
        latency_ms REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_encounters_date ON encounters(encounter_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meds_patient ON medications(patient_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meds_status ON medications(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_labs_patient_test ON lab_observations(patient_id, test_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals(patient_id);")

    conn.commit()
    conn.close()
    print(f"[DB] Initialized Health Copilot Relational Database at: {db_path}")


# ---------------------------------------------------------------------------
# High-Level Transactional CRUD Helpers
# ---------------------------------------------------------------------------

def upsert_patient(patient_data: Dict[str, Any], db_path: str = DB_FILE) -> str:
    """Insert or update patient demographic master record."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO patients (patient_id, abha_id, full_name, age, gender, contact_phone)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(patient_id) DO UPDATE SET
        abha_id = COALESCE(excluded.abha_id, patients.abha_id),
        full_name = COALESCE(excluded.full_name, patients.full_name),
        age = COALESCE(excluded.age, patients.age),
        gender = COALESCE(excluded.gender, patients.gender),
        contact_phone = COALESCE(excluded.contact_phone, patients.contact_phone);
    """, (
        patient_data["patient_id"],
        patient_data.get("abha_id"),
        patient_data.get("full_name", "Unknown Patient"),
        patient_data.get("age"),
        patient_data.get("gender"),
        patient_data.get("contact_phone"),
    ))
    conn.commit()
    conn.close()
    return patient_data["patient_id"]


def insert_encounter(enc: Dict[str, Any], db_path: str = DB_FILE) -> str:
    """Inserts a new clinical encounter document record."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO encounters (
        encounter_id, patient_id, encounter_date, record_type,
        hospital_name, department, doctor_name, doctor_reg_no, doctor_qualification,
        s3_raw_key, s3_artifacts_key, s3_fhir_key
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        enc["encounter_id"],
        enc["patient_id"],
        enc.get("encounter_date", datetime.utcnow().strftime("%Y-%m-%d")),
        enc.get("record_type", "prescription"),
        enc.get("hospital_name"),
        enc.get("department"),
        enc.get("doctor_name"),
        enc.get("doctor_reg_no"),
        enc.get("doctor_qualification"),
        enc.get("s3_raw_key"),
        enc.get("s3_artifacts_key"),
        enc.get("s3_fhir_key"),
    ))
    conn.commit()
    conn.close()
    return enc["encounter_id"]


def insert_clinical_bundle(payload: Dict[str, Any], db_path: str = DB_FILE):
    """
    Atomically ingests an entire parsed document bundle into the relational DB.
    Enforces ACID compliance via single database transaction.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION;")

        # 1. Upsert Patient
        p = payload["patient"]
        cursor.execute("""
        INSERT INTO patients (patient_id, abha_id, full_name, age, gender, contact_phone)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(patient_id) DO UPDATE SET
            abha_id = COALESCE(excluded.abha_id, patients.abha_id),
            full_name = COALESCE(excluded.full_name, patients.full_name),
            age = COALESCE(excluded.age, patients.age),
            gender = COALESCE(excluded.gender, patients.gender),
            contact_phone = COALESCE(excluded.contact_phone, patients.contact_phone);
        """, (
            p["patient_id"],
            p.get("abha_id"),
            p.get("full_name", "Unknown"),
            p.get("age"),
            p.get("gender"),
            p.get("contact_phone")
        ))

        # 2. Insert Encounter
        enc = payload["encounter"]
        encounter_id = enc["encounter_id"]
        patient_id = p["patient_id"]
        cursor.execute("""
        INSERT OR REPLACE INTO encounters (
            encounter_id, patient_id, encounter_date, record_type,
            hospital_name, department, doctor_name, doctor_reg_no, doctor_qualification,
            s3_raw_key, s3_artifacts_key, s3_fhir_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            encounter_id,
            patient_id,
            enc.get("encounter_date", datetime.utcnow().strftime("%Y-%m-%d")),
            enc.get("record_type", "prescription"),
            enc.get("hospital_name"),
            enc.get("department"),
            enc.get("doctor_name"),
            enc.get("doctor_reg_no"),
            enc.get("doctor_qualification"),
            enc.get("s3_raw_key"),
            enc.get("s3_artifacts_key"),
            enc.get("s3_fhir_key"),
        ))

        # 3. Insert Diagnoses
        for diag in payload.get("diagnoses", []):
            cursor.execute("""
            INSERT INTO diagnoses (encounter_id, patient_id, condition_name, icd10_code, clinical_status, severity)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (
                encounter_id,
                patient_id,
                diag["condition_name"],
                diag.get("icd10_code"),
                diag.get("clinical_status", "active"),
                diag.get("severity")
            ))

        # 4. Insert Vitals
        v = payload.get("vitals")
        if v:
            cursor.execute("""
            INSERT INTO vitals (
                encounter_id, patient_id, systolic_bp, diastolic_bp,
                pulse_bpm, temperature_f, spo2_percent, bmi, recorded_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                encounter_id,
                patient_id,
                v.get("systolic_bp"),
                v.get("diastolic_bp"),
                v.get("pulse_bpm"),
                v.get("temperature_f"),
                v.get("spo2_percent"),
                v.get("bmi"),
                v.get("recorded_date", enc.get("encounter_date"))
            ))

        # 5. Insert Medications
        for med in payload.get("medications", []):
            cursor.execute("""
            INSERT INTO medications (
                encounter_id, patient_id, drug_name, brand_name, dosage_form,
                strength, frequency_code, frequency_text, timing, duration,
                instructions_original, instructions_english, detected_language, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                encounter_id,
                patient_id,
                med["drug_name"],
                med.get("brand_name"),
                med.get("dosage_form"),
                med.get("strength"),
                med.get("frequency_code"),
                med.get("frequency_text"),
                med.get("timing"),
                med.get("duration"),
                med.get("instructions_original"),
                med.get("instructions_english"),
                med.get("detected_language"),
                med.get("status", "active")
            ))

        # 6. Insert Lab Observations
        for lab in payload.get("lab_observations", []):
            cursor.execute("""
            INSERT INTO lab_observations (
                encounter_id, patient_id, panel_name, test_name, test_code_loinc,
                value_numeric, value_string, unit, ref_range_low, ref_range_high,
                ref_range_string, interpretation, observation_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                encounter_id,
                patient_id,
                lab.get("panel_name"),
                lab["test_name"],
                lab.get("test_code_loinc"),
                lab.get("value_numeric"),
                lab.get("value_string"),
                lab.get("unit"),
                lab.get("ref_range_low"),
                lab.get("ref_range_high"),
                lab.get("ref_range_string"),
                lab.get("interpretation", "NORMAL"),
                lab.get("observation_date", enc.get("encounter_date"))
            ))

        # 7. Insert Clinical Instructions
        for inst in payload.get("clinical_instructions", []):
            cursor.execute("""
            INSERT INTO clinical_instructions (
                encounter_id, patient_id, category, instruction_original,
                instruction_english, detected_language, follow_up_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                encounter_id,
                patient_id,
                inst.get("category", "general"),
                inst.get("instruction_original"),
                inst.get("instruction_english"),
                inst.get("detected_language"),
                inst.get("follow_up_date")
            ))

        # 8. Record Ingestion Audit Log
        audit = payload.get("audit", {})
        cursor.execute("""
        INSERT INTO ingestion_audit_log (
            encounter_id, patient_id, ocr_line_count, entities_extracted,
            status, agent_model, latency_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            encounter_id,
            patient_id,
            audit.get("ocr_line_count", 0),
            audit.get("entities_extracted", 0),
            audit.get("status", "SUCCESS"),
            audit.get("agent_model", "IngestionAgent-v1"),
            audit.get("latency_ms", 0.0)
        ))

        conn.commit()
        print(f"[DB SUCCESS] Fully ingested clinical bundle for Encounter {encounter_id} (Patient: {patient_id})")

    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] Transaction rolled back due to error: {e}")
        raise e
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Downstream Clinical Query API (for Agents & Copilot UI)
# ---------------------------------------------------------------------------

def query_patient_timeline(patient_id: str, db_path: str = DB_FILE) -> Dict[str, Any]:
    """Retrieves full longitudinal health timeline for a patient."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE patient_id = ?;", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        conn.close()
        return {}

    cursor.execute("SELECT * FROM encounters WHERE patient_id = ? ORDER BY encounter_date DESC;", (patient_id,))
    encounters = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM medications WHERE patient_id = ? AND status = 'active';", (patient_id,))
    active_meds = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM diagnoses WHERE patient_id = ? AND clinical_status = 'active';", (patient_id,))
    diagnoses = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_date DESC LIMIT 5;", (patient_id,))
    recent_vitals = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT test_name, value_numeric, unit, ref_range_string, interpretation, observation_date 
        FROM lab_observations WHERE patient_id = ? ORDER BY observation_date DESC;
    """, (patient_id,))
    labs = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "patient": dict(patient),
        "encounters": encounters,
        "diagnoses": diagnoses,
        "active_medications": active_meds,
        "recent_vitals": recent_vitals,
        "lab_observations": labs
    }


def query_lab_trend(patient_id: str, test_name: str, db_path: str = DB_FILE) -> List[Dict[str, Any]]:
    """Retrieves chronological numeric trend of a specific test (e.g. FBS, HbA1c, Platelets)."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT observation_date, value_numeric, unit, ref_range_string, interpretation
        FROM lab_observations
        WHERE patient_id = ? AND LOWER(test_name) LIKE LOWER(?)
        ORDER BY observation_date ASC;
    """, (patient_id, f"%{test_name}%"))
    results = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return results


if __name__ == "__main__":
    init_db()
