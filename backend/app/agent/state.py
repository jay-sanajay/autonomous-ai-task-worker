"""
AgentOS - Explicit Task and Execution States.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    RETRYING = "RETRYING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    RECOVERED = "RECOVERED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    step_id: int
    title: str
    description: str
    expected_tool: Optional[str] = None
    status: StepStatus = StepStatus.SUCCESS
    result_summary: Optional[str] = None


class GoalRepresentation(BaseModel):
    objective: str
    required_outcome: str
    constraints: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    current_observations: List[str] = Field(default_factory=list)
    pending_actions: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
