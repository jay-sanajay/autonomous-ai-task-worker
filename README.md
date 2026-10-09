# CentraWorker: Autonomous AI Task Worker

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 14 Passed](https://img.shields.io/badge/Tests-14%20Passed-brightgreen.svg)]()

> **Submission for CentrAlign AI — AI Engineering Intern Role**  
> Problem Statement: **Autonomous AI Task Worker**

CentraWorker is an autonomous, goal-driven AI employee prototype capable of taking a natural language task and autonomously completing it across computer environments (file repositories, REST APIs, enterprise applications, and browser web forms).

---

## 🌟 Key Highlights & Evaluation Criteria Mapping

| Evaluation Criterion | Implementation in CentraWorker |
| :--- | :--- |
| **Autonomy** | Interprets end goals without step-by-step instructions. Breaks requests into dynamic plans, reasons over candidate documents, parses dates, compares version timestamps, and selects tools autonomously. |
| **Execution** | **Performs real work.** Actually inspects file systems, parses raw invoices, invokes internal ERP APIs, automates browser form submissions, and writes records to persistent storage. |
| **Reliability & Failure Recovery** | Features a dedicated **Failure Detection & Self-Correction Engine**. Detects transient HTTP 503 errors and applies exponential backoff retries. Detects API outages and dynamically switches to alternative tools (e.g. Browser Web Portal form). |
| **Verification** | Implements an **Independent Ground-Truth Critic**. Never assumes completion from model text; queries the underlying database to verify existence, numerical amount accuracy, and due date matching. Produces a cryptographic proof receipt. |
| **Human-in-the-Loop (HITL)** | Built-in risk engine. Automatically pauses execution and requests human authorization for high-risk operations (e.g. financial disbursements exceeding $10,000 USD). |
| **Generalization** | Completely decoupled agent engine (`GoalPlanner`, `MemoryManager`, `FailureHandler`, `ToolRegistry`). Easily extends to HR onboarding, contract management, or sales tasks simply by adding typed `BaseTool` classes. |
| **Zero Setup Barrier** | Ships with a pluggable LLM provider system including an intelligent, deterministic offline provider (`SmartMockProvider`). Reviewers can clone and run all scenarios immediately without needing third-party API keys, while OpenAI/Gemini can be activated with a single `.env` setting. |

---

## 🚀 Quickstart & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/centra-worker.git
cd centra-worker

# Install dependencies
pip install -r requirements.txt
```

### 2. Run All Automated Tests (14 Tests)
```bash
python -m pytest tests/ -v
```
All 14 tests verify goal decomposition, file reading, ERP posting, transient error recovery, human-in-the-loop safety gating, browser automation, and ground-truth verification.

---

## 🎮 Running the Demos

CentraWorker provides two interfaces: a **Rich Interactive Terminal CLI** and a **Modern Interactive Web Dashboard**.

### Option A: Interactive CLI Demo (Recommended for quick evaluation)
```bash
python run_demo.py
```
This launches an interactive menu with 5 guided scenarios:
1. **Standard Problem Statement:** `"Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done."`
2. **Reliability & Self-Correction:** Injects a simulated 503 Gateway failure into CentraERP; the agent detects the fault, applies exponential backoff, dynamically inserts a recovery step, and succeeds.
3. **Human-in-the-Loop Approval:** Processes a $52,000 capital equipment invoice for Nexus Technologies; pauses execution, displays risk reasoning, and waits for your interactive approval.
4. **Browser Automation:** Dispatches browser navigation and HTML form submission on the simulated company web portal.
5. **Custom Goal:** Enter your own custom natural language task.

---

### Option B: Modern Interactive Web Dashboard & CentraERP
```bash
python web_app.py
```
Open your browser at:
- **Agent Control Tower Dashboard:** [http://localhost:8000](http://localhost:8000)
- **CentraERP Accounts Payable Portal:** [http://localhost:8000/portal/invoices](http://localhost:8000/portal/invoices)

**Dashboard Features:**
- 1-Click Preset Scenario Chips.
- Live ReAct execution stream showing Agent Reasoning, Tool Invocations, and Observations in real-time.
- Interactive Human-in-the-Loop modal for high-risk approvals with payload inspection.
- Live view of the CentraERP ledger updating dynamically as the agent posts records.
- Verification card displaying the ground-truth receipt with cryptographic validation token.

---

## 🏗️ Architecture Overview

```
d:\ai-project\
├── centra_worker/               # Core Autonomous Agent Package
│   ├── engine/
│   │   ├── agent.py             # ReAct Execution Loop (Plan-Reason-Act-Observe-Verify)
│   │   ├── planner.py           # Goal Decomposition & Dynamic Replanning
│   │   ├── memory.py            # Working Memory & Entity Extractor
│   │   ├── failure_handler.py   # Error Categorization, Backoff & Tool Fallback
│   │   ├── approval_guard.py    # HITL Safety Gating & Risk Thresholds
│   │   └── verifier.py          # Ground-Truth Critic & Verification Receipt
│   ├── tools/
│   │   ├── base.py              # BaseTool Interface with Risk Assessment
│   │   ├── registry.py          # Dynamic Tool Discovery & Safe Execution
│   │   ├── file_tools.py        # File Discovery, Content Reading & Search
│   │   ├── erp_api_tools.py     # CentraERP REST API Integration
│   │   ├── browser_tools.py     # DOM Inspection & Web Form Automation
│   │   └── verification_tools.py# Independent Outcome Verification Tool
│   ├── models/                  # Strict Pydantic Data Contracts
│   │   ├── task.py              # TaskRequest, StepRecord, EvidenceReceipt
│   │   ├── plan.py              # ExecutionPlan, PlanStep
│   │   ├── memory.py            # WorkingMemory, DiscoveredEntity
│   │   └── approval.py          # ApprovalRequest, RiskLevel
│   └── llm/                     # Pluggable Model Providers
│       ├── base.py              # Provider Interface & AgentDecision Schema
│       ├── mock_provider.py     # Deterministic Smart Provider (offline / reproducible)
│       ├── openai_provider.py   # OpenAI GPT-4o / GPT-4o-mini
│       └── gemini_provider.py   # Google Gemini 1.5 / 2.0
├── simulated_company/           # Target Business Environment
│   ├── erp_server.py            # Simulated CentraERP (REST API, DB, Audit Log)
│   ├── web_portal/              # Simulated Corporate HTML Portal
│   └── data_store/files/        # Document Repository (historic & current invoices)
├── frontend/                    # Modern Dashboard UI (HTML, CSS, JS)
├── tests/                       # Complete Automated Test Suite (14 Tests)
├── run_demo.py                  # CLI Demo Runner
└── web_app.py                   # FastAPI Application Server
```

---

## 💡 Important Technical & Design Decisions

### 1. Independent Outcome Verification Critic
- **The Problem:** Many AI agent prototypes report "I entered the invoice" merely because their prompt concluded or a tool returned HTTP 200. If the database failed silently or dropped a field, the human is misled.
- **Our Solution:** A dedicated `OutcomeVerifier` runs after execution. It queries the database independently, tests whether `abs(record.amount - expected.amount) < 0.01`, matches the due date, checks the audit log, and generates a signed `EvidenceReceipt`.

### 2. Multi-Tier Failure Recovery & Tool Fallbacks
- **Transient Failures:** When the ERP returns 503 (simulated server overload), the agent calculates exponential backoff (`0.5 * 2^retry_count`), inserts a dynamic recovery step into the plan, and re-executes.
- **Strategy Fallback:** If the direct API is blocked or degraded, the agent's failure policy switches to browser automation, navigating to the company web portal and submitting the invoice via DOM form elements.

### 3. Human-in-the-Loop (HITL) Safety Gate
- Autonomous systems must not disburse funds or commit irreversible actions without governance.
- Tools declare an `assess_risk(arguments)` method. Any financial transaction over **$10,000 USD** triggers a pause, transitions the agent to `WAITING_FOR_APPROVAL`, and presents the exact payload diff to a human reviewer.

### 4. Pluggable, Zero-Dependency Offline Evaluation
- Evaluators should never have their review blocked by expired API keys or rate limits.
- CentraWorker features a built-in `SmartMockProvider` that demonstrates identical reasoning, self-correction, and tool usage out-of-the-box. To use live OpenAI or Gemini models, simply supply `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env`.

---

## ⚠️ Known Limitations

1. **OCR / Scanned Image Invoices:** The prototype currently parses text and structured digital documents (`.txt`, `.json`, `.csv`). Scanned visual raster images would require an integrated OCR/multimodal vision pipeline (e.g. Gemini 2.0 Flash or Tesseract).
2. **Session Persistence across Restarts:** Active agent memory is maintained in-process per task execution session. For enterprise production, working memory would be persisted to Redis or PostgreSQL.
3. **Complex Multi-Page Web Portals:** The simulated browser tool handles single-page and multi-input forms. Deep SPAs with complex OAuth redirects would benefit from a dedicated Playwright cluster.

---

## 🔮 What We Would Build Next (Future Roadmap)

1. **Multimodal Visual Grounding:** Equip the browser worker with visual coordinate clicking and vision-based DOM understanding for non-standard web interfaces.
2. **Persistent Enterprise Long-Term Memory (RAG):** Index historical company correspondence, PO databases, and vendor agreements into a vector store (Chroma/pgvector) for semantic retrieval.
3. **Collaborative Multi-Agent Hierarchy:** Deploy specialized sub-agents (e.g. `DocumentParserAgent`, `ComplianceAgent`, `ERPDataEntryAgent`) coordinated by an executive orchestrator.
4. **Active Workflow Learning (`/learn`):** Enable the agent to record human feedback or corrections and compile them into reusable execution workflows.

---

## 📋 Assumptions Made

- Documents are located in the company repository (`simulated_company/data_store/files/invoices`).
- Date formats follow standard ISO (`YYYY-MM-DD`) or conventional billing notation.
- Standard corporate approval policy mandates human authorization for transactions exceeding $10,000 USD.
- Company vendors are pre-registered in CentraERP.

---

## 📦 Models, Libraries & Tools Used

- **Runtime & Backend:** Python 3.13, FastAPI, Uvicorn, Pydantic v2
- **Agent Architecture:** ReAct Loop, Custom GoalPlanner, MemoryManager, FailureHandler, OutcomeVerifier
- **Terminal UX:** Rich (color-coded thoughts, live tables, interactive prompts)
- **Web Interface:** Vanilla HTML5/CSS3, JavaScript (Fetch API, live DOM updates)
- **Testing:** Pytest (14 automated unit & integration tests)
- **LLMs Supported:** OpenAI (GPT-4o), Google Gemini (Gemini 1.5/2.0), Deterministic Smart Mock Engine
