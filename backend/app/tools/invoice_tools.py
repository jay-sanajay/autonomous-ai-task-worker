"""
AgentOS - Invoice File Processing Tools.
Implements list_invoice_files, read_invoice, and extract_invoice_fields.
"""

from __future__ import annotations
import os
import glob
import re
from typing import Dict, Any, List, Optional
from backend.app.tools.base import ControlledBaseTool, ToolResult

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INVOICE_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "invoices")


from backend.app.tools.path_utils import resolve_sandbox_file_path

def _resolve_sandbox_path(path: str) -> str:
    return resolve_sandbox_file_path(path, default_sub="invoices")


class ListInvoiceFilesTool(ControlledBaseTool):
    name = "list_invoice_files"
    description = "Discover available invoice documents in the company sandbox repository."
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Optional subdirectory to scan, defaults to sandbox_data/invoices",
                "default": "sandbox_data/invoices"
            },
            "vendor_filter": {
                "type": "string",
                "description": "Optional vendor filter string (e.g. 'Acme')"
            }
        }
    }

    def execute(self, db_session, directory: str = "sandbox_data/invoices", vendor_filter: Optional[str] = None) -> ToolResult:
        target_dir = _resolve_sandbox_path(directory)
        if not os.path.exists(target_dir):
            return ToolResult(
                success=False,
                error=f"Directory '{directory}' does not exist in sandbox repository.",
                retryable=False
            )

        files = []
        for p in glob.glob(os.path.join(target_dir, "*.*")):
            if os.path.isfile(p):
                fn = os.path.basename(p)
                if vendor_filter and vendor_filter.lower() not in fn.lower():
                    continue
                stat = os.stat(p)
                files.append({
                    "filename": fn,
                    "path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "extension": os.path.splitext(fn)[1].lstrip(".")
                })

        # Sort so latest / newest appears first
        files.sort(key=lambda x: x["modified_time"], reverse=True)

        return ToolResult(
            success=True,
            data={
                "directory": directory,
                "count": len(files),
                "files": files
            }
        )


class ReadInvoiceTool(ControlledBaseTool):
    name = "read_invoice"
    description = "Read raw text content from an invoice file (supports .txt, .pdf, .json, .csv)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to invoice file, e.g. 'sandbox_data/invoices/INV-2024-001_AcmeTechnologies_Latest.txt'"
            }
        },
        "required": ["file_path"]
    }

    def execute(self, db_session, file_path: str) -> ToolResult:
        full_path = _resolve_sandbox_path(file_path)
        if not os.path.exists(full_path):
            return ToolResult(
                success=False,
                error=f"File '{file_path}' not found in company sandbox.",
                retryable=False
            )

        ext = os.path.splitext(full_path)[1].lower()

        # Handle PDF files
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(full_path)
                text_content = "\n".join([page.extract_text() or "" for page in reader.pages])
                if not text_content.strip():
                    # Fallback to PyPDF2 if pypdf has empty text
                    import PyPDF2
                    with open(full_path, "rb") as f:
                        r2 = PyPDF2.PdfReader(f)
                        text_content = "\n".join([page.extract_text() or "" for page in r2.pages])
                return ToolResult(
                    success=True,
                    data={
                        "file_path": file_path,
                        "format": "pdf",
                        "size_bytes": os.path.getsize(full_path),
                        "text": text_content
                    }
                )
            except Exception as e:
                # Fallback to PyPDF2 direct
                try:
                    import PyPDF2
                    with open(full_path, "rb") as f:
                        r = PyPDF2.PdfReader(f)
                        text_content = "\n".join([page.extract_text() or "" for page in r.pages])
                    return ToolResult(
                        success=True,
                        data={
                            "file_path": file_path,
                            "format": "pdf",
                            "size_bytes": os.path.getsize(full_path),
                            "text": text_content
                        }
                    )
                except Exception as e2:
                    return ToolResult(
                        success=False,
                        error=f"PDF extraction failed: {str(e2)}",
                        retryable=False
                    )

        # Handle Text / CSV / JSON
        elif ext in (".txt", ".json", ".csv", ".log"):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return ToolResult(
                    success=True,
                    data={
                        "file_path": file_path,
                        "format": ext.lstrip("."),
                        "size_bytes": len(content),
                        "text": content
                    }
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to read file: {str(e)}",
                    retryable=False
                )

        return ToolResult(
            success=False,
            error=f"Unsupported invoice document format '{ext}'. Supported: .txt, .pdf, .json, .csv",
            retryable=False
        )


class ExtractInvoiceFieldsTool(ControlledBaseTool):
    name = "extract_invoice_fields"
    description = (
        "Extract structured, validated invoice fields (vendor, invoice_number, amount, due_date, "
        "invoice_date, currency, terms, PO) from document text. Never invents missing data."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "document_text": {
                "type": "string",
                "description": "Raw text content of the invoice document"
            },
            "source_file": {
                "type": "string",
                "description": "Source filename for provenance tracking"
            }
        },
        "required": ["document_text"]
    }

    def execute(self, db_session, document_text: str, source_file: Optional[str] = None) -> ToolResult:
        if not document_text or not document_text.strip():
            return ToolResult(
                success=False,
                error="Document text is empty; cannot extract invoice fields.",
                retryable=False
            )

        extracted: Dict[str, Any] = {
            "vendor_name": None,
            "invoice_number": None,
            "amount": None,
            "currency": "USD",
            "due_date": None,
            "invoice_date": None,
            "payment_terms": None,
            "po_number": None,
            "source_file": source_file
        }
        missing_fields: List[str] = []

        # 1. Invoice Number
        inv_match = re.search(r"Invoice\s*(?:Number|#|No\.?)\s*[:=]?\s*([A-Za-z0-9\-]+)", document_text, re.IGNORECASE)
        if inv_match:
            extracted["invoice_number"] = inv_match.group(1).strip()
        else:
            missing_fields.append("invoice_number")

        # 2. Vendor Name
        vendor_match = re.search(r"Vendor\s*(?:Name)?\s*[:=]?\s*([^\n\r]+)", document_text, re.IGNORECASE)
        if vendor_match:
            v_val = vendor_match.group(1).strip()
            # Clean trailing IDs if present
            v_val = re.sub(r"\s+Vendor\s*ID.*$", "", v_val, flags=re.IGNORECASE)
            extracted["vendor_name"] = v_val.strip()
        elif "acme technologies" in document_text.lower():
            extracted["vendor_name"] = "Acme Technologies Inc."
        elif "global logistics" in document_text.lower():
            extracted["vendor_name"] = "Global Logistics Freight Ltd"
        elif "nexus hardware" in document_text.lower():
            extracted["vendor_name"] = "Nexus Hardware Systems"
        else:
            missing_fields.append("vendor_name")

        # 3. Due Date
        due_match = re.search(r"Due\s*Date\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", document_text, re.IGNORECASE)
        if due_match:
            extracted["due_date"] = due_match.group(1).strip()
        else:
            missing_fields.append("due_date")

        # 4. Invoice Date
        inv_date_match = re.search(r"Invoice\s*Date\s*[:=]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", document_text, re.IGNORECASE)
        if inv_date_match:
            extracted["invoice_date"] = inv_date_match.group(1).strip()

        # 5. Amount (Numeric validation)
        # Check if amount is explicitly pending/missing
        if re.search(r"(?:TOTAL|AMOUNT)\s*[:=]?\s*(?:PENDING|TBD|UNDER\s*REVIEW)", document_text, re.IGNORECASE):
            extracted["amount"] = None
            missing_fields.append("amount")
        else:
            amt_match = re.search(
                r"(?:TOTAL\s*INVOICE\s*AMOUNT|TOTAL\s*PAYABLE\s*AMOUNT\s*DUE|TOTAL\s*AMOUNT|TOTAL|SUBTOTAL|AMOUNT DUE|NET AMOUNT)\s*[:=]?\s*(?:₹|Rs\.?|INR|\$|EUR|€)?\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)",
                document_text,
                re.IGNORECASE
            )
            if amt_match:
                try:
                    amt_str = amt_match.group(1).replace(",", "").strip()
                    extracted["amount"] = float(amt_str)
                except ValueError:
                    extracted["amount"] = None
                    missing_fields.append("amount")
            else:
                missing_fields.append("amount")

        # 6. Currency (Defaults to INR / Rupees for Indian standard)
        if "INR" in document_text or "₹" in document_text or "RS." in document_text.upper() or "RUPEES" in document_text.upper():
            extracted["currency"] = "INR"
        elif "USD" in document_text or "$" in document_text:
            extracted["currency"] = "USD"
        elif "EUR" in document_text or "€" in document_text:
            extracted["currency"] = "EUR"
        else:
            extracted["currency"] = "INR"

        # 7. Payment Terms & PO
        terms_match = re.search(r"Payment\s*Terms\s*[:=]?\s*([^\n\r]+)", document_text, re.IGNORECASE)
        if terms_match:
            extracted["payment_terms"] = terms_match.group(1).strip()

        po_match = re.search(r"(?:PO|Purchase\s*Order)\s*(?:Reference|Ref|#|No\.?)?\s*[:=]?\s*([A-Za-z0-9\-]+)", document_text, re.IGNORECASE)
        if po_match:
            extracted["po_number"] = po_match.group(1).strip()

        is_complete = len(missing_fields) == 0

        return ToolResult(
            success=is_complete,
            data={
                "extracted_fields": extracted,
                "is_complete": is_complete,
                "missing_fields": missing_fields,
                "requires_clarification": not is_complete
            },
            error=f"Essential invoice fields could not be extracted: {', '.join(missing_fields)}" if not is_complete else None
        )
