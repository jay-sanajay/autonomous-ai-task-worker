"""
AgentOS - Independent Outcome Verification Critic.
Verifies ground truth directly against the SQLite database, ensuring the agent's
claims of success are mathematically and empirically confirmed.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.database.models import PayableRecord


class IndependentVerificationCritic:
    def verify(
        self,
        db_session: Session,
        invoice_number: str,
        expected_amount: float,
        expected_due_date: str,
        expected_vendor: Optional[str] = None
    ) -> Dict[str, Any]:
        clean_inv = invoice_number.strip().upper()
        record = db_session.query(PayableRecord).filter(
            PayableRecord.invoice_number == clean_inv
        ).first()

        if not record:
            return {
                "verified": False,
                "reason": f"Invoice '{invoice_number}' not found in database ledger.",
                "payable_id": None
            }

        amt_diff = abs(float(record.amount) - float(expected_amount))
        amt_match = amt_diff < 0.01
        due_match = record.due_date.strip() == expected_due_date.strip()

        vendor_match = True
        if expected_vendor:
            vendor_match = (
                expected_vendor.lower() in record.vendor_name.lower() or
                record.vendor_name.lower() in expected_vendor.lower()
            )

        all_passed = amt_match and due_match and vendor_match

        return {
            "verified": all_passed,
            "payable_id": record.id,
            "invoice_number": record.invoice_number,
            "vendor_name": record.vendor_name,
            "amount": record.amount,
            "due_date": record.due_date,
            "status": record.status,
            "verification_token": record.verification_hash,
            "checks": {
                "amount": {"expected": expected_amount, "actual": record.amount, "diff": amt_diff, "match": amt_match},
                "due_date": {"expected": expected_due_date, "actual": record.due_date, "match": due_match},
                "vendor": {"expected": expected_vendor, "actual": record.vendor_name, "match": vendor_match}
            },
            "audit_trail": f"Confirmed against SQLite ledger at {record.created_at.isoformat()}"
        }
