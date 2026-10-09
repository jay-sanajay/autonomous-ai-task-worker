from __future__ import annotations
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepRecord(BaseModel):
    step_number: int
    thought: str = Field(..., description="Agent reasoning before taking action")
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    status: str = "SUCCESS"  # SUCCESS, FAILED, RETRYING, RECOVERED, WAITING_APPROVAL
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvidenceReceipt(BaseModel):
    verified: bool
    record_id: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    due_date: Optional[str] = None
    verification_hash: Optional[str] = None
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit_notes: Optional[str] = None
    evidence_payload: Optional[Dict[str, Any]] = None


class TaskRequest(BaseModel):
    goal: str = Field(..., description="Natural language user task")
    session_id: Optional[str] = None
    auto_approve_high_risk: bool = False
    simulate_fault: bool = False  # triggers ERP 503 transient error to test retry/recovery
    preferred_tool: Optional[str] = None  # e.g. "api" or "browser"


class TaskResult(BaseModel):
    task_id: str
    goal: str
    status: TaskStatus
    summary: str
    steps_executed: int
    step_history: List[StepRecord] = Field(default_factory=list)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    evidence: Optional[EvidenceReceipt] = None
    approval_required: bool = False
    pending_approval: Optional[Dict[str, Any]] = None
    total_time_seconds: float = 0.0
