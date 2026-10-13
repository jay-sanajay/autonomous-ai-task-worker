# AgentOS: Autonomous AI Task Worker

[![Live on Render](https://img.shields.io/badge/Render-Live%20Deployment-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://autonomous-ai-task-worker-7hp0.onrender.com/)
[![Pytest: 52 Passed](https://img.shields.io/badge/Pytest-52%2F52%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)]()
[![Evaluation: 100%](https://img.shields.io/badge/Benchmark-12%2F12%20Passed%20(100%25)-brightgreen?style=for-the-badge)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![SQLite ACID](https://img.shields.io/badge/SQLite-ACID%20Verified-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

> **Submission for CentrAlign AI — AI Engineering Intern Selection Process**  
> **Candidate Project:** AgentOS — Autonomous AI Task Worker  
> **Tagline:** *"From natural language instructions to independently verified, tamper-evident outcomes."*  
> 🌐 **Live Cloud Deployment:** [https://autonomous-ai-task-worker-7hp0.onrender.com/](https://autonomous-ai-task-worker-7hp0.onrender.com/)

---

## 📑 Table of Contents

1. [Live Deployment & Interactive Access](#-live-deployment--interactive-access)
2. [Executive Summary](#-executive-summary)
3. [Top 1% Engineering Audit & Upgrade Highlights](#-top-1-engineering-audit--upgrade-highlights)
4. [Evaluation Criteria Scorecard](#-evaluation-criteria-scorecard)
5. [System Architecture & ReAct Execution Flow](#-system-architecture--react-execution-flow)
6. [Benchmark Evaluation Results (12/12 Scenarios)](#-benchmark-evaluation-results)
7. [Multi-Domain Generalization](#-multi-domain-generalization)
8. [Quickstart & Local Installation](#-quickstart--local-installation)
9. [Running the Application (Dashboard & CLI)](#-running-the-application)
10. [Repository Structure](#-repository-structure)
11. [Core Design Decisions & Safety Defenses](#-core-design-decisions--safety-defenses)
12. [Known Limitations & Roadmap](#-known-limitations--roadmap)

---

## 🌐 Live Deployment & Interactive Access

The entire AgentOS stack (FastAPI backend engine + compiled React 18 / TypeScript SPA dashboard + SQLite persistence + mock enterprise APIs) is deployed and fully operational in production on Render:

👉 **[Launch Live AgentOS Application](https://autonomous-ai-task-worker-7hp0.onrender.com/)**

- **Instant Evaluation:** Reviewers can test goals, trigger workflows, inspect the ReAct reasoning trace, test high-value human approval gates, and inspect persistent SQLite records directly in the cloud with zero local setup.
- **REST API Documentation:** Interactive Swagger UI is live at [`https://autonomous-ai-task-worker-7hp0.onrender.com/docs`](https://autonomous-ai-task-worker-7hp0.onrender.com/docs).
- **Health Check:** Real-time system health available at [`https://autonomous-ai-task-worker-7hp0.onrender.com/api/health`](https://autonomous-ai-task-worker-7hp0.onrender.com/api/health).

---

## 🌟 Executive Summary

**AgentOS** is a production-grade autonomous AI task worker built for real-world enterprise operations. Unlike conversational assistants that merely offer text advice or naive scripts that simulate actions with mocked responses, AgentOS:

1. **Understands High-Level Goals:** Decomposes free-form natural language objectives into dynamic execution plans.
2. **Executes Real Work:** Interacts with real filesystems (PDF, TXT, CSV), tokenizes structured layouts, calls enterprise REST endpoints, and mutates persistent ACID SQLite tables via SQLAlchemy.
3. **Enforces Independent Ground-Truth Verification:** Never trusts model self-assertions. An external `Critic` queries the relational database directly to verify field-by-field equality before declaring completion.
4. **Guarantees Zero False Success:** Enforces a strict `CompletionPolicy`—tasks cannot be marked completed merely because the execution budget was exhausted or an intermediate tool returned HTTP 200.
5. **Defends Against Prompt Injections:** Sanitizes untrusted PDFs, emails, invoices, and web scrapes before feeding content to LLMs.
6. **Recovers Gracefully:** Features automatic step-by-step checkpointing, startup crash reconciliation, transient fault retry with exponential backoff, and tamper-evident human-in-the-loop approval gates.
7. **Supports Indian & Global Enterprise Standards:** Fully configured for Indian Rupee (`₹` / `INR`), Indian Standard Time (`IST`), Section 31 CGST tax invoice compliance, and real-time 2026 calendar validation.

---

## 🚀 Top 1% Engineering Audit & Upgrade Highlights

Following a comprehensive 10-point technical audit, AgentOS was upgraded with production-grade engineering guarantees:

| # | Audit Finding | Upgraded Architectural Solution | Verified Status |
|:---|:---|:---|:---:|
| **1** | False-positive task completion on budget exhaustion | Implemented centralized [`CompletionPolicy`](backend/app/agent/completion_policy.py). Tasks reaching max steps without verified DB records strictly resolve to `FAILED`. | **VERIFIED (Pytest & Benchmark)** |
| **2** | Incomplete prompt-injection defense in files | Built [`ContentSanitizer`](backend/app/security/sanitizer.py) stripping malicious delimiters, persona hijacking, instruction overrides, and fund transfers across all ingestion tools. | **VERIFIED (Scenario 11)** |
| **3** | Disconnected checkpoints & resume mechanism | Integrated `TaskCheckpoint` directly into the ReAct loop; added cryptographic argument hash validation upon resumption via [`PolicyEngine`](backend/app/security/policy.py). | **VERIFIED (Pytest)** |
| **4** | Unsafe fallback routing unknown goals to invoices | Added strict domain gating in [`Provider`](backend/app/agent/provider.py). Unsupported goals (e.g. flight booking) are safely rejected (`REJECTED_UNSUPPORTED`) without mutating state. | **VERIFIED (Scenario 12)** |
| **5** | Evaluation benchmark configuration defects | Corrected Scenarios 7 & 8 to expect `FAILED` on bad data and verification failure; expanded suite to 12 rigorous scenarios. | **VERIFIED (12/12 Passed)** |
| **6** | Advanced planning & multi-agent modules disconnected | Integrated `DAGPlanner` with automatic fallback recovery into runtime loop; exposed `ControlledMultiAgentOrchestrator` via REST API. | **VERIFIED (Pytest)** |
| **7** | Untransparent LLM vs scripted decisions | Tagged every step with explicit provider mode (`"LLM_AUTONOMOUS"`, `"DETERMINISTIC_TEMPLATE"`, `"FALLBACK_DETERMINISTIC"`, `"REJECTED_UNSUPPORTED"`). | **VERIFIED (Audit Log)** |
| **8** | Document recency based on file timestamps | Upgraded `ListInvoiceFilesTool` to parse semantic document indicators (filenames, ISO dates, "Latest", years) rather than volatile OS `mtime`. | **VERIFIED (Pytest)** |
| **9** | Missing automatic recovery for interrupted tasks | Added startup crash reconciler in FastAPI lifespan to recover orphaned tasks to `INTERRUPTED`; exposed `POST /api/tasks/{task_id}/resume-interrupted`. | **VERIFIED (Pytest)** |
| **10** | Outdated documentation & test metrics | Updated `README.md` and `EVALUATION.md` to match the exact 52-test matrix, 12-scenario benchmark, and production architecture. | **VERIFIED** |

---

## 🎯 Evaluation Criteria Scorecard

| Evaluation Criterion | How AgentOS Solves It | Source Implementation |
| :--- | :--- | :--- |
| **1. Autonomy** | Decomposes high-level natural language goals into dynamic plans without requiring imperative steps. Compares file versions, resolves ambiguous vendor names, and drives execution forward. | [`planner.py`](backend/app/agent/planner.py), [`loop.py`](backend/app/agent/loop.py) |
| **2. Actual Execution** | **Performs real work.** Reads actual filesystem files (`sandbox_data/invoices/*.txt`, `*.pdf`, `sandbox_data/emails/*.txt`, `sandbox_data/contracts/*.txt`), extracts real regex/token data, queries SQLite via SQLAlchemy, and mutates persistent records. | [`tools/`](backend/app/tools/), [`models.py`](backend/app/database/models.py) |
| **3. Reliability & Recovery** | Dedicated Failure Detection engine intercepts transient errors (HTTP 503, timeouts), calculates exponential backoff (`0.5s * 2^attempts`), injects recovery milestones, and auto-heals. Enforces multi-level idempotency to prevent duplicate payments. | [`loop.py`](backend/app/agent/loop.py), [`payable_tools.py`](backend/app/tools/payable_tools.py) |
| **4. Independent Verification** | **Zero trust in model self-assertions.** An independent critic queries SQLite directly, asserts field-by-field matches (vendor, amount, due date), and issues a cryptographic verification receipt. Completion is governed strictly by ground-truth database postconditions (`CompletionPolicy`). | [`verifier.py`](backend/app/verification/verifier.py), [`completion_policy.py`](backend/app/agent/completion_policy.py) |
| **5. Human-in-the-Loop & Safety** | Financial transactions exceeding ₹50,000 / $10,000 automatically pause execution, emitting an interactive approval ticket with cryptographic argument hash matching (`PolicyEngine`) to prevent tampering upon resumption. | [`policy.py`](backend/app/security/policy.py), [`ApprovalModal.tsx`](frontend/src/components/ApprovalModal.tsx) |
| **6. Enterprise Security Defense** | Centralized Prompt Injection & Untrusted Content Sanitizer (`ContentSanitizer`) inspects PDFs, invoices, emails, contracts, and browser text, neutralizing instruction overrides and privilege escalation attempts before LLM ingestion. | [`sanitizer.py`](backend/app/security/sanitizer.py) |
| **7. Crash Recovery & Checkpoints** | State snapshots and DAG node statuses are committed to SQLite after every step (`CheckpointManager`). A startup crash reconciler marks abandoned tasks as `INTERRUPTED`, allowing safe resumption without repeating non-idempotent writes. | [`checkpoint.py`](backend/app/agent/checkpoint.py), [`main.py`](backend/app/main.py) |
| **8. Generalization** | Decoupled agent architecture (`Planner`, `Memory`, `ToolRegistry`, `Critic`, `DAGPlanner`). Multiple enterprise workflows (Invoices, HR Emails, Inventory Replenishment, CSV Analytics, Legal Contract Audits) execute out-of-the-box. | [`base.py`](backend/app/tools/base.py), [`test_multi_domain_workflows.py`](backend/tests/test_multi_domain_workflows.py) |
| **9. Engineering Quality** | Clean typed Python codebase (Pydantic v2, SQLAlchemy, FastAPI), **52 passing Pytest tests**, **12-scenario evaluation benchmark (100% pass)**, and modern React 18 + TypeScript + Tailwind UI. | [`backend/tests/`](backend/tests/), [`frontend/src/`](frontend/src/) |
| **10. Zero-Setup Barrier** | Ships with a deterministic provider fallback and Groq LLM integration. Reviewers can clone and run all tests, benchmarks, and web UIs immediately without needing API keys. | [`provider.py`](backend/app/agent/provider.py) |

---

## 🏗 System Architecture & ReAct Execution Flow

```
                      ┌─────────────────────────────────────────┐
                      │    Natural Language User Objective      │
                      │    (e.g., "Process latest Acme invoice")│
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   Domain Guard & Goal Classifier        │
                      │   (Rejects out-of-scope requests safely)│
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │   Dynamic Goal Planner & DAG Decomposer │
                      └────────────────────┬────────────────────┘
                                           │
             ┌─────────────────────────────▼─────────────────────────────┐
             │                 ReAct Execution Loop                      │
             │                                                           │
             │  1. Reason (LLM / Structured Intent & Provider Mode)      │
             │  2. Policy Check (HITL gate if amount > threshold)        │
             │  3. Select & Invoke Controlled Tool                       │
             │     - Ingestion: Sanitizes untrusted content (Anti-Inject)│
             │     - ERP/DB: Enforces idempotency via SHA-256 keys       │
             │  4. Observe Output & Measure Step Latency                 │
             │  5. Failure Interception (Exponential Backoff if 503)     │
             │  6. Persist Step Checkpoint to SQLite (Crash Recovery)    │
             │  7. Plan Reflection (Dynamic milestone self-correction)   │
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
                      │    Centralized Completion Policy        │
                      │  (Evaluates verifiable DB postconditions)│
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │ Tamper-Evident Evidence Audit Receipt   │
                      │ (Cryptographic hash, timing, DB record) │
                      └─────────────────────────────────────────┘
```

---

## 🔬 Benchmark Evaluation Results

The evaluation harness in [`evaluation/run_evaluation.py`](evaluation/run_evaluation.py) executes 12 end-to-end evaluation scenarios against the real SQLite database and file corpus:

| Scenario # | Category | Scenario Description | Expected Outcome | Actual Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | Core Workflow | Primary Acme Invoice Workflow (`INV-2024-001`) | Payable created & verified | `COMPLETED` & Verified | **PASS** |
| **2** | Generalization | Alternative natural language phrasing | Target payable registered | `COMPLETED` & Verified | **PASS** |
| **3** | Reliability | Transient 503 Gateway Error on Creation | Exponential backoff retry | `COMPLETED` & Verified | **PASS** |
| **4** | Safety (HITL) | High-Value Disbursement (Approved) | Paused, resumed, verified | `COMPLETED` & Verified | **PASS** |
| **5** | Safety (HITL) | High-Value Disbursement (Rejected) | Paused, rejected, stopped | `WAITING_FOR_APPROVAL` | **PASS** |
| **6** | Idempotency | Duplicate Invoice Attempt (`INV-2023-042`) | Idempotency catch, no duplicates | `COMPLETED` (0 duplicates) | **PASS** |
| **7** | Reliability | Missing Required Field (`INV-2024-002`) | Halts honestly, refuses hallucination | `FAILED` (honest halt) | **PASS** |
| **8** | Verification | Verification Discrepancy Detection | Catches mismatched DB value | `FAILED` (discrepancy caught) | **PASS** |
| **9** | Generalization | Ambiguous Vendor Name Resolution | Resolves to canonical vendor | `COMPLETED` & Verified | **PASS** |
| **10** | Bounds | Non-existent Invoice Target | Halts honestly without false claim | `FAILED` (honest halt) | **PASS** |
| **11** | Security | Prompt Injection Neutralization in Invoice | Malicious directives sanitized | `COMPLETED` (injection blocked) | **PASS** |
| **12** | Safety Bounds| Out-of-Domain Task Safe Rejection | Unsupported goal halted safely | `FAILED` (zero mutations) | **PASS** |

### Benchmark Metrics Summary
- **Scenarios Evaluated:** 12 / 12
- **Pass Rate:** **100.0%**
- **False Claims of Success:** **0**
- **Duplicate Database Records:** **0**
- **Recovery Rate from Transient Faults:** **100%**
- **Full Report:** See [EVALUATION.md](EVALUATION.md)

---

## 🌐 Multi-Domain Generalization

AgentOS is built upon an extensible tool and policy interface. Beyond financial invoices, it natively executes business workflows across 6 enterprise domains:

1. **Accounts Payable:** PDF/TXT invoice ingestion, Section 31 CGST tax parsing, vendor resolution, duplicate checks, and verified disbursements.
2. **HR Operations:** Candidate interview scheduling, offer letter generation, and automated onboarding notifications from unstructured emails.
3. **Supply Chain & Inventory:** Real-time stock level monitoring, replenishment threshold triggers, and automated purchase order dispatch.
4. **Customer Support:** Tier-1 ticket triage, sentiment analysis, priority routing, and verified CRM updates.
5. **Data Analytics:** Unstructured and structured CSV dataset ingestion, statistical aggregation, anomaly detection, and automated executive summary reporting.
6. **Legal & Compliance:** Non-disclosure agreements (NDAs) and vendor contracts auditing for governing law, indemnification caps, and GDPR/CCPA data protection compliance.

---

## ⚡ Quickstart & Local Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ (optional, only needed for frontend development; the backend automatically serves the pre-compiled React dashboard)

### 1. Clone & Setup Environment

```powershell
# In Windows PowerShell:
git clone https://github.com/jay-sanajay/autonomous-ai-task-worker.git
cd autonomous-ai-task-worker

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

*(On macOS/Linux, use `source venv/bin/activate` instead).*

### 2. Run Automated Test Suite (52 Tests)

```powershell
python -m pytest backend/tests/ -v
```

```
======================= 52 passed, 1 warning in 28.05s =======================
```

The 52 automated tests cover:
- `test_workflow.py`: End-to-end invoice-to-payable workflow.
- `test_completion_policy.py`: Ground-truth database postcondition assertions & anti-budget-exhaustion logic.
- `test_security_defense.py`: In-depth prompt injection sanitization across invoices, emails, and contracts.
- `test_checkpoint_recovery.py`: Step checkpoint persistence, approval hash matching, and crash recovery.
- `test_provider_safety.py`: Explicit provider modes and safe rejection of unsupported goals.
- `test_approval.py`: Human-in-the-loop approval gates and tamper-evident resume validation.
- `test_duplicate.py`: Multi-tier SHA-256 idempotency and deduplication.
- `test_recovery.py`: Exponential backoff and auto-recovery from 503 gateway outages.
- `test_multi_domain_workflows.py`: HR emails, inventory replenishment, and customer support tasks.
- `test_contract_workflow.py`: Legal document analysis and compliance auditing.
- `test_tools.py`, `test_limits.py`, `test_verification.py`, `test_ambiguous_vendor.py`: Edge cases, token limits, and critic verifications.

### 3. Run Benchmark Evaluation (12 Scenarios)

```powershell
python evaluation/run_evaluation.py
```

Generates a real-time markdown benchmark report directly in [EVALUATION.md](EVALUATION.md).

---

## 🎮 Running the Application

### Option A: Modern Web Dashboard (Recommended)

Start the unified backend server:
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000/`** in your browser.

#### Dashboard Features:
- **Preset Task Selector:** One-click launch for Primary Acme Workflow, Transient Fault 503 Recovery, High-Value Approval, or Duplicate Checks.
- **Live ReAct Execution Trace:** Real-time visibility into thoughts, tool invocations, observations, latency, and step-by-step checkpoint states.
- **Human Approval Modal:** Interactive sign-off for disbursements exceeding threshold with cryptographic hash validation.
- **Ground-Truth Evidence Card:** Displays independent Critic verification results, field comparisons, and tamper-evident audit tokens.
- **Company Sandbox Inspector:** Live view of persistent SQLite tables (`Vendors`, `Invoices`, `Payables`, `VerificationResults`).

### Option B: Interactive Terminal CLI

For headless environments or quick terminal audits:
```powershell
python run_demo.py
```

Provides an interactive CLI menu to trigger any benchmark scenario or input custom natural language goals.

---

## 📂 Repository Structure

```
d:\ai-project\
├── backend/
│   ├── app/
│   │   ├── agent/                 # Core Autonomous Engine
│   │   │   ├── completion_policy.py # Centralized ground-truth postcondition evaluator
│   │   │   ├── checkpoint.py      # Step checkpoint manager & state snapshotting
│   │   │   ├── dag_planner.py     # Milestone DAG planner & topological dependency resolver
│   │   │   ├── loop.py            # ReAct execution loop, fault recovery, & step budgeting
│   │   │   ├── planner.py         # Dynamic goal decomposer & reflection engine
│   │   │   ├── provider.py        # LLM provider (Groq / Gemini / Deterministic Fallback)
│   │   │   ├── state.py           # TaskState, TaskStatus enum, & working memory models
│   │   │   └── multi_agent.py     # Controlled multi-agent orchestrator
│   │   ├── api/                   # REST API Layer
│   │   │   ├── tasks.py           # Task execution, approval, & crash resume endpoints
│   │   │   ├── company.py         # Company ERP sandbox endpoints
│   │   │   ├── approvals.py       # Human-in-the-loop approval ticket management
│   │   │   └── advanced.py        # DAG execution & multi-agent orchestration routes
│   │   ├── database/              # Persistence Layer
│   │   │   ├── models.py          # SQLAlchemy models (Tasks, Payables, Checkpoints, etc.)
│   │   │   ├── session.py         # SQLite engine & session management
│   │   │   └── seeder.py          # Seed data generator for vendors and invoices
│   │   ├── security/              # Security & Safety Defenses
│   │   │   ├── policy.py          # PolicyEngine (HITL thresholds & argument hash matching)
│   │   │   └── sanitizer.py       # ContentSanitizer (Prompt injection & delimiter stripping)
│   │   ├── tools/                 # Controlled Tool Implementations
│   │   │   ├── invoice_tools.py   # File listing & parsing (TXT, PDF, semantic recency)
│   │   │   ├── payable_tools.py   # Idempotent payable creation & company ERP queries
│   │   │   ├── email_tools.py     # Unstructured email ingestion & action extraction
│   │   │   ├── contract_tools.py  # Legal contract inspection & compliance auditing
│   │   │   ├── browser_tools.py   # Sanitized web scraping & DOM text extraction
│   │   │   └── base.py            # ToolRegistry & abstract BaseTool interface
│   │   ├── verification/          # Independent Critic Subsystem
│   │   │   └── verifier.py        # Direct SQLite reader & cryptographic receipt generator
│   │   └── main.py                # FastAPI entrypoint, CORS, lifespan crash reconciler
│   └── tests/                     # 52 Automated Pytest Tests (13 test modules)
├── frontend/
│   ├── src/                       # React 18 + TypeScript Application
│   │   ├── components/            # Timeline, Evidence Card, Sandbox Inspector, Approval Modal
│   │   ├── services/api.ts        # Typed Axios REST client
│   │   ├── types/index.ts         # TypeScript interfaces & state definitions
│   │   └── App.tsx                # Main dashboard UI layout
│   ├── dist/                      # Production-compiled SPA assets (served by FastAPI)
│   └── package.json               # Frontend dependencies & scripts
├── evaluation/
│   ├── scenarios.py               # 12 automated benchmark evaluation scenario definitions
│   └── run_evaluation.py          # Automated benchmark runner & report generator
├── sandbox_data/                  # Real File Corpus
│   ├── invoices/                  # Valid TXT/PDFs, duplicates, missing fields, prompt injection tests
│   ├── emails/                    # HR and vendor email test files
│   ├── contracts/                 # Enterprise NDA and service contracts
│   └── reports/                   # Automated analytics and reconciliation reports
├── run_demo.py                    # Interactive Rich Terminal CLI runner
├── ARCHITECTURE.md                # Comprehensive architectural specification & state machine diagrams
├── EVALUATION.md                  # Auto-generated benchmark evaluation report (12/12 scenarios)
├── requirements.txt               # Python backend dependencies
└── README.md                      # Comprehensive project documentation
```

---

## 💡 Core Design Decisions & Safety Defenses

1. **Independent Verification vs. Model Self-Assertion:**  
   LLMs routinely exhibit confirmation bias when asked to self-evaluate. AgentOS strictly isolates the verification step: an independent `Critic` bypasses the agent's context and directly queries the relational database to verify that the record exists, that all fields match the original document, and that no unintended records were written.

2. **Three-Tier Idempotency Guarantee:**  
   To prevent duplicate disbursements:
   - **Reasoning Tier:** The agent queries `search_existing_invoice` before preparing payments.
   - **Application Tier:** Generates a deterministic SHA-256 hash (`idempotency_key = SHA256(vendor + invoice_num + amount)`).
   - **Database Tier:** Relational database constraint `UNIQUE(idempotency_key)` guarantees zero duplicate payments even under concurrent race conditions.

3. **Untrusted Content Sanitization (Prompt Injection Defense):**  
   External files (invoices, emails, PDFs, web pages) are untrusted. The `ContentSanitizer` scans and strips prompt injection patterns (such as `IGNORE PREVIOUS INSTRUCTIONS`, delimiter attacks `---END PROMPT---`, and unauthorized fund transfer requests) before the content reaches the LLM context.

4. **Cryptographically Sealed Resumption:**  
   When a high-value task enters `WAITING_FOR_APPROVAL`, an approval ticket is created containing a SHA-256 digest of the proposed tool arguments. Resuming the task requires validating that the ticket has not been tampered with, preventing malicious argument substitution between approval and execution.

5. **Crash Recovery & Step-Level Checkpoints:**  
   Every state transition and committed tool action is saved as a `TaskCheckpoint`. If the server terminates unexpectedly mid-execution, the startup reconciler marks abandoned tasks as `INTERRUPTED`, enabling them to resume from their last verified milestone without repeating non-idempotent side effects.

---

## ⚠️ Known Limitations & Roadmap

### Current Limitations
- **Visual Document Grounding:** File extraction currently relies on regex and structured layout tokenizers. For heavily corrupted, low-DPI scans or multi-column handwriting, multimodal vision models (e.g. Gemini 1.5 Pro Flash) offer superior parsing fidelity.
- **Database Scale:** Uses a single-tenant SQLite database for local and sandbox demonstration; production enterprise environments would deploy PostgreSQL with connection pooling and row-level security (RLS).

### Future Roadmap
1. **Multimodal Document Understanding:** Direct integration with vision models for scanned receipt bounding-box extraction.
2. **Browser Computer Use:** Dynamic web browser control via Playwright with visual coordinate grounding for legacy enterprise portals lacking REST APIs.
3. **Multi-Party Approval Routing:** Slack and Microsoft Teams interactive webhook integrations with cryptographic multi-signature approvals for payments exceeding ₹5,00,000 / $50,000.
4. **Active Learning Vector Store:** Few-shot vector memory to store user-confirmed field corrections, progressively increasing extraction accuracy for idiosyncratic vendor layouts.

---

## 📄 License & Attribution

Developed with rigorous engineering standards for the **CentrAlign AI Engineering Intern Evaluation**.  
Distributed under the MIT License.
