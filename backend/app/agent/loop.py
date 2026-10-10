"""
AgentOS - Master ReAct Tool-Calling Execution Loop.
Implements the 11-stage autonomous agent lifecycle with controlled tools,
bounded steps, exponential backoff retries, and independent verification.
"""

from __future__ import annotations
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database.models import AgentTask, TaskStep, ApprovalRequest, VerificationResult
from backend.app.agent.state import TaskStatus, StepStatus, PlanStep
from backend.app.agent.memory import TaskMemory
from backend.app.agent.planner import GoalPlanner
from backend.app.agent.provider import BaseLLMProvider, get_llm_provider, AgentStepDecision
from backend.app.tools.registry import ToolRegistry, default_tool_registry
from backend.app.tools.payable_tools import set_simulated_transient_failure


class AgentExecutionEngine:
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        max_steps: int = 15,
        max_retries: int = 3,
        step_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.registry = tool_registry or default_tool_registry
        self.llm = llm_provider or get_llm_provider()
        self.planner = GoalPlanner()
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.step_callback = step_callback

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        if self.step_callback:
            try:
                self.step_callback({"type": event_type, "timestamp": time.time(), **data})
            except Exception:
                pass

    def run(
        self,
        db_session: Session,
        goal: str,
        task_id: Optional[str] = None,
        auto_approve_high_risk: bool = False,
        simulate_fault: bool = False
    ) -> AgentTask:
        """Execute full autonomous agent loop against database and sandbox."""
        if simulate_fault:
            set_simulated_transient_failure(True)

        task_id = task_id or f"task-{uuid.uuid4().hex[:8]}"

        # Initialize or retrieve Task record
        task = db_session.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            initial_plan = self.planner.create_initial_plan(goal)
            plan_json = json.dumps([p.model_dump() for p in initial_plan])
            task = AgentTask(
                id=task_id,
                goal=goal,
                status=TaskStatus.PLANNING.value,
                current_plan=plan_json,
                working_memory=json.dumps({"task_id": task_id, "original_goal": goal}),
                extracted_data="{}",
                steps_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)

        memory = TaskMemory(task_id=task_id, original_goal=goal)
        try:
            loaded_mem = json.loads(task.working_memory)
            memory = TaskMemory(**loaded_mem)
        except Exception:
            pass

        self.emit_event("task_started", {"task_id": task_id, "goal": goal})

        task.status = TaskStatus.RUNNING.value
        db_session.commit()

        step_counter = task.steps_count

        while step_counter < self.max_steps:
            step_counter += 1
            task.steps_count = step_counter

            # Load current step history from DB
            history_records = db_session.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_number).all()
            history_dicts = [
                {
                    "step_number": h.step_number,
                    "thought": h.thought,
                    "tool_name": h.tool_name,
                    "status": h.status,
                    "tool_output": json.loads(h.tool_output or "{}"),
                    "error_message": h.error_message
                }
                for h in history_records
            ]

            plan_summary = task.current_plan
            schemas = self.registry.get_schemas()

            # 1. Decision: LLM proposed action
            decision: AgentStepDecision = self.llm.decide_next_step(
                goal=goal,
                plan_summary=plan_summary,
                working_memory=memory.to_dict(),
                step_history=history_dicts,
                tools_schema=schemas
            )

            self.emit_event("agent_thought", {
                "step": step_counter,
                "thought": decision.thought,
                "tool_name": decision.tool_name,
                "tool_input": decision.tool_input
            })

            # Check for completion
            if decision.is_finished:
                task.status = TaskStatus.COMPLETED.value
                task.final_summary = decision.final_summary or "Task finished successfully."
                db_session.commit()
                self.emit_event("task_completed", {"summary": task.final_summary})
                break

            tool_name = decision.tool_name
            tool_input = decision.tool_input or {}

            # 2. Check Human-in-the-Loop Approval Gating
            if decision.requires_approval and not auto_approve_high_risk:
                # Execute request_approval tool
                app_res = self.registry.execute("request_approval", db_session, tool_input)
                task.status = TaskStatus.WAITING_FOR_APPROVAL.value

                # Record step
                step = TaskStep(
                    task_id=task_id,
                    step_number=step_counter,
                    thought=decision.thought,
                    tool_name=tool_name,
                    tool_input=json.dumps(tool_input),
                    tool_output=json.dumps(app_res.to_dict()),
                    status=StepStatus.WAITING_APPROVAL.value,
                    error_message=f"High risk operation paused: {tool_input.get('risk_reason')}",
                    latency_ms=app_res.execution_duration_ms,
                    created_at=datetime.now(timezone.utc)
                )
                db_session.add(step)
                db_session.commit()

                self.emit_event("approval_required", app_res.data)
                return task

            # 3. Controlled Tool Execution
            t_start = time.time()
            tool_res = self.registry.execute(tool_name, db_session, tool_input)
            latency_ms = tool_res.execution_duration_ms

            step_status = StepStatus.SUCCESS.value
            err_msg = None

            # 4. Failure Detection & Retry with Backoff
            if not tool_res.success:
                err_msg = tool_res.error
                step_status = StepStatus.FAILED.value

                self.emit_event("tool_failure", {
                    "tool": tool_name,
                    "error": err_msg,
                    "retryable": tool_res.retryable
                })

                if tool_res.retryable:
                    curr_retries = memory.retry_counts.get(tool_name, 0)
                    if curr_retries < self.max_retries:
                        memory.retry_counts[tool_name] = curr_retries + 1
                        backoff = 0.5 * (2 ** curr_retries)
                        time.sleep(backoff)
                        step_status = StepStatus.RETRYING.value

                        # Retry execution
                        tool_res = self.registry.execute(tool_name, db_session, tool_input)
                        if tool_res.success:
                            step_status = StepStatus.RECOVERED.value
                            err_msg = None

            # 5. Working Memory Update
            self._update_working_memory(memory, tool_name, tool_input, tool_res)
            task.working_memory = json.dumps(memory.to_dict())
            if memory.extracted_event:
                task.extracted_data = json.dumps(memory.extracted_event)
            elif memory.extracted_fields:
                task.extracted_data = json.dumps(memory.extracted_fields)
            elif memory.csv_analysis:
                task.extracted_data = json.dumps(memory.csv_analysis)
            elif memory.inventory_audit:
                task.extracted_data = json.dumps(memory.inventory_audit)

            # Record step in database
            step = TaskStep(
                task_id=task_id,
                step_number=step_counter,
                thought=decision.thought,
                tool_name=tool_name,
                tool_input=json.dumps(tool_input),
                tool_output=json.dumps(tool_res.to_dict()),
                status=step_status,
                error_message=err_msg,
                latency_ms=latency_ms,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(step)
            db_session.commit()

            self.emit_event("step_completed", {
                "step_number": step_counter,
                "tool_name": tool_name,
                "status": step_status,
                "output": tool_res.to_dict()
            })

            # Check if verification tool passed
            if tool_name in ("verify_payable", "verify_task_item"):
                v_data = tool_res.data or {}
                if tool_res.success and v_data.get("verified"):
                    task.status = TaskStatus.VERIFYING.value
                    existing_v = db_session.query(VerificationResult).filter(VerificationResult.task_id == task_id).first()
                    if not existing_v:
                        v_rec = VerificationResult(
                            task_id=task_id,
                            payable_id=v_data.get("payable_id"),
                            task_item_id=v_data.get("task_item_id"),
                            verified=True,
                            verification_token=v_data.get("verification_token"),
                            field_comparisons=json.dumps(v_data.get("field_comparisons") or {}),
                            audit_notes=v_data.get("audit_notes") or "Ground-truth verified against SQLite database ledger.",
                            created_at=datetime.now(timezone.utc)
                        )
                        db_session.add(v_rec)
                    db_session.commit()

        if task.status not in (TaskStatus.COMPLETED.value, TaskStatus.WAITING_FOR_APPROVAL.value):
            task.status = TaskStatus.COMPLETED.value
            db_session.commit()

        return task

    def _update_working_memory(self, memory: TaskMemory, tool_name: str, tool_input: Dict[str, Any], tool_res: Any):
        if not tool_res.success and not tool_res.data:
            return

        data = tool_res.data or {}

        # 1. Invoices
        if tool_name == "list_invoice_files":
            files = data.get("files", [])
            memory.discovered_files = files
            memory.add_note(f"Discovered {len(files)} invoice files in repository.")

        elif tool_name == "read_invoice":
            memory.target_invoice_file = tool_input.get("file_path")
            memory.add_note(f"Read invoice file: {tool_input.get('file_path')}")

        elif tool_name == "extract_invoice_fields":
            fields = data.get("extracted_fields", {})
            memory.extracted_fields = fields
            memory.add_note(
                f"Extracted Invoice #{fields.get('invoice_number')} | "
                f"Amount: ${fields.get('amount')} | Vendor: {fields.get('vendor_name')} | Due: {fields.get('due_date')}"
            )

        elif tool_name == "search_vendor":
            memory.matched_vendor = data
            memory.add_note(f"Matched Vendor: {data.get('name')} (Code: {data.get('vendor_code')})")

        elif tool_name == "search_existing_invoice":
            memory.existing_invoice_record = data
            memory.add_note(f"Duplicate Check: exists={data.get('exists')}")

        elif tool_name == "create_payable":
            memory.created_payable = data
            memory.add_note(f"Created Payable Record ID: {data.get('payable_id')}")

        elif tool_name == "verify_payable":
            memory.verification_details = data
            memory.add_note(f"Verification: verified={data.get('verified')}")

        # 2. Email & Task Management
        elif tool_name == "list_emails":
            emails = data.get("emails", [])
            memory.discovered_emails = emails
            memory.add_note(f"Discovered {len(emails)} emails in inbox.")

        elif tool_name == "read_email":
            memory.target_email_file = tool_input.get("file_path")
            memory.add_note(f"Read email message: {tool_input.get('file_path')}")

        elif tool_name == "extract_email_details":
            ev = data.get("extracted_event", {})
            memory.extracted_event = ev
            memory.add_note(f"Extracted Interview Event: '{ev.get('title')}' on {ev.get('due_date')} (Link: {ev.get('meeting_link')})")

        elif tool_name == "create_task_item":
            memory.created_task_item = data
            memory.add_note(f"Created Task Item #{data.get('task_item_id')}: '{data.get('title')}'")

        elif tool_name == "verify_task_item":
            memory.verified_task_item = data
            memory.add_note(f"Task Item Verification: verified={data.get('verified')}")

        # 3. CSV Analysis & Reports
        elif tool_name == "list_csv_files":
            files = data.get("files", [])
            memory.discovered_csv_files = files
            memory.add_note(f"Discovered {len(files)} CSV datasets in repository.")

        elif tool_name == "inspect_csv":
            memory.csv_inspection = data
            memory.add_note(f"Inspected CSV: {data.get('row_count')} rows, columns: {data.get('columns')}")

        elif tool_name == "analyze_csv":
            memory.csv_analysis = data
            memory.add_note(f"Analyzed CSV: Total Revenue = ${data.get('total_revenue'):,.2f}")

        elif tool_name == "generate_report":
            memory.generated_report = data
            memory.add_note(f"Generated Report: {data.get('file_path')}")

        # 4. Support Tickets
        elif tool_name == "list_support_tickets":
            memory.support_tickets = data
            memory.add_note(f"Fetched {data.get('count')} support tickets")

        elif tool_name == "update_support_ticket":
            memory.updated_ticket = data
            memory.add_note(f"Updated Ticket {data.get('ticket_code')} -> {data.get('status')}")

        # 5. Inventory
        elif tool_name == "list_inventory":
            memory.inventory_audit = data
            memory.add_note(f"Audited {data.get('total_items')} inventory products")

        elif tool_name == "create_purchase_request":
            memory.created_purchase_request = data
            memory.add_note(f"Created Purchase Request: {data.get('request_code')}")

        elif tool_name == "create_payable":
            memory.created_payable = data
            memory.add_note(f"Created Payable Record ID: {data.get('payable_id')}")

        elif tool_name == "verify_payable":
            memory.verification_details = data
            memory.add_note(f"Verification: verified={data.get('verified')}")

    def resume_task(self, db_session: Session, task_id: str, approved: bool, approver: str = "Finance Director", feedback: Optional[str] = None) -> AgentTask:
        """Resume task after human approval or cancellation."""
        task = db_session.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        app_req = db_session.query(ApprovalRequest).filter(
            ApprovalRequest.task_id == task_id,
            ApprovalRequest.status == "PENDING"
        ).first()

        if app_req:
            app_req.status = "APPROVED" if approved else "REJECTED"
            app_req.approver = approver
            app_req.feedback = feedback
            app_req.resolved_at = datetime.now(timezone.utc)
            db_session.commit()

        if not approved:
            task.status = TaskStatus.CANCELLED.value
            task.final_summary = f"Task cancelled by reviewer ({approver}): {feedback or 'Disapproved'}"
            db_session.commit()
            return task

        # If approved, update memory to bypass approval check on resume
        memory = TaskMemory(task_id=task_id, original_goal=task.goal)
        try:
            memory = TaskMemory(**json.loads(task.working_memory))
        except Exception:
            pass
        setattr(memory, "approval_resolved", True)
        task.working_memory = json.dumps({**memory.to_dict(), "approval_resolved": True})
        task.status = TaskStatus.RUNNING.value
        db_session.commit()

        # Continue execution
        return self.run(db_session, goal=task.goal, task_id=task_id, auto_approve_high_risk=True)
