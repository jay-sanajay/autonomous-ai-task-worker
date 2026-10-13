import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord, AgentTask
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_primary_acme_invoice_workflow_end_to_end():
    """
    Primary demonstration workflow test:
    'Find the latest invoice from Acme Technologies, extract the invoice number,
     amount, due date, and vendor, create a payable record in the company system,
     verify that the record was saved correctly, and summarize the result.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = (
            "Find the latest invoice from Acme Technologies, extract the invoice number, "
            "amount, due date, and vendor, create a payable record in the company system, "
            "verify that the record was saved correctly, and summarize the result."
        )

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert task.steps_count >= 5

        # Check payable record in database
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-001", "INV-2026-001"])).first()
        assert payable is not None
        assert payable.vendor_name == "Acme Technologies Inc."
        assert payable.amount == 8450.00
        assert "2026-" in payable.due_date or "2024-" in payable.due_date
        assert payable.status == "VERIFIED"
        assert "VERIFIED-" in payable.verification_hash
    finally:
        db.close()


def test_alternative_natural_language_phrasing():
    """
    Test generalization across different phrasing:
    'Find the newest Acme invoice and register it as a payable.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Find the newest Acme invoice and register it as a payable."
        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        payable = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-001", "INV-2026-001"])).first()
        assert payable is not None
        assert payable.status == "VERIFIED"
    finally:
        db.close()
