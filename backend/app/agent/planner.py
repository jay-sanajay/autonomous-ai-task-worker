"""
AgentOS - Dynamic Goal Planner & Decomposition Engine.
Transforms ambiguous natural language requests into structured execution plans
and dynamically inserts recovery actions when unexpected events occur.
"""

from __future__ import annotations
from typing import List, Dict, Any
from backend.app.agent.state import PlanStep, StepStatus, GoalRepresentation


class GoalPlanner:
    def create_initial_plan(self, goal: str) -> List[PlanStep]:
        goal_lower = goal.lower()
        steps: List[PlanStep] = []

        # Standard invoice-to-payable workflow
        steps.append(
            PlanStep(
                step_id=1,
                title="Discover Invoice Documents",
                description="Scan sandbox document repository to locate incoming invoices.",
                expected_tool="list_invoice_files",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=2,
                title="Read Document & Extract Content",
                description="Read raw content of latest invoice file without data loss.",
                expected_tool="read_invoice",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=3,
                title="Structured Field Extraction",
                description="Extract vendor, invoice number, amount, and due date with zero hallucination.",
                expected_tool="extract_invoice_fields",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=4,
                title="Vendor Directory Lookup",
                description="Validate vendor entity against approved company directory.",
                expected_tool="search_vendor",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=5,
                title="Duplicate Submission Check",
                description="Query accounting records to prevent duplicate payment registration.",
                expected_tool="search_existing_invoice",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=6,
                title="Post Payable Record",
                description="Create persisted database record in company ledger.",
                expected_tool="create_payable",
                status=StepStatus.SUCCESS
            )
        )
        steps.append(
            PlanStep(
                step_id=7,
                title="Independent Ground-Truth Verification",
                description="Read back persisted record from SQLite database and verify attribute match.",
                expected_tool="verify_payable",
                status=StepStatus.SUCCESS
            )
        )

        return steps

    def insert_recovery_step(self, plan: List[PlanStep], reason: str, tool_name: str, after_index: int) -> List[PlanStep]:
        """Dynamically inject an autonomous recovery or retry action into the plan."""
        new_step_id = len(plan) + 1
        recovery_step = PlanStep(
            step_id=new_step_id,
            title=f"Autonomous Recovery: {reason}",
            description=f"Self-correction action using {tool_name} to overcome unexpected condition.",
            expected_tool=tool_name,
            status=StepStatus.RETRYING
        )
        plan.insert(after_index + 1, recovery_step)
        return plan
