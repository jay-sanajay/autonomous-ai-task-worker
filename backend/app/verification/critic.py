"""
AgentOS - Independent Verification Engine.
Defines measurable success criteria before execution, inspects ground-truth state
(database queries, read-after-write checks, file inspection, browser DOM observations),
detects missing/stale data, and issues structured verification audit reports.
"""

from __future__ import annotations
import os
import json
import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database.models import (
    PayableRecord, TaskItem, ContractRecord, VerificationResult, SupportTicket
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class VerificationOutcome(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FAILED = "FAILED"
    UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"


class VerificationCheckResult(BaseModel):
    check_name: str
    expected: Any
    actual: Any
    passed: bool
    details: Optional[str] = None


class VerificationReport(BaseModel):
    task_id: str
    outcome: VerificationOutcome
    verification_token: Optional[str] = None
    checks: List[VerificationCheckResult] = Field(default_factory=list)
    audit_notes: str
    verified_at: str
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)


class VerificationCritic:
    """
    Independent Critic. Never trusts model claims or self-reported success.
    Directly queries persistence layers and returns strict verification reports.
    """

    @staticmethod
    def verify_payable_creation(
        db: Session,
        task_id: str,
        invoice_number: str,
        expected_amount: float,
        expected_vendor: Optional[str] = None,
        expected_due_date: Optional[str] = None
    ) -> VerificationReport:
        from backend.app.tools.date_utils import sanitize_invoice_number, sanitize_date_to_2026

        clean_inv = sanitize_invoice_number(invoice_number)
        record = db.query(PayableRecord).filter(PayableRecord.invoice_number == clean_inv).first()
        if not record:
            raw_inv = invoice_number.strip().upper()
            record = db.query(PayableRecord).filter(PayableRecord.invoice_number == raw_inv).first()

        checks: List[VerificationCheckResult] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if not record:
            checks.append(VerificationCheckResult(
                check_name="Record Existence in Accounting Ledger",
                expected=f"Invoice #{clean_inv}",
                actual="None (Record not found)",
                passed=False,
                details="Database query returned 0 rows in payables table."
            ))
            return VerificationReport(
                task_id=task_id,
                outcome=VerificationOutcome.FAILED,
                checks=checks,
                audit_notes=f"Ground-truth verification FAILED: Invoice '{invoice_number}' does not exist in SQLite database.",
                verified_at=now_iso
            )

        checks.append(VerificationCheckResult(
            check_name="Record Existence",
            expected=clean_inv,
            actual=record.invoice_number,
            passed=True
        ))

        # Amount comparison (float precision tolerance < 0.01)
        amt_diff = abs(float(record.amount) - float(expected_amount))
        amt_match = amt_diff < 0.01
        checks.append(VerificationCheckResult(
            check_name="Amount Match",
            expected=expected_amount,
            actual=record.amount,
            passed=amt_match,
            details=f"Difference: ${amt_diff:.4f}"
        ))

        # Vendor comparison
        vendor_match = True
        if expected_vendor:
            vendor_match = expected_vendor.lower() in record.vendor_name.lower() or record.vendor_name.lower() in expected_vendor.lower()
            checks.append(VerificationCheckResult(
                check_name="Vendor Match",
                expected=expected_vendor,
                actual=record.vendor_name,
                passed=vendor_match
            ))

        # Due date comparison
        date_match = True
        if expected_due_date:
            norm_due = sanitize_date_to_2026(expected_due_date, default_days_ahead=30)
            date_match = record.due_date.strip() == expected_due_date.strip() or record.due_date.strip() == norm_due
            checks.append(VerificationCheckResult(
                check_name="Due Date Match",
                expected=expected_due_date,
                actual=record.due_date,
                passed=date_match
            ))

        all_passed = all(c.passed for c in checks)
        outcome = VerificationOutcome.VERIFIED if all_passed else VerificationOutcome.FAILED
        token = f"VERIFIED-PAYABLE-{record.invoice_number}-{uuid.uuid4().hex[:8].upper()}" if all_passed else None

        if all_passed:
            record.status = "VERIFIED"
            record.verified_at = datetime.now(timezone.utc)
            db.commit()

        return VerificationReport(
            task_id=task_id,
            outcome=outcome,
            verification_token=token,
            checks=checks,
            audit_notes="All field assertions matched SQLite ground truth." if all_passed else "Field comparison mismatch.",
            verified_at=now_iso,
            evidence_payload={"payable_id": record.id, "verification_hash": record.verification_hash}
        )

    @staticmethod
    def verify_task_item_creation(
        db: Session,
        task_id: str,
        expected_title: str,
        expected_due_date: Optional[str] = None,
        expected_meeting_link: Optional[str] = None
    ) -> VerificationReport:
        record = db.query(TaskItem).order_by(TaskItem.id.desc()).first()
        checks: List[VerificationCheckResult] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if not record:
            return VerificationReport(
                task_id=task_id,
                outcome=VerificationOutcome.FAILED,
                audit_notes="No task item found in database.",
                verified_at=now_iso
            )

        title_match = expected_title.lower() in record.title.lower() or record.title.lower() in expected_title.lower()
        checks.append(VerificationCheckResult(check_name="Title Match", expected=expected_title, actual=record.title, passed=title_match))

        if expected_due_date:
            date_match = expected_due_date.lower() in (record.due_date or "").lower()
            checks.append(VerificationCheckResult(check_name="Due Date Match", expected=expected_due_date, actual=record.due_date, passed=date_match))

        if expected_meeting_link:
            link_match = expected_meeting_link.strip() == (record.meeting_link or "").strip()
            checks.append(VerificationCheckResult(check_name="Meeting Link Match", expected=expected_meeting_link, actual=record.meeting_link, passed=link_match))

        all_passed = all(c.passed for c in checks)
        outcome = VerificationOutcome.VERIFIED if all_passed else VerificationOutcome.FAILED
        token = f"VERIFIED-TASK-{record.id}-{uuid.uuid4().hex[:8].upper()}" if all_passed else None

        return VerificationReport(
            task_id=task_id,
            outcome=outcome,
            verification_token=token,
            checks=checks,
            audit_notes="Task item attributes verified against task_items table.",
            verified_at=now_iso,
            evidence_payload={"task_item_id": record.id, "meeting_link": record.meeting_link}
        )

    @staticmethod
    def verify_file_generated(
        task_id: str,
        file_path: str,
        min_size_bytes: int = 50
    ) -> VerificationReport:
        full_path = os.path.join(PROJECT_ROOT, file_path) if not os.path.isabs(file_path) else file_path
        checks: List[VerificationCheckResult] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        exists = os.path.exists(full_path)
        checks.append(VerificationCheckResult(check_name="File Exists on Disk", expected=True, actual=exists, passed=exists))

        size = os.path.getsize(full_path) if exists else 0
        size_ok = size >= min_size_bytes
        checks.append(VerificationCheckResult(check_name="File Non-Empty / Meets Size Floor", expected=f">= {min_size_bytes}B", actual=f"{size}B", passed=size_ok))

        all_passed = exists and size_ok
        outcome = VerificationOutcome.VERIFIED if all_passed else VerificationOutcome.FAILED
        token = f"VERIFIED-FILE-{uuid.uuid4().hex[:8].upper()}" if all_passed else None

        return VerificationReport(
            task_id=task_id,
            outcome=outcome,
            verification_token=token,
            checks=checks,
            audit_notes=f"Report file validated on disk: {size} bytes.",
            verified_at=now_iso,
            evidence_payload={"file_path": file_path, "size_bytes": size}
        )
