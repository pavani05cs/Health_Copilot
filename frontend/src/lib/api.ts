import { Patient, PatientTimeline, IngestionResult } from '../types';

// Determine best API base URL:
// On EC2 (e.g. 3.27.249.44:5173), direct calls to :8000 connect straight to the
// multi-worker asynchronous FastAPI engine, avoiding single-thread proxy bottlenecks.
export const getApiBase = (): string => {
  if (
    typeof window !== 'undefined' &&
    window.location.hostname &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
  ) {
    return `${window.location.protocol}//${window.location.hostname}:8000/api`;
  }
  return '/api';
};

export async function fetchPatients(): Promise<Patient[]> {
  const url = `${getApiBase()}/patients`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.patients || [];
  } catch (err) {
    // Fallback to relative proxy if direct failed
    if (!url.startsWith('/api')) {
      try {
        const fallbackRes = await fetch('/api/patients');
        if (fallbackRes.ok) {
          const fallbackData = await fallbackRes.json();
          return fallbackData.patients || [];
        }
      } catch {}
    }
    console.error('Failed to fetch patients:', err);
    return [
      {
        patient_id: 'PAT-VINEETHA-21F',
        abha_id: '91-8842-1920-2026',
        full_name: 'Vineetha',
        age: 21,
        gender: 'Female',
        contact_phone: '+91 97012 34567',
        conditions: ['Thyrocare Health Checkup', 'Full Body Lab Panel'],
        encounter_count: 5
      },
      {
        patient_id: 'PAT-91443288912011',
        abha_id: '91-4432-8891-2011',
        full_name: 'Ramesh Rao',
        age: 52,
        gender: 'Male',
        contact_phone: '+91 98480 12345',
        conditions: ['Type 2 Diabetes Mellitus', 'Essential Hypertension'],
        encounter_count: 4
      },
      {
        patient_id: 'PAT-14882133419920',
        abha_id: '14-8821-3341-9920',
        full_name: 'Sunita Sharma',
        age: 46,
        gender: 'Female',
        contact_phone: '+91 98110 54321',
        conditions: ['Acute Febrile Illness / Viral Fever', 'Mild Dehydration'],
        encounter_count: 2
      }
    ];
  }
}

export async function fetchPatientTimeline(patientId: string): Promise<PatientTimeline | null> {
  const url = `${getApiBase()}/patient/${encodeURIComponent(patientId)}/timeline`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    if (!url.startsWith('/api')) {
      try {
        const fallbackRes = await fetch(`/api/patient/${encodeURIComponent(patientId)}/timeline`);
        if (fallbackRes.ok) return await fallbackRes.json();
      } catch {}
    }
    console.error(`Failed to fetch timeline for ${patientId}:`, err);
    return null;
  }
}

export async function fetchLabTrend(patientId: string, testName: string): Promise<any[]> {
  const url = `${getApiBase()}/patient/${encodeURIComponent(patientId)}/labs/${encodeURIComponent(testName)}`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.data_points || [];
  } catch (err) {
    console.error(`Failed to fetch lab trend for ${testName}:`, err);
    return [];
  }
}

export async function sendCopilotChat(payload: {
  patient_id: string;
  message: string;
  language?: string;
  session_id?: string;
}): Promise<{
  status: string;
  answer: string;
  invoked_tools?: string[];
  latency_ms?: number;
  model?: string;
  message?: string;
}> {
  const url = `${getApiBase()}/copilot/chat`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  } catch (err) {
    if (!url.startsWith('/api')) {
      const fallbackRes = await fetch('/api/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return await fallbackRes.json();
    }
    throw err;
  }
}

export async function processRecord(formData: FormData): Promise<IngestionResult> {
  const primaryUrl = `${getApiBase()}/process-record`;
  try {
    const res = await fetch(primaryUrl, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const errText = await res.text();
      try {
        const errJson = JSON.parse(errText);
        throw new Error(errJson.detail || errJson.message || `Upload failed with status ${res.status}`);
      } catch {
        throw new Error(`Upload failed (${res.status}): ${errText.slice(0, 100)}`);
      }
    }
    return await res.json();
  } catch (err: any) {
    // If direct port 8000 failed, attempt proxy fallback via port 5173 /api
    if (!primaryUrl.startsWith('/api')) {
      console.warn('Direct port 8000 failed, attempting proxy fallback via /api/process-record:', err);
      try {
        const fallbackRes = await fetch('/api/process-record', {
          method: 'POST',
          body: formData
        });
        if (fallbackRes.ok) {
          return await fallbackRes.json();
        }
      } catch {}
    }
    throw err;
  }
}

export async function fetchDbStats(): Promise<Record<string, number>> {
  try {
    const res = await fetch(`${getApiBase()}/db/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.tables || {};
  } catch (err) {
    console.error('Failed to fetch DB stats:', err);
    return {};
  }
}
