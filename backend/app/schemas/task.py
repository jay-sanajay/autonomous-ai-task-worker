from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    goal: str = Field(..., description="Natural language business request")
    auto_approve_high_risk: bool = Field(default=False, description="Automatically approve high-value actions")
    simulate_fault: bool = Field(default=False, description="Simulate transient 503 error for retry testing")


class TaskStepResponse(BaseModel):
    id: Optional[int] = None
    step_number: int
    thought: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    created_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    goal: str
    status: str
    current_plan: List[Dict[str, Any]] = Field(default_factory=list)
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    final_summary: Optional[str] = None
    error_message: Optional[str] = None
    steps_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskDetailResponse(TaskResponse):
    steps: List[TaskStepResponse] = Field(default_factory=list)
    pending_approval: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
