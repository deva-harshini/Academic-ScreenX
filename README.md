# Academic-ScreenX: Autonomous Multi-Agent Abstract Filter

**Academic-ScreenX** is a production-ready, autonomous multi-agent paper screening platform engineered for university faculty and academic review committees. It evaluates uploaded student research proposals (PDFs) through a sequential 3-stage funnel:

```
                  ┌─────────────────────────────────┐
                  │   Uploaded Proposal PDF(s)      │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │ Stage 1: Compliance Auditor (Structure & Length)    │
        │ - Strict 250–500 word count validation              │
        │ - 4 Mandatory Sections (Intro, Method, Results, Con)│
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │ Stage 2: Novelty Assessor (Duplicate Detection)     │
        │ - Automated methodology & keyword extraction        │
        │ - Simulated / Live Web Search (DuckDuckGo / Tavily) │
        │ - Identification of saturated/replicated tutorials  │
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
        ┌─────────────────────────────────────────────────────┐
        │ Stage 3: Technical Critic (Feasibility & Scoring)   │
        │ - Composite Peer Score S ∈ [1, 10]                  │
        │ - Dataset feasibility analysis (e.g. MIT-BIH, edge) │
        │ - Strict 3-Sentence Executive Summary Review        │
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Faculty Dashboard: "Approved", "Needs Revision", "Flagged Low Novelty" │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Features

- **Single-Stack Lightweight Python**: Built with FastAPI, SQLite with SQLAlchemy, Jinja2, and TailwindCSS (via CDN). No heavy Node.js or React build overhead.
- **Async Background Task Engine**: Proposal evaluation is non-blocking via FastAPI `BackgroundTasks`, keeping upload and dashboard browsing fast.
- **Zero-Credit Mock Guardrails**: Default `USE_MOCK_LLM=True` mode allows complete offline verification without consuming API tokens or requiring credit cards.
- **Faculty Dashboard & Real-Time Stats**:
  - Live summary statistics (Total Uploaded, Approved %, Flagged %, Avg Processing Time).
  - Drag-and-drop batch upload dropzone with instant upload queueing.
  - Interactive table filterable by status (`Approved`, `Needs Revision`, `Flagged for Low Novelty`), sortable by score, date, or novelty.
  - Modal evaluation dossier displaying compliance audit checklists, search queries, and 3-sentence reviews.
  - Dedicated printable/exportable report views.
- **1-Click Sample Testing**: Includes 3 pre-configured realistic academic PDFs in `/sample_pdfs` (`01_invalid_format.pdf`, `02_copied_idea.pdf`, `03_innovative_idea.pdf`).

---

## 🚀 Quick Start (Local Setup)

### 1. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate sample test PDFs
```bash
python tests/generate_samples.py
```

### 4. Run automated test suite
```bash
PYTHONPATH=. pytest tests/test_pipeline.py -v
```

### 5. Launch the application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **http://localhost:8000** (or **http://localhost:8000/dashboard**).

---

## 🔑 Default Faculty Credentials

- **Email**: `faculty@university.edu`
- **Password**: `admin123`
*(A 1-click "Auto-Fill Faculty Demo Credentials" button is provided on the login page)*

---

## 🐳 Docker Deployment

### Run with Docker Compose
```bash
docker-compose up --build -d
```
Access the application at `http://localhost:8000`.

### Run standalone Docker container
```bash
docker build -t academic-screenx .
docker run -p 8000:8000 academic-screenx
```

---

## 🌐 Cloud Deployment (Render / Fly.io / Heroku)

- **Render**: Connect repository and select `render.yaml` blueprint.
- **Procfile**: Ready for Heroku/Fly.io deployments via `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

---

## 🧪 Architecture & Agent Stages

| Agent Stage | Name | Role & Output |
| :--- | :--- | :--- |
| **Stage 1** | `ComplianceAuditor` | Validates word count ($250 \le W \le 500$) and detects section headers (*Introduction*, *Methodology*, *Results*, *Conclusion*). |
| **Stage 2** | `NoveltyAssessor` | Generates 3 academic search queries, scans for replicated baselines (e.g. MNIST CNN, Titanic tutorial), and computes novelty score. |
| **Stage 3** | `TechnicalCritic` | Evaluates dataset feasibility, computes overall score $S \in [1, 10]$, writes strict 3-sentence executive summary review, and decides triage state. |

---

## 📄 License
MIT License. Built for Academic Institutions and Faculty Review Committees.
