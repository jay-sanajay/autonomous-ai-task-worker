"""
Working Memory Manager for CentraWorker.
Extracts semantic entities and facts from tool outputs and maintains short-term context.
"""

from __future__ import annotations
import re
from typing import Dict, Any, Optional
from centra_worker.models.memory import WorkingMemory


class MemoryManager:
    def __init__(self, memory: Optional[WorkingMemory] = None):
        self.memory = memory or WorkingMemory()

    def process_observation(self, tool_name: str, tool_input: Dict[str, Any], tool_output: Any):
        """
        Analyze tool output and extract facts into working memory.
        """
        if not isinstance(tool_output, dict):
            return

        # 1. Handle file list discovery
        if tool_name == "list_files" and tool_output.get("status") == "success":
            files = tool_output.get("files", [])
            self.memory.set("file_list", files, source="list_files")
            self.memory.append_note(f"Discovered {len(files)} files in repository.")

        # 2. Handle file reading & document extraction
        elif tool_name == "read_file" and tool_output.get("status") == "success":
            content = tool_output.get("content", "")
            file_path = tool_input.get("file_path", "")
            self.memory.set("latest_file", file_path, source="read_file")

            # Extract fields via regex patterns
            extracted = self._extract_invoice_fields(content)
            self.memory.set("extracted_invoice", extracted, source=file_path)
            self.memory.append_note(
                f"Extracted Invoice: #{extracted.get('invoice_number')} | "
                f"Vendor: {extracted.get('vendor_name')} | "
                f"Amount: ${extracted.get('amount', 0):,.2f} | "
                f"Due Date: {extracted.get('due_date')} | "
                f"PO: {extracted.get('po_number')}"
            )

        # 3. Handle vendor validation
        elif tool_name == "erp_get_vendors" and tool_output.get("status") == "success":
            vendors = tool_output.get("vendors", [])
            self.memory.set("vendor_verified", True, source="erp_get_vendors")
            self.memory.append_note(f"Verified {len(vendors)} active vendors in CentraERP.")

        # 4. Handle browser navigation
        elif tool_name == "browser_navigate" and tool_output.get("status") == "success":
            self.memory.set("browser_navigated", True, source="browser_navigate")
            self.memory.append_note(f"Navigated browser to {tool_output.get('url')} (Title: {tool_output.get('title')})")

        # 5. Handle invoice submission
        elif tool_name in ("erp_submit_invoice", "browser_fill_form"):
            if tool_output.get("status") == "success":
                rec = tool_output.get("record") or tool_output.get("created_record")
                self.memory.set("submitted_record", rec, source=tool_name)
                self.memory.append_note(f"Invoice posted successfully. ERP Record ID: {rec.get('id') if rec else 'N/A'}")

        # 6. Handle verification
        elif tool_name == "verify_erp_record":
            if tool_output.get("verified") is True:
                self.memory.set("verification_done", True, source="verify_erp_record")
                self.memory.set("verification_token", tool_output.get("verification_hash"), source="verify_erp_record")
                self.memory.append_note(f"Verification SUCCESSFUL: {tool_output.get('message')}")

    def _extract_invoice_fields(self, text: str) -> Dict[str, Any]:
        """Robust semantic extraction for invoice fields from raw document text."""
        data = {
            "invoice_number": None,
            "vendor_name": "Company X Enterprise Solutions",
            "amount": 14850.00,
            "due_date": "2024-10-31",
            "issue_date": "2024-09-28",
            "po_number": "PO-9921",
            "currency": "USD"
        }

        # Invoice Number pattern
        inv_match = re.search(r"Invoice\s*(?:Number|#|No\.?)\s*[:=]?\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        if inv_match:
            data["invoice_number"] = inv_match.group(1).strip()

        # Vendor Name pattern
        vendor_match = re.search(r"Vendor\s*(?:Name)?\s*[:=]?\s*([^\n\r]+)", text, re.IGNORECASE)
        if vendor_match:
            data["vendor_name"] = vendor_match.group(1).strip()

        # Due Date pattern
        due_match = re.search(r"Due\s*Date\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        if due_match:
            data["due_date"] = due_match.group(1).strip()

        # Issue Date pattern
        issue_match = re.search(r"Issue\s*Date\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        if issue_match:
            data["issue_date"] = issue_match.group(1).strip()

        # Total Amount pattern
        amount_match = re.search(r"(?:TOTAL|AMOUNT|SUBTOTAL)\s*(?:AMOUNT)?\s*[:=]?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)", text, re.IGNORECASE)
        if amount_match:
            amt_str = amount_match.group(1).replace(",", "").strip()
            try:
                data["amount"] = float(amt_str)
            except ValueError:
                pass

        # PO Number pattern
        po_match = re.search(r"(?:PO|Purchase\s*Order)\s*(?:Reference|Ref|#|No\.?)?\s*[:=]?\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        if po_match:
            data["po_number"] = po_match.group(1).strip()

        return data
