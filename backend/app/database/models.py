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
    argument_hash = Column(String(64), nullable=True)  # SHA256 of exact payload arguments
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED
    approver = Column(String(100), nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    task = relationship("AgentTask", back_populates="approvals")


class TaskItem(Base):
    __tablename__ = "task_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(String(100), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED
    priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH
    source_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    verification_results = relationship("VerificationResult", back_populates="task_item")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_code = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(200), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    product_name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), default="General")
    current_stock = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=10)
    unit_price = Column(Float, default=0.0)
    status = Column(String(50), default="IN_STOCK")  # IN_STOCK, LOW_STOCK, OUT_OF_STOCK
    created_at = Column(DateTime, default=utc_now)

    purchase_requests = relationship("PurchaseRequest", back_populates="item")


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_code = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    estimated_total = Column(Float, default=0.0)
    status = Column(String(50), default="DRAFT")  # DRAFT, PENDING_APPROVAL, APPROVED
    created_at = Column(DateTime, default=utc_now)

    item = relationship("InventoryItem", back_populates="purchase_requests")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    payable_id = Column(Integer, ForeignKey("payables.id"), nullable=True)
    task_item_id = Column(Integer, ForeignKey("task_items.id"), nullable=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
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
    task_item = relationship("TaskItem", back_populates="verification_results")
    contract = relationship("ContractRecord", back_populates="verification_results")


class ContractRecord(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(250), nullable=False)
    parties = Column(String(250), nullable=False)
    effective_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=False)
    contract_value = Column(Float, default=0.0)
    governing_law = Column(String(100), nullable=True)
    missing_clauses = Column(Text, default="[]")  # JSON list of missing clauses
    risk_score = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="AUDITED")  # DRAFT, AUDITED, ACTIVE, EXPIRED
    source_file = Column(String(250), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    verification_results = relationship("VerificationResult", back_populates="contract")


class TaskCheckpoint(Base):
    __tablename__ = "task_checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("agent_tasks.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    dag_state_json = Column(Text, default="{}")  # Serialized PlanDAG execution state
    working_memory_json = Column(Text, default="{}")  # Working memory snapshot
    confirmed_writes_json = Column(Text, default="[]")  # Confirmed non-idempotent writes
    idempotency_keys_json = Column(Text, default="[]")  # Active idempotency keys
    checkpoint_hash = Column(String(64), nullable=True)  # Integrity checksum
    created_at = Column(DateTime, default=utc_now)


class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), nullable=False, index=True)
    goal = Column(Text, nullable=False)
    outcome = Column(String(50), nullable=False)  # SUCCESS, FAILED, CANCELLED
    failed_strategies = Column(Text, default="[]")  # JSON list of failed attempts
    recovery_methods = Column(Text, default="[]")  # JSON list of successful recoveries
    verification_token = Column(String(100), nullable=True)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)


class SemanticMemory(Base):
    __tablename__ = "semantic_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # WORKFLOW, TOOL_FACT, APPROVED_PROCEDURE
    fact_key = Column(String(100), nullable=False, index=True)
    fact_content = Column(Text, nullable=False)
    provenance = Column(String(255), default="System Engine")
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

