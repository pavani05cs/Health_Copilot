import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import LandingPage from './components/ui/saa-s-template';
import { IngestionStudio } from './components/IngestionStudio';
import { CopilotChat } from './components/CopilotChat';
import { BiomarkerTrends } from './components/BiomarkerTrends';
import { SbarHandover } from './components/SbarHandover';
import { fetchPatients } from './lib/api';
import { Patient } from './types';
import { ShieldCheck, Activity, Sparkles, ArrowRight, FileText, MessageSquare, TrendingUp, ClipboardList } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('PAT-VINEETHA-21F');

  useEffect(() => {
    let mounted = true;
    async function loadPatientsList() {
      const list = await fetchPatients();
      if (mounted && list.length > 0) {
        setPatients(list);
        const vineetha = list.find(p => p.patient_id.includes('VINEETHA') || p.full_name.toLowerCase().includes('vineetha'));
        if (vineetha) {
          setSelectedPatientId(vineetha.patient_id);
        } else if (!list.some(p => p.patient_id === selectedPatientId)) {
          setSelectedPatientId(list[0].patient_id);
        }
      }
    }
    loadPatientsList();

    // Support hash-based direct links e.g. #chat, #ingestion, #trends, #handover
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['landing', 'ingestion', 'chat', 'trends', 'handover'].includes(hash)) {
        setActiveTab(hash);
      }
    };
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    return () => {
      mounted = false;
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    window.location.hash = tab;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#080d1a] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Universal Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        patients={patients}
        selectedPatientId={selectedPatientId}
        setSelectedPatientId={setSelectedPatientId}
      />

      {/* Main View Container */}
      <main className="flex-1">
        {activeTab === 'landing' && (
          <div>
            {/* Quick Action Navigation Bar on Landing Page */}
            <div className="bg-gradient-to-r from-sky-950/60 via-slate-900/90 to-teal-950/60 border-b border-slate-800/80 py-3 px-4">
              <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 text-cyan-300">
                  <Sparkles size={14} />
                  <span className="font-semibold">Explore System Modules:</span>
                </div>
                <div className="flex items-center gap-2 overflow-x-auto">
                  <button
                    onClick={() => handleTabChange('ingestion')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-950 hover:bg-sky-900 border border-sky-700/60 text-sky-200 font-medium transition-all"
                  >
                    <FileText size={13} />
                    <span>Ingestion Studio</span>
                  </button>
                  <button
                    onClick={() => handleTabChange('chat')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-700/60 text-cyan-200 font-medium transition-all"
                  >
                    <MessageSquare size={13} />
                    <span>Copilot Chat (GPT-6)</span>
                  </button>
                  <button
                    onClick={() => handleTabChange('trends')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 font-medium transition-all"
                  >
                    <TrendingUp size={13} />
                    <span>Biomarker Trends</span>
                  </button>
                  <button
                    onClick={() => handleTabChange('handover')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-950 hover:bg-teal-900 border border-teal-700/60 text-teal-200 font-medium transition-all"
                  >
                    <ClipboardList size={13} />
                    <span>SBAR Handover</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Landing Page Content */}
            <LandingPage />
          </div>
        )}

        {activeTab === 'ingestion' && (
          <IngestionStudio
            onRecordIngested={(newPatientId) => {
              setSelectedPatientId(newPatientId);
              // Refresh patient list
              fetchPatients().then(setPatients);
            }}
          />
        )}

        {activeTab === 'chat' && (
          <CopilotChat
            selectedPatientId={selectedPatientId}
            patients={patients}
          />
        )}

        {activeTab === 'trends' && (
          <BiomarkerTrends
            selectedPatientId={selectedPatientId}
            patients={patients}
          />
        )}

        {activeTab === 'handover' && (
          <SbarHandover
            selectedPatientId={selectedPatientId}
            patients={patients}
          />
        )}
      </main>

      {/* Global Clinical Compliance Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/90 py-8 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
              <Activity size={14} />
            </div>
            <span>
              HealthCopilot.ai &bull; ABDM M3 & FHIR R4 Interoperability Protocol
            </span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-mono">
            <span className="text-emerald-400">● EC2 Live: 3.27.249.44</span>
            <span className="text-slate-500">|</span>
            <span className="text-cyan-400">GPT-6-Luna Ingestion & Reasoning</span>
            <span className="text-slate-500">|</span>
            <span className="text-teal-400">PP-OCRv6 Indic</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
