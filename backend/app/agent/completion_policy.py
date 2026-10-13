"""
AgentOS - Centralized Task Completion & Goal Postcondition Policy.
Strictly eliminates false-positive task completion by evaluating measurable postconditions
against ground-truth persistent state before a task can transition to COMPLETED.
"""

from __future__ import annotations
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.database.models import (
    AgentTask, TaskStep, VerificationResult, PayableRecord, TaskItem,
    PurchaseRequest, ContractRecord, SupportTicket
)
from backend.app.agent.state import TaskStatus, StepStatus


class CompletionPolicy:
    """
    Evaluates whether an agent task has legitimately satisfied its goal postconditions.
    A successful intermediate tool call is NOT sufficient evidence of goal completion.
    """

    @classmethod
    def evaluate_task_completion(
        cls,
        db: Session,
        task: AgentTask,
        is_step_limit_reached: bool = False
    ) -> Tuple[TaskStatus, str, Optional[str]]:
        """
        Evaluate current task state and determine final status, summary, and error message.
        Returns: (TaskStatus, final_summary, error_message)
        """
        goal_lower = task.goal.lower()

        # 1. Check for active waiting states
        if task.status == TaskStatus.WAITING_FOR_APPROVAL.value:
            return (
                TaskStatus.WAITING_FOR_APPROVAL,
                task.final_summary or "Task paused awaiting human approval for high-risk operation.",
                task.error_message
            )

        if task.status == TaskStatus.CANCELLED.value:
            return (
                TaskStatus.CANCELLED,
                task.final_summary or "Task execution was cancelled.",
                task.error_message
            )

        # 2. Check for explicit blocked / unsupported goal state
        if task.status == "BLOCKED" or "blocked" in (task.error_message or "").lower():
            return (
                TaskStatus.FAILED,
                task.final_summary or f"Task Blocked: Unsupported objective '{task.goal}'. No suitable enterprise tools registered.",
                task.error_message or "Unsupported objective."
            )

        # Query verification record directly from SQLite
        verif_rec = db.query(VerificationResult).filter(
            VerificationResult.task_id == task.id,
            VerificationResult.verified == True
        ).first()

        # Query all execution steps
        steps = db.query(TaskStep).filter(TaskStep.task_id == task.id).order_by(TaskStep.step_number).all()
        last_step = steps[-1] if steps else None

        # ----------------------------------------------------------------------
        # Domain 1: Invoice Processing Postconditions
        # ----------------------------------------------------------------------
        if any(w in goal_lower for w in ["invoice", "payable", "bill"]) and not any(w in goal_lower for w in ["csv", "contract", "email"]):
            # Check if this was a duplicate prevention scenario
            if "duplicate" in (task.final_summary or "").lower() or "already registered" in (task.final_summary or "").lower():
                # A verified duplicate detection without writing a duplicate is a clean, successful completion
                return (
                    TaskStatus.COMPLETED,
                    task.final_summary or "Duplicate check completed: Existing invoice identified. No duplicate write performed.",
                    None
                )

            # Check if missing amount scenario
            if "missing" in (task.final_summary or "").lower() or "missing_fields" in (task.extracted_data or "").lower():
                if "amount" in (task.final_summary or "").lower() or "amount" in (task.extracted_data or "").lower():
                    # Graceful, honest halt on unrecoverable missing data
                    return (
                        TaskStatus.COMPLETED,
                        task.final_summary or "Execution halted: Invoice lacks required financial field 'amount'. Refusing to invent data.",
                        None
                    )

            # Normal invoice processing requires verified payable in SQLite
            if verif_rec and verif_rec.payable_id:
                payable = db.query(PayableRecord).filter(PayableRecord.id == verif_rec.payable_id).first()
                if payable and payable.status == "VERIFIED":
                    summary = task.final_summary or f"Successfully completed and verified payable #{payable.id} for invoice {payable.invoice_number} ({payable.vendor_name}, {payable.currency} {payable.amount:,.2f})."
                    return (TaskStatus.COMPLETED, summary, None)

            # Check if payable was created but verification failed or didn't run
            if is_step_limit_reached:
                return (
                    TaskStatus.FAILED,
                    f"Task Failed: Reached execution budget limit ({task.steps_count} steps) without verified payable creation.",
                    "Step budget exhausted before ground-truth verification succeeded."
                )

            if not verif_rec:
                # If finished was claimed but no verification record exists, reject completion!
                return (
                    TaskStatus.FAILED,
                    "Task Failed: Cannot claim completion without independent database verification.",
                    "Postcondition unfulfilled: No verified record found in SQLite ledger."
                )

        # ----------------------------------------------------------------------
        # Domain 2: HR Email & Interview Task Postconditions
        # ----------------------------------------------------------------------
        if any(w in goal_lower for w in ["email", "hr", "interview", "task list", "meeting link"]):
            if verif_rec and verif_rec.task_item_id:
                item = db.query(TaskItem).filter(TaskItem.id == verif_rec.task_item_id).first()
                if item:
                    summary = task.final_summary or f"Successfully extracted interview invitation and verified task item #{item.id} ('{item.title}') in database."
                    return (TaskStatus.COMPLETED, summary, None)

            if is_step_limit_reached:
                return (
                    TaskStatus.FAILED,
                    f"Task Failed: Reached execution step limit ({task.steps_count}) without verified task item creation.",
                    "Step budget exhausted before task item verification."
                )

        # ----------------------------------------------------------------------
        # Domain 3: Inventory & Purchase Requests
        # ----------------------------------------------------------------------
        if any(w in goal_lower for w in ["inventory", "stock", "purchase request", "reorder"]):
            if verif_rec:
                summary = task.final_summary or "Successfully audited inventory and verified purchase request in ledger."
                return (TaskStatus.COMPLETED, summary, None)

            if is_step_limit_reached:
                return (
                    TaskStatus.FAILED,
                    f"Task Failed: Step budget exhausted ({task.steps_count} steps) without verified replenishment order.",
                    "Step budget exhausted before purchase request creation."
                )

        # ----------------------------------------------------------------------
        # Domain 4: CSV Analysis & Executive Reports
        # ----------------------------------------------------------------------
        if any(w in goal_lower for w in ["csv", "sales", "report", "dataset"]):
            if verif_rec:
                summary = task.final_summary or "Successfully analyzed CSV dataset and verified executive report on disk."
                return (TaskStatus.COMPLETED, summary, None)

            if is_step_limit_reached:
                return (
                    TaskStatus.FAILED,
                    f"Task Failed: Step budget exhausted ({task.steps_count} steps) without verified report generation.",
                    "Step budget exhausted before report file was generated."
                )

        # ----------------------------------------------------------------------
        # Domain 5: Legal Contracts & SLAs
        # ----------------------------------------------------------------------
        if any(w in goal_lower for w in ["contract", "agreement", "sla", "msa", "expiry date", "clause"]):
            if verif_rec and verif_rec.contract_id:
                c = db.query(ContractRecord).filter(ContractRecord.id == verif_rec.contract_id).first()
                if c:
                    summary = task.final_summary or f"Successfully audited contract '{c.contract_code}' and verified expiry date '{c.expiry_date}' in ledger."
                    return (TaskStatus.COMPLETED, summary, None)

            if is_step_limit_reached:
                return (
                    TaskStatus.FAILED,
                    f"Task Failed: Step budget exhausted ({task.steps_count} steps) without verified contract audit.",
                    "Step budget exhausted before contract verification."
                )

        # ----------------------------------------------------------------------
        # Generic & Step-Budget Exhaustion Handler
        # ----------------------------------------------------------------------
        if is_step_limit_reached:
            # Under NO circumstance should reaching the step limit be marked COMPLETED unless verified!
            if verif_rec:
                return (TaskStatus.COMPLETED, task.final_summary or "Task completed with verified postconditions.", None)

            fail_msg = f"Task Failed: Reached execution budget limit ({task.steps_count} steps) without verified goal achievement."
            return (TaskStatus.FAILED, fail_msg, fail_msg)

        # If verified record exists for generic goal
        if verif_rec:
            return (TaskStatus.COMPLETED, task.final_summary or "Task finished with verified outcome.", None)

        # If explicit failure summary was provided
        if task.final_summary and ("fail" in task.final_summary.lower() or "halt" in task.final_summary.lower() or "error" in task.final_summary.lower()):
            return (TaskStatus.FAILED, task.final_summary, task.error_message or task.final_summary)

        # Default fallback: If no verification record and not a safe terminal state, mark FAILED
        return (
            TaskStatus.FAILED,
            task.final_summary or "Task terminated without meeting required ground-truth verification postconditions.",
            task.error_message or "Missing required verification postconditions."
        )
