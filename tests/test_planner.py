import pytest
from centra_worker.engine.planner import GoalPlanner
from centra_worker.models.plan import PlanStepStatus


def test_goal_decomposition_invoice_task():
    planner = GoalPlanner()
    goal = "Find the latest invoice from Company X, extract the amount and due date, enter it into our internal system, and tell me once it is done."
    plan = planner.create_initial_plan(goal)

    assert plan.goal == goal
    assert len(plan.steps) >= 4
    step_titles = [s.title for s in plan.steps]
    assert any("Discover" in t for t in step_titles)
    assert any("Extract" in t or "Analyze" in t for t in step_titles)
    assert any("Post" in t or "Internal" in t for t in step_titles)
    assert any("Verification" in t for t in step_titles)


def test_dynamic_recovery_insertion():
    planner = GoalPlanner()
    plan = planner.create_initial_plan("Test invoice goal")
    initial_length = len(plan.steps)

    planner.insert_recovery_step(plan, reason="503 Gateway Retry", tool_name="erp_submit_invoice")

    assert len(plan.steps) == initial_length + 1
    assert plan.replan_count == 1
    inserted = plan.steps[1]
    assert "Self-Correction" in inserted.title
    assert inserted.status == PlanStepStatus.PENDING
