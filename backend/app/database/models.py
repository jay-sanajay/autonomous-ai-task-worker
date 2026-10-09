"""
AgentOS - SQLAlchemy Database Models.
Implements the sandbox company application schema including vendors, invoices,
payable records with idempotency and uniqueness constraints, and agent execution tracking.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    aliases = Column(Text, nullable=True)  # JSON or comma-separated list of common names
    payment_terms = Column(String(50), default="Net 30")
    category = Column(String(100), default="Technology & Cloud Services")
    status = Column(String(50), default="APPROVED")
    created_at = Column(DateTime, default=utc_now)

    payables = relationship("PayableRecord", back_populates="vendor")


class InvoiceDocument(Base):
    __tablename__ = "invoice_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), unique=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), default="txt")
    file_size_bytes = Column(Integer, default=0)
    vendor_name_hint = Column(String(200), nullable=True)
    is_latest_for_vendor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


class PayableRecord(Base):
    __tablename__ = "payables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_name = Column(String(200), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    invoice_date = Column(String(50), nullable=True)
    due_date = Column(String(50), nullable=False)
    payment_terms = Column(String(50), default="Net 30")
    po_number = Column(String(100), nullable=True)
    
    # Critical idempotency and deduplication key
    idempotency_key = Column(String(150), unique=True, nullable=False, index=True)
    
    status = Column(String(50), default="ENTERED")  # PENDING_APPROVAL, ENTERED, VERIFIED, REJECTED
    created_by = Column(String(100), default="AgentOS_Worker")
    notes = Column(Text, nullable=True)
    verification_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    verified_at = Column(DateTime, nullable=True)

    vendor = relationship("Vendor", back_populates="payables")
    verification_results = relationship("VerificationResult", back_populates="payable")

    # Enforce uniqueness across vendor and invoice number
    __table_args__ = (
        UniqueConstraint("vendor_name", "invoice_number", name="uq_vendor_invoice_number"),
    )


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(String(50), primary_key=True)  # e.g. "task-abc12345"
    goal = Column(Text, nullable=False)
    status = Column(String(50), default="PLANNING")  # PLANNING, RUNNING, WAITING_FOR_APPROVAL, VERIFYING, COMPLETED, FAILED, CANCELLED
    current_plan = Column(Text, default="[]")  # JSON encoded list of plan steps
    working_memory = Column(Text, default="{}")  # JSON encoded discovered entities
    extracted_data = Column(Text, default="{}")  # JSON encoded invoice fields
    final_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    steps_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan", order_by="TaskStep.step_number")
    approvals = relationship("ApprovalRequest", back_populates="task", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    thought = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)
    tool_input = Column(Text, default="{}")  # JSON encoded sanitized inputs
    tool_output = Column(Text, default="{}")  # JSON encoded outputs
    status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILED, RETRYING, RECOVERED, WAITING_APPROVAL
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)

    task = relationship("AgentTask", back_populates="steps")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(50), primary_key=True)  # e.g. "APP-XYZ123"
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    action_description = Column(String(255), nullable=False)
    risk_level = Column(String(20), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    risk_reason = Column(Text, nullable=False)
    pending_payload = Column(Text, default="{}")  # JSON encoded
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED
    approver = Column(String(100), nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    task = relationship("AgentTask", back_populates="approvals")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    payable_id = Column(Integer, ForeignKey("payables.id"), nullable=True)
    verified = Column(Boolean, default=False)
    amount_matched = Column(Boolean, default=False)
    due_date_matched = Column(Boolean, default=False)
    vendor_matched = Column(Boolean, default=False)
    invoice_num_matched = Column(Boolean, default=False)
    field_comparisons = Column(Text, default="{}")  # JSON comparison diff
    verification_token = Column(String(100), nullable=True)
    audit_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    task = relationship("AgentTask", back_populates="verification_results")
    payable = relationship("PayableRecord", back_populates="verification_results")
