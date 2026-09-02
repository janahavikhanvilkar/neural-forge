# SmartBiz – AI-Powered Business Process Automation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0+](https://img.shields.io/badge/framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Database-SQLite](https://img.shields.io/badge/database-SQLite%20%2F%20SQLAlchemy-green.svg)](https://www.sqlite.org/)
[![AI-Google_Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev/)
[![HITL-Enabled](https://img.shields.io/badge/Human--in--the--Loop-Active-red.svg)](#human-in-the-loop-hitl)

SmartBiz is a centralized, production-grade business automation platform designed to process high-volume enterprise data, perform structured extraction, classify requests, score leads, route workflows to appropriate departments, generate contextual AI responses, and enforce **Human-in-the-Loop (HITL)** verification whenever AI confidence is low or sensitivity is high.

---

## 🚀 Core Philosophy

```
Input Documents / Requests
         ↓
  AI Processing & OCR (Google Gemini API / Pattern Engine)
         ↓
  Validation, Arithmetic & Anomaly Checks
         ↓
  Confidence Score Calculation (0 – 100%)
         ↓
┌──────────────────────────────────────────────┐
│ Decision Gate                                │
│   ├─ High Confidence (≥80%) → Straight-Through Automation → Target Department
│   └─ Low Confidence / Discrepancy (<80%) → HITL Verification Queue → Human Reviewer
└──────────────────────────────────────────────┘
         ↓
  Department Finalization (Finance / Sales / HR / Support)
         ↓
  Real-Time Analytics & Audit Trail
```

---

## 🌟 Modules & Features

### 1. Invoice Processing & Financial Audit
- **Multi-Format Ingestion**: Supports PDF, DOCX, PNG, JPG, and TXT invoices.
- **AI Structured Extraction**: Automatically extracts Vendor, Invoice Number, Invoice Date, Due Date, Subtotal, Tax/GST, Total, Currency, and Payment Info.
- **Automated Validation & Math Checks**: Validates that $\text{Subtotal} + \text{Tax} = \text{Total}$, checks for duplicate invoice numbers in the database, and flags anomalies.
- **Routing & HITL**: Automatically routes clean invoices to the Finance Department ($\ge 80\%$ confidence); flags calculation errors or duplicates to the HITL queue ($<80\%$).
- **Editable Verification**: Finance users can review, correct line items, approve, or reject invoices with recorded audit reasons.

### 2. B2B Lead Scoring & Sales Routing
- **Lead Intelligence**: Analyzes deal budget, company scale, industry, engagement level, and interaction history.
- **Scoring Engine**: Calculates an AI Lead Score ($0 - 100$) and categorizes into **HOT** ($\ge 80$), **WARM** ($60 - 79$), or **COLD** ($<60$).
- **Actionable Insights**: Outlines key reasons for the score and generates recommended next steps.
- **Automatic Sales Handoff**: HOT leads are immediately assigned to the Sales Department queue.

### 3. AI Resume Screening & HR Ranking
- **Job Description Manager**: Create and customize required skills and experience requirements.
- **Batch Resume Screening**: Upload and parse multiple resumes simultaneously (PDF, DOCX, TXT).
- **Match Matrix**: Calculates Skills Match %, Experience Match %, and Overall Fit Score, clearly highlighting Matched Skills (Green) vs Missing Skills (Red).
- **Assistive Shortlisting**: Ranks candidates in an interactive pool and supports HR status workflows (Shortlisted, Interviewing, Hired, Rejected).

### 4. Support Ticket AI Triage & Response Generation
- **NLP Classification**: Categorizes incoming tickets into *Billing*, *Technical*, *Account*, *Product*, or *General*.
- **Priority & Sentiment Detection**: Identifies urgency (*Critical*, *High*, *Medium*, *Low*) and emotional tone (*Positive*, *Neutral*, *Negative*).
- **Automated Response Drafting**: Generates context-aware, empathetic resolution drafts.
- **Human Verification Controls**: Allows support agents to **Generate**, **Regenerate**, **Edit**, **Approve & Send**, or **Reject** responses before customer dispatch.

### 5. Dedicated Human-in-the-Loop (HITL) Queue
- Centralized queue intercepting tasks across all modules whenever AI confidence is low, math discrepancies occur, or sensitive actions require sign-off.
- **Side-by-Side Audit View**: Inspects original raw input alongside AI structured extractions and alert flags.
- **Human Actions**: Approve, Reject, Edit extracted values, Reassign department, and Record audit comments.

### 6. Interactive Visual Workflows
- Step-by-step pipeline maps for all 4 workflows with real-time stage counters and visual process transparency.

### 7. Real-Time Analytics Dashboard
- Comprehensive Chart.js visualizations: Tasks by Module, Straight-Through Automation vs Human Intervention, Confidence Score Distributions, Lead Scoring Heatmaps, Department Workloads, and Timeline Trends.

### 8. Global Search, Notifications & Audit Log
- Fast global search across invoices, leads, resumes, and support tickets with keyboard shortcut (`/`).
- Real-time notification popover with unread counters.
- Full compliance activity audit trail capturing every automated and human decision.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Flask 3.1, SQLAlchemy, Werkzeug |
| **Database** | SQLite with structured relational schema |
| **AI / LLM** | Google Gemini API (`gemini-1.5-flash` / `gemini-2.5-flash`) + Resilient Local Fallback Engine |
| **Document OCR** | `pypdf`, `python-docx`, `Pillow` |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5, Bootstrap Icons |
| **Data Viz** | Chart.js 4.4 |

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repo-url>
cd SmartBiz
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure:
```env
SECRET_KEY=smartbiz-hackathon-super-secret-key-2026
GEMINI_API_KEY=your_gemini_api_key_here
AUTO_PROCESS_THRESHOLD=80
HITL_REVIEW_THRESHOLD=60
PORT=5000
FLASK_DEBUG=1
```
> **Note on AI API Key**: If a `GEMINI_API_KEY` is provided, SmartBiz executes live Gemini LLM API calls. If left empty, SmartBiz automatically runs its built-in high-accuracy pattern and NLP heuristic engine without errors.

---

## ▶️ Running the Application

Start the Flask server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 👥 Demo Login Credentials

SmartBiz includes 1-click quick-login buttons on the login page for instant role switching during hackathon evaluations:

| Role | Email | Password | Primary Focus |
|---|---|---|---|
| **Admin** | `admin@smartbiz.ai` | `admin123` | Full system access, threshold settings, HITL queue |
| **Finance** | `finance@smartbiz.ai` | `finance123` | Invoice extraction, arithmetic audit, billing tickets |
| **Sales** | `sales@smartbiz.ai` | `sales123` | High-value lead scoring, pipeline management |
| **HR** | `hr@smartbiz.ai` | `hr123` | Job descriptions, resume screening & candidate ranking |
| **Support** | `support@smartbiz.ai` | `support123` | Support ticket triage, AI response verification |

---

## 🎬 Step-by-Step Hackathon Demo Walkthrough

### Demo 1 – Invoice Processing & HITL Validation
1. Log in as **Finance** (`finance@smartbiz.ai`).
2. Navigate to **Invoice Processing** and click **Upload & Extract Invoice**.
3. Select `uploads/samples/sample_clean_invoice.txt` $\rightarrow$ AI extracts vendor, dates, and amounts with **96% Confidence** and auto-processes to Finance.
4. Upload `uploads/samples/sample_math_error_invoice.txt` $\rightarrow$ AI detects a **$250 math discrepancy** ($5,000 + $400 \ne $5,850) $\rightarrow$ Confidence drops to **52%** and routes to the **HITL Verification Queue**.
5. Open **HITL Verification**, inspect the side-by-side discrepancy diff, correct the total, and click **Approve**.

### Demo 2 – AI Lead Scoring & Sales Routing
1. Log in as **Sales** (`sales@sales.ai`).
2. Go to **Lead Scoring** $\rightarrow$ Click **Score New Lead**.
3. Enter enterprise details (Budget: $75,000, Size: 1000+, High Engagement).
4. AI calculates a score of **94/100 (HOT)**, outlines the justification, and routes the lead to Sales.

### Demo 3 – Resume Screening & Candidate Ranking
1. Log in as **HR** (`hr@smartbiz.ai`).
2. Go to **Resume Screening** $\rightarrow$ Select the *Senior Full-Stack Automation Engineer* job opening.
3. Click **Upload Resumes** $\rightarrow$ Upload `uploads/samples/sample_senior_engineer_resume.txt`.
4. AI screens the candidate, identifies matched skills (*Python, Flask, SQL, Docker*), computes a **94% Match Score**, and classifies as a **Strong Match**.
5. HR marks candidate as **Shortlisted**.

### Demo 4 – Support Ticket NLP & Verified AI Response
1. Go to **Support Tickets** $\rightarrow$ Click **New Support Ticket**.
2. Submit: *"My payment was deducted twice for August subscription."*
3. AI automatically classifies: Category = **Billing**, Priority = **High**, Sentiment = **Negative**, Department = **Finance**.
4. Click **Review & Send** to inspect the AI-generated empathetic refund draft.
5. Edit or click **Approve & Send Response** $\rightarrow$ Status transitions to **Resolved**.

---

## 🏛️ Architecture & Folder Structure

```
SmartBiz/
├── app.py                      # Flask Application Factory & Server Entry Point
├── config.py                   # App Configuration & Thresholds
├── requirements.txt            # Python Dependencies
├── .env.example                # Example Environment Variables
├── .env                        # Local Environment Config
├── README.md                   # Complete Platform Documentation
│
├── database/
│   ├── smartbiz.db             # SQLite Database
│   └── seed_data.py            # Demo Data Seeder
│
├── models/
│   └── models.py               # SQLAlchemy Database Models
│
├── routes/
│   ├── auth.py                 # Authentication & Role Switching
│   ├── dashboard.py            # Overview Metrics & Chart Data APIs
│   ├── invoices.py             # Invoice Processing & OCR Routes
│   ├── leads.py                # Lead Scoring & Category Routing
│   ├── resumes.py              # Resume Screening & Ranking
│   ├── support.py              # Support Ticket Triage & Responses
│   ├── hitl.py                 # HITL Verification Queue & Resolution
│   ├── workflows.py            # Visual Workflow Engine
│   ├── analytics.py            # Quantitative SLA & Efficiency Analytics
│   ├── settings.py             # Confidence Threshold & AI Key Config
│   └── api.py                  # Search & Notifications APIs
│
├── services/
│   ├── ai_service.py           # Centralized Google Gemini AI & Heuristic Fallback
│   ├── invoice_service.py      # Invoice Validation & Duplicate Detection
│   ├── lead_service.py         # Lead Scoring & Categorization
│   ├── resume_service.py       # Resume Matching & Skill Gap Analysis
│   ├── support_service.py      # Ticket NLP & Response Drafting
│   └── hitl_service.py         # HITL Routing & Entity Synchronization
│
├── utils/
│   ├── file_parser.py          # PDF, DOCX, TXT, and Image Document Parser
│   └── helpers.py              # RBAC Decorators, Logger & Notifier
│
├── templates/                  # Modern Jinja2 SaaS HTML Templates
└── static/                     # CSS & Modular JavaScript
```

---

## 🔒 Security & Reliability

- **Password Security**: Passwords hashed using Werkzeug PBKDF2 with SHA-256.
- **Zero API Key Leakage**: AI calls are strictly backend-mediated; API keys are never passed to the frontend.
- **Input & File Sanitization**: File type whitelisting and size capping (16MB).
- **Graceful Fallbacks**: AI failure or network timeouts fallback gracefully to heuristic models without crashing or exposing stack traces.

---

## 📜 License
SmartBiz is licensed under the MIT License.
