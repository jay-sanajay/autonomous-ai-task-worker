import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_step_limit_bounded_execution():
    """
    Test that the execution engine strictly respects max_steps limits
    and halts rather than executing infinite loops.
    """
    db = SessionLocal()
    try:
        # Engine with strict max_steps = 2
        engine = AgentExecutionEngine(max_steps=2)
        goal = "Find the latest invoice from Acme Technologies and register as payable."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.steps_count <= 2
    finally:
        db.close()
