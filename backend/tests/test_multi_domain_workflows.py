import os
import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import SupportTicket, PurchaseRequest, AgentTask
from backend.app.agent.loop import AgentExecutionEngine

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_sales_csv_analysis_workflow():
    """
    Test sales CSV analysis and report generation:
    'Analyze the sales CSV, identify the top five products by revenue, check for missing data, and generate a report.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Analyze the sales CSV, identify the top five products by revenue, check for missing data, and generate a report."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert task.steps_count >= 3

        # Check report file was generated
        report_path = os.path.join(PROJECT_ROOT, "sandbox_data", "reports", "q3_sales_analysis_report.md")
        assert os.path.exists(report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Total Revenue" in content
            assert "Top 5 Products" in content
    finally:
        db.close()


def test_customer_support_ticket_triage():
    """
    Test support ticket retrieval and status update:
    'Find unresolved customer tickets, prioritize them, and update their statuses.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Find unresolved customer tickets, prioritize them, and update their statuses."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        # Check that at least one ticket was prioritized
        crit_ticket = db.query(SupportTicket).filter(SupportTicket.priority == "CRITICAL").first()
        assert crit_ticket is not None
        assert crit_ticket.status == "IN_PROGRESS"
    finally:
        db.close()


def test_inventory_low_stock_purchase_request():
    """
    Test inventory low-stock audit and purchase request generation:
    'Check inventory, identify low-stock products, and create draft purchase requests.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Check inventory, identify low-stock products, and create draft purchase requests."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        # Check purchase request created
        pr = db.query(PurchaseRequest).order_by(PurchaseRequest.id.desc()).first()
        assert pr is not None
        assert pr.status == "DRAFT"
        assert pr.quantity > 0
        assert pr.estimated_total > 0
    finally:
        db.close()
