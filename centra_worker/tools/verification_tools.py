from __future__ import annotations
from typing import Dict, Any
from centra_worker.tools.base import BaseTool
from simulated_company.erp_server import erp_db


class ERPVerifyRecordTool(BaseTool):
    name = "verify_erp_record"
    description = (
        "Independently verify whether an invoice record was successfully and accurately written "
        "to the internal CentraERP system. Checks existence, amount precision, and due date matching."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": "string",
                "description": "Invoice number to verify"
            },
            "expected_amount": {
                "type": "number",
                "description": "Expected numeric amount extracted from source invoice"
            },
            "expected_due_date": {
                "type": "string",
                "description": "Expected due date in YYYY-MM-DD format"
            }
        },
        "required": ["invoice_number", "expected_amount", "expected_due_date"]
    }

    def run(self, invoice_number: str, expected_amount: float, expected_due_date: str) -> Dict[str, Any]:
        result = erp_db.verify_record(
            invoice_number=invoice_number,
            expected_amount=expected_amount,
            expected_due_date=expected_due_date
        )
        return result
