"""
AgentOS - Task Management API Routes.
Exposes endpoints for creating tasks, inspecting execution timeline, and resolving approvals.
"""

from __future__ import annotations
import json
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models import AgentTask, TaskStep, ApprovalRequest, VerificationResult
from backend.app.schemas.task import TaskCreate, TaskResponse, TaskDetailResponse, TaskStepResponse
from backend.app.schemas.approval import ApprovalResolution
from backend.app.agent.loop import AgentExecutionEngine

router = APIRouter(prefix="/api/tasks", tags=["Agent Tasks"])
execution_engine = AgentExecutionEngine()


def safe_json_loads(val: Optional[str], default: Any) -> Any:
    """Safely parse JSON strings, returning default fallback on corruption or None."""
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        return default


@router.post("", response_model=TaskDetailResponse)
def create_and_run_task(req: TaskCreate, db: Session = Depends(get_db)):
    """Launch autonomous AI worker to achieve natural language goal."""
    task = execution_engine.run(
        db_session=db,
        goal=req.goal,
        auto_approve_high_risk=req.auto_approve_high_risk,
        simulate_fault=req.simulate_fault
    )
    return get_task_details(task.id, db)


@router.get("", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """List all agent tasks ordered by creation time."""
    tasks = db.query(AgentTask).order_by(AgentTask.created_at.desc()).all()
    results = []
    for t in tasks:
        results.append(
            TaskResponse(
                id=t.id,
                goal=t.goal,
                status=t.status,
                current_plan=safe_json_loads(t.current_plan, []),
                working_memory=safe_json_loads(t.working_memory, {}),
                extracted_data=safe_json_loads(t.extracted_data, {}),
                final_summary=t.final_summary,
                error_message=t.error_message,
                steps_count=t.steps_count,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
        )
    return results


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task_details(task_id: str, db: Session = Depends(get_db)):
    """Retrieve full step-by-step execution trace and verification receipt."""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    steps = db.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_number).all()
    step_responses = [
        TaskStepResponse(
            id=s.id,
            step_number=s.step_number,
            thought=s.thought,
            tool_name=s.tool_name,
            tool_input=safe_json_loads(s.tool_input, {}),
            tool_output=safe_json_loads(s.tool_output, {}),
            status=s.status,
            error_message=s.error_message,
            latency_ms=s.latency_ms,
            created_at=s.created_at
        )
        for s in steps
    ]

    # Check latest approval request regardless of status for historical audit visibility
    latest_app = db.query(ApprovalRequest).filter(
        ApprovalRequest.task_id == task_id
    ).order_by(ApprovalRequest.created_at.desc()).first()

    app_dict = None
    if latest_app:
        app_dict = {
            "approval_id": latest_app.id,
            "status": latest_app.status,
            "tool_name": latest_app.tool_name,
            "action_description": latest_app.action_description,
            "risk_level": latest_app.risk_level,
            "risk_reason": latest_app.risk_reason,
            "approver": latest_app.approver,
            "feedback": latest_app.feedback,
            "pending_payload": safe_json_loads(latest_app.pending_payload, {})
        }

    # Check verification
    verif = db.query(VerificationResult).filter(VerificationResult.task_id == task_id).first()
    verif_dict = None
    if verif:
        verif_dict = {
            "verified": verif.verified,
            "payable_id": verif.payable_id,
            "task_item_id": verif.task_item_id,
            "contract_id": verif.contract_id,
            "verification_token": verif.verification_token,
            "audit_notes": verif.audit_notes,
            "field_comparisons": safe_json_loads(verif.field_comparisons, {})
        }

    return TaskDetailResponse(
        id=task.id,
        goal=task.goal,
        status=task.status,
        current_plan=safe_json_loads(task.current_plan, []),
        working_memory=safe_json_loads(task.working_memory, {}),
        extracted_data=safe_json_loads(task.extracted_data, {}),
        final_summary=task.final_summary,
        error_message=task.error_message,
        steps_count=task.steps_count,
        created_at=task.created_at,
        updated_at=task.updated_at,
        steps=step_responses,
        pending_approval=app_dict,
        verification=verif_dict
    )


@router.post("/{task_id}/approve", response_model=TaskDetailResponse)
def approve_task(task_id: str, resolution: ApprovalResolution, db: Session = Depends(get_db)):
    """Authorize a pending consequential action and resume execution."""
    try:
        task = execution_engine.resume_task(
            db_session=db,
            task_id=task_id,
            approved=resolution.approved,
            approver=resolution.approver or "Jay (Administrator)",
            feedback=resolution.feedback
        )
        return get_task_details(task.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/reject", response_model=TaskDetailResponse)
def reject_task(task_id: str, resolution: ApprovalResolution, db: Session = Depends(get_db)):
    """Reject a pending operation and cancel the task."""
    try:
        task = execution_engine.resume_task(
            db_session=db,
            task_id=task_id,
            approved=False,
            approver=resolution.approver or "Jay (Administrator)",
            feedback=resolution.feedback or "Rejected by reviewer"
        )
        return get_task_details(task.id, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    """Cancel an active task."""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "CANCELLED"

    # Also update all pending ApprovalRequest records for that task to status "CANCELLED"
    pending_approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.task_id == task_id,
        ApprovalRequest.status == "PENDING"
    ).all()
    for app_req in pending_approvals:
        app_req.status = "CANCELLED"

    db.commit()
    return {"status": "success", "message": f"Task '{task_id}' marked as CANCELLED."}
