# CentraWorker Architecture & Design Specification

CentraWorker is an autonomous AI worker prototype designed for enterprise task execution. It bridges unstructured natural language objectives and structured computer environments (file systems, REST APIs, internal enterprise ERP applications, and web portals).

---

## 1. Design Philosophy

Traditional automation (RPA, rigid scripts) breaks whenever a selector shifts or a document format alters slightly. Naive LLM wrappers, conversely, suffer from hallucination and "simulated autonomy" without verifying that actions succeeded in the underlying system of record.

CentraWorker is built on four core tenets:
1. **Goal-Driven Autonomy:** The user specifies the *outcome* ("Find the latest invoice from Company X, extract amount and due date, enter it into our internal system, and tell me once it is done"), not the step-by-step imperative clicks.
2. **ReAct Execution Loop:** The agent alternates continuously between reasoning, taking action via typed tools, and updating working memory from observations.
3. **Resilience & Self-Correction:** Transient errors (e.g., HTTP 503, gateway timeouts) trigger exponential backoff retries. System degradation triggers alternative execution routes (e.g., falling back to browser web portal forms when a direct API is unavailable).
4. **Independent Ground-Truth Verification:** An action is never assumed to have succeeded simply because an LLM emitted a confirmation. The agent invokes an independent verification critic that queries the target system's ground truth database and validates attributes before marking a task complete.

```
                           ┌────────────────────────────┐
                           │   Natural Language Goal    │
                           └─────────────┬──────────────┘
                                         ▼
                           ┌────────────────────────────┐
                           │    Goal Decomposition      │
                           │     & Dynamic Planner      │
                           └─────────────┬──────────────┘
                                         │
                 ┌───────────────────────▼──────────────────────┐
                 │             ReAct Execution Loop             │
                 │                                              │
                 │  1. Reason (LLM Chain of Thought)            │
                 │  2. Safety & Risk Gate (HITL if > $10,000)   │
                 │  3. Execute Tool (File, API, Browser)        │
                 │  4. Observe Output & Detect Failures         │
                 │  5. Self-Correction / Retry with Backoff     │
                 │  6. Working Memory Entity Extraction         │
                 │  7. Dynamic Plan Reflection                  │
                 └───────────────────────┬──────────────────────┘
                                         │
                                         ▼
                           ┌────────────────────────────┐
                           │   Outcome Verification     │
                           │ (Critic asserts ground     │
                           │  truth state in ERP DB)    │
                           └─────────────┬──────────────┘
                                         │
                                         ▼
                           ┌────────────────────────────┐
                           │ Cryptographic Proof &      │
                           │ Execution Evidence Receipt │
                           └────────────────────────────┘
```

---

## 2. Core Subsystems

### A. Dynamic Goal Planner (`centra_worker.engine.planner`)
- Breaks ambiguous natural language tasks into an initial sequence of milestones.
- Dynamically mutates the active plan at runtime: if a step fails or requires retries, recovery steps are inserted on the fly without aborting the overarching mission.

### B. Working Memory & Semantic Store (`centra_worker.engine.memory`)
- Maintains short-term scratchpad notes and a typed entity dictionary.
- Automatically parses incoming observations (e.g. reading invoice files extracts invoice numbers, vendor entities, amounts, due dates, and PO references).
- Passes the cumulative context into subsequent ReAct steps so the agent never "forgets" what it discovered earlier.

### C. Multi-Tool Ecosystem (`centra_worker.tools`)
Each tool implements `BaseTool` with strict parameter validation and self-contained risk assessment:
- **File Tools:** `list_files`, `read_file`, `search_files` (handles multi-file comparison, date parsing, and directory scans).
- **Enterprise API Tools:** `erp_get_vendors`, `erp_get_invoices`, `erp_submit_invoice` (interacts directly with internal accounting systems).
- **Browser Automation Tools:** `browser_navigate`, `browser_fill_form` (inspects DOM, fills input forms, and triggers button submissions).
- **Verification Tools:** `verify_erp_record` (queries system of record to independently confirm record presence and attribute match).

### D. Failure Detection & Self-Correction Engine (`centra_worker.engine.failure_handler`)
Errors are intercepted and classified into:
- **`TRANSIENT_503_OR_NETWORK`**: Applies exponential backoff delay with jitter, records retry attempts, and retries the operation.
- **`ALTERNATIVE_REQUIRED`**: If an endpoint is degraded or max retries are exceeded, the agent dynamically switches execution strategy (e.g., from direct REST API to browser web portal entry).
- **`SCHEMA_VALIDATION`**: Triggers document re-inspection to retrieve missing parameters.

### E. Human-in-the-Loop Safety Gate (`centra_worker.engine.approval_guard`)
- Sensitive tools evaluate arguments before execution.
- If an invoice amount exceeds the enterprise risk threshold ($10,000 USD), the execution loop transitions to `WAITING_FOR_APPROVAL`.
- Emits an `ApprovalRequest` ticket containing risk score, payload diff, and rationale.
- The human reviewer can approve or reject the request via the Web UI Modal or CLI prompt, and the agent resumes or cancels safely.

### F. Independent Ground-Truth Verification (`centra_worker.engine.verifier`)
- Rather than trusting the model's self-generated text, an independent critic queries the underlying ERP ledger:
  - Asserts that the invoice number exists in the database.
  - Asserts that the numerical amount matches the source document (tolerance `< 0.01`).
  - Asserts that the payment due date matches.
- Generates a tamper-evident `EvidenceReceipt` with cryptographic SHA-256 hash, timestamp, and audit trail record.

---

## 3. Generalization & Extensibility

CentraWorker's core agent engine is completely decoupled from any single domain. To support a new enterprise department (e.g. HR onboarding or Legal contract review):
1. Define a new tool inheriting from `BaseTool`:
   ```python
   class HREmployeeStatusTool(BaseTool):
       name = "hr_update_status"
       description = "Update employee onboarding status in Workday"
       ...
   ```
2. Register it with `default_registry.register(HREmployeeStatusTool())`.
3. Provide the natural language task: "Find Jane Doe's signed offer letter, extract the start date, and activate her employee profile."
4. The agent decomposes the goal, locates the file, calls the new tool, verifies the status, and provides the receipt without changing a single line of the agent loop!
