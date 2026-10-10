"""
AgentOS - Task-Scoped Working Memory and Execution Trace.
Persists context, discovered entities, and tool outputs across execution steps.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskMemory(BaseModel):
    model_config = ConfigDict(extra="allow")

    task_id: str
    original_goal: str
    discovered_files: List[Dict[str, Any]] = Field(default_factory=list)
    target_invoice_file: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    matched_vendor: Optional[Dict[str, Any]] = None
    existing_invoice_record: Optional[Dict[str, Any]] = None
    created_payable: Optional[Dict[str, Any]] = None
    verification_details: Optional[Dict[str, Any]] = None
    pending_approval_id: Optional[str] = None
    approval_resolved: bool = False
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    scratchpad_notes: List[str] = Field(default_factory=list)

    # Multi-domain memory fields
    discovered_emails: List[Dict[str, Any]] = Field(default_factory=list)
    target_email_file: Optional[str] = None
    extracted_event: Optional[Dict[str, Any]] = None
    created_task_item: Optional[Dict[str, Any]] = None
    verified_task_item: Optional[Dict[str, Any]] = None
    csv_inspection: Optional[Dict[str, Any]] = None
    csv_analysis: Optional[Dict[str, Any]] = None
    generated_report: Optional[Dict[str, Any]] = None
    support_tickets: Optional[Dict[str, Any]] = None
    updated_ticket: Optional[Dict[str, Any]] = None
    inventory_audit: Optional[Dict[str, Any]] = None
    created_purchase_request: Optional[Dict[str, Any]] = None

    def add_note(self, note: str):
        now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.scratchpad_notes.append(f"[{now_time}] {note}")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
