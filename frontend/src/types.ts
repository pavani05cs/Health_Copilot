export interface Patient {
  patient_id: string;
  full_name: string;
  age?: number;
  gender?: string;
  abha_id?: string;
  contact_phone?: string;
  created_at?: string;
  encounter_count?: number;
  conditions?: string[];
}

export interface Encounter {
  encounter_id: string;
  patient_id: string;
  encounter_date: string;
  record_type: string;
  hospital_name?: string;
  doctor_name?: string;
  doctor_reg_no?: string;
  doctor_qualification?: string;
  s3_raw_key?: string;
  s3_artifacts_key?: string;
  s3_fhir_key?: string;
}

export interface Diagnosis {
  diagnosis_id?: number;
  condition_name: string;
  icd10_code?: string;
  clinical_status?: string;
  severity?: string;
}

export interface Medication {
  medication_id?: number;
  drug_name: string;
  strength?: string;
  dosage_form?: string;
  frequency?: string;
  duration?: string;
  instructions_original?: string;
  instructions_english?: string;
  language_code?: string;
  is_active?: number;
}

export interface LabObservation {
  observation_id?: number;
  test_name: string;
  value_numeric?: number;
  unit?: string;
  reference_range?: string;
  interpretation?: string;
  observation_date?: string;
}

export interface Vital {
  vital_id?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  pulse_bpm?: number;
  temperature_f?: number;
  spo2_percent?: number;
  bmi?: number;
  recorded_date?: string;
}

export interface PatientTimeline {
  patient: Patient;
  encounters: Encounter[];
  diagnoses: Diagnosis[];
  active_medications: Medication[];
  all_medications: Medication[];
  lab_observations: LabObservation[];
  vitals: Vital[];
  clinical_instructions: any[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  language?: string;
  invoked_tools?: string[];
  latency_ms?: number;
  timestamp: string;
}

export interface IngestionResult {
  status: string;
  patient_id?: string;
  encounter_id?: string;
  language_detected?: string;
  ocr_latency_ms?: number;
  llm_latency_ms?: number;
  structured_data?: {
    patient?: Partial<Patient>;
    encounter?: Partial<Encounter>;
    vitals?: Partial<Vital>;
    diagnoses?: Diagnosis[];
    medications?: Medication[];
    lab_observations?: LabObservation[];
    clinical_instructions?: any[];
  };
  s3_storage?: {
    raw_bucket?: string;
    raw_key?: string;
    artifacts_bucket?: string;
    ocr_tokens_key?: string;
    fhir_bucket?: string;
    fhir_key?: string;
    summaries?: any;
  };
}
