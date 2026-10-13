import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord, ApprovalRequest, AgentTask
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_consequential_action_pauses_for_approval():
    """
    Test that high-value transactions (> $10,000) pause execution
    and create a pending approval ticket.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process high value invoice INV-2024-099 from Nexus Hardware Systems ($48,500.00)."

        task = engine.run(db, goal=goal, auto_approve_high_risk=False)

        assert task.status == "WAITING_FOR_APPROVAL"

        # Check pending approval request exists
        app_req = db.query(ApprovalRequest).filter(ApprovalRequest.task_id == task.id).first()
        assert app_req is not None
        assert app_req.status == "PENDING"
        assert app_req.risk_level == "HIGH"

        # Payable must NOT be created yet
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-099", "INV-2026-099"])).first()
        assert payable is None
    finally:
        db.close()


def test_approval_resumption_and_completion():
    """
    Test resuming task after explicit human authorization.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process high value invoice INV-2024-099 from Nexus Hardware Systems ($48,500.00)."

        task = engine.run(db, goal=goal, auto_approve_high_risk=False)
        assert task.status == "WAITING_FOR_APPROVAL"

        # Resume with approval
        resumed_task = engine.resume_task(
            db,
            task_id=task.id,
            approved=True,
            approver="CFO Sarah Connor",
            feedback="Authorized under Q4 Compute Expansion Budget"
        )

        assert resumed_task.status == "COMPLETED"

        # Now the payable must exist
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-099", "INV-2026-099"])).first()
        assert payable is not None
        assert payable.amount == 48500.00
        assert payable.status == "VERIFIED"
    finally:
        db.close()


def test_approval_rejection_cancels_task():
    """
    Test that rejecting the approval cancels the task without writing payables.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process high value invoice INV-2024-099 from Nexus Hardware Systems."

        task = engine.run(db, goal=goal, auto_approve_high_risk=False)
        assert task.status == "WAITING_FOR_APPROVAL"

        # Reject
        rejected_task = engine.resume_task(
            db,
            task_id=task.id,
            approved=False,
            approver="CFO Sarah Connor",
            feedback="Rejected: Unbudgeted capital expense"
        )

        assert rejected_task.status == "CANCELLED"
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number == "INV-2024-099").first()
        assert payable is None
    finally:
        db.close()
