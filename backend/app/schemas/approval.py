from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ApprovalResolution(BaseModel):
    approval_id: str
    approved: bool
    approver: Optional[str] = "Finance Director"
    feedback: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    task_id: str
    tool_name: str
    action_description: str
    risk_level: str
    risk_reason: str
    pending_payload: Dict[str, Any] = Field(default_factory=dict)
    status: str
    approver: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
