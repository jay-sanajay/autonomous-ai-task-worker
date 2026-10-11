"""
AgentOS - Adaptive Dependency Graph (DAG) Planning & Execution Engine.
Represents task plans as a directed acyclic graph supporting parallel execution
of independent read-only actions, sequential dependent steps, conditional branches,
dynamic replanning upon failure, and cancellation propagation.
"""

from __future__ import annotations
import uuid
import copy
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
import concurrent.futures


class RiskClassification(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK_REVERSIBLE = "LOW_RISK_REVERSIBLE"
    CONSEQUENTIAL = "CONSEQUENTIAL"
    CRITICAL = "CRITICAL"


class StepExecutionStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class PlanStepNode(BaseModel):
    step_id: str
    description: str
    tool_name: str
    tool_input: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    expected_output: str = ""
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 3, "backoff": 0.5})
    risk_level: RiskClassification = RiskClassification.READ_ONLY
    status: StepExecutionStatus = StepExecutionStatus.PENDING
    verification_requirements: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    retry_count: int = 0
    is_non_idempotent_write: bool = False
    is_confirmed_complete: bool = False

    def is_read_only(self) -> bool:
        return self.risk_level == RiskClassification.READ_ONLY


class PlanDAG(BaseModel):
    nodes: Dict[str, PlanStepNode] = Field(default_factory=dict)
    confirmed_writes: Set[str] = Field(default_factory=set)  # Tracks successfully executed non-idempotent steps

    def add_node(self, node: PlanStepNode):
        self.nodes[node.step_id] = node

    def get_node(self, step_id: str) -> Optional[PlanStepNode]:
        return self.nodes.get(step_id)

    def get_ready_steps(self) -> List[PlanStepNode]:
        """Return all steps whose dependencies have all completed successfully."""
        ready: List[PlanStepNode] = []
        for step in self.nodes.values():
            if step.status != StepExecutionStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_satisfied = True
            for dep_id in step.dependencies:
                dep_node = self.nodes.get(dep_id)
                if not dep_node or dep_node.status != StepExecutionStatus.COMPLETED:
                    deps_satisfied = False
                    break

            if deps_satisfied:
                step.status = StepExecutionStatus.READY
                ready.append(step)
        return ready

    def mark_completed(self, step_id: str, output_data: Dict[str, Any], latency_ms: float = 0.0):
        node = self.nodes.get(step_id)
        if node:
            node.status = StepExecutionStatus.COMPLETED
            node.output_data = output_data
            node.latency_ms = latency_ms
            node.is_confirmed_complete = True
            if node.is_non_idempotent_write:
                self.confirmed_writes.add(step_id)

    def mark_failed(self, step_id: str, error_message: str):
        node = self.nodes.get(step_id)
        if node:
            node.status = StepExecutionStatus.FAILED
            node.error_message = error_message
            self.propagate_cancellation(step_id)

    def propagate_cancellation(self, failed_step_id: str):
        """Propagate failure down the dependency graph, marking dependent steps as BLOCKED."""
        to_block = [s_id for s_id, n in self.nodes.items() if failed_step_id in n.dependencies and n.status in (StepExecutionStatus.PENDING, StepExecutionStatus.READY)]
        for s_id in to_block:
            self.nodes[s_id].status = StepExecutionStatus.BLOCKED
            self.nodes[s_id].error_message = f"Dependency '{failed_step_id}' failed."
            self.propagate_cancellation(s_id)

    def replan_alternative_path(self, failed_step_id: str, recovery_node: PlanStepNode):
        """
        Dynamically update the graph by replacing or rerouting around a failed node
        without repeating confirmed successful actions.
        """
        old_node = self.nodes.get(failed_step_id)
        if not old_node:
            return

        self.nodes[recovery_node.step_id] = recovery_node
        # Reroute blocked downstream nodes to depend on recovery node instead
        for node in self.nodes.values():
            if failed_step_id in node.dependencies:
                node.dependencies.remove(failed_step_id)
                node.dependencies.append(recovery_node.step_id)
                if node.status == StepExecutionStatus.BLOCKED:
                    node.status = StepExecutionStatus.PENDING
                    node.error_message = None

    def is_finished(self) -> bool:
        """Returns True if no nodes are PENDING, READY, or RUNNING."""
        for node in self.nodes.values():
            if node.status in (StepExecutionStatus.PENDING, StepExecutionStatus.READY, StepExecutionStatus.RUNNING):
                return False
        return True

    def has_failures(self) -> bool:
        return any(n.status in (StepExecutionStatus.FAILED, StepExecutionStatus.BLOCKED) for n in self.nodes.values())

    def to_summary_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "step_id": n.step_id,
                "description": n.description,
                "tool_name": n.tool_name,
                "dependencies": n.dependencies,
                "status": n.status.value,
                "risk_level": n.risk_level.value,
                "latency_ms": n.latency_ms,
                "error_message": n.error_message,
                "is_read_only": n.is_read_only()
            }
            for n in self.nodes.values()
        ]


class DAGPlanner:
    """Creates structured dependency graphs for various enterprise tasks."""

    def create_dag_for_goal(self, goal: str) -> PlanDAG:
        goal_lower = goal.lower()
        dag = PlanDAG()

        # 1. Primary Invoice Processing Workflow
        if any(w in goal_lower for w in ["invoice", "payable", "acme", "bill"]):
            # Step 1A: Scan file repository (Read-Only)
            dag.add_node(PlanStepNode(
                step_id="step-1a",
                description="Scan filesystem repository to locate target invoice document.",
                tool_name="list_invoice_files",
                tool_input={"directory": "sandbox_data/invoices"},
                risk_level=RiskClassification.READ_ONLY,
                expected_output="List of available invoice documents"
            ))

            # Step 1B: Look up vendor directory in parallel (Read-Only)
            dag.add_node(PlanStepNode(
                step_id="step-1b",
                description="Query company vendor directory concurrently for approved vendor entities.",
                tool_name="search_vendor",
                tool_input={"vendor_name": "Acme Technologies"},
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Matched approved vendor directory record"
            ))

            # Step 2: Read target invoice document (depends on step-1a)
            dag.add_node(PlanStepNode(
                step_id="step-2",
                description="Read raw content of invoice document without data truncation.",
                tool_name="read_invoice",
                tool_input={"file_path": "sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.txt"},
                dependencies=["step-1a"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Extracted raw text content of invoice"
            ))

            # Step 3: Extract structured fields (depends on step-2)
            dag.add_node(PlanStepNode(
                step_id="step-3",
                description="Extract invoice number, total amount, due date, and vendor name.",
                tool_name="extract_invoice_fields",
                tool_input={"file_path": "sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.txt"},
                dependencies=["step-2"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Validated structured fields"
            ))

            # Step 4: Duplicate Check in accounting ledger (depends on step-3 and step-1b)
            dag.add_node(PlanStepNode(
                step_id="step-4",
                description="Query accounting records to prevent duplicate payment registration.",
                tool_name="search_existing_invoice",
                tool_input={"vendor_name": "Acme Technologies", "invoice_number": "INV-2024-001"},
                dependencies=["step-3", "step-1b"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Duplicate status confirmation"
            ))

            # Step 5: Post Payable Record (Consequential Write, depends on step-4)
            dag.add_node(PlanStepNode(
                step_id="step-5",
                description="Create persisted payable record in company accounting database.",
                tool_name="create_payable",
                tool_input={
                    "vendor_name": "Acme Technologies Inc.",
                    "invoice_number": "INV-2024-001",
                    "amount": 2450.00,
                    "due_date": "2024-11-15"
                },
                dependencies=["step-4"],
                risk_level=RiskClassification.CONSEQUENTIAL,
                is_non_idempotent_write=True,
                expected_output="Persisted payable ID and idempotency key"
            ))

            # Step 6: Independent Ground-Truth Verification (depends on step-5)
            dag.add_node(PlanStepNode(
                step_id="step-6",
                description="Independently query SQLite database ledger and assert all fields match source truth.",
                tool_name="verify_payable",
                tool_input={
                    "invoice_number": "INV-2024-001",
                    "expected_amount": 2450.00,
                    "expected_due_date": "2024-11-15",
                    "expected_vendor": "Acme Technologies Inc."
                },
                dependencies=["step-5"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Cryptographic verification token"
            ))

            # Step 7: Final Summary (depends on step-6)
            dag.add_node(PlanStepNode(
                step_id="step-7",
                description="Synthesize executive audit receipt with verified proof token.",
                tool_name="report_task_result",
                tool_input={"task_id": "auto"},
                dependencies=["step-6"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Final summary report"
            ))
            return dag

        # 2. Browser Portal Automated Workflow
        elif any(w in goal_lower for w in ["portal", "browser", "web", "click", "form"]):
            dag.add_node(PlanStepNode(
                step_id="step-b1",
                description="Open simulated enterprise company portal in controlled Playwright browser.",
                tool_name="browser_open_url",
                tool_input={"url": "http://127.0.0.1:8000/portal/invoices"},
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Loaded company portal invoices page"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-b2",
                description="Inspect portal interactive elements, forms, and accessibility locators.",
                tool_name="browser_inspect_page",
                tool_input={},
                dependencies=["step-b1"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Accessible input elements and buttons list"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-b3",
                description="Fill invoice registration form fields in browser portal.",
                tool_name="browser_fill_field",
                tool_input={"selector": "#vendor_name", "value": "CentrAlign Systems"},
                dependencies=["step-b2"],
                risk_level=RiskClassification.LOW_RISK_REVERSIBLE,
                expected_output="Populated form inputs"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-b4",
                description="Submit registration form by clicking submit button with auto-recovery for stale locators.",
                tool_name="browser_click",
                tool_input={"selector": "#submit-btn"},
                dependencies=["step-b3"],
                risk_level=RiskClassification.CONSEQUENTIAL,
                is_non_idempotent_write=True,
                expected_output="Form submission response"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-b5",
                description="Verify browser DOM state and capture evidence screenshot.",
                tool_name="browser_verify_page_state",
                tool_input={"expected_text": "Successfully Registered"},
                dependencies=["step-b4"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Verified browser state banner"
            ))
            return dag

        # 3. Contract Compliance Workflow
        elif any(w in goal_lower for w in ["contract", "agreement", "sla", "msa", "expiry date", "clause"]):
            dag.add_node(PlanStepNode(
                step_id="step-c1",
                description="Discover contract documents and SLA agreements in sandbox repository.",
                tool_name="list_contract_files",
                tool_input={"directory": "sandbox_data/contracts"},
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Discovered contract documents"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-c2",
                description="Perform universal file inspection and parse document structure.",
                tool_name="inspect_document",
                tool_input={"file_path": "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.txt"},
                dependencies=["step-c1"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Extracted text and metadata"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-c3",
                description="Extract contracting parties, effective date, expiry date, and audit for missing clauses.",
                tool_name="extract_contract_details",
                tool_input={"file_path": "sandbox_data/contracts/Master_Services_Agreement_CentrAlign_Acme.txt"},
                dependencies=["step-c2"],
                risk_level=RiskClassification.LOW_RISK_REVERSIBLE,
                expected_output="Audited contract record with risk score"
            ))

            dag.add_node(PlanStepNode(
                step_id="step-c4",
                description="Independently verify contract expiry date against SQLite database ledger.",
                tool_name="verify_contract",
                tool_input={"contract_code": "CTR-2024-MSA-088", "expected_expiry_date": "January 14, 2025"},
                dependencies=["step-c3"],
                risk_level=RiskClassification.READ_ONLY,
                expected_output="Cryptographic verification token"
            ))
            return dag

        # 4. Default: Generic DAG
        dag.add_node(PlanStepNode(
            step_id="step-1",
            description=f"Inspect workspace and execute instruction: {goal}",
            tool_name="inspect_document",
            tool_input={"file_path": "sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.txt"},
            risk_level=RiskClassification.READ_ONLY,
            expected_output="Workspace analysis"
        ))
        return dag
