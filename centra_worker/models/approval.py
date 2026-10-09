from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalRequest(BaseModel):
    approval_id: str
    tool_name: str
    action_description: str
    risk_level: RiskLevel
    risk_reason: str
    pending_payload: Dict[str, Any]
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    user_feedback: Optional[str] = None
