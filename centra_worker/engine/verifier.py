"""
Outcome Verification Engine for CentraWorker.
Independently verifies that the user's requested end goal was genuinely achieved in the
underlying target system, rather than relying on unverified LLM assumptions.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from centra_worker.models.task import EvidenceReceipt
from simulated_company.erp_server import erp_db


class OutcomeVerifier:
    def verify_invoice_completion(
        self,
        invoice_number: str,
        expected_amount: float,
        expected_due_date: str,
        vendor_name: Optional[str] = None
    ) -> EvidenceReceipt:
        """
        Query system of record to assert ground truth.
        """
        verification_result = erp_db.verify_record(
            invoice_number=invoice_number,
            expected_amount=expected_amount,
            expected_due_date=expected_due_date
        )

        if verification_result.get("verified") is True:
            return EvidenceReceipt(
                verified=True,
                record_id=verification_result.get("record_id"),
                invoice_number=invoice_number,
                vendor_name=verification_result.get("vendor_name") or vendor_name,
                amount=verification_result.get("amount"),
                currency=verification_result.get("currency", "USD"),
                due_date=verification_result.get("due_date"),
                verification_hash=verification_result.get("verification_hash"),
                verified_at=datetime.now(timezone.utc).isoformat(),
                audit_notes="Ground-truth verified against CentraERP ledger: Record exists with exact amount and due date.",
                evidence_payload=verification_result
            )
        else:
            return EvidenceReceipt(
                verified=False,
                invoice_number=invoice_number,
                audit_notes=f"Verification failed: {verification_result.get('reason')}",
                evidence_payload=verification_result
            )
