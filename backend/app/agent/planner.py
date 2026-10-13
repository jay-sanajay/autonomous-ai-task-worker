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

        # 1. HR Email / Interview Task Workflow
        if any(w in goal_lower for w in ["email", "hr", "interview", "task list", "meeting link"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Discover Candidate Emails",
                    description="Scan sandbox email inbox repository to locate candidate HR communications.",
                    expected_tool="list_emails",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Read Latest HR Message",
                    description="Read raw content of newest interview invitation email.",
                    expected_tool="read_email",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Extract Interview Metadata",
                    description="Extract interview date, time, and video meeting link without hallucination.",
                    expected_tool="extract_email_details",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=4,
                    title="Create Task Item",
                    description="Persist interview event to internal task list in SQLite database.",
                    expected_tool="create_task_item",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=5,
                    title="Independent Task Verification",
                    description="Assert persisted task item attributes match source email ground truth.",
                    expected_tool="verify_task_item",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=6,
                    title="Synthesize Executive Receipt",
                    description="Generate final evidence report with meeting link and verified token.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 2. Inventory & Purchase Request Workflow
        if any(w in goal_lower for w in ["inventory", "stock", "purchase request", "reorder"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Audit Inventory Stock",
                    description="Query warehouse database to identify products below reorder threshold.",
                    expected_tool="list_inventory",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Draft Purchase Request",
                    description="Create replenishment purchase order in database.",
                    expected_tool="create_purchase_request",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Safety Gating / Verification",
                    description="Verify purchase request state and check enterprise disbursement limits.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 3. Customer Support Tickets Workflow
        if any(w in goal_lower for w in ["ticket", "support", "unresolved", "prioritize", "customer"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Retrieve Support Queue",
                    description="Fetch unresolved customer tickets from support database.",
                    expected_tool="list_support_tickets",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Prioritize & Update Statuses",
                    description="Triage urgent issues and update ticket statuses in database.",
                    expected_tool="update_support_ticket",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Verify Ticket Ledger",
                    description="Confirm status changes against SQLite support_tickets table.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 4. CSV Analysis & Reporting Workflow
        if any(w in goal_lower for w in ["csv", "sales", "top five", "q3"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Discover Available CSV Datasets",
                    description="Scan repository to identify available data files.",
                    expected_tool="list_csv_files",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Inspect CSV Dataset",
                    description="Read columns, row count, data types, and check for missing values.",
                    expected_tool="inspect_csv",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Compute Pandas Analytics",
                    description="Perform aggregations, calculate revenue, and rank top products.",
                    expected_tool="analyze_csv",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=4,
                    title="Generate Persistent Report",
                    description="Save comprehensive markdown report file with rankings to disk.",
                    expected_tool="generate_report",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=5,
                    title="Deliver Verified Output",
                    description="Verify report existence and present execution evidence receipt.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 5. Legal Contract & Agreement Audit Workflow
        if any(w in goal_lower for w in ["contract", "agreement", "sla", "msa", "expiry date", "missing information", "missing clause", "audit contract"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Discover Contract Documents",
                    description="Scan sandbox and uploaded documents to locate targeted contract or SLA agreement.",
                    expected_tool="list_contract_files",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Inspect & Classify Document",
                    description="Perform universal file inspection, read structure, and extract text without truncation.",
                    expected_tool="inspect_document",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Extract Expiry & Audit Clauses",
                    description="Extract contracting parties, effective date, expiry date, value, and audit for missing critical clauses.",
                    expected_tool="extract_contract_details",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=4,
                    title="Independent Ground-Truth Verification",
                    description="Query SQLite contracts table, assert expiry date matches source truth, and generate verification token.",
                    expected_tool="verify_contract",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=5,
                    title="Synthesize Executive Legal Receipt",
                    description="Compile comprehensive compliance summary with expiry date, risk score, and missing clause alerts.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 6. Universal Document Inspection Workflow
        if any(w in goal_lower for w in ["inspect file", "check document", "file structure", "read file", "inspect"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Universal Document Inspection",
                    description="Inspect file, extract metadata, page counts, columns, and classify document type.",
                    expected_tool="inspect_document",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Synthesize Inspection Summary",
                    description="Present structural breakdown, preview, and entity analysis.",
                    expected_tool="report_task_result",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 7. Invoice-to-Payable Workflow (Explicit keyword gating)
        if any(w in goal_lower for w in ["invoice", "payable", "acme", "bill", "vendor", "payment", "due date", "remit"]):
            steps.append(
                PlanStep(
                    step_id=1,
                    title="Discover Invoice Documents",
                    description="Scan sandbox document repository to locate incoming invoices.",
                    expected_tool="list_invoice_files",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=2,
                    title="Read Document & Extract Content",
                    description="Read raw content of latest invoice file without data loss.",
                    expected_tool="read_invoice",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=3,
                    title="Structured Field Extraction",
                    description="Extract vendor, invoice number, amount, and due date with zero hallucination.",
                    expected_tool="extract_invoice_fields",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=4,
                    title="Vendor Directory Lookup",
                    description="Validate vendor entity against approved company directory.",
                    expected_tool="search_vendor",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=5,
                    title="Duplicate Submission Check",
                    description="Query accounting records to prevent duplicate payment registration.",
                    expected_tool="search_existing_invoice",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=6,
                    title="Post Payable Record",
                    description="Create persisted database record in company ledger.",
                    expected_tool="create_payable",
                    status=StepStatus.PENDING
                )
            )
            steps.append(
                PlanStep(
                    step_id=7,
                    title="Independent Ground-Truth Verification",
                    description="Read back persisted record from SQLite database and verify attribute match.",
                    expected_tool="verify_payable",
                    status=StepStatus.PENDING
                )
            )
            return steps

        # 8. Unsupported Goal Plan: Halt execution cleanly without side effects
        steps.append(
            PlanStep(
                step_id=1,
                title="Capability & Feasibility Assessment",
                description=f"Assess objective '{goal}' against registered enterprise tools. Halt on unsupported operation.",
                expected_tool="report_task_result",
                status=StepStatus.PENDING
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
