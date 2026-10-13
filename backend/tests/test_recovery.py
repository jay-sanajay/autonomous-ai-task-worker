import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord, TaskStep
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_transient_tool_failure_and_successful_retry():
    """
    Test recoverable failure:
    Inject a simulated 503 Service Overloaded error into create_payable.
    The agent detects retryable=True, applies backoff, dynamically retries, and succeeds.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process latest invoice from Acme Technologies and register as payable."

        # simulate_fault=True triggers the 503 error on first call to create_payable
        task = engine.run(db, goal=goal, auto_approve_high_risk=True, simulate_fault=True)

        assert task.status == "COMPLETED"

        # Check that retry was logged in task steps
        steps = db.query(TaskStep).filter(TaskStep.task_id == task.id).all()
        statuses = [s.status for s in steps]
        assert "RETRYING" in statuses or "RECOVERED" in statuses

        # The payable record should still be created and verified
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-001", "INV-2026-001"])).first()
        assert payable is not None
        assert payable.status == "VERIFIED"
    finally:
        db.close()


def test_permanent_tool_failure_handling():
    """
    Test permanent unrecoverable failure:
    Requesting a non-existent document file path.
    The agent observes the failure and halts gracefully without false claims.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        # Request reading non-existent file directly via tool
        res = engine.registry.execute("read_invoice", db, {"file_path": "sandbox_data/invoices/NON_EXISTENT_FILE.txt"})

        assert res.success is False
        assert "not found" in res.error.lower()
        assert res.retryable is False
    finally:
        db.close()
