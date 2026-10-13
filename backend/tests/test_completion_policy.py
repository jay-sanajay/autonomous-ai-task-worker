"""
AgentOS - Regression Tests for CompletionPolicy & False Success Elimination.
Validates that tasks can NEVER falsely report COMPLETED upon execution budget exhaustion.
"""

import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import AgentTask, TaskStep, VerificationResult, PayableRecord
from backend.app.agent.state import TaskStatus, StepStatus
from backend.app.agent.completion_policy import CompletionPolicy
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def clean_db():
    reset_database()
    yield


def test_step_budget_exhaustion_must_never_claim_success():
    """
    Core regression test: Reaching the step limit without verified database postconditions
    must transition the task to FAILED, even if the last executed tool succeeded (e.g. list_files).
    """
    db = SessionLocal()
    try:
        # Create a task with max_steps = 1
        # The first step will be 'list_invoice_files', which succeeds.
        # But invoice creation/verification has NOT occurred.
        engine = AgentExecutionEngine(max_steps=1)
        task = engine.run(
            db_session=db,
            goal="Find the latest invoice from Acme Technologies and register as payable.",
            auto_approve_high_risk=True
        )

        assert task.status == TaskStatus.FAILED.value, (
            f"Expected task to fail upon step exhaustion, but got '{task.status}'. "
            "A successful intermediate read must NEVER result in a COMPLETED task!"
        )
        assert "execution budget limit" in task.final_summary.lower() or "step limit" in task.final_summary.lower()
        assert task.error_message is not None
    finally:
        db.close()


def test_completion_policy_rejects_unverified_invoice_task():
    """
    If an invoice task claims it is finished but no verification record exists,
    CompletionPolicy must strictly reject completion.
    """
    db = SessionLocal()
    try:
        task = AgentTask(
            id="test-task-unverified",
            goal="Process invoice from Acme Technologies",
            status=TaskStatus.RUNNING.value,
            steps_count=3,
            final_summary="Finished all actions."
        )
        db.add(task)
        db.commit()

        status, summary, err = CompletionPolicy.evaluate_task_completion(
            db=db,
            task=task,
            is_step_limit_reached=False
        )

        assert status == TaskStatus.FAILED
        assert "verification" in err.lower() or "postcondition" in err.lower()
    finally:
        db.close()


def test_completion_policy_approves_verified_payable():
    """
    When a genuine payable record exists and has passed verification,
    CompletionPolicy approves COMPLETED status.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        task = AgentTask(
            id="test-task-verified",
            goal="Process invoice from Acme Technologies",
            status=TaskStatus.RUNNING.value,
            steps_count=6,
            final_summary="Processed invoice INV-2026-001."
        )
        db.add(task)
        db.commit()

        payable = PayableRecord(
            idempotency_key="IDEM-TEST-001",
            invoice_number="INV-2026-001",
            vendor_name="Acme Technologies Inc.",
            amount=2450.00,
            currency="INR",
            due_date="2026-11-14",
            status="VERIFIED"
        )
        db.add(payable)
        db.commit()

        v_rec = VerificationResult(
            task_id="test-task-verified",
            payable_id=payable.id,
            verified=True,
            verification_token="TOKEN-TEST-1234",
            field_comparisons="{}",
            audit_notes="Ground truth verified.",
            created_at=datetime.now(timezone.utc)
        )
        db.add(v_rec)
        db.commit()

        status, summary, err = CompletionPolicy.evaluate_task_completion(
            db=db,
            task=task,
            is_step_limit_reached=False
        )

        assert status == TaskStatus.COMPLETED
        assert err is None
        assert "processed" in summary.lower() or "completed" in summary.lower() or "successfully" in summary.lower()
    finally:
        db.close()
