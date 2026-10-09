import pytest
from centra_worker import AutonomousAgent, TaskRequest, TaskStatus
from centra_worker.engine.failure_handler import FailureHandler, ErrorCategory
from simulated_company.erp_server import erp_db


def test_failure_handler_categorization():
    handler = FailureHandler()
    is_fail = handler.is_failure({"status": "transient_error", "error": "Gateway Error 503: Service Overloaded"})
    assert is_fail is True

    cat, msg = handler.categorize_error("erp_submit_invoice", {"status": "transient_error", "error": "503 Server Overloaded"})
    assert cat == ErrorCategory.TRANSIENT_503_OR_NETWORK

    rec = handler.decide_recovery("erp_submit_invoice", {}, {"status": "transient_error", "error": "503"})
    assert rec["action"] == "RETRY_WITH_BACKOFF"


def test_agent_transient_failure_recovery():
    erp_db.reset()
    agent = AutonomousAgent()

    # Request with simulate_fault=True will inject a 503 on the first ERP submission attempt
    req = TaskRequest(
        goal="Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done.",
        simulate_fault=True,
        auto_approve_high_risk=True
    )
    result = agent.run(req)

    assert result.status == TaskStatus.COMPLETED
    # Check that retry/recovery was recorded in step history
    statuses = [s.status for s in result.step_history]
    assert "RETRYING" in statuses or "RECOVERED" in statuses
    assert result.evidence is not None
    assert result.evidence.verified is True
