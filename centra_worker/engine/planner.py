from __future__ import annotations
import re
from typing import List
from centra_worker.models.plan import ExecutionPlan, PlanStep, PlanStepStatus


class GoalPlanner:
    """
    Decomposes natural language requests into structured execution plans
    and dynamically adapts the plan when failures or new requirements arise.
    """

    def create_initial_plan(self, goal: str) -> ExecutionPlan:
        goal_lower = goal.lower()
        steps: List[PlanStep] = []

        if "invoice" in goal_lower or "bill" in goal_lower:
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Discover Invoices",
                    description="Scan invoice repository to locate incoming files and identify invoices for the requested company.",
                    expected_tool="list_files"
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Analyze & Extract Latest Invoice",
                    description="Identify the most recent invoice among candidates, read document, and extract amount, due date, vendor, and PO.",
                    expected_tool="read_file"
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Validate Vendor & Compliance",
                    description="Query internal ERP system to ensure vendor is registered and terms are met.",
                    expected_tool="erp_get_vendors"
                )
            )
            steps.append(
                PlanStep(
                    step_id=4,
                    title="Post Invoice to Internal System",
                    description="Enter extracted invoice details into CentraERP accounts payable ledger.",
                    expected_tool="erp_submit_invoice"
                )
            )
            steps.append(
                PlanStep(
                    step_id=5,
                    title="Independent Outcome Verification",
                    description="Query system of record to independently verify that the invoice was entered with exact matching figures.",
                    expected_tool="verify_erp_record"
                )
            )
        else:
            # Generic decomposition for open-ended enterprise tasks
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Inspect Environment & Assets",
                    description=f"Discover relevant files, documents, or systems related to: {goal}",
                    expected_tool="list_files"
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Execute Task Core Action",
                    description="Process files or update target internal application.",
                    expected_tool="custom"
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Verify Task Outcome",
                    description="Check ground truth state to ensure desired outcome was completed.",
                    expected_tool="verification"
                )
            )

        return ExecutionPlan(goal=goal, steps=steps, current_step_index=0)

    def insert_recovery_step(self, plan: ExecutionPlan, reason: str, tool_name: str) -> ExecutionPlan:
        """
        Dynamically insert a recovery or retry step into the active plan.
        """
        plan.replan_count += 1
        new_step_id = len(plan.steps) + 1
        recovery_step = PlanStep(
            step_id=new_step_id,
            title=f"Self-Correction: {reason}",
            description=f"Autonomous recovery action using {tool_name} to overcome failure.",
            expected_tool=tool_name,
            status=PlanStepStatus.PENDING
        )
        # Insert right after the current step
        insert_idx = plan.current_step_index + 1
        plan.steps.insert(insert_idx, recovery_step)
        return plan
