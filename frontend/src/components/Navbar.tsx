import React from 'react';
import { Activity, FileText, MessageSquare, TrendingUp, ClipboardList, ShieldCheck, ChevronDown, Sparkles } from 'lucide-react';
import { Patient } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  patients: Patient[];
  selectedPatientId: string;
  setSelectedPatientId: (id: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  patients,
  selectedPatientId,
  setSelectedPatientId,
}) => {
  const [patientMenuOpen, setPatientMenuOpen] = React.useState(false);
  const selectedPatient = patients.find(p => p.patient_id === selectedPatientId) || patients[0];

  const navItems = [
    { id: 'landing', label: 'Home', icon: Sparkles },
    { id: 'ingestion', label: 'Ingestion Studio', icon: FileText, badge: 'Indic OCR' },
    { id: 'chat', label: 'Copilot Chat', icon: MessageSquare, badge: 'GPT-6' },
    { id: 'trends', label: 'Biomarkers', icon: TrendingUp },
    { id: 'handover', label: 'SBAR Handover', icon: ClipboardList, badge: 'Doctor' },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-[#080d1a]/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <div 
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => setActiveTab('landing')}
        >
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 via-cyan-500 to-teal-400 p-[1.5px] shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#080d1a] rounded-[10px] flex items-center justify-center">
              <Activity className="text-cyan-400 animate-pulse" size={20} />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base sm:text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                HealthCopilot<span className="text-cyan-400">.ai</span>
              </span>
              <span className="hidden sm:inline-flex text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded border border-cyan-500/30 bg-cyan-950/60 text-cyan-300 font-semibold">
                FHIR R4
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">
              ABDM Multilingual Clinical Copilot
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden lg:flex items-center gap-1 bg-slate-900/60 border border-slate-800/80 p-1 rounded-xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon size={14} className={isActive ? 'text-cyan-400' : 'text-slate-400'} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                    isActive 
                      ? 'bg-cyan-500/30 text-cyan-200' 
                      : 'bg-slate-800 text-slate-400'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Section: Patient Switcher & Server Status */}
        <div className="flex items-center gap-3">
          {/* Active Patient Pill Dropdown */}
          <div className="relative">
            <button
              onClick={() => setPatientMenuOpen(!patientMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700/80 hover:border-cyan-500/40 transition-colors text-left"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <div className="text-xs">
                <span className="text-[10px] text-slate-400 block leading-tight">Patient Context</span>
                <span className="font-semibold text-slate-100 block truncate max-w-[120px] sm:max-w-[150px]">
                  {selectedPatient ? selectedPatient.full_name : 'Select Patient'}
                </span>
              </div>
              <ChevronDown size={14} className="text-slate-400 ml-1" />
            </button>

            {patientMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900/95 border border-slate-700/80 shadow-2xl backdrop-blur-xl py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3 py-1.5 border-b border-slate-800 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  Select Active Clinical Record
                </div>
                {patients.map((p) => {
                  const isSelected = p.patient_id === selectedPatientId;
                  return (
                    <div
                      key={p.patient_id}
                      onClick={() => {
                        setSelectedPatientId(p.patient_id);
                        setPatientMenuOpen(false);
                      }}
                      className={`px-3 py-2 cursor-pointer flex items-center justify-between text-xs transition-colors ${
                        isSelected
                          ? 'bg-cyan-500/15 text-cyan-300 font-semibold border-l-2 border-cyan-400'
                          : 'text-slate-200 hover:bg-slate-800/60'
                      }`}
                    >
                      <div>
                        <div className="font-medium text-slate-100">{p.full_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {p.patient_id} &bull; {p.gender}, {p.age}y
                        </div>
                      </div>
                      {isSelected && (
                        <span className="text-[10px] bg-cyan-950 text-cyan-300 px-1.5 py-0.5 rounded font-mono border border-cyan-800">
                          Active
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* EC2 Online Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-[11px] font-mono text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>EC2 Live</span>
          </div>
        </div>
      </div>

      {/* Mobile Tab Bar */}
      <div className="lg:hidden flex items-center justify-around border-t border-slate-800/60 bg-slate-950/80 px-2 py-2 overflow-x-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded text-[11px] whitespace-nowrap ${
                isActive ? 'text-cyan-400 font-medium' : 'text-slate-400'
              }`}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
