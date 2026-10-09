"""
CentraERP - Simulated Internal Company Accounting & Operations System.
Provides REST API and web endpoints for internal invoice processing, vendor lookups,
audit logging, and realistic error injection for testing agent resilience.
"""

from __future__ import annotations
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Default path for persistent ERP database state
DEFAULT_DB_FILE = os.path.join(os.path.dirname(__file__), "data_store", "erp_db.json")


class InvoiceSubmission(BaseModel):
    vendor_name: str = Field(..., description="Name of the vendor")
    invoice_number: str = Field(..., description="Unique invoice identifier")
    amount: float = Field(..., description="Total invoice amount")
    currency: str = Field(default="USD", description="Currency code (e.g. USD)")
    due_date: str = Field(..., description="Invoice due date in YYYY-MM-DD format")
    issue_date: Optional[str] = Field(default=None, description="Issue date")
    po_number: Optional[str] = Field(default=None, description="Purchase order reference")
    notes: Optional[str] = Field(default="Entered by Autonomous AI Task Worker")


class ERPDatabase:
    def __init__(self, db_file: str = DEFAULT_DB_FILE):
        self.db_file = db_file
        self.transient_error_counter: int = 0
        self.force_transient_error: bool = False
        self.load()

    def get_initial_data(self) -> Dict[str, Any]:
        return {
            "vendors": [
                {
                    "vendor_id": "VEND-001X",
                    "name": "Company X Enterprise Solutions",
                    "status": "APPROVED",
                    "category": "Cloud & AI Infrastructure",
                    "payment_terms": "Net-30"
                },
                {
                    "vendor_id": "VEND-002A",
                    "name": "Acme Corp",
                    "status": "APPROVED",
                    "category": "Office Equipment",
                    "payment_terms": "Net-15"
                },
                {
                    "vendor_id": "VEND-009N",
                    "name": "Nexus Technologies Group",
                    "status": "APPROVED",
                    "category": "Compute Hardware",
                    "payment_terms": "Net-30"
                }
            ],
            "invoices": [
                {
                    "id": "INVREC-0001",
                    "invoice_number": "INV-2023-102",
                    "vendor_name": "Company X Enterprise Solutions",
                    "vendor_id": "VEND-001X",
                    "amount": 4200.0,
                    "currency": "USD",
                    "issue_date": "2023-11-15",
                    "due_date": "2023-12-15",
                    "po_number": "PO-8120",
                    "status": "PAID",
                    "entered_by": "System Migration",
                    "created_at": "2023-11-16T10:00:00Z",
                    "verification_hash": "hash_legacy_102"
                }
            ],
            "audit_logs": [
                {
                    "timestamp": "2023-11-16T10:00:00Z",
                    "action": "SYSTEM_INIT",
                    "actor": "admin",
                    "details": "Initial seed database loaded"
                }
            ]
        }

    def load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    return
            except Exception:
                pass
        self.data = self.get_initial_data()
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def reset(self):
        self.data = self.get_initial_data()
        self.transient_error_counter = 0
        self.force_transient_error = False
        self.save()

    def log_audit(self, action: str, actor: str, details: str):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "details": details
        }
        self.data["audit_logs"].append(entry)
        self.save()

    def get_vendors(self) -> List[Dict[str, Any]]:
        return self.data.get("vendors", [])

    def get_invoices(self, vendor: Optional[str] = None, invoice_num: Optional[str] = None) -> List[Dict[str, Any]]:
        invoices = self.data.get("invoices", [])
        if vendor:
            invoices = [inv for inv in invoices if vendor.lower() in inv["vendor_name"].lower()]
        if invoice_num:
            invoices = [inv for inv in invoices if inv["invoice_number"].strip().lower() == invoice_num.strip().lower()]
        return invoices

    def add_invoice(self, submission: InvoiceSubmission, actor: str = "CentraWorker_AI") -> Dict[str, Any]:
        # Check for simulated transient error
        if self.force_transient_error:
            self.transient_error_counter += 1
            if self.transient_error_counter == 1:
                # First attempt fails with 503 Service Unavailable
                raise ConnectionError("CentraERP Gateway Error 503: Service Temporarily Overloaded. Please retry.")
            else:
                # Second attempt succeeds!
                self.force_transient_error = False

        # Check duplicate
        for existing in self.data["invoices"]:
            if existing["invoice_number"].strip().upper() == submission.invoice_number.strip().upper():
                raise ValueError(f"Invoice '{submission.invoice_number}' already exists in CentraERP system.")

        # Find vendor
        matched_vendor = None
        for v in self.data["vendors"]:
            if v["name"].lower() in submission.vendor_name.lower() or submission.vendor_name.lower() in v["name"].lower():
                matched_vendor = v
                break

        vendor_id = matched_vendor["vendor_id"] if matched_vendor else "VEND-UNKNOWN"

        # Generate cryptographic verification hash
        hash_payload = f"{submission.invoice_number}|{submission.amount}|{submission.due_date}|{datetime.now(timezone.utc).isoformat()}"
        verification_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16]

        record_id = f"INVREC-{len(self.data['invoices']) + 1:04d}"
        new_record = {
            "id": record_id,
            "invoice_number": submission.invoice_number,
            "vendor_name": submission.vendor_name,
            "vendor_id": vendor_id,
            "amount": float(submission.amount),
            "currency": submission.currency,
            "issue_date": submission.issue_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "due_date": submission.due_date,
            "po_number": submission.po_number or "UNSPECIFIED",
            "status": "ENTERED",
            "entered_by": actor,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verification_hash": f"VERIFIED-{verification_hash}",
            "notes": submission.notes
        }

        self.data["invoices"].append(new_record)
        self.log_audit(
            action="INVOICE_ENTERED",
            actor=actor,
            details=f"Created record {record_id} for invoice {submission.invoice_number} (Vendor: {submission.vendor_name}, Amount: ${submission.amount:,.2f}, Due: {submission.due_date})"
        )
        return new_record

    def verify_record(self, invoice_number: str, expected_amount: float, expected_due_date: str) -> Dict[str, Any]:
        """
        Independent verification tool logic.
        Queries ground truth database and validates all attributes.
        """
        matches = [inv for inv in self.data["invoices"] if inv["invoice_number"].strip().upper() == invoice_number.strip().upper()]
        if not matches:
            return {
                "verified": False,
                "reason": f"Invoice '{invoice_number}' not found in internal ERP ledger."
            }

        rec = matches[0]
        # Compare numeric amount with tolerance for floating point
        amount_match = abs(float(rec["amount"]) - float(expected_amount)) < 0.01
        due_match = rec["due_date"].strip() == expected_due_date.strip()

        if not amount_match:
            return {
                "verified": False,
                "reason": f"Amount mismatch: Expected ${expected_amount:,.2f} but ERP record shows ${rec['amount']:,.2f}",
                "record": rec
            }

        if not due_match:
            return {
                "verified": False,
                "reason": f"Due date mismatch: Expected {expected_due_date} but ERP record shows {rec['due_date']}",
                "record": rec
            }

        return {
            "verified": True,
            "record_id": rec["id"],
            "invoice_number": rec["invoice_number"],
            "vendor_name": rec["vendor_name"],
            "amount": rec["amount"],
            "currency": rec["currency"],
            "due_date": rec["due_date"],
            "status": rec["status"],
            "verification_hash": rec["verification_hash"],
            "entered_at": rec["created_at"],
            "message": "Independent verification SUCCESSFUL: Record exists and matches extracted document values."
        }


# Singleton instance for easy local access
erp_db = ERPDatabase()
