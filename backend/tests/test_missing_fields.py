import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_missing_required_fields_handling():
    """
    Test invoice with missing required field (missing amount):
    INV-2024-002 has amount 'PENDING_CALCULATION / TBD'.
    The agent must detect the missing field and halt safely without inventing numbers.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process incomplete invoice INV-2024-002 from Acme Technologies."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert "missing required fields" in task.final_summary.lower() or "clarification" in task.final_summary.lower()

        # No payable record should be created
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number == "INV-2024-002").first()
        assert payable is None
    finally:
        db.close()
