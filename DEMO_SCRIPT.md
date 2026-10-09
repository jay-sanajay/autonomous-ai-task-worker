# AgentOS: Autonomous AI Task Worker — Demo Video & Presentation Script

> **Evaluation Presentation Guide for CentrAlign AI Engineering Intern Role**  
> **Duration:** 3–5 Minutes  
> **Tagline:** *"From instructions to verified outcomes."*

---

## 🎯 Executive Overview & Script Setup

This script guides you through recording an end-to-end video demo or conducting a live technical walkthrough of **AgentOS**. It is structured to directly hit all 8 evaluation criteria: **Autonomy, Execution, Reliability, Verification, Generalization, Engineering Quality, Product Thinking, and Technical Understanding.**

### Quick Pre-Demo Verification
Open two terminal windows in PowerShell:
- **Terminal 1 (Backend & API):**
  ```powershell
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Terminal 2 (Frontend Dashboard or Interactive CLI):**
  ```powershell
  cd frontend; npm run dev
  # Dashboard opens at: http://localhost:5173
  ```
  *Alternative CLI Demo:*
  ```powershell
  python run_demo.py
  ```

---

## 🎬 Section-by-Section Walkthrough (3–5 Minutes)

### 0:00 – 0:35 | Introduction & Problem Statement
- **Visual:** Open browser to `http://localhost:5173`. Show the dark-mode AgentOS interface with real-time metrics cards, task launcher, execution timeline, and live SQLite database tables.
- **Narrator Voiceover:**
  > "Hi everyone, I'm excited to present **AgentOS**, an autonomous AI employee built for the CentrAlign AI Engineering Intern challenge.
  >
  > Most LLM demonstrations are either static chatbots or brittle scripts that simply claim 'task completed' without touching a real system of record.
  >
  > We built AgentOS around a core philosophy: **From instructions to verified outcomes.** When given an end-goal in natural language, AgentOS decomposes the objective into dynamic milestones, operates real tools across file systems and company databases, self-corrects from transient failures, respects human-in-the-loop safety boundaries, and **independently verifies** that the underlying SQLite database was updated accurately."

---

### 0:35 – 1:35 | Act 1: The Core Mission (Primary Acme Workflow)
- **Action:**
  1. Click the preset: **"Primary Acme Workflow"** in the UI (or press `[1]` in CLI).
  2. The goal loads: *"Find the latest invoice from Acme Technologies, extract the invoice number, amount, due date, and vendor, create a payable record in the company system, verify that the record was saved correctly, and summarize the result."*
  3. Click **"Execute Objective"**.
- **Visual:**
  - Watch the **Dynamic Execution Plan** render milestones.
  - Watch each step stream in real time:
    - Step 1: `list_invoice_files` (discovers all candidate invoices in `sandbox_data/invoices/`).
    - Step 2: `read_invoice` (inspects both `INV-2023-042` and `INV-2024-001`, dynamically selects the latest 2024 invoice).
    - Step 3: `extract_invoice_fields` (extracts `$8,450.00`, due date `2024-10-31`, invoice `INV-2024-001`, PO `PO-ACME-902`).
    - Step 4: `search_vendor` (resolves "Acme Technologies" to `Acme Technologies Inc.` with ID `1`).
    - Step 5: `search_existing_invoice` (checks for duplicates).
    - Step 6: `create_payable` (writes the payable record to SQLite).
    - Step 7: `verify_payable` (critic queries SQLite directly, asserts field matches).
- **Narrator Voiceover:**
  > "Notice what's happening here: AgentOS wasn't given imperative code. It reasoned over the invoices directory, compared timestamps, parsed both TXT and binary PDF formats, extracted key financial attributes, and verified vendor identity.
  >
  > Most importantly, look at the **Independent Ground-Truth Evidence Card**. The agent doesn't just say 'Done'—our critic queried the SQLite database directly, verified the primary key, checked all 4 field comparisons, and generated an SHA-256 audit token. If we switch to the **Company Sandbox Tab**, we can see the exact record in the database."

---

### 1:35 – 2:30 | Act 2: Reliability & Self-Correction (Transient 503 Fault Recovery)
- **Action:**
  1. Toggle on **"Simulate 503 Gateway Fault"** checkbox.
  2. Select preset **"503 Fault & Auto-Recovery"**.
  3. Click **"Execute Objective"** (or choose scenario `[2]` in CLI).
- **Visual:**
  - Step 1 executes.
  - On the first call to `create_payable`, a **`503 Service Unavailable: Simulated transient gateway outage`** occurs.
  - Step shows a red badge: `FAILED (Transient)`.
  - Self-correction engine immediately kicks in: calculates exponential backoff (`0.5s * 2^attempts`), inserts a retry step into the active plan without failing the task.
  - Attempt 2 succeeds: status changes to `RECOVERED` (green).
  - Task proceeds to independent SQLite verification and completes with 100% data integrity.
- **Narrator Voiceover:**
  > "Real enterprise systems fail unpredictably. Here, we injected a transient 503 Gateway outage.
  >
  > Instead of crashing or asking the user to start over, the AgentOS Failure Detection engine recognized this as a retryable transient error. It computed exponential backoff, injected a recovery milestone, and automatically succeeded on retry. Real execution with real resilience."

---

### 2:30 – 3:15 | Act 3: Human-in-the-Loop Safety Gate (Financial Risk Threshold)
- **Action:**
  1. Select preset **"High-Value ($48k) HITL Sign-off"**.
  2. Uncheck **"Auto-Approve High Value"**.
  3. Click **"Execute Objective"** (or scenario `[3]` in CLI).
- **Visual:**
  - Agent processes `INV-2024-099` for **$48,500.00**.
  - Execution immediately pauses in state: `WAITING_FOR_APPROVAL`.
  - An amber **Human-in-the-Loop Approval Modal** pops up with:
    - Risk Level: `HIGH`
    - Reason: `Amount $48,500.00 exceeds $10,000.00 approval threshold`
    - Action: `create_payable`
    - Payload Diff: vendor, amount, due date.
  - Type an audit note: *"Authorized under Q4 Infrastructure Compute Budget"*, and click **"Approve Action"**.
  - Execution resumes instantly: creates the record, critic verifies SQLite, and final receipt logs the approver's name and notes.
- **Narrator Voiceover:**
  > "Autonomy without safety is dangerous in enterprise finance. When AgentOS encountered this $48,500 invoice, it automatically recognized that disbursements over $10,000 require human authorization.
  >
  > It halted before writing to the database, emitted an interactive approval ticket, and waited. Once I authorized it as Finance Director, it seamlessly resumed, logged the audit note, and completed the task."

---

### 3:15 – 3:55 | Act 4: Hallucination Prevention & Database Idempotency
- **Action:**
  1. Select preset **"Duplicate Invoice Check"** (`INV-2023-042`).
  2. Click **"Execute Objective"**.
  - **Visual:** The agent inspects `INV-2023-042`, searches the database, finds that this invoice already exists, and halts gracefully: *"Invoice INV-2023-042 already registered. Aborting creation to prevent duplicate disbursement."*
  3. Select preset **"Missing Required Fields"** (`INV-2024-002`).
  2. Click **"Execute Objective"**.
  - **Visual:** The agent parses the document, discovers the amount field is absent, refuses to hallucinate an arbitrary number, and safely marks the task failed with an actionable error.
- **Narrator Voiceover:**
  > "Notice how AgentOS avoids common LLM pitfalls. When given a duplicate invoice, it asserts database idempotency and stops before double-paying a vendor. And when given an invoice missing critical fields, it refuses to hallucinate numbers."

---

### 3:55 – 4:30 | Act 5: Automated Evaluation Benchmark & Architecture
- **Action:**
  - Switch to terminal and run:
    ```powershell
    python evaluation/run_evaluation.py
    ```
- **Visual:**
  - Rich benchmark table runs 10 evaluation scenarios across 5 categories:
    - Happy path & alternative phrasing
    - Fault recovery & retry backoff
    - Human approval gating & rejection handling
    - Idempotency & duplicate prevention
    - Missing data & ambiguous vendor resolution
  - Final Result: **100.0% Pass Rate (10/10)**, 0 False Claims, 0 Duplicates.
- **Narrator Voiceover:**
  > "We verified AgentOS against an automated benchmark suite of 10 rigorous evaluation scenarios. It achieved a 100% scenario pass rate with zero false claims and zero duplicate records.
  >
  > In addition, our test suite has 17 unit and integration tests passing in Pytest.
  >
  > Under the hood, AgentOS is built on a clean, modular Python and FastAPI backend, SQLAlchemy with SQLite, and a modern React + TypeScript dashboard. It ships with a deterministic provider fallback so anyone on the team can clone the repository and run all tests and demos out of the box with zero external API dependencies."

---

### 4:30 – 4:45 | Conclusion
- **Visual:** Return to the live dashboard showing completed metrics and verified receipts.
- **Narrator Voiceover:**
  > "AgentOS represents what a true autonomous AI worker should be: goal-driven, self-healing, safe, and verifiable. Thank you for your time, and I look forward to discussing the architecture with the team!"

---

## 📋 Checklist for the Reviewer
- [x] Clone repo and run `pip install -r requirements.txt`
- [x] Run `python -m pytest backend/tests/ -v` (17/17 tests pass)
- [x] Run `python evaluation/run_evaluation.py` (10/10 scenarios pass)
- [x] Run `python run_demo.py` (CLI interactive walkthrough)
- [x] Run backend + frontend for GUI interactive experience
