"""
AgentOS - Regression Tests for Provider Safety & Goal Rejection.
Verifies that unsupported or out-of-domain goals are safely halted and never
routed into unintended workflows (e.g. paying invoices).
"""

import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.agent.provider import DeterministicFallbackProvider, AgentStepDecision
from backend.app.agent.loop import AgentExecutionEngine
from backend.app.agent.state import TaskStatus


@pytest.fixture(autouse=True)
def clean_db():
    reset_database()
    yield


def test_unsupported_goal_is_safely_rejected():
    """
    Ensure out-of-scope requests (e.g. booking flights, hacking) are explicitly
    rejected with REJECTED_UNSUPPORTED rather than defaulting to invoice processing.
    """
    provider = DeterministicFallbackProvider()
    unsupported_goals = [
        "Book a one-way flight from New York to London departing tomorrow.",
        "Deploy the backend microservices to AWS production cluster.",
        "Scrape all user profiles from LinkedIn.",
        "Write a 500-word sci-fi novel about space exploration."
    ]

    for goal in unsupported_goals:
        decision = provider.decide_next_step(
            goal=goal,
            plan_summary="",
            working_memory={},
            step_history=[],
            tools_schema=[]
        )

        assert decision.is_finished is True, f"Goal '{goal}' should have finished immediately with rejection"
        assert decision.provider_mode == "REJECTED_UNSUPPORTED"
        assert "blocked" in decision.final_summary.lower() or "unsupported" in decision.final_summary.lower()
        assert decision.tool_name is None, f"Goal '{goal}' should not propose any tool"


def test_unsupported_goal_execution_loop_produces_failed_task():
    """
    When an unsupported goal is run through AgentExecutionEngine,
    the task must terminate with FAILED status and zero database mutations.
    """
    db = SessionLocal()
    try:
        from backend.app.database.models import PayableRecord
        initial_payables = db.query(PayableRecord).count()

        engine = AgentExecutionEngine()
        task = engine.run(
            db_session=db,
            goal="Book a roundtrip airline flight to Tokyo departing next Monday.",
            auto_approve_high_risk=True
        )

        assert task.status == TaskStatus.FAILED.value
        assert "unsupported" in (task.final_summary or "").lower() or "blocked" in (task.final_summary or "").lower()

        # Assert no payables were created
        final_payables = db.query(PayableRecord).count()
        assert final_payables == initial_payables
    finally:
        db.close()


def test_provider_mode_attribution():
    """
    Assert that decisions carry truthful provider_mode metadata.
    """
    provider = DeterministicFallbackProvider()
    decision = provider.decide_next_step(
        goal="Find the latest invoice from Acme Technologies and register as payable.",
        plan_summary="",
        working_memory={},
        step_history=[],
        tools_schema=[]
    )
    assert decision.provider_mode == "DETERMINISTIC_TEMPLATE"
    assert decision.tool_name == "list_invoice_files"
