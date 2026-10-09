from __future__ import annotations
from typing import Dict, Any, Optional
from centra_worker.tools.base import BaseTool
from centra_worker.models.approval import RiskLevel
from simulated_company.erp_server import erp_db, InvoiceSubmission


class ERPGetVendorsTool(BaseTool):
    name = "erp_get_vendors"
    description = "Query the internal CentraERP system to look up approved vendors, vendor IDs, and payment terms."
    parameters_schema = {
        "type": "object",
        "properties": {}
    }

    def run(self) -> Dict[str, Any]:
        vendors = erp_db.get_vendors()
        return {
            "status": "success",
            "count": len(vendors),
            "vendors": vendors
        }


class ERPGetInvoicesTool(BaseTool):
    name = "erp_get_invoices"
    description = "Query CentraERP accounts payable ledger to check existing invoices or check for duplicates."
    parameters_schema = {
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "Optional vendor filter"
            },
            "invoice_number": {
                "type": "string",
                "description": "Optional invoice number filter"
            }
        }
    }

    def run(self, vendor_name: Optional[str] = None, invoice_number: Optional[str] = None) -> Dict[str, Any]:
        invoices = erp_db.get_invoices(vendor=vendor_name, invoice_num=invoice_number)
        return {
            "status": "success",
            "count": len(invoices),
            "invoices": invoices
        }


class ERPSubmitInvoiceTool(BaseTool):
    name = "erp_submit_invoice"
    description = "Post a validated invoice into the internal CentraERP accounting system."
    parameters_schema = {
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "Full name of the vendor"
            },
            "invoice_number": {
                "type": "string",
                "description": "Invoice reference number, e.g. 'INV-2024-089'"
            },
            "amount": {
                "type": "number",
                "description": "Total amount in USD, e.g. 14850.00"
            },
            "due_date": {
                "type": "string",
                "description": "Due date in YYYY-MM-DD format, e.g. '2024-10-31'"
            },
            "issue_date": {
                "type": "string",
                "description": "Issue date in YYYY-MM-DD format"
            },
            "po_number": {
                "type": "string",
                "description": "Purchase order reference (e.g. 'PO-9921')"
            },
            "notes": {
                "type": "string",
                "description": "Optional notes or audit context"
            }
        },
        "required": ["vendor_name", "invoice_number", "amount", "due_date"]
    }

    def assess_risk(self, kwargs: Dict[str, Any]) -> tuple[RiskLevel, Optional[str]]:
        amount = float(kwargs.get("amount", 0))
        # High financial threshold: transactions over $10,000 require human sign-off
        if amount >= 10000.0:
            return (
                RiskLevel.HIGH,
                f"Financial Risk Gate: Invoice amount (${amount:,.2f}) exceeds autonomous approval limit of $10,000.00 USD."
            )
        return (RiskLevel.LOW, None)

    def run(
        self,
        vendor_name: str,
        invoice_number: str,
        amount: float,
        due_date: str,
        issue_date: Optional[str] = None,
        po_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            submission = InvoiceSubmission(
                vendor_name=vendor_name,
                invoice_number=invoice_number,
                amount=amount,
                due_date=due_date,
                issue_date=issue_date,
                po_number=po_number,
                notes=notes or "Autonomous processing by CentraWorker"
            )
            created_record = erp_db.add_invoice(submission, actor="CentraWorker_AI")
            return {
                "status": "success",
                "message": f"Invoice {invoice_number} successfully posted to CentraERP.",
                "record": created_record
            }
        except ConnectionError as ce:
            # Emulated transient network / service 503 error
            return {
                "status": "transient_error",
                "error_type": "ConnectionError",
                "error": str(ce),
                "retryable": True,
                "suggestion": "Retry operation with backoff or attempt web portal fallback."
            }
        except ValueError as ve:
            # Duplicate or validation error
            return {
                "status": "validation_error",
                "error_type": "ValueError",
                "error": str(ve),
                "retryable": False
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error": str(e),
                "retryable": False
            }
