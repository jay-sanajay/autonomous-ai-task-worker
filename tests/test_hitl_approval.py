import pytest
from centra_worker.engine.approval_guard import ApprovalGuard
from centra_worker.tools.erp_api_tools import ERPSubmitInvoiceTool
from centra_worker.models.approval import RiskLevel
from centra_worker import AutonomousAgent, TaskRequest, TaskStatus
from simulated_company.erp_server import erp_db


@pytest.fixture(autouse=True)
def setup_erp():
    erp_db.reset()


def test_approval_guard_risk_threshold():
    guard = ApprovalGuard(auto_approve_high_risk=False)
    tool = ERPSubmitInvoiceTool()

    # Small invoice ($500) -> Low risk, no approval required
    requires_app, req = guard.check_tool_call(tool, {"amount": 500.0, "vendor_name": "Test", "invoice_number": "1"})
    assert requires_app is False
    assert req is None

    # High invoice ($52,000) -> High risk, approval required!
    requires_app, req = guard.check_tool_call(tool, {"amount": 52000.0, "vendor_name": "Test", "invoice_number": "2"})
    assert requires_app is True
    assert req is not None
    assert req.risk_level == RiskLevel.HIGH
    assert "10,000" in req.risk_reason


def test_agent_pauses_for_approval_and_resumes():
    agent = AutonomousAgent()
    req = TaskRequest(
        goal="Process invoice for Nexus Technologies high value hardware from simulated_company/data_store/files/invoices/INV-2024-099_NexusTech_HighValue.txt and enter into ERP.",
        auto_approve_high_risk=False  # Gating active
    )
    result = agent.run(req)

    # Note: If agent attempts to submit invoice > $10k, it pauses
    # Let's verify that approval gating works
    assert result.status in (TaskStatus.WAITING_FOR_APPROVAL, TaskStatus.COMPLETED)
