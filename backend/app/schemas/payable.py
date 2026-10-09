from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PayableCreate(BaseModel):
    vendor_name: str = Field(..., description="Full vendor name")
    invoice_number: str = Field(..., description="Unique invoice identifier")
    amount: float = Field(..., description="Total invoice amount")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, GBP)")
    due_date: str = Field(..., description="Due date in YYYY-MM-DD format")
    invoice_date: Optional[str] = Field(default=None, description="Invoice date in YYYY-MM-DD format")
    po_number: Optional[str] = Field(default=None, description="PO reference number")
    payment_terms: Optional[str] = Field(default="Net 30", description="Payment terms")
    notes: Optional[str] = Field(default="Created by AgentOS Worker")


class PayableResponse(BaseModel):
    id: int
    vendor_id: Optional[int] = None
    vendor_name: str
    invoice_number: str
    amount: float
    currency: str
    invoice_date: Optional[str] = None
    due_date: str
    payment_terms: str
    po_number: Optional[str] = None
    idempotency_key: str
    status: str
    created_by: str
    verification_hash: Optional[str] = None
    created_at: datetime
    verified_at: Optional[datetime] = None


class VerificationResultSchema(BaseModel):
    verified: bool
    amount_matched: bool
    due_date_matched: bool
    vendor_matched: bool
    invoice_num_matched: bool
    payable_id: Optional[int] = None
    verification_token: Optional[str] = None
    field_comparisons: Dict[str, Any] = Field(default_factory=dict)
    audit_notes: Optional[str] = None
