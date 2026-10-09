from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanStepStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECOVERED = "RECOVERED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    step_id: int
    title: str = Field(..., description="Short title of this action")
    description: str = Field(..., description="Detailed description of what to achieve")
    expected_tool: Optional[str] = None
    status: PlanStepStatus = PlanStepStatus.PENDING
    result_summary: Optional[str] = None


class ExecutionPlan(BaseModel):
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    replan_count: int = 0

    def get_current_step(self) -> Optional[PlanStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def mark_step_completed(self, summary: str):
        if 0 <= self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].status = PlanStepStatus.COMPLETED
            self.steps[self.current_step_index].result_summary = summary
            self.current_step_index += 1

    def mark_step_failed(self, error: str):
        if 0 <= self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].status = PlanStepStatus.FAILED
            self.steps[self.current_step_index].result_summary = f"Failed: {error}"
