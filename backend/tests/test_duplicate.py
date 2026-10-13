import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import PayableRecord
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_duplicate_invoice_detection():
    """
    Test duplicate invoice prevention:
    INV-2023-042 is pre-seeded in the database.
    The agent must discover it already exists and avoid creating a duplicate payable.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process old invoice INV-2023-042 from Acme Technologies and register as payable."
        initial_payables_count = db.query(PayableRecord).count()

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert "Duplicate" in task.final_summary or "already registered" in task.final_summary

        # Payables count must NOT increase
        final_payables_count = db.query(PayableRecord).count()
        assert final_payables_count == initial_payables_count
    finally:
        db.close()


def test_repeated_task_submission_idempotency():
    """
    Test submitting the exact same invoice processing task twice.
    First run creates the record; second run safely halts without duplicate writes.
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Process latest invoice INV-2024-001 from Acme Technologies."

        # First run
        t1 = engine.run(db, goal=goal, auto_approve_high_risk=True)
        assert t1.status == "COMPLETED"
        count_after_first = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-001", "INV-2026-001"])).count()
        assert count_after_first == 1

        # Second run
        t2 = engine.run(db, goal=goal, auto_approve_high_risk=True)
        assert t2.status == "COMPLETED"
        assert "Duplicate" in t2.final_summary

        count_after_second = db.query(PayableRecord).filter(PayableRecord.invoice_number.in_(["INV-2024-001", "INV-2026-001"])).count()
        assert count_after_second == 1
    finally:
        db.close()
