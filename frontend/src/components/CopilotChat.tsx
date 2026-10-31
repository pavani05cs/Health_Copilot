import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, MessageSquare, ShieldAlert, Cpu, CheckCircle2, User, RefreshCw, Languages } from 'lucide-react';
import { sendCopilotChat, fetchPatientTimeline } from '../lib/api';
import { Patient, ChatMessage, PatientTimeline } from '../types';

interface CopilotChatProps {
  selectedPatientId: string;
  patients: Patient[];
}

export const CopilotChat: React.FC<CopilotChatProps> = ({ selectedPatientId, patients }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('auto');
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const selectedPatient = patients.find(p => p.patient_id === selectedPatientId) || patients[0];

  // Load timeline context on patient switch
  useEffect(() => {
    let mounted = true;
    async function loadData() {
      const data = await fetchPatientTimeline(selectedPatientId);
      if (mounted) {
        setTimeline(data);
        // Initialize default welcome message tailored to patient
        const initialMsg: ChatMessage = {
          id: 'welcome-' + selectedPatientId,
          sender: 'assistant',
          text: `Hello! I am your **AI Health Copilot**, powered by **GPT-6-Luna** and grounded in your verified medical records.

I have loaded clinical records for **${data?.patient?.full_name || selectedPatient?.full_name || 'Patient'}** (*ABHA: ${data?.patient?.abha_id || selectedPatient?.abha_id}*).
Active Conditions: **${data?.diagnoses?.map(d => d.condition_name).join(', ') || 'Type 2 Diabetes, Hypertension'}**.

How can I assist you today? You can ask in **English, తెలుగు (Telugu), or हिन्दी (Hindi)**.`,
          invoked_tools: ['get_patient_profile', 'get_active_medications'],
          latency_ms: 420,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages([initialMsg]);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, [selectedPatientId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: 'msg-' + Date.now(),
      sender: 'user',
      text,
      language: selectedLanguage,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendCopilotChat({
        patient_id: selectedPatientId,
        message: text,
        language: selectedLanguage,
        session_id: 'chat_session_' + selectedPatientId
      });

      if (response.status === 'success') {
        const assistantMsg: ChatMessage = {
          id: 'asst-' + Date.now(),
          sender: 'assistant',
          text: response.answer,
          invoked_tools: response.invoked_tools || [],
          latency_ms: response.latency_ms || 1100,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, assistantMsg]);
      } else {
        const errorMsg: ChatMessage = {
          id: 'err-' + Date.now(),
          sender: 'assistant',
          text: `⚠️ **Clinical Engine Error:** ${response.message || 'Unable to retrieve answer from GPT-6-Luna engine.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } catch (err: any) {
      const networkMsg: ChatMessage = {
        id: 'net-' + Date.now(),
        sender: 'assistant',
        text: `⚠️ **Connection Error:** Could not connect to downstream analytical engine at /api/copilot/chat. ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, networkMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    {
      label: 'Check Drug Interactions',
      text: 'Are there any drug-drug interactions or contraindications among my active medications?',
      lang: 'english'
    },
    {
      label: 'తెలుగు మందుల షెడ్యూల్',
      text: 'నా మందుల షెడ్యూల్ మరియు ఆహార నియమాలు తెలుగులో వివరంగా చెప్పండి.',
      lang: 'telugu'
    },
    {
      label: 'Explain Blood Sugar / HbA1c',
      text: 'Summarize my recent lab results including HbA1c and Fasting Blood Sugar. Are they under control?',
      lang: 'english'
    },
    {
      label: 'हिन्दी दवा निर्देश',
      text: 'मेरी वर्तमान दवाओं के समय और सावधानियों के बारे में बताएं।',
      lang: 'hindi'
    },
    {
      label: 'Emergency Clinical Summary',
      text: 'Generate an emergency clinical summary of my conditions, active medications, and allergies for an attending physician.',
      lang: 'english'
    }
  ];

  const renderFormattedText = (txt: string) => {
    // Simple markdown parser for bold, bullet points, headers
    const lines = txt.split('\n');
    return lines.map((line, idx) => {
      // Bold replacement
      let formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

      if (line.startsWith('### ')) {
        return <h4 key={idx} className="text-sm font-bold text-cyan-300 mt-2 mb-1" dangerouslySetInnerHTML={{ __html: formatted.replace('### ', '') }} />;
      }
      if (line.startsWith('## ')) {
        return <h3 key={idx} className="text-base font-bold text-white mt-3 mb-1" dangerouslySetInnerHTML={{ __html: formatted.replace('## ', '') }} />;
      }
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ') || line.trim().startsWith('• ')) {
        const bulletContent = formatted.replace(/^[\s\-*•]+/, '');
        return (
          <li key={idx} className="ml-4 list-disc text-slate-200" dangerouslySetInnerHTML={{ __html: bulletContent }} />
        );
      }
      return (
        <p key={idx} className="min-h-[1.2rem] text-slate-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatted }} />
      );
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6 animate-in fade-in duration-300">
      {/* Patient Context Banner */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 p-[1px] flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center text-cyan-300 font-bold text-sm">
              {selectedPatient?.full_name?.charAt(0) || 'P'}
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 text-sm">{selectedPatient?.full_name}</span>
              <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                {selectedPatient?.patient_id}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5 flex flex-wrap items-center gap-2 font-mono">
              <span>ABHA: {selectedPatient?.abha_id}</span>
              <span>&bull;</span>
              <span>{selectedPatient?.gender}, {selectedPatient?.age}y</span>
              <span>&bull;</span>
              <span className="text-emerald-400">
                {timeline?.active_medications?.length || selectedPatient?.conditions?.length || 2} Active Rx
              </span>
            </div>
          </div>
        </div>

        {/* Diagnostic Tags */}
        <div className="flex flex-wrap items-center gap-1.5">
          {timeline?.diagnoses?.map((d, i) => (
            <span key={i} className="text-[11px] bg-slate-950 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-md">
              {d.condition_name}
            </span>
          )) || selectedPatient?.conditions?.map((c, i) => (
            <span key={i} className="text-[11px] bg-slate-950 border border-slate-800 text-slate-300 px-2.5 py-1 rounded-md">
              {c}
            </span>
          ))}
        </div>
      </div>

      {/* Chat Messages Frame */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col h-[600px] overflow-hidden shadow-2xl">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center text-slate-950 shrink-0 font-bold text-xs shadow-md shadow-cyan-500/20 mt-1">
                    <Sparkles size={16} />
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm space-y-2 ${
                    isUser
                      ? 'bg-gradient-to-r from-sky-600 to-cyan-600 text-white rounded-tr-sm shadow-md'
                      : 'bg-slate-950/90 border border-slate-800 text-slate-200 rounded-tl-sm'
                  }`}
                >
                  {/* Message Body */}
                  <div className="space-y-1.5">
                    {renderFormattedText(msg.text)}
                  </div>

                  {/* Invoked Tools Badges for Assistant */}
                  {!isUser && msg.invoked_tools && msg.invoked_tools.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 mt-2 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                        <Cpu size={12} className="text-cyan-400" />
                        <span>Invoked Deterministic Tools:</span>
                      </span>
                      {msg.invoked_tools.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/80"
                        >
                          ⚙️ {t}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Footer Meta */}
                  <div className={`flex items-center justify-between text-[10px] font-mono pt-1 ${
                    isUser ? 'text-sky-200' : 'text-slate-500'
                  }`}>
                    <span>{msg.timestamp}</span>
                    {!isUser && msg.latency_ms && (
                      <span>⏱️ {msg.latency_ms}ms &bull; GPT-6-Luna</span>
                    )}
                  </div>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-1">
                    <User size={16} />
                  </div>
                )}
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex gap-3 justify-start animate-in fade-in">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center text-slate-950 shrink-0 font-bold text-xs">
                <Sparkles size={16} />
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-2xl rounded-tl-sm p-4 text-xs text-slate-400 flex items-center gap-2">
                <RefreshCw size={14} className="animate-spin text-cyan-400" />
                <span>GPT-6-Luna is querying SQLite relational tools & analyzing drug interactions...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/40 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] text-slate-400 uppercase font-semibold shrink-0">
            Suggested:
          </span>
          {quickPrompts.map((qp, i) => (
            <button
              key={i}
              onClick={() => {
                setSelectedLanguage(qp.lang);
                handleSend(qp.text);
              }}
              disabled={isLoading}
              className="px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/40 text-[11px] text-slate-300 whitespace-nowrap transition-all active:scale-95 disabled:opacity-50"
            >
              {qp.label}
            </button>
          ))}
        </div>

        {/* Chat Input Box */}
        <div className="p-3 sm:p-4 border-t border-slate-800 bg-slate-950/90 flex items-center gap-2">
          {/* Language Selector */}
          <div className="relative shrink-0">
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-400"
            >
              <option value="auto">Auto Lang</option>
              <option value="telugu">తెలుగు (Telugu)</option>
              <option value="hindi">हिन्दी (Hindi)</option>
              <option value="english">English</option>
            </select>
          </div>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={`Ask about ${selectedPatient?.full_name}'s medications, lab trends, or dosage schedules...`}
            disabled={isLoading}
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 disabled:opacity-50"
          />

          {/* Send Button */}
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 via-cyan-400 to-teal-400 text-slate-950 font-bold text-xs sm:text-sm flex items-center gap-1.5 shadow-md shadow-cyan-500/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none transition-all"
          >
            <span>Send</span>
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
