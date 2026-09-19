# Academic-ScreenX

> **Autonomous Multi-Agent Paper Screening Platform & AI-Powered RAG Document Evaluator for University Faculty & Academic Review Committees**

---

## What is Academic-ScreenX?

Academic-ScreenX is an autonomous multi-agent paper screening and document evaluation platform that solves the **Faculty Review Bottleneck** by evaluating student project proposals (PDF & TXT) through a sequential 3-stage funnel and an integrated **AI RAG (Retrieval-Augmented Generation)** criteria evaluation layer:
- ✅ **Automated Structural Compliance Auditing**: Verifies strict word count ($250 \le W \le 500$) and detects mandatory academic sections (*Introduction, Methodology, Results, Conclusion*).
- ✅ **Methodology Extraction & Novelty Assessment**: Generates targeted literature search queries and detects generic/saturated tutorial duplicates (e.g., standard MNIST CNNs, basic Kaggle Titanic trees, naive sentiment analysis).
- ✅ **Technical Feasibility & Composite Scoring**: Evaluates dataset feasibility (*High / Moderate / Low*), computes peer score $S \in [1, 10]$, and writes a strict 3-sentence executive summary review.
- ✅ **AI-Powered RAG Document Evaluation Layer**: LangChain vector indexing (`Chroma` + `OpenAIEmbeddings`) and retrieval chain (`ChatOpenAI` `gpt-4o-mini`) evaluating documents against customizable job/academic criteria, extracting **Match Status**, **Key Evidence Found**, and **Missing Requirements**.
- ✅ **One-Click Faculty Triage**: Automatically categorizes proposals into `Approved for Faculty`, `Needs Revision`, and `Flagged for Low Novelty`.
- ✅ **Clean Light-Mode Faculty Dashboard**: Real-time stats cards, batch drag-and-drop PDF/TXT dropzone, interactive data table with status filters, and instant evaluation dossier modal.
- ✅ **Zero-Credit Mock Guardrails**: Default offline mock engine (`USE_MOCK_LLM=True`) runs without external API dependencies or costs, with instant support for live Tavily/OpenAI/Gemini keys.
- ✅ **Production & Serverless Ready**: Native support for Vercel Serverless, Docker, Docker Compose, and Cloud PaaS (Render/Fly.io).

---

## Documentation Structure

### **Start Here**
1. **[Quick Start Guide](#-quick-start-guide)** 
   - Get running in 3 minutes
   - Virtual environment setup
   - Run multi-agent & RAG pipeline
   - Launch faculty dashboard

### **Architecture & Funnel Design**
2. **[3-Stage Multi-Agent Screening Funnel](#-3-stage-multi-agent-screening-funnel)**
   - Stage 1: Compliance Auditor
   - Stage 2: Novelty Assessor
   - Stage 3: Technical Critic
   - Multi-agent sequential chain

3. **[🧠 AI-Powered RAG Document Evaluation Layer](#-ai-powered-rag-document-evaluation-layer)**
   - Semantic chunking & vector indexing (`RecursiveCharacterTextSplitter`, `Chroma`)
   - Automated criteria-based evaluation (`evaluate_document`)
   - Structured tri-field diagnostic extraction

4. **[API Endpoints & Database Schema](#-api-endpoints--database-schema)**
   - REST API specification
   - SQLite ORM models
   - JWT authentication & cookie session management

5. **[Deployment Options](#-deployment-options)**
   - Vercel Serverless deployment

6. **[Benchmark Test Suite & Verification](#-benchmark-test-suite--verification)**
   - Automated pytest suite
   - 3 Pre-configured sample PDFs
   - Evaluation triage results

---

## Project & Code Structure

### **AI Services & RAG Evaluator Layer** 
```
services/ & app/services/
├── __init__.py           ✅ Package exports & evaluate_document binding
└── ai_evaluator.py       ✅ LangChain RAG pipeline (PyPDF/TextLoader, Chroma, OpenAIEmbeddings, ChatOpenAI)
```

### **Multi-Agent Pipeline** 
```
app/agents/
├── base.py            ✅ Base agent interface & structured logging
├── compliance.py      ✅ Stage 1: Compliance Auditor (Structure & word count)
├── novelty.py         ✅ Stage 2: Novelty Assessor (Methodology & literature duplicate check)
├── critic.py          ✅ Stage 3: Technical Critic (Scoring S ∈ [1,10] & 3-sentence review)
└── pipeline.py        ✅ Sequential multi-agent orchestrator & RAG integration
```

### **Backend & Core API** 
```
app/
├── auth.py            ✅ Password hashing (bcrypt) & JWT token session handling
├── config.py          ✅ Dynamic serverless environment detection & storage config
├── database.py        ✅ SQLite / SQLAlchemy engine & auto-init migration handler
├── models.py          ✅ User & Submission ORM models (with RAG fields)
├── schemas.py         ✅ Pydantic schemas for API inputs, agent outputs & RAG diagnostics
└── routes/
    ├── auth_routes.py        ✅ POST /register, POST /login, POST /logout, GET /me
    ├── submission_routes.py  ✅ POST /upload, GET /list, GET /stats, GET /{id}/report, DELETE /{id}
    └── web_routes.py         ✅ GET /, GET /login, GET /dashboard, GET /report/{id}, POST /demo/load-samples
```

### **Frontend UI & Design System**
```
app/
├── static/
│   ├── css/custom.css        ✅ Premium typography, subtle animations & badge themes
│   └── js/dashboard.js       ✅ Upload dropzone, live polling, filter & RAG dossier modal
└── templates/
    ├── base.html             ✅ Semantic HTML5 base layout & responsive navbar
    ├── login.html            ✅ Faculty authentication & 1-click demo login
    ├── register.html         ✅ Account registration interface
    ├── dashboard.html        ✅ Main faculty dashboard, stats bento & submissions table
    └── report.html           ✅ Official printable dossier with RAG evaluation breakdown
```

---

## AI-Powered RAG Document Evaluation Layer

The RAG layer (`services/ai_evaluator.py`) ingests candidate documents (PDF or TXT), builds isolated vector embeddings, and performs targeted contextual retrieval to verify document alignment against job or academic criteria.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      AI RAG EVALUATION PIPELINE                        │
│                                                                        │
│   Candidate Doc (PDF / TXT)                                            │
│              │                                                         │
│              ▼                                                         │
│   Document Loader (PyPDFLoader / TextLoader)                           │
│              │                                                         │
│              ▼                                                         │
│   RecursiveCharacterTextSplitter (chunk_size=500, chunk_overlap=50)    │
│              │                                                         │
│              ▼                                                         │
│   Chroma Vector Store + OpenAIEmbeddings (text-embedding-3-small)      │
│              │                                                         │
│              ▼                                                         │
│   Similarity Retriever (k=4 most relevant chunks)                     │
│              │                                                         │
│              ▼                                                         │
│   ChatOpenAI (gpt-4o-mini) with Structured Evaluation Prompt           │
│              │                                                         │
│              ▼                                                         │
│   Structured Output:                                                   │
│   - Match Status: Qualified | Not Qualified | Needs Review             │
│   - Key Evidence Found: [ Citable evidence retrieved from text ]       │
│   - Missing Requirements: [ Missing criteria / revision points ]      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3-Stage Multi-Agent Screening Funnel

```
                       [ Uploaded Student PDF / TXT ]
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │             STAGE 1: Compliance Auditor                     │
      │   - Extracts text, title, and student metadata              │
      │   - Enforces word count: 250 <= W <= 500 words              │
      │   - Validates sections: Intro, Method, Results, Conclusion  │
      │   - Output: Compliance Score (0 - 10) & Error Diagnostics   │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │             STAGE 2: Novelty Assessor                       │
      │   - Extracts core algorithmic methodology                   │
      │   - Formulates targeted academic search queries             │
      │   - Scans literature index to flag duplicate/tutorial ideas │
      │   - Output: Novelty Score (0 - 10) & Saturated Match Links  │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │             STAGE 3: Technical Critic                       │
      │   - Evaluates dataset feasibility & technical depth         │
      │   - Calculates final composite score S in [1, 10]           │
      │   - Generates exact 3-sentence executive summary review     │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │            AI RAG DOCUMENT EVALUATION LAYER                 │
      │   - LangChain Chroma Vector Retrieval (chunks of 500)       │
      │   - GPT-4o-mini criteria comparison                         │
      │   - Match Status, Key Evidence, Missing Requirements        │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │ Faculty Triage: Approved for Faculty | Needs Revision | Flagged  │
    └──────────────────────────────────────────────────────────────────┘
```
---

## Quick Start Guide

Open at **[https://academic-screen-x.vercel.app/dashboard](https://academic-screen-x.vercel.app/dashboard)**.

---

### Agent Roles & Evaluation Criteria

| Agent Stage | Class Name | Input Context | Analysis & Output Metrics |
| :--- | :--- | :--- | :--- |
| **Stage 1** | `ComplianceAuditor` | Raw PDF Document | Extracts title/author, counts tokens, checks for 4 mandatory sections (*Introduction, Methodology, Results, Conclusion*), outputs Compliance Score (0–10) & diagnostic feedback. |
| **Stage 2** | `NoveltyAssessor` | Extracted Abstract Text | Extracts methodology keywords, generates 3 academic search queries, scans for replicated baselines, outputs Novelty Score (0–10) & literature overlap matches. |
| **Stage 3** | `TechnicalCritic` | Compliance & Novelty Results | Evaluates empirical dataset feasibility, calculates composite score $S \in [1, 10]$, determines triage state, and writes a strict **3-sentence executive summary review**. |
| **RAG Layer** | `evaluate_document` | Vector Chunks & Criteria | Ingests PDF/TXT, chunks text with overlap, performs similarity search in Chroma, and runs `gpt-4o-mini` evaluation returning **Match Status**, **Key Evidence**, and **Missing Requirements**. |

---


## Default Faculty Credentials

The application automatically seeds a default faculty committee account on startup:

| Field | Value |
| :--- | :--- |
| **Email** | `faculty@university.edu` |
| **Password** | `admin123` |
| **Role** | Faculty Committee Chair |

> **Note**: A 1-click **"⚡ Auto-Fill Faculty Demo Credentials"** button is provided on the login page for effortless evaluation.

---

## Benchmark Test Suite & Verification

The project includes 3 realistic academic proposals in `/sample_pdfs` representing the triage funnel:

| Sample Document | Evaluation Profile | Stage 1 Compliance | Stage 2 Novelty | Stage 3 Score | RAG Status | Final Triage Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`01_invalid_format.pdf`** | Structural defect (87 words, missing *Methodology* & *Results*) | ✗ 3.5 / 10 | — | 7.0 / 10 | **Needs Review** | **Needs Revision** |
| **`02_copied_idea.pdf`** | Standard MNIST CNN tutorial replicate | ✓ 10.0 / 10 | ✗ 2.5 / 10 | 4.8 / 10 | **Qualified** | **Flagged (Low Novelty)** |
| **`03_innovative_idea.pdf`** | Novel Neuromorphic HDC Edge MEMS architecture | ✓ 10.0 / 10 | ✓ 9.2 / 10 | 9.2 / 10 | **Qualified** | **Approved for Faculty** |

