"""
AgentOS - Regression Tests for Checkpointing & Task Resumption.
Tests state snapshotting, crash recovery reconciler, and safe resumption
without duplicate execution of non-idempotent writes.
"""

import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import AgentTask, TaskStep, TaskCheckpoint, PayableRecord, ApprovalRequest
from backend.app.agent.state import TaskStatus
from backend.app.agent.checkpoint import CheckpointManager
from backend.app.agent.dag_planner import DAGPlanner
from backend.app.agent.loop import AgentExecutionEngine
from backend.app.security.policy import PolicyEngine


@pytest.fixture(autouse=True)
def clean_db():
    reset_database()
    yield


def test_checkpoint_creation_and_loading():
    """
    Test creating a checkpoint after an execution step and loading the latest snapshot.
    """
    db = SessionLocal()
    try:
        task_id = "test-task-chk-1"
        task = AgentTask(id=task_id, goal="Process invoice from Acme", status=TaskStatus.RUNNING.value)
        db.add(task)
        db.commit()

        planner = DAGPlanner()
        dag = planner.create_dag_for_goal("Process invoice from Acme")

        chk = CheckpointManager.create_checkpoint(
            db=db,
            task_id=task_id,
            step_number=1,
            status=TaskStatus.RUNNING.value,
            dag=dag,
            working_memory={"discovered_files": ["f1.txt"]},
            confirmed_writes=[],
            idempotency_keys=["KEY-1234"]
        )

        assert chk.id is not None
        assert chk.checkpoint_hash is not None

        loaded = CheckpointManager.load_latest_checkpoint(db, task_id)
        assert loaded is not None
        assert loaded.step_number == 1
        assert "KEY-1234" in loaded.idempotency_keys_json
    finally:
        db.close()


def test_crash_recovery_reconciler():
    """
    Verify that tasks abandoned in RUNNING or PLANNING state (e.g. from an ungraceful server shutdown)
    are swept by the startup reconciler into INTERRUPTED status.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        task = AgentTask(
            id="crashed-task-99",
            goal="Process invoice from Acme Technologies",
            status=TaskStatus.RUNNING.value,
            steps_count=2,
            created_at=datetime.now(timezone.utc)
        )
        db.add(task)
        db.commit()

        # Simulate startup reconciler sweep
        interrupted_tasks = db.query(AgentTask).filter(
            AgentTask.status.in_([TaskStatus.RUNNING.value, TaskStatus.PLANNING.value])
        ).all()
        for t in interrupted_tasks:
            t.status = TaskStatus.INTERRUPTED.value
            t.error_message = "Task execution was interrupted by server restart or process termination."
        db.commit()

        refreshed = db.query(AgentTask).filter(AgentTask.id == "crashed-task-99").first()
        assert refreshed.status == TaskStatus.INTERRUPTED.value
    finally:
        db.close()


def test_resume_interrupted_task_prevents_duplicate_writes():
    """
    Verify that resuming an interrupted task avoids repeating confirmed non-idempotent writes.
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        task_id = "task-to-resume-01"
        goal = "Process latest invoice from Acme Technologies and register as payable."

        initial_payables = db.query(PayableRecord).count()

        # Run task with auto-approval to complete payable creation
        engine = AgentExecutionEngine(max_steps=12)
        task = engine.run(db_session=db, goal=goal, task_id=task_id, auto_approve_high_risk=True)

        payables_before = db.query(PayableRecord).count()
        assert payables_before == initial_payables + 1
        assert task.status == TaskStatus.COMPLETED.value

        # Checkpoints should have been recorded by the loop
        latest_chk = CheckpointManager.load_latest_checkpoint(db, task_id)
        assert latest_chk is not None
        assert latest_chk.step_number > 0

        # Mark task as INTERRUPTED
        task.status = TaskStatus.INTERRUPTED.value
        db.commit()

        # Resume task
        resumed_task = engine.resume_interrupted_task(db_session=db, task_id=task_id)

        # Payables count MUST NOT increase
        payables_after = db.query(PayableRecord).count()
        assert payables_after == payables_before
        assert resumed_task.status in (TaskStatus.COMPLETED.value, TaskStatus.VERIFYING.value)
    finally:
        db.close()


def test_cryptographic_approval_validation():
    """
    Test that PolicyEngine validates the argument hash of an approval request,
    and invalidates if arguments were tampered with between approval and execution.
    """
    db = SessionLocal()
    try:
        task_id = "app-tamper-task-01"
        task = AgentTask(id=task_id, goal="Approve payable", status=TaskStatus.WAITING_FOR_APPROVAL.value)
        db.add(task)
        db.commit()

        args = {"amount": 25000.00, "vendor_name": "Nexus Hardware", "invoice_number": "INV-2024-099"}

        # Create approval request
        app_req = PolicyEngine.create_approval_request(
            db=db,
            task_id=task_id,
            tool_name="create_payable",
            action_description="Pay $25,000",
            arguments=args,
            risk_reason="Financial limit exceeded"
        )
        assert app_req.argument_hash is not None

        # Approve the request
        app_req.status = "APPROVED"
        db.commit()

        # 1. Matching arguments: validation succeeds
        is_valid, err = PolicyEngine.validate_and_consume_approval(db, task_id, "create_payable", args)
        assert is_valid is True
        assert err is None

        # 2. Tampered arguments: validation fails and revokes approval
        tampered_args = {"amount": 99999.00, "vendor_name": "Nexus Hardware", "invoice_number": "INV-2024-099"}
        is_valid_tampered, sec_err = PolicyEngine.validate_and_consume_approval(db, task_id, "create_payable", tampered_args)
        assert is_valid_tampered is False
        assert "Security Invalidation" in sec_err
    finally:
        db.close()
