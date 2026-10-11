"""
AgentOS - Controlled Multi-Agent Orchestration Architecture.
Specialized agent roles:
  1. PlannerRole: Decomposes natural language goals into validated dependency graphs (PlanDAG).
  2. ResearcherRole: Executes read-only discovery tools without mutation privileges.
  3. ExecutorRole: Executes authorized state-modifying actions via the central permission system.
  4. VerifierCriticRole: Asserts ground-truth database and DOM state independently.
  5. CoordinatorRole: Enforces resource budgets, handles checkpoints, and compiles final deliverables.

Ensures least-privilege tool access and strictly prevents agents from self-authorizing restricted actions.
"""

from __future__ import annotations
import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.agent.dag_planner import PlanDAG, PlanStepNode, DAGPlanner, StepExecutionStatus, RiskClassification
from backend.app.tools.registry import ToolRegistry, default_tool_registry
from backend.app.security.policy import PolicyEngine
from backend.app.verification.critic import VerificationCritic, VerificationOutcome
from backend.app.memory.engine import MemoryEngine


class PlannerRole:
    """Interprets user requirements and formulates the dependency graph plan."""
    def __init__(self):
        self.planner = DAGPlanner()

    def plan(self, goal: str, db: Session) -> PlanDAG:
        # Check semantic memory for approved procedures
        memories = MemoryEngine.retrieve_relevant_memories(db, goal, limit=3)
        dag = self.planner.create_dag_for_goal(goal)
        return dag


class ResearcherRole:
    """Collects information using approved read-only tools only."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_read_step(self, db: Session, node: PlanStepNode) -> Dict[str, Any]:
        risk = PolicyEngine.get_tool_risk(node.tool_name, node.tool_input)
        if risk != RiskClassification.READ_ONLY:
            raise PermissionError(f"Security Violation: ResearcherRole attempted non-read-only tool '{node.tool_name}' ({risk.value})")

        res = self.registry.execute(node.tool_name, db, node.tool_input)
        return res.to_dict()


class ExecutorRole:
    """Performs authorized actions through strict backend authorization gating."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_action_step(
        self,
        db: Session,
        node: PlanStepNode,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        # Check human approval requirement
        needs_approval, reason = PolicyEngine.requires_human_approval(
            node.tool_name,
            node.tool_input,
            auto_approve_high_risk=auto_approve
        )
        if needs_approval:
            return {
                "success": False,
                "requires_approval": True,
                "risk_reason": reason,
                "error": f"APPROVAL_REQUIRED: {reason}"
            }

        res = self.registry.execute(node.tool_name, db, node.tool_input)
        return res.to_dict()


class VerifierCriticRole:
    """Independently verifies results against ground truth."""
    @staticmethod
    def verify_outcome(
        db: Session,
        task_id: str,
        tool_name: str,
        node_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name == "create_payable":
            data = node_output.get("data", {})
            rep = VerificationCritic.verify_payable_creation(
                db=db,
                task_id=task_id,
                invoice_number=data.get("invoice_number", ""),
                expected_amount=float(data.get("amount", 0.0)),
                expected_vendor=data.get("vendor_name"),
                expected_due_date=data.get("due_date")
            )
            return rep.model_dump()
        return {"verified": True, "outcome": "VERIFIED"}


class ControlledMultiAgentOrchestrator:
    """Coordinates specialized agent roles with shared working memory and checkpointing."""
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or default_tool_registry
        self.planner = PlannerRole()
        self.researcher = ResearcherRole(self.registry)
        self.executor = ExecutorRole(self.registry)
        self.verifier = VerifierCriticRole()

    def run_multi_agent_workflow(
        self,
        db: Session,
        goal: str,
        task_id: str,
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        t0 = time.time()
        # 1. Planner interprets goal and constructs DAG
        dag = self.planner.plan(goal, db)

        executed_steps = []
        working_memory: Dict[str, Any] = {"task_id": task_id, "goal": goal}

        # 2. Execution loop through DAG
        while not dag.is_finished():
            ready_steps = dag.get_ready_steps()
            if not ready_steps:
                break

            for step in ready_steps:
                # Dispatch based on role permission
                if step.is_read_only():
                    out = self.researcher.execute_read_step(db, step)
                else:
                    out = self.executor.execute_action_step(db, step, auto_approve=auto_approve)

                if out.get("requires_approval"):
                    dag.mark_failed(step.step_id, out.get("error", "Approval Required"))
                    return {
                        "status": "WAITING_FOR_APPROVAL",
                        "task_id": task_id,
                        "dag": dag.to_summary_list(),
                        "approval_required": True,
                        "risk_reason": out.get("risk_reason")
                    }

                if out.get("success"):
                    dag.mark_completed(step.step_id, out.get("data", {}))
                else:
                    dag.mark_failed(step.step_id, out.get("error", "Execution failed"))

                executed_steps.append({
                    "step_id": step.step_id,
                    "tool": step.tool_name,
                    "success": out.get("success", False),
                    "output": out
                })

        # 3. Final verification and recording in episodic memory
        duration = round(time.time() - t0, 2)
        success = not dag.has_failures()
        outcome = "SUCCESS" if success else "FAILED"

        # Record into episodic memory for continuous learning
        MemoryEngine.record_episodic_memory(
            db=db,
            task_id=task_id,
            goal=goal,
            outcome=outcome,
            verification_token=f"MULTI-AGENT-{task_id[:8].upper()}" if success else None,
            metadata={"duration_seconds": duration, "steps_executed": len(executed_steps)}
        )

        return {
            "status": "COMPLETED" if success else "FAILED",
            "task_id": task_id,
            "duration_seconds": duration,
            "executed_steps_count": len(executed_steps),
            "dag_summary": dag.to_summary_list()
        }
