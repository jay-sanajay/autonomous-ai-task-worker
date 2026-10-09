import pytest
from centra_worker import AutonomousAgent, TaskRequest, TaskStatus
from simulated_company.erp_server import erp_db


@pytest.fixture(autouse=True)
def clean_database():
    erp_db.reset()


def test_end_to_end_company_x_invoice_processing():
    """
    Primary problem statement benchmark test:
    'Find the latest invoice from Company X, extract the amount and due date,
     enter it into our internal system, and tell me once it is done.'
    """
    agent = AutonomousAgent()
    request = TaskRequest(
        goal="Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done.",
        auto_approve_high_risk=True
    )

    result = agent.run(request)

    # 1. Verification of Task Status
    assert result.status == TaskStatus.COMPLETED
    assert result.steps_executed >= 4

    # 2. Verification of Discovered / Extracted Data
    extracted = result.extracted_data.get("extracted_invoice", {})
    assert extracted.get("invoice_number") == "INV-2024-089"
    assert extracted.get("amount") == 14850.00
    assert extracted.get("due_date") == "2024-10-31"

    # 3. Ground Truth Verification Check
    assert result.evidence is not None
    assert result.evidence.verified is True
    assert result.evidence.record_id is not None
    assert result.evidence.amount == 14850.00
    assert result.evidence.due_date == "2024-10-31"
    assert "VERIFIED-" in result.evidence.verification_hash

    # 4. Verify system of record state directly
    invoices = erp_db.get_invoices(invoice_num="INV-2024-089")
    assert len(invoices) == 1
    assert invoices[0]["amount"] == 14850.00
    assert invoices[0]["due_date"] == "2024-10-31"
    assert invoices[0]["status"] == "ENTERED"


def test_browser_automation_invoice_processing():
    """
    Alternative tooling benchmark test using Browser Web Portal form submission.
    """
    agent = AutonomousAgent()
    request = TaskRequest(
        goal="Use browser automation on internal web portal to enter the latest Company X invoice.",
        auto_approve_high_risk=True
    )

    result = agent.run(request)

    assert result.status == TaskStatus.COMPLETED
    assert result.evidence is not None
    assert result.evidence.verified is True
    assert result.evidence.invoice_number == "INV-2024-089"
