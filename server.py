"""
FastAPI Production Server for AI-Powered Personal Health Copilot
Integrates:
  1. Lightweight PP-OCRv6 & Indic PP-OCRv5 OCR Engines (English, Telugu, Hindi)
  2. GPT-6-Luna Autonomous Ingestion Agent (General DB Toolset)
  3. GPT-6-Luna Downstream Patient Copilot Analytical Engine (Clinical Tools & Triage)
  4. Relational Clinical Database (SQLite / MySQL-compatible health_copilot.db)
  5. S3 3-Tier Storage Pipeline (Raw Vault, Processed Artifacts, FHIR Records)
  6. Longitudinal Patient Timeline & Lab Trends Query APIs
  7. Interactive Web Dashboard UI with Multilingual AI Chat
"""

import os
import sys

# oneDNN CPU execution compatibility flags
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import time
import json
import shutil
import re
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize Database Schema
import health_db
health_db.init_db()

# Import S3 Manager & Luna Ingestion Agent
import s3_storage_manager as s3_mgr
from luna_ingestion_agent import LunaIngestionAgent
from copilot_analytical_engine import PatientCopilotAgent

app = FastAPI(
    title="AI-Powered Personal Health Copilot API",
    description="End-to-End ABDM, FHIR R4, and GPT-6-Luna Clinical Pipeline",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Copilot Analytical Engine
copilot_agent = PatientCopilotAgent(model="gpt-6-luna")


# ---------------------------------------------------------------------------
# OCR Engine Management (PP-OCRv6 + Indic Lightweight PP-OCRv5)
# ---------------------------------------------------------------------------

engines: Dict[str, Any] = {}

def get_engine(language: str = "auto", tier: str = "small"):
    """
    Returns cached PaddleOCR engine configured for the target language.
    Avoids OOM by pairing PP-OCRv6_small_det with language-specific recognizers.
    """
    lang_norm = (language or "auto").lower().strip()
    tier_norm = (tier or "small").lower().strip()
    cache_key = f"{lang_norm}_{tier_norm}"

    if cache_key not in engines:
        from paddleocr import PaddleOCR
        if lang_norm in ["te", "telugu"]:
            print(f"[OCR INIT] Initializing Telugu Engine: PP-OCRv6_small_det + te_PP-OCRv5_mobile_rec...")
            engines[cache_key] = PaddleOCR(
                text_detection_model_name="PP-OCRv6_small_det",
                text_recognition_model_name="te_PP-OCRv5_mobile_rec",
                use_textline_orientation=True
            )
        elif lang_norm in ["hi", "hindi", "devanagari"]:
            print(f"[OCR INIT] Initializing Hindi Engine: PP-OCRv6_small_det + devanagari_PP-OCRv5_mobile_rec...")
            engines[cache_key] = PaddleOCR(
                text_detection_model_name="PP-OCRv6_small_det",
                text_recognition_model_name="devanagari_PP-OCRv5_mobile_rec",
                use_textline_orientation=True
            )
        else:
            # Universal / English / Latin (PP-OCRv6)
            det_name = f"PP-OCRv6_{tier_norm}_det"
            rec_name = f"PP-OCRv6_{tier_norm}_rec"
            print(f"[OCR INIT] Initializing Universal PP-OCRv6 Engine: ({det_name}, {rec_name})...")
            engines[cache_key] = PaddleOCR(
                text_detection_model_name=det_name,
                text_recognition_model_name=rec_name,
                use_textline_orientation=True
            )
    return engines[cache_key]


@app.on_event("startup")
def startup_event():
    print("[SERVER STARTUP] Health Copilot Relational Database and GPT-6-Luna Services Initialized.")


# ---------------------------------------------------------------------------
# Interactive Web Dashboard UI
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Powered Personal Health Copilot</title>
    <style>
        :root {
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --bg: #f8fafc;
            --card: #ffffff;
            --border: #e2e8f0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            margin: 0;
            padding: 24px 16px;
            color: #0f172a;
        }
        .container {
            max-width: 980px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 14px;
            box-shadow: 0 4px 12px -2px rgb(0 0 0 / 0.08);
            padding: 32px;
        }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
        h1 { margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px; }
        .badge { background: #e0f2fe; color: #0369a1; font-size: 13px; font-weight: 600; padding: 4px 10px; border-radius: 9999px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
        .form-group { margin-bottom: 14px; }
        label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 13px; color: #334155; }
        select, input[type="text"], input[type="file"], textarea, button {
            width: 100%; box-sizing: border-box; padding: 10px 12px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 14px;
        }
        button { background: var(--primary); color: white; border: none; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 6px; padding: 12px; font-size: 15px; }
        button:hover { background: var(--primary-dark); }
        .nav-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        .tab-btn { background: #f1f5f9; color: #475569; border: 1px solid var(--border); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; }
        .tab-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }
        #results { margin-top: 24px; border-top: 1px solid var(--border); padding-top: 20px; display: none; }
        .stat-card { display: inline-block; background: #f1f5f9; padding: 8px 14px; border-radius: 8px; font-size: 13px; margin-right: 8px; margin-bottom: 12px; font-weight: 500; }
        .summary-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 18px; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #166534; }
        .s3-box { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 18px; font-size: 13px; color: #334155; word-break: break-all; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 24px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
        th { background: #f8fafc; font-weight: 600; color: #475569; }
        .badge-danger { background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .badge-warning { background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .badge-success { background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .indic-text { font-family: 'Gautami', 'Mandali', 'Nirmala UI', sans-serif; color: #0369a1; font-size: 14px; font-weight: 500; }
        .card-title { font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 8px; color: #1e293b; display: flex; align-items: center; gap: 8px; }

        /* Copilot Chat Styling */
        .chat-container { display: flex; flex-direction: column; height: 520px; border: 1px solid var(--border); border-radius: 10px; background: #fafafa; overflow: hidden; }
        .chat-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .msg { max-width: 82%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
        .msg-user { align-self: flex-end; background: #0284c7; color: white; border-bottom-right-radius: 2px; }
        .msg-copilot { align-self: flex-start; background: white; color: #0f172a; border: 1px solid #e2e8f0; border-bottom-left-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .msg-copilot h2, .msg-copilot h3, .msg-copilot h4 { margin: 8px 0 4px 0; font-size: 15px; color: #0369a1; }
        .msg-copilot ul, .msg-copilot ol { margin: 4px 0; padding-left: 20px; }
        .msg-copilot table { margin: 8px 0; }
        .chip-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
        .chip { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 6px 12px; border-radius: 9999px; font-size: 12px; cursor: pointer; font-weight: 600; transition: background 0.15s; }
        .chip:hover { background: #dcfce7; }
        .chip-danger { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
        .chip-danger:hover { background: #fee2e2; }
        .chat-input-row { display: flex; gap: 8px; padding: 12px; background: white; border-top: 1px solid var(--border); }
        .chat-input-row input { flex: 1; margin: 0; }
        .chat-input-row button { width: 100px; margin: 0; padding: 10px; }
        .tool-pill { display: inline-block; font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; margin-right: 4px; margin-top: 6px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>AI-Powered Personal Health Copilot <span class="badge">GPT-6-Luna & Relational DB</span></h1>
                <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">
                    ABDM & FHIR R4 Compliant &bull; Multilingual Indic OCR (Telugu, Hindi, English) &bull; Downstream Analytical Copilot
                </p>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="tab-btn active" onclick="switchTab('tab-upload')">Upload & Ingest Record</button>
            <button class="tab-btn" onclick="switchTab('tab-copilot');">AI Copilot Chat (GPT-6-Luna) 🤖</button>
            <button class="tab-btn" onclick="switchTab('tab-timeline'); loadTimeline();">Patient Timeline</button>
            <button class="tab-btn" onclick="switchTab('tab-stats'); loadStats();">Database Stats</button>
        </div>

        <!-- TAB 1: UPLOAD & INGEST -->
        <div id="tab-upload" class="tab-pane active">
            <form id="healthForm">
                <div class="grid-3">
                    <div class="form-group">
                        <label>ABHA ID / Patient ID:</label>
                        <input type="text" name="abha_id" id="abha_id" value="91-4432-8891-2011" required>
                    </div>
                    <div class="form-group">
                        <label>Record Type:</label>
                        <select name="record_type" id="record_type">
                            <option value="prescription" selected>Prescription</option>
                            <option value="lab_report">Diagnostic / Lab Report</option>
                            <option value="discharge_summary">Discharge Summary</option>
                            <option value="other">General Medical Record</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Language Engine:</label>
                        <select name="language" id="language">
                            <option value="te" selected>Telugu (తెలుగు PP-OCRv5)</option>
                            <option value="hi">Hindi (हिन्दी PP-OCRv5)</option>
                            <option value="auto">Universal / English (PP-OCRv6)</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Medical Record File (PDF, PNG, JPG):</label>
                    <input type="file" name="file" id="file" required>
                </div>
                
                <button type="submit" id="btnSubmit">Run OCR & Ingest via GPT-6-Luna</button>
            </form>

            <div id="results">
                <div id="statsBar"></div>
                
                <div class="card-title">&#129302; Autonomous Clinical Ingestion Summary (GPT-6-Luna)</div>
                <div id="summaryCard" class="summary-box"></div>

                <div style="margin-bottom: 20px;">
                    <button style="background: #10b981; width: auto; padding: 8px 18px; font-size: 14px;" onclick="goToChatWithPatient()">
                        💬 Ask AI Copilot About This Record &rarr;
                    </button>
                </div>

                <div class="card-title">&#128138; Prescribed Medications (Preserved Indic & Normalized English)</div>
                <table id="tblMedications">
                    <thead>
                        <tr>
                            <th>Drug Name</th>
                            <th>Form / Strength</th>
                            <th>Code / Frequency</th>
                            <th>Original Regional Directions</th>
                            <th>Normalized English Translation</th>
                        </tr>
                    </thead>
                    <tbody id="medBody"></tbody>
                </table>

                <div class="card-title">&#128300; Lab Observations & Diagnostics</div>
                <table id="tblLabs">
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>Value</th>
                            <th>Unit</th>
                            <th>Reference Range</th>
                            <th>Interpretation</th>
                        </tr>
                    </thead>
                    <tbody id="labBody"></tbody>
                </table>

                <div class="card-title">&#128274; ABDM 3-Tier S3 Storage Vaults</div>
                <div id="s3VaultBar" class="s3-box"></div>
            </div>
        </div>

        <!-- TAB 2: COPILOT CHAT (GPT-6-LUNA) -->
        <div id="tab-copilot" class="tab-pane">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; gap: 10px; align-items: center;">
                    <label style="margin: 0;">Patient Context:</label>
                    <input type="text" id="chatPatientId" value="PAT-91443288912011" style="width: 220px; padding: 6px 10px;">
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <label style="margin: 0;">Language:</label>
                    <select id="chatLang" style="width: 140px; padding: 6px 10px;">
                        <option value="auto">Auto / English</option>
                        <option value="te" selected>Telugu (తెలుగు)</option>
                        <option value="hi">Hindi (हिन्दी)</option>
                    </select>
                </div>
            </div>

            <!-- Quick Action Chips -->
            <div class="chip-container">
                <span class="chip" onclick="sendQuickPrompt('నా మందులు ఎప్పుడు, ఎలా వేసుకోవాలి? వివరంగా తెలుగులో చెప్పండి.', 'te')">💊 మందుల వివరాలు (Telugu)</span>
                <span class="chip" onclick="sendQuickPrompt('What do my Fasting Blood Sugar and HbA1c results mean? Are they normal or high?', 'en')">🧪 Lab Interpretation (FBS & HbA1c)</span>
                <span class="chip" onclick="sendQuickPrompt('Can I take Metformin, Glimepiride, and Telmisartan together? Check drug interactions.', 'en')">⚠️ Drug Interaction Check</span>
                <span class="chip" onclick="sendQuickPrompt('What diet and lifestyle exercise instructions did Dr. Srinivas prescribe?', 'en')">🥗 Diet & Exercise Advice</span>
                <span class="chip chip-danger" onclick="sendQuickPrompt('I took my morning tablets an hour ago and I feel very shaky, cold sweating and dizzy. What should I do right now?', 'en')">🚨 Emergency Hypoglycemia Triage</span>
                <span class="chip" onclick="sendQuickPrompt('Please generate a concise SBAR clinical handover summary for my upcoming doctor consultation.', 'en')">📋 Doctor Handover (SBAR)</span>
            </div>

            <!-- Chat Container -->
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="msg msg-copilot">
                        <b>👋 Hello! I am your AI Health Copilot (powered by GPT-6-Luna).</b><br/>
                        I have real-time access to your relational health records from Apollo Clinic & Healthcare.<br/>
                        You can ask me questions about your prescribed medicines, lab results, drug safety interactions, or doctor's instructions in <b>English, Telugu (తెలుగు), or Hindi (हिन्दी)</b>.
                    </div>
                </div>
                <form class="chat-input-row" id="chatForm">
                    <input type="text" id="chatInput" placeholder="Ask a health question (e.g. నా మందుల షెడ్యూల్ ఏమిటి? / What does HbA1c 7.8% mean?)..." required autocomplete="off">
                    <button type="submit" id="btnChatSend">Send</button>
                </form>
            </div>
        </div>

        <!-- TAB 3: TIMELINE -->
        <div id="tab-timeline" class="tab-pane">
            <div style="display: flex; gap: 10px; margin-bottom: 16px;">
                <input type="text" id="timelinePatientId" value="PAT-91443288912011" placeholder="Patient ID (e.g. PAT-91443288912011)">
                <button style="width: 180px; margin: 0;" onclick="loadTimeline()">Fetch Timeline</button>
            </div>
            <div id="timelineContainer">Select or enter a Patient ID to view their full longitudinal health records.</div>
        </div>

        <!-- TAB 4: STATS -->
        <div id="tab-stats" class="tab-pane">
            <div id="statsContainer">Loading relational database statistics...</div>
        </div>
    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // Highlight button
            const btns = Array.from(document.querySelectorAll('.tab-btn'));
            const matchBtn = btns.find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId));
            if (matchBtn) matchBtn.classList.add('active');
        }

        function goToChatWithPatient() {
            switchTab('tab-copilot');
            const abha = document.getElementById('abha_id').value;
            if (abha) {
                document.getElementById('chatPatientId').value = abha;
            }
        }

        // Upload Form Handler
        const form = document.getElementById('healthForm');
        const btn = document.getElementById('btnSubmit');
        const resultsDiv = document.getElementById('results');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            btn.disabled = true;
            btn.innerText = 'Extracting OCR & Running GPT-6-Luna Ingestion Agent...';
            resultsDiv.style.display = 'none';

            const formData = new FormData(form);
            try {
                const res = await fetch('/api/process-record', { method: 'POST', body: formData });
                const data = await res.json();
                
                if (data.status !== 'success') {
                    throw new Error(data.message || 'Ingestion failed');
                }

                // Stats Bar
                document.getElementById('statsBar').innerHTML = `
                    <div class="stat-card">Patient: <b>${data.patient_id}</b></div>
                    <div class="stat-card">Encounter: <b>${data.encounter_id}</b></div>
                    <div class="stat-card">Model: <b>${data.ingestion.model}</b></div>
                    <div class="stat-card">OCR Latency: <b>${data.ocr_latency_ms.toFixed(1)} ms</b></div>
                    <div class="stat-card">Lines Extracted: <b>${data.extracted_lines_count}</b></div>
                `;

                // Summary Card
                document.getElementById('summaryCard').innerHTML = (data.ingestion.summary || '').replace(/\\n/g, '<br/>');

                // Medications Table
                const medBody = document.getElementById('medBody');
                medBody.innerHTML = '';
                const meds = data.records.medications || [];
                if (meds.length === 0) {
                    medBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#64748b;">No medication records detected.</td></tr>';
                } else {
                    meds.forEach(m => {
                        medBody.innerHTML += `<tr>
                            <td><b>${escapeHtml(m.drug_name || '')}</b></td>
                            <td>${escapeHtml(m.dosage_form || '')} ${escapeHtml(m.strength || '')}</td>
                            <td><code>${escapeHtml(m.frequency_code || m.frequency_text || '-')}</code></td>
                            <td class="indic-text">${escapeHtml(m.instructions_original || '-')}</td>
                            <td>${escapeHtml(m.instructions_english || '-')}</td>
                        </tr>`;
                    });
                }

                // Labs Table
                const labBody = document.getElementById('labBody');
                labBody.innerHTML = '';
                const labs = data.records.lab_observations || [];
                if (labs.length === 0) {
                    labBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#64748b;">No lab observation records detected.</td></tr>';
                } else {
                    labs.forEach(l => {
                        let badgeClass = 'badge-success';
                        if (l.interpretation === 'HIGH') badgeClass = 'badge-danger';
                        if (l.interpretation === 'LOW') badgeClass = 'badge-warning';
                        labBody.innerHTML += `<tr>
                            <td><b>${escapeHtml(l.test_name || '')}</b></td>
                            <td><b>${l.value_numeric !== null ? l.value_numeric : escapeHtml(l.value_string || '')}</b></td>
                            <td>${escapeHtml(l.unit || '')}</td>
                            <td>${escapeHtml(l.ref_range_string || '-')}</td>
                            <td><span class="${badgeClass}">${escapeHtml(l.interpretation || 'NORMAL')}</span></td>
                        </tr>`;
                    });
                }

                // S3 Vaults Bar
                document.getElementById('s3VaultBar').innerHTML = `
                    &bull; <b>Raw Vault:</b> <code>${data.s3_storage.raw_bucket}/${data.s3_storage.raw_key}</code><br/>
                    &bull; <b>Processed Artifacts:</b> <code>${data.s3_storage.artifacts_bucket}/${data.s3_storage.ocr_tokens_key}</code><br/>
                    &bull; <b>FHIR R4 Bundle:</b> <code>${data.s3_storage.fhir_bucket}/${data.s3_storage.fhir_key}</code>
                `;

                resultsDiv.style.display = 'block';
            } catch (err) {
                alert('Processing Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = 'Run OCR & Ingest via GPT-6-Luna';
            }
        });

        // Chat Form Handler
        const chatForm = document.getElementById('chatForm');
        const chatInput = document.getElementById('chatInput');
        const chatMessages = document.getElementById('chatMessages');
        const btnChatSend = document.getElementById('btnChatSend');

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text) return;
            sendChatMessage(text);
        });

        function sendQuickPrompt(prompt, lang) {
            document.getElementById('chatLang').value = lang;
            sendChatMessage(prompt);
        }

        async function sendChatMessage(text) {
            const pid = document.getElementById('chatPatientId').value.trim();
            const lang = document.getElementById('chatLang').value;
            chatInput.value = '';

            // Append User message
            chatMessages.innerHTML += `<div class="msg msg-user"><b>You:</b><br/>${escapeHtml(text)}</div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Append Loading message
            const loadingId = 'loading_' + Date.now();
            chatMessages.innerHTML += `<div class="msg msg-copilot" id="${loadingId}"><i>🤖 Consulting GPT-6-Luna & querying clinical database...</i></div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;

            btnChatSend.disabled = true;

            try {
                const res = await fetch('/api/copilot/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pid,
                        message: text,
                        language: lang,
                        session_id: 'web_sess_' + pid
                    })
                });

                const data = await res.json();
                const loadEl = document.getElementById(loadingId);
                if (loadEl) loadEl.remove();

                if (data.status === 'success') {
                    let toolPills = '';
                    (data.invoked_tools || []).forEach(t => {
                        toolPills += `<span class="tool-pill">⚙️ ${t}</span>`;
                    });

                    const formattedAnswer = renderMarkdown(data.answer);
                    chatMessages.innerHTML += `
                        <div class="msg msg-copilot">
                            <b>AI Health Copilot (GPT-6-Luna):</b><br/>
                            ${formattedAnswer}
                            <div style="margin-top: 8px;">${toolPills}</div>
                            <div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">⏱️ Latency: ${data.latency_ms}ms &bull; Model: ${data.model}</div>
                        </div>
                    `;
                } else {
                    chatMessages.innerHTML += `<div class="msg msg-copilot" style="color: #dc2626;"><b>Error:</b> ${escapeHtml(data.message || 'Error processing request')}</div>`;
                }
            } catch (err) {
                const loadEl = document.getElementById(loadingId);
                if (loadEl) loadEl.remove();
                chatMessages.innerHTML += `<div class="msg msg-copilot" style="color: #dc2626;"><b>Network Error:</b> ${escapeHtml(err.message)}</div>`;
            } finally {
                btnChatSend.disabled = false;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        function renderMarkdown(md) {
            if (!md) return '';
            let html = escapeHtml(md);
            // bold
            html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
            // italic
            html = html.replace(/\\*(.*?)\\*/g, '<i>$1</i>');
            // newlines
            html = html.replace(/\\n/g, '<br/>');
            return html;
        }

        async function loadTimeline() {
            const pid = document.getElementById('timelinePatientId').value.trim();
            const container = document.getElementById('timelineContainer');
            if (!pid) return;
            container.innerHTML = 'Loading timeline for ' + pid + '...';
            try {
                const res = await fetch('/api/patient/' + encodeURIComponent(pid) + '/timeline');
                const data = await res.json();
                if (!data.patient) {
                    container.innerHTML = '<p style="color:#dc2626;">Patient not found in relational database.</p>';
                    return;
                }
                let html = `<h3>Patient: ${data.patient.full_name} (${data.patient.patient_id})</h3>`;
                html += `<p>ABHA: <b>${data.patient.abha_id}</b> | Age: ${data.patient.age || 'N/A'} | Gender: ${data.patient.gender || 'N/A'}</p>`;
                
                html += `<h4>Encounters (${data.encounters.length})</h4><ul>`;
                data.encounters.forEach(e => {
                    html += `<li><b>${e.encounter_date}</b> - ${e.encounter_id} (${e.hospital_name || 'Hospital'}) - Dr. ${e.doctor_name || 'Doctor'}</li>`;
                });
                html += `</ul>`;

                html += `<h4>Active Medications (${data.active_medications.length})</h4><ul>`;
                data.active_medications.forEach(m => {
                    html += `<li><b>${m.drug_name}</b> ${m.strength || ''} - <i>${m.instructions_english || m.instructions_original}</i></li>`;
                });
                html += `</ul>`;

                html += `<h4>Historical Lab Observations (${data.lab_observations.length})</h4><ul>`;
                data.lab_observations.forEach(l => {
                    html += `<li><b>${l.test_name}</b>: ${l.value_numeric} ${l.unit || ''} [${l.interpretation}] (${l.observation_date})</li>`;
                });
                html += `</ul>`;

                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = 'Error: ' + err.message;
            }
        }

        async function loadStats() {
            const container = document.getElementById('statsContainer');
            try {
                const res = await fetch('/api/db/stats');
                const data = await res.json();
                let html = '<h3>Relational Database Tables & Record Counts</h3><table><thead><tr><th>Table Name</th><th>Record Count</th></tr></thead><tbody>';
                for (const [tbl, count] of Object.entries(data.tables)) {
                    html += `<tr><td><b>${tbl}</b></td><td><span class="badge">${count}</span></td></tr>`;
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (err) {
                container.innerHTML = 'Error loading stats: ' + err.message;
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# POST /api/process-record: End-to-End Pipeline
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Patient Identity Extractor & Dynamic Demographic Normalizer
# ---------------------------------------------------------------------------

def extract_patient_identity(lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    full_name = None
    age = None
    gender = None

    text_lines = [str(l.get("text", "")).strip() for l in lines if l.get("text")]

    for i, t in enumerate(text_lines):
        # Pattern 1: Standalone "Name" or "Patient Name" label followed by next line
        if re.search(r'^(patient\s*name|pt\.?\s*name|name|రోగి|పేరు|मरीज़|नाम)\s*[:\-]?\s*$', t, re.IGNORECASE):
            if i + 1 < len(text_lines):
                candidate = text_lines[i+1].strip()
                # Check format e.g. "Vineetha(21Y/F)" or "Vineetha (21 Y / Female)"
                m = re.match(r'([A-Za-z\s\u0C00-\u0C7F\u0900-\u097F]+?)(?:\s*\((\d+)\s*[Yy]?\s*/?\s*([MFmf])\))?$', candidate)
                if m:
                    cand_name = m.group(1).strip()
                    cand_name = re.sub(r'^(mr|ms|mrs|miss|dr|sri|smt)\.?\s+', '', cand_name, flags=re.IGNORECASE).strip()
                    if len(cand_name) >= 2 and not cand_name.lower().startswith("date") and not cand_name.lower().startswith("test"):
                        full_name = cand_name
                        if m.group(2): age = int(m.group(2))
                        if m.group(3): gender = 'Female' if m.group(3).upper() == 'F' else 'Male'
                        break

        # Pattern 2: Inline pattern e.g. "Name: Vineetha(21Y/F)" or "రోగి: రమేష్ రావు, వయస్సు: 52"
        m_inline = re.search(r'(?:patient\s*name|pt\.?\s*name|name|రోగి|పేరు|मरीज़|नाम)\s*[:\-]\s*([^\d,\n\(\)]+)', t, re.IGNORECASE)
        if m_inline:
            clean_n = m_inline.group(1).strip()
            clean_n = re.sub(r'^(mr|ms|mrs|miss|dr|sri|smt)\.?\s+', '', clean_n, flags=re.IGNORECASE).strip()
            if len(clean_n) >= 2 and not clean_n.lower().startswith("date") and not clean_n.lower().startswith("test"):
                full_name = clean_n
                combined_context = ' '.join(text_lines[i:min(i+3, len(text_lines))])
                m_age = re.search(r'(?:age|వయస్సు|आयु|\()\s*[:\-]?\s*(\d{1,3})', combined_context, re.IGNORECASE)
                if m_age: age = int(m_age.group(1))
                m_gen = re.search(r'(?:gender|sex|లింగం|लिंग|/)\s*[:\-]?\s*(female|male|f|m|స్త్రీ|పురుషుడు|महिला|पुरुष)', combined_context, re.IGNORECASE)
                if m_gen:
                    g = m_gen.group(1).lower()
                    gender = 'Female' if g in ['female', 'f', 'స్త్రీ', 'महिला'] else 'Male'
                break

    return {"full_name": full_name, "age": age, "gender": gender}


def _execute_ingestion_pipeline(
    temp_file_path: str,
    file_name: str,
    user_abha_id: Optional[str],
    record_type: str,
    language: str,
    tier: str
) -> Dict[str, Any]:
    """Synchronous CPU worker executed in background thread pool."""
    record_id = f"rec_{int(time.time()*1000)}"
    encounter_id = f"ENC-{record_id}"
    temp_dir = Path(temp_file_path).parent
    file_ext = Path(file_name).suffix.lower()

    rendered_images: List[str] = []

    try:
        # 1. Render PDF to images or use direct image (scale 1.5 for speed & crisp OCR)
        if file_ext == ".pdf":
            import pypdfium2 as pdfium
            pdf = pdfium.PdfDocument(temp_file_path)
            max_pages = min(len(pdf), 8)
            for i in range(max_pages):
                img_path = str(temp_dir / f"{record_id}_page_{i+1}.png")
                pdf[i].render(scale=1.5).to_pil().save(img_path)
                rendered_images.append(img_path)
        else:
            rendered_images.append(temp_file_path)

        # 2. Execute OCR Extraction
        ocr_start = time.time()
        engine = get_engine(language=language, tier=tier)
        all_lines = []

        for img_p in rendered_images:
            res_list = engine.predict(img_p)
            for res in res_list:
                texts = res.get("rec_texts", [])
                scores = res.get("rec_scores", [])
                polys = res.get("rec_polys", [])
                for idx, (t, s) in enumerate(zip(texts, scores)):
                    poly = polys[idx].tolist() if idx < len(polys) and hasattr(polys[idx], "tolist") else []
                    all_lines.append({
                        "text": str(t).strip(),
                        "confidence": float(s),
                        "box": poly,
                    })

        ocr_latency = (time.time() - ocr_start) * 1000

        # 3. Dynamic Patient Identity Extraction & Deduplication
        pat_info = extract_patient_identity(all_lines)
        conn = health_db.get_connection()
        cursor = conn.cursor()

        resolved_patient_id = None
        resolved_abha_id = user_abha_id
        patient_record = {}

        if pat_info.get("full_name"):
            pname = pat_info["full_name"]
            page = pat_info.get("age") or 30
            pgender = pat_info.get("gender") or "Unknown"

            # Check if this patient already exists in DB
            existing = cursor.execute(
                "SELECT patient_id, abha_id, full_name, age, gender FROM patients WHERE LOWER(full_name) LIKE ?;", 
                (f"%{pname.lower()}%",)
            ).fetchone()

            if existing:
                resolved_patient_id = existing[0]
                resolved_abha_id = existing[1]
                patient_record = {
                    "patient_id": resolved_patient_id, 
                    "abha_id": resolved_abha_id, 
                    "full_name": existing[2], 
                    "age": existing[3] or page, 
                    "gender": existing[4] or pgender
                }
            else:
                # Generate clean deterministic patient ID and synthetic ABHA
                clean_tag = re.sub(r'[^A-Z0-9]', '', pname.upper())[:10]
                resolved_patient_id = f"PAT-{clean_tag}-{page}{pgender[0] if pgender else 'U'}"
                resolved_abha_id = f"91-{clean_tag[:4]}-{int(time.time())%10000:04d}-2026"
                phone_num = "+91 97" + str(int(time.time())%100000000).zfill(8)
                cursor.execute("""
                    INSERT INTO patients (patient_id, abha_id, full_name, age, gender, contact_phone, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (resolved_patient_id, resolved_abha_id, pname, page, pgender, phone_num, time.strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                patient_record = {
                    "patient_id": resolved_patient_id, 
                    "abha_id": resolved_abha_id, 
                    "full_name": pname, 
                    "age": page, 
                    "gender": pgender
                }
        elif user_abha_id and user_abha_id != "auto":
            existing = cursor.execute(
                "SELECT patient_id, abha_id, full_name, age, gender FROM patients WHERE abha_id = ? OR patient_id = ?;", 
                (user_abha_id, user_abha_id)
            ).fetchone()
            if existing:
                resolved_patient_id = existing[0]
                resolved_abha_id = existing[1]
                patient_record = {
                    "patient_id": resolved_patient_id, 
                    "abha_id": resolved_abha_id, 
                    "full_name": existing[2], 
                    "age": existing[3], 
                    "gender": existing[4]
                }

        if not resolved_patient_id:
            # Fallback to the latest patient registered in DB or Vineetha
            latest_pat = cursor.execute("SELECT patient_id, abha_id, full_name, age, gender FROM patients ORDER BY rowid DESC LIMIT 1;").fetchone()
            if latest_pat:
                resolved_patient_id = latest_pat[0]
                resolved_abha_id = latest_pat[1]
                patient_record = {"patient_id": resolved_patient_id, "abha_id": resolved_abha_id, "full_name": latest_pat[2], "age": latest_pat[3], "gender": latest_pat[4]}
            else:
                resolved_patient_id = "PAT-VINEETHA-21F"
                resolved_abha_id = "91-8842-1920-2026"
                patient_record = {"patient_id": resolved_patient_id, "abha_id": resolved_abha_id, "full_name": "Vineetha", "age": 21, "gender": "Female"}

        # 4. Upload Raw Medical Record to S3 Vault
        raw_s3_info = s3_mgr.upload_raw_medical_record(
            temp_file_path,
            user_id=resolved_abha_id,
            record_id=record_id,
            record_type=record_type,
        )

        # 5. Save OCR Artifacts to S3 Processed Bucket
        ocr_payload = {
            "record_id": record_id,
            "encounter_id": encounter_id,
            "patient_id": resolved_patient_id,
            "patient_name": patient_record.get("full_name"),
            "language": language,
            "line_count": len(all_lines),
            "lines": all_lines,
        }
        artifact_s3_info = s3_mgr.upload_ocr_artifacts(
            user_id=resolved_abha_id,
            record_id=record_id,
            ocr_json_data=ocr_payload,
            page_image_paths=rendered_images,
        )

        # 6. Invoke GPT-6-Luna Clinical Ingestion Agent
        metadata = {
            "encounter_id": encounter_id,
            "encounter_date": time.strftime("%Y-%m-%d"),
            "record_type": record_type,
            "patient_id": resolved_patient_id,
            "patient_name": patient_record.get("full_name"),
            "patient_age": patient_record.get("age"),
            "patient_gender": patient_record.get("gender"),
            "abha_id": resolved_abha_id,
            "s3_raw_key": raw_s3_info["key"],
            "s3_artifacts_key": artifact_s3_info["ocr_json_key"],
            "s3_fhir_key": f"fhir/{resolved_patient_id}/{encounter_id}_fhir.json"
        }

        agent_model = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
        luna_agent = LunaIngestionAgent(model=agent_model)
        ingestion_result = luna_agent.process_document(all_lines, metadata)

        # 7. Retrieve Structured Committed Records from Relational Database
        meds = [dict(r) for r in cursor.execute("SELECT * FROM medications WHERE encounter_id = ?;", (encounter_id,)).fetchall()]
        labs = [dict(r) for r in cursor.execute("SELECT * FROM lab_observations WHERE encounter_id = ?;", (encounter_id,)).fetchall()]
        vitals = [dict(r) for r in cursor.execute("SELECT * FROM vitals WHERE encounter_id = ?;", (encounter_id,)).fetchall()]
        diags = [dict(r) for r in cursor.execute("SELECT * FROM diagnoses WHERE encounter_id = ?;", (encounter_id,)).fetchall()]
        instructions = [dict(r) for r in cursor.execute("SELECT * FROM clinical_instructions WHERE encounter_id = ?;", (encounter_id,)).fetchall()]
        conn.close()

        # 8. Build ABDM / FHIR R4 Bundle with Live Extracted Clinical Entities
        fhir_entries = [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": resolved_patient_id,
                    "name": [{"text": patient_record.get("full_name", "Identified Patient")}],
                    "identifier": [{"system": "https://abdm.gov.in/abha", "value": resolved_abha_id}],
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": encounter_id,
                    "status": "finished",
                    "subject": {"reference": f"Patient/{resolved_patient_id}"},
                }
            }
        ]

        for m in meds:
            fhir_entries.append({
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"med_{m.get('medication_id')}",
                    "status": m.get("status", "active"),
                    "medicationCodeableConcept": {"text": f"{m.get('drug_name')} {m.get('strength') or ''}".strip()},
                    "dosageInstruction": [
                        {
                            "text": m.get("instructions_english") or m.get("instructions_original"),
                            "timing": {"code": {"text": m.get("frequency_text") or m.get("frequency_code")}}
                        }
                    ]
                }
            })

        for l in labs:
            fhir_entries.append({
                "resource": {
                    "resourceType": "Observation",
                    "id": f"lab_{l.get('observation_id')}",
                    "status": "final",
                    "code": {"text": l.get("test_name")},
                    "valueQuantity": {
                        "value": l.get("value_numeric"),
                        "unit": l.get("unit")
                    },
                    "interpretation": [{"text": l.get("interpretation")}]
                }
            })

        for d in diags:
            fhir_entries.append({
                "resource": {
                    "resourceType": "Condition",
                    "id": f"diag_{d.get('diagnosis_id')}",
                    "clinicalStatus": {"text": d.get("clinical_status", "active")},
                    "code": {"text": d.get("condition_name")}
                }
            })

        fhir_bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "identifier": {"system": "https://abdm.gov.in/records", "value": encounter_id},
            "entry": fhir_entries
        }

        # Multilingual Summaries
        pat_display_name = patient_record.get("full_name", "Patient")
        summaries = {
            "en": f"Encounter {encounter_id} for {pat_display_name} ingested with {len(meds)} medications, {len(labs)} lab observations, and {len(diags)} diagnoses.",
            "te": f"రోగి {pat_display_name} కొరకు ఎన్‌కౌంటర్ {encounter_id} విజయవంతంగా ప్రాసెస్ చేయబడింది: {len(meds)} మందులు, {len(labs)} ల్యాబ్ పరీక్షలు నమోదు చేయబడ్డాయి.",
            "hi": f"मरीज़ {pat_display_name} के लिए मुलाकात {encounter_id} सफलतापूर्वक दर्ज की गई: {len(meds)} दवाएं, {len(labs)} लैब परीक्षण दर्ज किए गए।"
        }

        # 9. Upload Real FHIR Bundle to S3 Vault
        fhir_s3_info = s3_mgr.upload_fhir_and_summaries(
            patient_id=resolved_patient_id,
            record_id=encounter_id,
            fhir_bundle=fhir_bundle,
            summaries=summaries,
        )

        return {
            "status": "success",
            "record_id": record_id,
            "encounter_id": encounter_id,
            "patient_id": resolved_patient_id,
            "patient": patient_record,
            "record_type": record_type,
            "ocr_latency_ms": round(ocr_latency, 1),
            "extracted_lines_count": len(all_lines),
            "ingestion": {
                "status": ingestion_result.get("status", "success"),
                "model": agent_model,
                "summary": ingestion_result.get("summary", ""),
                "conversation_steps": ingestion_result.get("conversation_steps", 0),
                "medications_count": len(meds),
                "labs_count": len(labs),
                "diagnoses_count": len(diags),
                "instructions_count": len(instructions)
            },
            "records": {
                "patient": patient_record,
                "medications": meds,
                "lab_observations": labs,
                "vitals": vitals,
                "diagnoses": diags,
                "clinical_instructions": instructions
            },
            "structured_data": {
                "patient": patient_record,
                "medications": meds,
                "lab_observations": labs,
                "vitals": vitals,
                "diagnoses": diags,
                "clinical_instructions": instructions
            },
            "s3_storage": {
                "raw_bucket": s3_mgr.RAW_BUCKET,
                "raw_key": raw_s3_info["key"],
                "artifacts_bucket": s3_mgr.ARTIFACTS_BUCKET,
                "ocr_tokens_key": artifact_s3_info["ocr_json_key"],
                "fhir_bucket": s3_mgr.FHIR_BUCKET,
                "fhir_key": fhir_s3_info["fhir_key"],
                "summaries": fhir_s3_info["summaries"],
            }
        }

    finally:
        # Clean up temporary local page images
        for img in rendered_images:
            p = Path(img)
            if p.exists() and str(p) != temp_file_path:
                try:
                    p.unlink()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# POST /api/process-record: End-to-End Non-Blocking Pipeline Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/process-record")
async def process_record(
    file: UploadFile = File(...),
    abha_id: Optional[str] = Form(None),
    record_type: str = Form("prescription"),
    language: str = Form("auto"),
    language_hint: Optional[str] = Form(None),
    encounter_type: Optional[str] = Form(None),
    tier: str = Form("small")
):
    if language_hint:
        language = "te" if language_hint == "telugu" else ("hi" if language_hint == "hindi" else language_hint)
    if encounter_type:
        record_type = encounter_type

    temp_dir = Path("/tmp/health_uploads") if os.name != "nt" else Path("./temp_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file = temp_dir / f"rec_{int(time.time()*1000)}_{file.filename}"
    with open(temp_file, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Offload CPU-heavy OCR and GPT-6-Luna agent reasoning to non-blocking thread pool
        result = await asyncio.to_thread(
            _execute_ingestion_pipeline,
            temp_file_path=str(temp_file),
            file_name=file.filename,
            user_abha_id=abha_id,
            record_type=record_type,
            language=language,
            tier=tier
        )
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# POST /api/copilot/chat: Downstream AI Copilot Chat Endpoint (GPT-6-Luna)
# ---------------------------------------------------------------------------

class CopilotChatRequest(BaseModel):
    patient_id: str = "PAT-91443288912011"
    message: str
    language: Optional[str] = "auto"
    session_id: Optional[str] = None

@app.post("/api/copilot/chat")
async def copilot_chat(req: CopilotChatRequest):
    try:
        # Offload GPT-6-Luna analytical reasoning and tool execution to async thread pool
        res = await asyncio.to_thread(
            copilot_agent.chat,
            patient_id=req.patient_id,
            message=req.message,
            session_id=req.session_id,
            language=req.language or "auto"
        )
        return JSONResponse(content=res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ---------------------------------------------------------------------------
# Downstream Query APIs
# ---------------------------------------------------------------------------

@app.get("/api/patient/{patient_id}/timeline")
def get_patient_timeline(patient_id: str):
    data = health_db.query_patient_timeline(patient_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return data


@app.get("/api/patient/{patient_id}/labs/{test_name}")
def get_lab_trend(patient_id: str, test_name: str):
    trends = health_db.query_lab_trend(patient_id, test_name)
    return {"patient_id": patient_id, "test_name": test_name, "data_points": trends}


@app.head("/api/db/stats")
@app.get("/api/db/stats")
def get_db_stats():
    conn = health_db.get_connection()
    c = conn.cursor()
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    counts = {t: c.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0] for t in tables}
    conn.close()
    return {"status": "success", "tables": counts}


@app.get("/api/patients")
def list_patients():
    conn = health_db.get_connection()
    c = conn.cursor()
    patients = [dict(r) for r in c.execute("SELECT * FROM patients ORDER BY created_at DESC;").fetchall()]
    for p in patients:
        pid = p["patient_id"]
        enc_count = c.execute("SELECT COUNT(*) FROM encounters WHERE patient_id = ?", (pid,)).fetchone()[0]
        conditions = [r[0] for r in c.execute("SELECT DISTINCT condition_name FROM diagnoses WHERE patient_id = ?", (pid,)).fetchall()]
        p["encounter_count"] = enc_count
        p["conditions"] = conditions
    conn.close()
    return {"status": "success", "patients": patients}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
