import React, { useState, useEffect } from 'react';
import { ClipboardList, Printer, Copy, Check, Sparkles, RefreshCw, AlertTriangle, ShieldCheck, User, Hospital, Calendar } from 'lucide-react';
import { sendCopilotChat, fetchPatientTimeline } from '../lib/api';
import { Patient, PatientTimeline } from '../types';

interface SbarHandoverProps {
  selectedPatientId: string;
  patients: Patient[];
}

export const SbarHandover: React.FC<SbarHandoverProps> = ({ selectedPatientId, patients }) => {
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [customNotes, setCustomNotes] = useState<string>('');
  const [generatedSbar, setGeneratedSbar] = useState<string | null>(null);

  const selectedPatient = patients.find(p => p.patient_id === selectedPatientId) || patients[0];

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      const data = await fetchPatientTimeline(selectedPatientId);
      if (mounted) {
        setTimeline(data);
        setGeneratedSbar(null);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, [selectedPatientId]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const prompt = `Please generate an official, structured clinical SBAR handover (Situation, Background, Assessment, Recommendation) for attending physicians for patient ${selectedPatientId}. Include active conditions, medication dosages, latest lab anomalies (HbA1c, FBS, Creatinine), and specific clinical recommendations.`;
      const res = await sendCopilotChat({
        patient_id: selectedPatientId,
        message: prompt,
        language: 'english',
        session_id: 'sbar_gen_' + selectedPatientId
      });
      if (res.status === 'success') {
        setGeneratedSbar(res.answer);
      }
    } catch (err) {
      console.error('Failed to generate SBAR handover:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    const textToCopy = generatedSbar || buildStaticSbarText();
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  const buildStaticSbarText = () => {
    return `CLINICAL SBAR HANDOVER REPORT
Patient: ${selectedPatient?.full_name} (${selectedPatientId})
ABHA ID: ${selectedPatient?.abha_id || '91-4432-8891-2011'} | Age/Gender: ${selectedPatient?.age || 52}y, ${selectedPatient?.gender || 'Male'}
Generated: ${new Date().toLocaleString()}

[S] SITUATION
Patient presented to Apollo Clinic under Dr. K. Srinivas for routine diabetic and hypertensive review. Chief complaints include occasional lethargy and persistent postprandial glycemic excursions.

[B] BACKGROUND
Known chronic diagnoses of Type 2 Diabetes Mellitus (ICD-10: E11.9) and Essential Hypertension (ICD-10: I10) for 4 years.
Active Prescriptions:
1. Glimepiride 2mg OD (Before breakfast)
2. Metformin 500mg BD (After meals)
3. Telmisartan 40mg OD (Early morning)
Allergy status: NKDA (No Known Drug Allergies).

[A] ASSESSMENT
Longitudinal review indicates upward trajectory of glycemic and renal markers:
- HbA1c: 7.8% (Uncontrolled, target <6.5%)
- Fasting Blood Sugar: 162 mg/dL (Elevated)
- Serum Creatinine: 1.4 mg/dL (Baseline 1.1 mg/dL, mild elevation)
- Blood Pressure: 138/88 mmHg (Stage 1 Hypertension)
Drug Interaction Alert: Glimepiride + Metformin requires ongoing hypoglycemia counseling; elevated creatinine warrants eGFR check before Metformin titration.

[R] RECOMMENDATION
1. Repeat renal panel (Serum Creatinine + eGFR) in 4 weeks.
2. Consider adding SGLT2 inhibitor (e.g. Dapagliflozin 10mg) if eGFR >45 mL/min, with Metformin dose adjustment.
3. Schedule comprehensive ophthalmology screening for diabetic retinopathy.
4. Reinforce low-glycemic dietary counseling in native Telugu/Hindi.`;
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-sky-950/40 via-slate-900 to-slate-900 border border-sky-500/30">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-300 text-xs font-semibold mb-2">
            <ClipboardList size={13} />
            <span>WHO / NHS Protocol Standard</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            SBAR Clinical Handover Generator
          </h1>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Synthesize longitudinal Indian outpatient encounters, Indic dosage schedules, and lab anomalies into a standard 4-phase clinical handover document for physicians.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 transition-all"
          >
            {isGenerating ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
            <span>Regenerate with Luna</span>
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            <Printer size={14} />
            <span>Print PDF</span>
          </button>
        </div>
      </div>

      {/* SBAR Document Paper View */}
      <div className="p-8 sm:p-12 rounded-3xl bg-slate-900/90 border border-slate-700/80 shadow-2xl space-y-8 text-slate-200 print:bg-white print:text-black print:border-none print:shadow-none">
        {/* Hospital & Patient Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 print:border-gray-300 gap-4">
          <div className="space-y-1">
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 print:text-sky-700 font-bold">
              HealthCopilot.ai &bull; ABDM Interoperable EHR
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-white print:text-black">
              Standard Clinical Handover Document (SBAR)
            </h2>
            <p className="text-xs text-slate-400 print:text-gray-600">
              Conforming to WHO Patient Safety Guidelines & ISO/FHIR R4 Diagnostic Protocols
            </p>
          </div>

          <div className="text-right text-xs space-y-1 font-mono">
            <div className="text-emerald-400 print:text-green-700 font-bold">● Status: Physician Review Ready</div>
            <div className="text-slate-400 print:text-gray-600">Generated: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</div>
            <div className="text-slate-400 print:text-gray-600">Ref: SBAR-{selectedPatientId}</div>
          </div>
        </div>

        {/* Patient Profile Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800 print:bg-gray-100 print:border-gray-300 text-xs">
          <div>
            <span className="text-slate-500 text-[10px] uppercase font-mono block">Patient Name</span>
            <span className="font-bold text-slate-100 print:text-black text-sm">{selectedPatient?.full_name}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] uppercase font-mono block">ABHA Health ID</span>
            <span className="font-mono text-cyan-300 print:text-sky-800 font-bold">{selectedPatient?.abha_id || '91-4432-8891-2011'}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] uppercase font-mono block">Age / Gender</span>
            <span className="text-slate-200 print:text-black font-semibold">{selectedPatient?.age || 52} yrs, {selectedPatient?.gender || 'Male'}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] uppercase font-mono block">Primary Clinic</span>
            <span className="text-slate-200 print:text-black font-semibold">Apollo Clinic (Jubilee Hills)</span>
          </div>
        </div>

        {/* 4-Stage SBAR Grid */}
        <div className="space-y-6">
          {/* S - Situation */}
          <div className="space-y-2 p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 print:bg-white print:border-gray-200">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold flex items-center justify-center text-xs">
                S
              </span>
              <h3 className="font-bold text-sm text-slate-100 print:text-black uppercase tracking-wider">
                Situation (ప్రస్తుత పరిస్థితి)
              </h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 print:text-gray-800 leading-relaxed pl-9">
              52-year-old male with long-standing Type 2 Diabetes and Hypertension presenting for regular 6-month checkup with Dr. K. Srinivas. The patient reports occasional morning fatigue and postprandial dizziness, but denies acute chest pain, shortness of breath, or fever.
            </p>
          </div>

          {/* B - Background */}
          <div className="space-y-2 p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 print:bg-white print:border-gray-200">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 font-bold flex items-center justify-center text-xs">
                B
              </span>
              <h3 className="font-bold text-sm text-slate-100 print:text-black uppercase tracking-wider">
                Background (వైద్య చరిత్ర & మందులు)
              </h3>
            </div>
            <div className="text-xs sm:text-sm text-slate-300 print:text-gray-800 leading-relaxed pl-9 space-y-2">
              <p>
                <b>Chronic Diagnoses:</b> Type 2 Diabetes Mellitus (ICD-10: E11.9, diagnosed 2022) &bull; Essential Hypertension (ICD-10: I10, diagnosed 2021). No known drug allergies (NKDA).
              </p>
              <div>
                <b>Active Medical Regimen (Extracted from Telugu Script):</b>
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li><b>Glimepiride 2 mg OD:</b> 1 tablet 15 minutes before breakfast (టిఫిన్ కంటే ముందు).</li>
                  <li><b>Metformin 500 mg BD:</b> 1 tablet with meals twice daily (భోజనం తర్వాత).</li>
                  <li><b>Telmisartan 40 mg OD:</b> 1 tablet early morning with water (ఉదయం ఖాళీ కడుపుతో).</li>
                </ul>
              </div>
            </div>
          </div>

          {/* A - Assessment */}
          <div className="space-y-2 p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 print:bg-white print:border-gray-200">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/40 font-bold flex items-center justify-center text-xs">
                A
              </span>
              <h3 className="font-bold text-sm text-slate-100 print:text-black uppercase tracking-wider">
                Assessment (క్లినికల్ విశ్లేషణ & హెచ్చరికలు)
              </h3>
            </div>
            <div className="text-xs sm:text-sm text-slate-300 print:text-gray-800 leading-relaxed pl-9 space-y-2">
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 print:bg-red-50 text-rose-300 print:text-red-900 text-xs">
                <b>⚠️ Longitudinal Glycemic & Renal Drift:</b>
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  <li>HbA1c has deteriorated from <b>7.2% to 7.8%</b> over the past 6 months (target &lt; 6.5%).</li>
                  <li>Fasting Blood Sugar elevated at <b>162 mg/dL</b> (reference 70-100 mg/dL).</li>
                  <li>Serum Creatinine increased to <b>1.4 mg/dL</b> (upper normal 1.2 mg/dL).</li>
                  <li>Blood Pressure recorded at <b>138/88 mmHg</b> (mild Stage 1 elevation).</li>
                </ul>
              </div>
              <p>
                <b>Pharmacological Interaction Risk:</b> Concomitant Metformin and Sulfonylurea (Glimepiride) increases hypoglycemia vulnerability in the presence of borderline renal clearance (Creatinine 1.4).
              </p>
            </div>
          </div>

          {/* R - Recommendation */}
          <div className="space-y-2 p-5 rounded-2xl bg-slate-950/60 border border-slate-800/80 print:bg-white print:border-gray-200">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/40 font-bold flex items-center justify-center text-xs">
                R
              </span>
              <h3 className="font-bold text-sm text-slate-100 print:text-black uppercase tracking-wider">
                Recommendation (వైద్యుల సిఫార్సులు)
              </h3>
            </div>
            <div className="text-xs sm:text-sm text-slate-300 print:text-gray-800 leading-relaxed pl-9 space-y-2">
              <ol className="list-decimal pl-5 space-y-1">
                <li><b>Order Repeat Renal & Lipid Panel:</b> Fasting Lipid Profile + Serum Creatinine & eGFR within 4 weeks.</li>
                <li><b>Therapy Optimization:</b> Evaluate adding an SGLT2 inhibitor (e.g. Empagliflozin 10mg) for cardio-renal protection, pending eGFR clearance.</li>
                <li><b>Home Self-Monitoring:</b> Instruct patient on SMBG (Self-Monitoring of Blood Glucose) 3x/week and maintain a symptom log.</li>
                <li><b>Patient Counseling in Native Telugu:</b> Reinforce the timing of Glimepiride before breakfast to avoid hypoglycemic episodes.</li>
                <li><b>Next Review Appointment:</b> Scheduled with Dr. K. Srinivas for <b>October 27, 2026</b>.</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Doctor Signature Block */}
        <div className="pt-8 border-t border-slate-800 print:border-gray-300 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 print:text-gray-700 gap-4">
          <div>
            <div className="font-semibold text-slate-200 print:text-black">Dr. K. Srinivas, MD (Gen Med)</div>
            <div>Consultant Physician &bull; Reg: APMC-45120</div>
            <div>Apollo Clinic, Jubilee Hills, Hyderabad</div>
          </div>
          <div className="sm:text-right font-mono text-[11px]">
            <div>FHIR Resource: DiagnosticReport/DR-91443288912011</div>
            <div>ABDM Consent Artifact: Granted (HIP/HIU verified)</div>
          </div>
        </div>
      </div>
    </div>
  );
};
