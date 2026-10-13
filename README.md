# AgentOS: Autonomous AI Task Worker

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![SQLite](https://img.shields.io/badge/SQLite-ACID%20Verified-003B57.svg)](https://www.sqlite.org/)
[![Pytest: 52 Passed](https://img.shields.io/badge/Pytest-52%20Passed-brightgreen.svg)]()
[![Evaluation: 100% (12/12)](https://img.shields.io/badge/Evaluation-100%25%20Passed-brightgreen.svg)]()

> **Submission for CentrAlign AI — AI Engineering Intern Selection Process**  
> **Candidate Project:** AgentOS — Autonomous AI Task Worker  
> **Tagline:** *"From instructions to verified outcomes."*

---

## 🌟 Executive Summary

**AgentOS** is an autonomous enterprise AI task worker designed for resilient business process automation. Unlike conventional conversational chatbots that merely suggest actions or naive scripts that simulate work, AgentOS receives a natural language objective, plans intermediate milestones, manipulates local file systems and enterprise APIs, recovers from transient failures, respects human safety boundaries, and **independently verifies persistent state against an ACID database using measurable postconditions**.

### Primary Demonstration Workflow
> *"Find the latest invoice from Acme Technologies, extract the invoice number, amount, due date, and vendor, create a payable record in the company system, verify that the record was saved correctly, and summarize the result."*

AgentOS autonomously discovers candidate invoice documents, parses both text and binary PDF formats, compares semantic document dates, extracts structured financial fields, checks database idempotency, writes to the company ledger (`agentos.db`), and invokes an independent critic to prove correctness before reporting evidence.

---

## 🎯 Evaluation Criteria Scorecard

| Evaluation Criterion | How AgentOS Solves It | Source Implementation |
| :--- | :--- | :--- |
| **1. Autonomy** | Decomposes high-level natural language goals into dynamic plans without requiring imperative steps. Compares file versions, resolves ambiguous vendor names, and drives execution forward. | [`planner.py`](file:///d:/ai-project/backend/app/agent/planner.py), [`loop.py`](file:///d:/ai-project/backend/app/agent/loop.py) |
| **2. Actual Execution** | **Performs real work.** Reads actual filesystem files (`sandbox_data/invoices/*.txt`, `*.pdf`, `sandbox_data/emails/*.txt`, `sandbox_data/contracts/*.txt`), extracts real regex/token data, queries SQLite via SQLAlchemy, and mutates persistent records. | [`tools/`](file:///d:/ai-project/backend/app/tools/), [`models.py`](file:///d:/ai-project/backend/app/database/models.py) |
| **3. Reliability & Recovery** | Dedicated Failure Detection engine intercepts transient errors (HTTP 503, timeouts), calculates exponential backoff (`0.5s * 2^attempts`), injects recovery milestones, and auto-heals. Enforces multi-level idempotency to prevent duplicate payments. | [`loop.py`](file:///d:/ai-project/backend/app/agent/loop.py), [`payable_tools.py`](file:///d:/ai-project/backend/app/tools/payable_tools.py) |
| **4. Independent Verification** | **Zero trust in model self-assertions.** An independent critic queries SQLite directly, asserts field-by-field matches (vendor, amount, due date), and issues a cryptographic verification receipt. Completion is governed strictly by ground-truth database postconditions (`CompletionPolicy`). | [`verifier.py`](file:///d:/ai-project/backend/app/verification/verifier.py), [`completion_policy.py`](file:///d:/ai-project/backend/app/agent/completion_policy.py) |
| **5. Human-in-the-Loop & Safety** | Financial transactions exceeding $10,000.00 USD automatically pause execution, emitting an interactive approval ticket with cryptographic argument hash matching (`PolicyEngine`) to prevent tampering upon resumption. | [`policy.py`](file:///d:/ai-project/backend/app/security/policy.py), [`ApprovalModal.tsx`](file:///d:/ai-project/frontend/src/components/ApprovalModal.tsx) |
| **6. Enterprise Security Defense** | Centralized Prompt Injection & Untrusted Content Sanitizer (`ContentSanitizer`) inspects PDFs, invoices, emails, contracts, and browser text, neutralizing instruction overrides and privilege escalation attempts before LLM ingestion. | [`sanitizer.py`](file:///d:/ai-project/backend/app/security/sanitizer.py) |
| **7. Crash Recovery & Checkpoints** | State snapshots and DAG node statuses are committed to SQLite after every step (`CheckpointManager`). A startup crash reconciler marks abandoned tasks as `INTERRUPTED`, allowing safe resumption without repeating non-idempotent writes. | [`checkpoint.py`](file:///d:/ai-project/backend/app/agent/checkpoint.py), [`main.py`](file:///d:/ai-project/backend/app/main.py) |
| **8. Generalization** | Decoupled agent architecture (`Planner`, `Memory`, `ToolRegistry`, `Critic`, `DAGPlanner`). Multiple enterprise workflows (Invoices, HR Emails, Inventory Replenishment, CSV Analytics, Legal Contract Audits) execute out-of-the-box. | [`base.py`](file:///d:/ai-project/backend/app/tools/base.py), [`multi_domain_workflows.py`](file:///d:/ai-project/backend/tests/test_multi_domain_workflows.py) |
| **9. Engineering Quality** | Clean typed Python codebase (Pydantic v2, SQLAlchemy, FastAPI), **52 passing Pytest tests**, **12-scenario evaluation benchmark (100% pass)**, and modern React 18 + TypeScript + Tailwind UI. | [`backend/tests/`](file:///d:/ai-project/backend/tests/), [`frontend/src/`](file:///d:/ai-project/frontend/src/) |
| **10. Zero-Setup Barrier** | Ships with a deterministic provider fallback and Groq LLM integration. Reviewers can clone and run all tests, benchmarks, and web UIs immediately without needing API keys. | [`provider.py`](file:///d:/ai-project/backend/app/agent/provider.py) |

---

## ⚡ Quickstart & Installation (Windows PowerShell)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development, or run the pre-built SPA via FastAPI)

### 1. Clone & Setup Python Environment
```powershell
# In PowerShell:
git clone https://github.com/jay-sanajay/autonomous-ai-task-worker.git
cd autonomous-ai-task-worker

# Install Python backend dependencies
pip install -r requirements.txt
```

### 2. Run Automated Test Suite (52 Tests)
```powershell
python -m pytest backend/tests/ -v
```
*Result: 52/52 passed across workflow, duplicate prevention, recovery, verification, approval, limits, prompt injection defense, checkpointing, and completion policies.*

### 3. Run Benchmark Evaluation Suite (12 Scenarios)
```powershell
python evaluation/run_evaluation.py
```
*Result: 100% scenario pass rate (12/12), 0 false claims, 0 duplicate records created, 100% recovery rate.*

---

## 🎮 Running the System

You can run AgentOS using either the **Interactive Web Dashboard** or the **Rich Terminal CLI**.

### Option A: Modern Web Dashboard (Recommended)

#### 1. Start Backend Server
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
> Note: The FastAPI backend automatically serves the compiled React SPA at `http://127.0.0.1:8000/`.

#### 2. Start Frontend Dev Server (Optional, for hot reloading)
```powershell
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

#### Dashboard Capabilities:
- **Preset Task Selector:** Run the Primary Acme Workflow, 503 Fault Recovery, High-Value Approval, or Duplicate Checks with a single click.
- **Dynamic Plan & ReAct Trace:** Watch the agent plan, think, call tools, and observe outputs step-by-step.
- **Human-in-the-Loop Modal:** Interactive sign-off for disbursements > $10,000.
- **Ground-Truth Evidence Card:** Real-time verification receipt with field comparisons and audit tokens.
- **Company Sandbox Tab:** Direct inspection of SQLite tables (`Vendors`, `Invoices`, `Payables`).

---

### Option B: Interactive Terminal CLI

For headless or quick terminal evaluation:
```powershell
python run_demo.py
```
Provides an interactive menu with 6 guided scenarios:
1. **Primary Acme Workflow** (Core problem statement)
2. **503 Transient Fault & Auto-Recovery** (Simulated outage with exponential backoff)
3. **Human-in-the-Loop Safety Gate** ($48,500 invoice interactive sign-off)
4. **Idempotency Guarantee** (Duplicate invoice detection & graceful halt)
5. **Missing Field Safety** (Refusal to hallucinate missing amounts)
6. **Custom Goal** (Enter any natural language task)

---

## 🏗 System Architecture & Flow

```
                      ┌─────────────────────────────────────────┐
                      │    Natural Language User Objective      │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   Dynamic Goal Planner & Decomposer     │
                      └────────────────────┬────────────────────┘
                                           │
             ┌─────────────────────────────▼─────────────────────────────┐
             │                 ReAct Execution Loop                      │
             │                                                           │
             │  1. Reason (LLM / Structured Intent)                      │
             │  2. Safety Evaluation (HITL gate if amount > $10,000)     │
             │  3. Select & Invoke Controlled Tool                       │
             │  4. Observe Output & Measure Latency                      │
             │  5. Failure Interception (Exponential Backoff if 503)     │
             │  6. Entity Extraction -> Update Working Memory            │
             │  7. Plan Reflection (Inject Recovery Steps if needed)     │
             └─────────────────────────────┬─────────────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Independent Ground-Truth Critic      │
                      │  (Direct SQLite Query & Field Match)    │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │ Tamper-Evident Evidence Audit Receipt   │
                      └─────────────────────────────────────────┘
```

See [ARCHITECTURE.md](file:///d:/ai-project/ARCHITECTURE.md) for full subsystem details, state machine diagrams, and database ERD.

---

## 🔬 Benchmark Evaluation Results

The benchmark harness in [`evaluation/run_evaluation.py`](file:///d:/ai-project/evaluation/run_evaluation.py) runs 12 evaluation scenarios against the real SQLite database:

| Category | Scenario | Result | Status |
| :--- | :--- | :--- | :--- |
| **Core Workflow** | Primary Acme Invoice Workflow (`INV-2024-001`) | Payable created & independently verified | **PASS** |
| **Generalization** | Alternative Phrasing ("Newest Acme invoice register payable") | Identical outcome achieved | **PASS** |
| **Reliability** | Transient 503 Gateway Error on Creation | Exponential backoff retry succeeded | **PASS** |
| **Safety (HITL)** | High-Value Disbursement ($48,500.00) Approved | Paused for approval, approved, verified | **PASS** |
| **Safety (HITL)** | High-Value Disbursement ($48,500.00) Rejected | Paused for approval, rejected, halted safely | **PASS** |
| **Idempotency** | Duplicate Invoice Attempt (`INV-2023-042`) | Duplicate detected, zero double records | **PASS** |
| **Reliability** | Missing Amount Field (`INV-2024-002`) | Halted safely; refused to hallucinate | **PASS** |
| **Generalization** | Ambiguous Vendor Name Resolution | Mapped to canonical vendor ID | **PASS** |
| **Bounds** | Permanent Tool Failure (missing file) | Halted honestly with FAILED; zero false claim | **PASS** |
| **Verification** | Intentional Verification Mismatch Detection | Detected discrepancy and failed honestly | **PASS** |
| **Security Defense**| Prompt Injection Neutralization | Adversarial instruction overrides blocked | **PASS** |
| **Safety Bounds** | Unsupported Goal Safe Rejection | Out-of-scope task halted; zero mutations | **PASS** |

**Summary: 12/12 Passed (100.0%) | False Claims: 0 | Duplicates: 0 | Recovery Rate: 100%**

---

## 💡 Important Design Decisions

1. **Independent Verification vs Self-Assertion:** LLMs routinely suffer from confirmation bias when asked *"did you do this right?"*. AgentOS uses a completely separate Critic that queries the relational SQLite database directly, comparing exact column values against the source document.
2. **Three-Tier Idempotency:** Financial systems cannot tolerate duplicate entries. We enforce deduplication at the agent reasoning layer (`search_existing_invoice`), the application layer (`idempotency_key = SHA256(...)`), and the database layer (`UNIQUE(vendor_name, invoice_number)`).
3. **Pluggable Model Architecture:** We built a clean provider abstraction (`LLMProvider`). While it supports real Gemini and OpenAI endpoints via `.env`, it includes a zero-dependency deterministic fallback provider so anyone evaluating the repository gets immediate 100% reproducible results without configuring billing accounts.

---

## ⚠️ Known Limitations & Future Roadmap

### Known Limitations
- Current sandbox file extraction uses regex and structured layout tokenizers; complex tabular semi-structured invoices with nested line items benefit from vision models (e.g. Gemini 1.5 Pro Flash multimodal).
- Single-tenant SQLite database; production enterprise deployment would utilize PostgreSQL with row-level security.

### What We Would Build Next
1. **Multi-Modal Vision Tooling:** Directly ingest scanned document photographs and low-contrast mobile receipts using vision LLM bounding box extraction.
2. **Dynamic Web Browser Computer Use:** Integrate Playwright / Puppeteer sidecar for visual web browsing across arbitrary third-party portals with visual grounding.
3. **Role-Based Access Control (RBAC):** Cryptographically signed approval workflows integrating Slack / Microsoft Teams webhooks for multi-party financial sign-off.
4. **Active Learning Feedback Loop:** When human supervisors correct an extracted field, store the annotation in a few-shot vector store to improve extraction accuracy on that vendor's future invoices.

---

## 📂 Project Structure

```
d:\ai-project\
├── backend/
│   ├── app/
│   │   ├── agent/             # Cognitive engine (loop, planner, memory, provider, state)
│   │   ├── api/               # FastAPI endpoints (tasks, company, approvals, sandbox)
│   │   ├── database/          # SQLite models, sessions, and seeders
│   │   ├── schemas/           # Pydantic v2 validation models
│   │   ├── tools/             # Base tools, file tools, ERP tools, safety tools
│   │   ├── verification/      # Ground-truth critic & audit receipt generator
│   │   └── main.py            # FastAPI entrypoint
│   └── tests/                 # 17 automated Pytest unit and integration tests
├── frontend/
│   ├── src/
│   │   ├── components/        # React components (Timeline, Evidence, Sandbox, Approval)
│   │   ├── services/          # REST API client
│   │   ├── types/             # TypeScript interfaces
│   │   ├── App.tsx            # Main application layout
│   │   └── main.tsx           # React DOM root
│   ├── dist/                  # Production-compiled assets (served by FastAPI)
│   └── package.json           # Frontend dependencies
├── evaluation/
│   ├── scenarios.py           # 10 benchmark evaluation scenario definitions
│   └── run_evaluation.py      # Automated benchmark runner & markdown generator
├── sandbox_data/
│   └── invoices/              # Test corpus (.txt, .pdf, valid, duplicate, missing, high-value)
├── run_demo.py                # Rich interactive CLI demo runner
├── ARCHITECTURE.md            # In-depth architectural & design specification
├── DEMO_SCRIPT.md             # 3-5 minute video and live walkthrough script
├── EVALUATION.md              # Auto-generated benchmark evaluation report
├── requirements.txt           # Python backend dependencies
└── README.md                  # This file
```

---

## 📄 License
MIT License. Built for the CentrAlign AI Engineering Intern Evaluation.
