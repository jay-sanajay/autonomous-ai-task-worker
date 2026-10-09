"""
Autonomous Task Worker - Core Agent Execution Loop.
Implements the full Plan-Reason-Act-Observe-Recover-Verify lifecycle.
"""

from __future__ import annotations
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from centra_worker.models.task import (
    TaskRequest,
    TaskResult,
    TaskStatus,
    StepRecord,
    EvidenceReceipt
)
from centra_worker.models.plan import ExecutionPlan, PlanStepStatus
from centra_worker.models.memory import WorkingMemory
from centra_worker.models.approval import ApprovalRequest
from centra_worker.engine.planner import GoalPlanner
from centra_worker.engine.memory import MemoryManager
from centra_worker.engine.failure_handler import FailureHandler
from centra_worker.engine.approval_guard import ApprovalGuard
from centra_worker.engine.verifier import OutcomeVerifier
from centra_worker.tools.registry import ToolRegistry, default_registry
from centra_worker.llm.base import BaseLLMProvider, AgentDecision
from centra_worker.llm import get_llm_provider
from simulated_company.erp_server import erp_db


class AutonomousAgent:
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        auto_approve_high_risk: bool = False,
        max_steps: int = 15,
        step_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.llm = llm_provider or get_llm_provider()
        self.registry = tool_registry or default_registry
        self.planner = GoalPlanner()
        self.failure_handler = FailureHandler()
        self.approval_guard = ApprovalGuard(auto_approve_high_risk=auto_approve_high_risk)
        self.verifier = OutcomeVerifier()
        self.max_steps = max_steps
        self.step_callback = step_callback

        # Active state
        self.task_id: str = ""
        self.plan: Optional[ExecutionPlan] = None
        self.memory_manager = MemoryManager()
        self.history: List[StepRecord] = []
        self.status = TaskStatus.PENDING
        self.pending_approval: Optional[ApprovalRequest] = None

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        if self.step_callback:
            try:
                self.step_callback({"type": event_type, "timestamp": time.time(), **data})
            except Exception:
                pass

    def run(self, request: TaskRequest) -> TaskResult:
        """
        Execute the autonomous agent loop for the given natural language goal.
        """
        start_time = time.time()
        self.task_id = request.session_id or f"TASK-{uuid.uuid4().hex[:8].upper()}"
        self.status = TaskStatus.PLANNING
        self.approval_guard.auto_approve_high_risk = request.auto_approve_high_risk

        if request.simulate_fault:
            erp_db.force_transient_error = True

        self.emit_event("task_started", {"task_id": self.task_id, "goal": request.goal})

        # 1. Goal decomposition into dynamic plan
        self.plan = self.planner.create_initial_plan(request.goal)
        self.emit_event("plan_created", {"plan": self.plan.model_dump()})

        self.status = TaskStatus.RUNNING
        step_num = 0

        while step_num < self.max_steps:
            step_num += 1

            # Prepare state representation for LLM
            plan_summary = "\n".join(
                [f"[{s.status.value}] Step {s.step_id}: {s.title} - {s.description}" for s in self.plan.steps]
            )
            history_dicts = [h.model_dump() for h in self.history]
            schemas = self.registry.get_schemas()

            # 2. ReAct Decision: Reason and select next action
            decision: AgentDecision = self.llm.decide_next_action(
                goal=request.goal,
                plan_summary=plan_summary,
                working_memory=self.memory_manager.memory.entities,
                step_history=history_dicts,
                tools_schema=schemas
            )

            self.emit_event("agent_thought", {
                "step": step_num,
                "thought": decision.thought,
                "tool_name": decision.tool_name,
                "tool_input": decision.tool_input
            })

            # Check if task is finished
            if decision.is_finished:
                self.status = TaskStatus.COMPLETED
                self.emit_event("task_completed", {"summary": decision.final_summary})
                break

            # 3. Tool Preparation & Safety / Risk Gate
            tool = self.registry.get(decision.tool_name) if decision.tool_name else None
            if not tool:
                record = StepRecord(
                    step_number=step_num,
                    thought=decision.thought,
                    tool_name=decision.tool_name,
                    status="FAILED",
                    error_message=f"Tool '{decision.tool_name}' not found."
                )
                self.history.append(record)
                continue

            # Check Human-in-the-Loop gating
            requires_approval, app_req = self.approval_guard.check_tool_call(tool, decision.tool_input or {})
            if requires_approval and app_req:
                self.status = TaskStatus.WAITING_FOR_APPROVAL
                self.pending_approval = app_req
                self.emit_event("approval_required", {"approval": app_req.model_dump()})

                # Record step waiting for approval
                record = StepRecord(
                    step_number=step_num,
                    thought=decision.thought,
                    tool_name=tool.name,
                    tool_input=decision.tool_input,
                    status="WAITING_APPROVAL",
                    error_message=f"Action paused: {app_req.risk_reason}"
                )
                self.history.append(record)

                # Return early with WAITING_FOR_APPROVAL status
                return TaskResult(
                    task_id=self.task_id,
                    goal=request.goal,
                    status=self.status,
                    summary="Execution paused: high-risk operation requires human approval.",
                    steps_executed=step_num,
                    step_history=self.history,
                    extracted_data=self.memory_manager.memory.entities,
                    approval_required=True,
                    pending_approval=app_req.model_dump(),
                    total_time_seconds=round(time.time() - start_time, 2)
                )

            # 4. Tool Execution
            t_exec_start = time.time()
            tool_output = self.registry.execute(decision.tool_name, decision.tool_input or {})
            exec_duration_ms = round((time.time() - t_exec_start) * 1000, 2)

            # 5. Failure Detection & Autonomous Self-Correction
            step_status = "SUCCESS"
            error_msg = None

            if self.failure_handler.is_failure(tool_output):
                recovery = self.failure_handler.decide_recovery(decision.tool_name, decision.tool_input or {}, tool_output)
                step_status = "FAILED"
                error_msg = str(tool_output.get("error") or tool_output.get("reason"))

                self.emit_event("failure_detected", {
                    "tool": decision.tool_name,
                    "error": error_msg,
                    "recovery_plan": recovery
                })

                if recovery["action"] == "RETRY_WITH_BACKOFF":
                    step_status = "RETRYING"
                    time.sleep(recovery.get("delay_seconds", 0.5))
                    # Insert recovery step in plan
                    self.planner.insert_recovery_step(self.plan, "Transient Error Retry", decision.tool_name)
                    # Retry call
                    t_exec_start2 = time.time()
                    tool_output = self.registry.execute(decision.tool_name, decision.tool_input or {})
                    exec_duration_ms += round((time.time() - t_exec_start2) * 1000, 2)
                    if not self.failure_handler.is_failure(tool_output):
                        step_status = "RECOVERED"
                        error_msg = None

                elif recovery["action"] == "SWITCH_TO_ALTERNATIVE_TOOL":
                    # Mark working memory to use browser portal
                    self.memory_manager.memory.set("fallback_to_browser", True, source="failure_handler")
                    self.planner.insert_recovery_step(self.plan, "Switch to Browser Portal", "browser_navigate")

            # 6. Update Working Memory & Extract Entities
            self.memory_manager.process_observation(decision.tool_name, decision.tool_input or {}, tool_output)

            # Record step execution
            record = StepRecord(
                step_number=step_num,
                thought=decision.thought,
                tool_name=decision.tool_name,
                tool_input=decision.tool_input,
                tool_output=tool_output,
                status=step_status,
                error_message=error_msg,
                latency_ms=exec_duration_ms
            )
            self.history.append(record)

            self.emit_event("step_completed", {
                "step_number": step_num,
                "tool_name": decision.tool_name,
                "status": step_status,
                "output_snippet": str(tool_output)[:200]
            })

            # Advance current plan step
            self.plan.mark_step_completed(f"Completed {decision.tool_name} with status {step_status}")

        total_time = round(time.time() - start_time, 2)

        # 7. Outcome Verification (Critic)
        evidence = None
        extracted = self.memory_manager.memory.entities.get("extracted_invoice", {})
        if extracted.get("invoice_number") and extracted.get("amount") and extracted.get("due_date"):
            evidence = self.verifier.verify_invoice_completion(
                invoice_number=extracted["invoice_number"],
                expected_amount=extracted["amount"],
                expected_due_date=extracted["due_date"],
                vendor_name=extracted.get("vendor_name")
            )

        summary_text = (
            f"Successfully completed task autonomously in {step_num} steps ({total_time}s). "
            f"Processed invoice {extracted.get('invoice_number')} for {extracted.get('vendor_name')}. "
            f"Verification: {'CONFIRMED' if (evidence and evidence.verified) else 'UNVERIFIED'}."
        )

        return TaskResult(
            task_id=self.task_id,
            goal=request.goal,
            status=self.status if self.status != TaskStatus.RUNNING else TaskStatus.COMPLETED,
            summary=summary_text,
            steps_executed=step_num,
            step_history=self.history,
            extracted_data=self.memory_manager.memory.entities,
            evidence=evidence,
            approval_required=False,
            total_time_seconds=total_time
        )

    def resume_with_approval(self, approval_id: str, approved: bool, approver: str = "Manager", feedback: Optional[str] = None) -> TaskResult:
        """
        Resume execution after human approval decision.
        """
        if not self.pending_approval or self.pending_approval.approval_id != approval_id:
            raise ValueError(f"No active pending approval with ID {approval_id}")

        if approved:
            self.approval_guard.approve(approval_id, approver=approver, feedback=feedback)
            # Re-execute task with auto-approval flag enabled for this execution
            req = TaskRequest(
                goal=f"Resume approved task {self.task_id}",
                auto_approve_high_risk=True,
                session_id=self.task_id
            )
            return self.run(req)
        else:
            self.approval_guard.reject(approval_id, approver=approver, feedback=feedback)
            self.status = TaskStatus.CANCELLED
            return TaskResult(
                task_id=self.task_id,
                goal="Resumed task",
                status=TaskStatus.CANCELLED,
                summary=f"Task cancelled by human reviewer ({approver}): {feedback or 'Disapproved'}",
                steps_executed=len(self.history),
                step_history=self.history,
                extracted_data=self.memory_manager.memory.entities,
                approval_required=False,
                total_time_seconds=0.0
            )
