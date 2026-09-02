# 🎓 Academic-ScreenX - Complete Documentation Index

> **Autonomous Multi-Agent Paper Screening Platform for University Faculty & Academic Review Committees**

---

## 🎯 What is Academic-ScreenX?

Academic-ScreenX is a full-stack, autonomous multi-agent paper screening platform that solves the **Faculty Review Bottleneck** by evaluating student project proposals (PDFs) through a sequential 3-stage funnel:
- ✅ **Automated Structural Compliance Auditing**: Verifies strict word count ($250 \le W \le 500$) and detects mandatory academic sections (*Introduction, Methodology, Results, Conclusion*).
- ✅ **Methodology Extraction & Novelty Assessment**: Generates targeted literature search queries and detects generic/saturated tutorial duplicates (e.g., standard MNIST CNNs, basic Kaggle Titanic trees, naive sentiment analysis).
- ✅ **Technical Feasibility & Composite Scoring**: Evaluates dataset feasibility (*High / Moderate / Low*), computes peer score $S \in [1, 10]$, and writes a strict 3-sentence executive summary review.
- ✅ **One-Click Faculty Triage**: Automatically categorizes proposals into `Approved for Faculty`, `Needs Revision`, and `Flagged for Low Novelty`.
- ✅ **Clean Light-Mode Faculty Dashboard**: Real-time stats cards, batch drag-and-drop PDF dropzone, interactive data table with status filters, and instant evaluation dossier modal.
- ✅ **Zero-Credit Mock Guardrails**: Default offline mock engine (`USE_MOCK_LLM=True`) runs without external API dependencies or costs, with instant support for live Tavily/OpenAI/Gemini keys.
- ✅ **Production & Serverless Ready**: Native support for Vercel Serverless, Docker, Docker Compose, and Cloud PaaS (Render/Fly.io).

---

## 📖 Documentation Structure

### 🏁 **Start Here**
1. **[Quick Start Guide](#-quick-start-guide)** ⭐ **START HERE**
   - Get running in 3 minutes
   - Virtual environment setup
   - Run multi-agent pipeline
   - Launch faculty dashboard

### 📊 **Architecture & Funnel Design**
2. **[3-Stage Multi-Agent Pipeline](#-3-stage-multi-agent-screening-funnel)**
   - Stage 1: Compliance Auditor
   - Stage 2: Novelty Assessor
   - Stage 3: Technical Critic
   - Multi-agent sequential chain

3. **[API Endpoints & Database Schema](#-api-endpoints--database-schema)**
   - REST API specification
   - SQLite / SQLAlchemy ORM models
   - JWT authentication & cookie session management

4. **[Deployment Options](#-deployment-options)**
   - Vercel Serverless deployment
   - Docker & Docker Compose
   - Render / PaaS deployment
   - Environment variables configuration

5. **[Benchmark Test Suite & Verification](#-benchmark-test-suite--verification)**
   - Automated pytest suite
   - 3 Pre-configured sample PDFs
   - Evaluation triage results

---

## 🗂️ Project & Code Structure

### **Multi-Agent Pipeline** (Created ✅)
```
app/agents/
├── base.py            ✅ Base agent interface & structured logging
├── compliance.py      ✅ Stage 1: Compliance Auditor (Structure & word count)
├── novelty.py         ✅ Stage 2: Novelty Assessor (Methodology & literature duplicate check)
├── critic.py          ✅ Stage 3: Technical Critic (Scoring S ∈ [1,10] & 3-sentence review)
└── pipeline.py        ✅ Sequential multi-agent orchestrator
```

### **Backend & Core API** (Created ✅)
```
app/
├── auth.py            ✅ Password hashing (bcrypt) & JWT token session handling
├── config.py          ✅ Dynamic serverless environment detection & storage config
├── database.py        ✅ SQLite / SQLAlchemy engine & auto-init cold-start handler
├── models.py          ✅ User & Submission ORM models
├── schemas.py         ✅ Pydantic schemas for API inputs & agent outputs
└── routes/
    ├── auth_routes.py        ✅ POST /register, POST /login, POST /logout, GET /me
    ├── submission_routes.py  ✅ POST /upload, GET /list, GET /stats, GET /{id}/report, DELETE /{id}
    └── web_routes.py         ✅ GET /, GET /login, GET /dashboard, GET /report/{id}, POST /demo/load-samples
```

### **Frontend UI & Design System** (Created ✅)
```
app/
├── static/
│   ├── css/custom.css        ✅ Premium light-mode design system & animations
│   └── js/dashboard.js       ✅ Batch dropzone upload, live table filters, modal dossier view
└── templates/
    ├── base.html             ✅ Clean base layout, Tailwind CSS CDN & responsive navigation
    ├── dashboard.html        ✅ Faculty review dashboard with 5 top stat cards & table
    ├── login.html            ✅ Faculty sign-in portal with 1-click demo button
    ├── register.html         ✅ Account registration page
    └── report.html           ✅ Printable official evaluation dossier
```

### **Deployment & Serverless** (Created ✅)
```
├── api/
│   └── index.py       ✅ Vercel serverless entry point (ASGI handler)
├── vercel.json        ✅ Modern Vercel Zero-Config rewrites
├── Dockerfile         ✅ Production multi-stage Docker container
├── docker-compose.yml ✅ Container orchestration
├── render.yaml        ✅ Cloud PaaS deployment blueprint
├── Procfile           ✅ Web worker entrypoint for Heroku/Fly.io
├── .env.example       ✅ Environment variable reference template
└── requirements.txt   ✅ Minimal dependency footprint (single-stack Python)
```

### **Testing & Benchmark Datasets** (Created ✅)
```
sample_pdfs/
├── 01_invalid_format.pdf   ✅ Benchmark PDF: Word count violation & missing sections
├── 02_copied_idea.pdf      ✅ Benchmark PDF: Saturated MNIST CNN tutorial duplicate
└── 03_innovative_idea.pdf  ✅ Benchmark PDF: Novel Neuromorphic HDC Edge proposal

tests/
├── generate_samples.py     ✅ Programmatic PDF generator via ReportLab
├── test_pipeline.py        ✅ Pytest suite testing all 3 agents & REST endpoints
└── verify_live.py          ✅ Live HTTP end-to-end integration verifier
```

---

## 🤖 3-Stage Multi-Agent Screening Funnel

```
                  ┌────────────────────────────────────────┐
                  │    Uploaded Student Proposal (PDF)     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
         ┌────────────────────────────────────────────────────────┐
         │  Stage 1: Compliance Auditor (Structure & Formatting)  │
         │  • Word Count Validator (Target: 250–500 words)        │
         │  • 4 Section Parser (Intro, Method, Results, Concl)    │
         └────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
         ┌────────────────────────────────────────────────────────┐
         │  Stage 2: Novelty Assessor (Methodology & Duplicates)  │
         │  • Core technical keyword & methodology extraction     │
         │  • Academic literature & prior-art query synthesis     │
         │  • Detection of saturated tutorials (MNIST, Titanic)   │
         └────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
         ┌────────────────────────────────────────────────────────┐
         │  Stage 3: Technical Critic (Feasibility & Peer Review) │
         │  • Dataset Feasibility (High / Moderate / Low)         │
         │  • Composite Peer Score S ∈ [1, 10]                    │
         │  • Strict 3-Sentence Executive Summary Review          │
         └────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │ Faculty Triage: Approved for Faculty | Needs Revision | Flagged  │
    └──────────────────────────────────────────────────────────────────┘
```

### Agent Roles & Evaluation Criteria

| Agent Stage | Class Name | Input Context | Analysis & Output Metrics |
| :--- | :--- | :--- | :--- |
| **Stage 1** | `ComplianceAuditor` | Raw PDF Document | Extracts title/author, counts tokens, checks for 4 mandatory sections (*Introduction, Methodology, Results, Conclusion*), outputs Compliance Score (0–10) & diagnostic feedback. |
| **Stage 2** | `NoveltyAssessor` | Extracted Abstract Text | Extracts methodology keywords, generates 3 academic search queries, scans for replicated baselines, outputs Novelty Score (0–10) & literature overlap matches. |
| **Stage 3** | `TechnicalCritic` | Compliance & Novelty Results | Evaluates empirical dataset feasibility, calculates composite score $S \in [1, 10]$, determines triage state, and writes a strict **3-sentence executive summary review**. |

---

## 🚀 Quick Start Guide

### 1. Clone the repository
```bash
git clone https://github.com/deva-harshini/Academic-ScreenX.git
cd Academic-ScreenX
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate sample benchmark PDFs
```bash
python tests/generate_samples.py
```

### 5. Run automated test suite
```bash
PYTHONPATH=. pytest tests/ -v
```

### 6. Launch the local server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at **[http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)**.

---

## 🔑 Default Faculty Credentials

The application automatically seeds a default faculty committee account on startup:

| Field | Value |
| :--- | :--- |
| **Email** | `faculty@university.edu` |
| **Password** | `admin123` |
| **Role** | Faculty Committee Chair |

> **Note**: A 1-click **"⚡ Auto-Fill Faculty Demo Credentials"** button is provided on the login page for effortless evaluation.

---

## 🌐 Deployment Options

### 1. Vercel Serverless (Recommended for Demo)
Academic-ScreenX includes native Vercel Serverless support via `api/index.py` and modern Zero-Config `vercel.json`:
1. Push this repository to GitHub.
2. Import the repository in [Vercel Dashboard](https://vercel.com/new).
3. Vercel automatically detects Python, packages the application, and deploys the serverless functions.

### 2. Docker & Docker Compose
```bash
# Run with Docker Compose
docker-compose up --build -d

# Or build standalone container
docker build -t academic-screenx .
docker run -p 8000:8000 academic-screenx
```

### 3. Cloud PaaS (Render / Fly.io / Heroku)
- **Render**: Connect repository and select `render.yaml` blueprint.
- **Procfile**: Ready for Heroku/Fly.io deployments via `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` to customize settings:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | `academic-screenx-super-secure-secret-key-2026` | JWT secret for signing auth session tokens. |
| `USE_MOCK_LLM` | `True` | Runs offline mock agent engine (zero token/credit costs). |
| `TAVILY_API_KEY` | `""` | Optional live web search API key for Stage 2 novelty check. |
| `OPENAI_API_KEY` | `""` | Optional OpenAI key for live LLM evaluations. |
| `GEMINI_API_KEY` | `""` | Optional Google Gemini key for live LLM evaluations. |
| `DATABASE_URL` | *(Auto-detected)* | Defaults to local SQLite (`./academic_screenx.db`) or `/tmp` on Vercel. |

---

## 🧪 Benchmark Test Suite & Verification

The project includes 3 realistic academic proposals in `/sample_pdfs` representing the triage funnel:

| Sample Document | Evaluation Profile | Stage 1 Compliance | Stage 2 Novelty | Stage 3 Score | Final Triage Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`01_invalid_format.pdf`** | Structural defect (87 words, missing *Methodology* & *Results*) | ✗ 3.5 / 10 | — | 7.0 / 10 | **Needs Revision** |
| **`02_copied_idea.pdf`** | Standard MNIST CNN tutorial replicate | ✓ 10.0 / 10 | ✗ 2.5 / 10 | 4.8 / 10 | **Flagged (Low Novelty)** |
| **`03_innovative_idea.pdf`** | Novel Neuromorphic HDC Edge MEMS architecture | ✓ 10.0 / 10 | ✓ 9.2 / 10 | 9.2 / 10 | **Approved for Faculty** |

---

## 📄 License

MIT License. Designed and built for Academic Institutions, University Faculty, and Project Review Committees.
