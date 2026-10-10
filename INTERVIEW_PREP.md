# AgentOS: Technical Interview Defense & Architectural Deep-Dive Guide

> **Preparation for CentrAlign Technical Discussion & Code Review**  
> *"Be prepared to explain, debug, or modify your implementation during the technical discussion."*

---

## 1. Top Interview Questions & Model Answers

### Q1: "Why did you build a custom execution loop instead of using LangChain, CrewAI, or AutoGen?"
**Answer:**
> "Frameworks like LangChain or CrewAI are helpful for rapid prototyping, but in enterprise engineering they introduce heavy abstraction layers, opaque prompt injection chains, and hidden retry logic that make debugging and strict determinism difficult.
>
> In AgentOS, we built a transparent, modular ReAct loop using pure Python, FastAPI, and SQLAlchemy. This gives us three critical production advantages:
> 1. **Complete Control Over Execution Bounds:** We enforce a strict step budget (`max_steps=15`), custom exponential backoff delays, and state machine persistence directly in SQLite.
> 2. **Decoupled Verification Critic:** Most frameworks let the agent evaluate itself. We decouple execution from verification: an independent critic queries SQLite directly with zero LLM hallucination risk.
> 3. **Deterministic Zero-Barrier Portability:** By controlling the loop, we built a deterministic fallback provider that lets reviewers evaluate 10 benchmark scenarios offline with 100% reproducibility in sub-second time."

---

### Q2: "How does the system guarantee that an invoice will not be double-paid if a network timeout occurs midway?"
**Answer:**
> "Financial double-payment is a critical real-world failure mode. We enforce a **three-tier idempotency architecture**:
> 1. **Agent Level:** The execution loop calls `search_existing_invoice` before attempting creation.
> 2. **Application Level:** We compute a deterministic `idempotency_key = SHA-256(vendor_name + invoice_number)`.
> 3. **Database Level:** The SQLite schema enforces a composite unique constraint: `UNIQUE(vendor_name, invoice_number)`. Even if an agent crashes and replays the step, the database transaction rolls back with an integrity error, preventing duplicate insertion."

---

### Q3: "What is the difference between the agent's internal reflection and the Independent Ground-Truth Critic?"
**Answer:**
> "Agent reflection is an LLM chain-of-thought step where the model inspects its previous tool output. However, LLMs suffer from severe confirmation bias: when asked *'did you enter the invoice correctly?'*, models frequently answer *'Yes, I verified that the invoice was entered'*, even when the database call failed or wasn't made!
>
> In contrast, our `IndependentVerificationCritic` does not use LLM text generation at all. It uses direct Python/SQL code to query `agentos.db`, asserts field-by-field matches against the source document (tolerance `< 0.01` for amounts), and issues a cryptographic verification hash (`VERIFIED-...`). The task cannot transition to `COMPLETED` unless this independent Critic returns `verified=True`."

---

### Q4: "How does the failure detection engine distinguish between a transient error and a permanent failure?"
**Answer:**
> "Tools return a typed `ToolResult` object with a `retryable: bool` flag:
> - **Transient Errors (e.g. HTTP 503, network timeouts, database lock):** Marked as `retryable=True`. The engine intercepts this, computes exponential backoff jitter (`0.5s * 2^attempts`), logs the step as `RETRYING`, and injects a retry milestone into the active plan. If it succeeds, the step transitions to `RECOVERED`.
> - **Permanent Errors (e.g. missing required field, file not found):** Marked as `retryable=False`. The engine recognizes that retrying won't change the outcome. Rather than hallucinating missing numbers or entering an infinite loop, it halts execution safely with an informative diagnostic error."

---

### Q5: "If we asked you to add a new workflow right now (e.g. HR employee onboarding), how would you modify the system?"
**Answer:**
> "The AgentOS cognitive loop is completely decoupled from any single domain. To support HR onboarding:
> 1. Create a new tool inheriting from `ControlledBaseTool`:
>    ```python
>    class CreateEmployeeRecordTool(ControlledBaseTool):
>        name = "create_employee_record"
>        description = "Enter new employee details into HRIS database"
>        ...
>    ```
> 2. Register it with `default_tool_registry.register(CreateEmployeeRecordTool())`.
> 3. Provide the natural language goal: *'Read Jane Doe's signed offer letter, extract start date and salary, and create her employee profile in HRIS.'*
> 4. The `GoalPlanner` decomposes the objective, reads the file, extracts fields, and executes the new tool without changing a single line of the ReAct execution engine!"

---

### Q6: "Why did you use SQLite instead of in-memory dictionaries or PostgreSQL?"
**Answer:**
> "Using in-memory Python dictionaries (`records = {}`) is a common pitfall in prototypes because it mocks away real database behavior—there are no ACID transactions, no unique constraints, and state disappears on process restart.
> 
> We chose SQLite with SQLAlchemy because it provides a genuine relational database with foreign keys (`PRAGMA foreign_keys=ON`) and unique constraints, while maintaining zero external setup friction for the reviewer. Furthermore, because we used SQLAlchemy ORM, switching to PostgreSQL in production is a single connection-string change in `.env` (`DATABASE_URL=postgresql://...`)."

---

### Q7: "How does the Human-in-the-Loop (HITL) safety gate work under the hood?"
**Answer:**
> "Before any write tool (like `create_payable`) is executed, the engine runs an enterprise risk policy:
> - If `amount > $10,000.00 USD` and `auto_approve_high_risk` is `False`, the agent loop halts immediately.
> - It records an `ApprovalRequest` in SQLite with risk level `HIGH`, the exact payload diff, and the financial reasoning.
> - The task status transitions to `WAITING_FOR_APPROVAL`.
> - In the Web Dashboard, an amber modal renders the approval diff and prompts the supervisor. In the CLI, an interactive confirmation prompt appears.
> - When the user approves or rejects, the endpoint `/api/tasks/{id}/approve` records the approver's name and notes, and the execution loop safely resumes or cancels."

---

### Q8: "What was a non-obvious engineering challenge you faced, and how did you resolve it?"
**Answer:**
> "A subtle challenge occurred with Pydantic v2 validation during agent resumption:
> Pydantic v2 models default to `extra='forbid'`. When resuming a task from human approval, we needed to pass dynamic state (`approval_resolved: bool`) through the working memory model. Initially, setting dynamic attributes raised a `ValueError: 'TaskMemory' object has no field 'approval_resolved'`.
>
> We resolved this cleanly by explicitly declaring the typed field on `TaskMemory` with proper defaults and serialization helpers, ensuring that both database JSON fields and Pydantic schemas stay in lockstep without sacrificing type safety."

---

## 2. Live Code Modification Checklist (During Discussion)

If the interviewer asks you to make a live modification during the interview:

| Scenario Requested | File to Edit | Key Change |
| :--- | :--- | :--- |
| **Change the approval threshold from $10k to $5k** | `backend/app/agent/loop.py` | Change `if amount > 10000.0:` to `if amount > 5000.0:` |
| **Add a new field to invoice extraction (e.g. Tax)** | `backend/app/tools/invoice_tools.py` | Add regex pattern for `TAX` or `Tax Amount` in `ExtractInvoiceFieldsTool` |
| **Add a new vendor to the sandbox** | `backend/app/database/seed.py` | Add a new `Vendor(...)` entry in `seed_database()` |
| **Increase the step budget from 15 to 25** | `backend/app/agent/loop.py` | Change `max_steps=15` in `AgentExecutionEngine.__init__` |

---

## 3. Quick Verification Commands Cheat Sheet

```powershell
# 1. Start server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 2. Run all tests
python -m pytest backend/tests/ -v

# 3. Run benchmark evaluation
python evaluation/run_evaluation.py

# 4. Run CLI walkthrough
python run_demo.py

# 5. Check Git history
git log -n 5 --oneline
```
