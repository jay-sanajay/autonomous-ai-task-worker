"""
AgentOS - Observability, Telemetry & Safe Replay Engine.
Tracks granular execution telemetry, error categories, and provides a safe replay mode
that uses recorded outputs to inspect past runs without repeating irreversible writes.
"""

from __future__ import annotations
import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.models import AgentTask, TaskStep, VerificationResult, ApprovalRequest
from backend.app.memory.engine import redact_sensitive_data


class TelemetryEvent(BaseModel):
    task_id: str
    step_id: Optional[str] = None
    step_number: int
    tool_name: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = True
    retry_count: int = 0
    error_category: Optional[str] = None
    model_provider: str = "DeterministicFallback"
    verification_outcome: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class ReplayStepResult(BaseModel):
    step_number: int
    tool_name: str
    was_simulated: bool
    side_effects_prevented: bool
    recorded_output: Dict[str, Any]
    thought: str


class ReplayEngine:
    """Safe Replay Engine: Executes simulation using recorded historical traces."""

    @staticmethod
    def replay_task(db: Session, task_id: str) -> Dict[str, Any]:
        """
        Replay a completed task safely.
        Uses recorded database outputs without calling external tools or creating duplicate writes!
        """
        task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found for replay.")

        steps = db.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_number.asc()).all()

        replayed_steps: List[ReplayStepResult] = []
        prevented_writes_count = 0

        for step in steps:
            # Detect write operations that must not be repeated
            is_write = step.tool_name in ("create_payable", "create_purchase_request", "update_support_ticket", "create_task_item")
            if is_write:
                prevented_writes_count += 1

            recorded_out = {}
            try:
                recorded_out = json.loads(step.tool_output or "{}")
            except Exception:
                pass

            replayed_steps.append(ReplayStepResult(
                step_number=step.step_number,
                tool_name=step.tool_name or "reasoning",
                was_simulated=True,
                side_effects_prevented=is_write,
                recorded_output=recorded_out,
                thought=redact_sensitive_data(step.thought or "")
            ))

        return {
            "status": "REPLAY_COMPLETED",
            "task_id": task_id,
            "original_goal": redact_sensitive_data(task.goal),
            "original_status": task.status,
            "replayed_steps_count": len(replayed_steps),
            "prevented_writes_count": prevented_writes_count,
            "safety_assertion": "Zero external mutations or duplicate database records created during replay.",
            "steps": [s.model_dump() for s in replayed_steps]
        }


class TelemetryCollector:
    """Collects and aggregates observable performance metrics across all task runs."""

    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
        tasks = db.query(AgentTask).all()
        total_tasks = len(tasks)
        if total_tasks == 0:
            return {
                "total_tasks": 0,
                "completion_rate": 0.0,
                "failure_rate": 0.0,
                "recovery_rate": 0.0,
                "verification_success_rate": 0.0,
                "avg_duration_ms": 0.0
            }

        completed = sum(1 for t in tasks if t.status == "COMPLETED")
        failed = sum(1 for t in tasks if t.status == "FAILED")
        verifications = db.query(VerificationResult).filter(VerificationResult.verified == True).count()

        steps = db.query(TaskStep).all()
        recovered_steps = sum(1 for s in steps if s.status == "RECOVERED")
        total_latency = sum(s.latency_ms for s in steps)
        avg_latency = round(total_latency / len(steps), 2) if steps else 0.0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "completion_rate": round((completed / total_tasks) * 100, 1),
            "failure_rate": round((failed / total_tasks) * 100, 1),
            "recovered_steps_count": recovered_steps,
            "verified_outcomes_count": verifications,
            "verification_success_rate": round((verifications / max(completed, 1)) * 100, 1),
            "average_step_latency_ms": avg_latency
        }
