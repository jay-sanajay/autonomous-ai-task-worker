import pytest
from backend.app.database.session import SessionLocal, reset_database
from backend.app.database.models import TaskItem, VerificationResult, AgentTask
from backend.app.agent.loop import AgentExecutionEngine


@pytest.fixture(autouse=True)
def setup_sandbox():
    reset_database()


def test_hr_email_workflow_end_to_end():
    """
    Test end-to-end execution of the HR Interview Email & Task List workflow:
    'Find the latest email from HR, extract the interview date and meeting link, and add the event to my task list'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Find the latest email from HR, extract the interview date and meeting link, and add the event to my task list"

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        assert task.steps_count >= 5

        # Check created TaskItem record in SQLite database
        task_item = db.query(TaskItem).order_by(TaskItem.id.desc()).first()
        assert task_item is not None
        assert "Interview" in task_item.title
        assert "2024-10-24" in task_item.due_date
        assert "02:00 PM" in task_item.due_date
        assert task_item.meeting_link == "https://meet.google.com/abc-defg-hij"
        assert task_item.priority == "HIGH"
        assert task_item.status == "PENDING"

        # Check independent verification record
        v_res = db.query(VerificationResult).filter(VerificationResult.task_id == task.id).first()
        assert v_res is not None
        assert v_res.verified is True
        assert "VERIFIED-TASK-" in v_res.verification_token
        assert v_res.task_item_id == task_item.id

        # Verify summary output
        assert task.final_summary is not None
        assert "https://meet.google.com/abc-defg-hij" in task.final_summary
        assert "2024-10-24" in task.final_summary
    finally:
        db.close()


def test_hr_email_alternative_phrasing():
    """
    Test alternative phrasing:
    'Read my interview emails and create a task for each upcoming interview.'
    """
    db = SessionLocal()
    try:
        engine = AgentExecutionEngine()
        goal = "Read my interview emails and create a task for each upcoming interview."

        task = engine.run(db, goal=goal, auto_approve_high_risk=True)

        assert task.status == "COMPLETED"
        task_item = db.query(TaskItem).order_by(TaskItem.id.desc()).first()
        assert task_item is not None
        assert "2024-10-24" in task_item.due_date
        assert task_item.meeting_link == "https://meet.google.com/abc-defg-hij"
    finally:
        db.close()
