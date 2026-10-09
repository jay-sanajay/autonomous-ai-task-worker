"""
Browser Automation Tools for CentraWorker.
Provides programmatic browser actions (navigating pages, inspecting forms, filling inputs, clicking buttons)
against the company's internal web portal.
"""

from __future__ import annotations
import os
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from centra_worker.tools.base import BaseTool
from simulated_company.erp_server import erp_db, InvoiceSubmission


class BrowserSession:
    """Simulated in-memory browser state tracker."""
    def __init__(self):
        self.current_url: Optional[str] = None
        self.current_html: Optional[str] = None
        self.dom: Optional[BeautifulSoup] = None

    def navigate(self, url: str) -> Dict[str, Any]:
        self.current_url = url
        # If navigating to local web portal file or relative path
        if "invoices" in url:
            portal_path = os.path.join(os.path.dirname(__file__), "..", "..", "simulated_company", "web_portal", "invoices.html")
            portal_path = os.path.normpath(portal_path)
            if os.path.exists(portal_path):
                with open(portal_path, "r", encoding="utf-8") as f:
                    self.current_html = f.read()
            else:
                self.current_html = "<html><body><h1>CentraERP Portal</h1></body></html>"
        else:
            self.current_html = f"<html><body><h1>Page: {url}</h1></body></html>"

        self.dom = BeautifulSoup(self.current_html, "html.parser")
        title = self.dom.title.string if self.dom.title else "Untitled Page"

        # Discover interactive elements
        forms = []
        for form in self.dom.find_all("form"):
            inputs = [inp.get("id") or inp.get("name") for inp in form.find_all(["input", "textarea", "select"])]
            buttons = [b.get("id") or b.text.strip() for b in form.find_all("button")]
            forms.append({"form_id": form.get("id"), "inputs": inputs, "buttons": buttons})

        return {
            "status": "success",
            "url": self.current_url,
            "title": title,
            "forms_detected": forms,
            "page_snippet": self.dom.get_text()[:400].replace("\n", " ").strip()
        }

    def fill_and_submit_form(self, form_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.dom:
            return {"status": "error", "error": "No page currently loaded. Call browser_navigate first."}

        # Check form exists
        form = self.dom.find("form", id=form_id)
        if not form:
            return {"status": "error", "error": f"Form with id '{form_id}' not found on page."}

        # Execute submission directly through ERP business logic backend
        try:
            submission = InvoiceSubmission(
                vendor_name=form_data["vendor_name"],
                invoice_number=form_data["invoice_number"],
                amount=float(form_data["amount"]),
                due_date=form_data["due_date"],
                po_number=form_data.get("po_number"),
                notes=form_data.get("notes", "Submitted via Browser Automation")
            )
            created = erp_db.add_invoice(submission, actor="BrowserWorker_Automation")
            return {
                "status": "success",
                "action": "form_submitted",
                "message": f"Successfully submitted form '{form_id}' via browser for invoice {created['invoice_number']}.",
                "created_record": created,
                "ui_feedback": f"Success alert displayed: Invoice {created['invoice_number']} entered with ID {created['id']}"
            }
        except Exception as e:
            return {
                "status": "error",
                "action": "form_submitted",
                "error": str(e),
                "ui_feedback": f"Error alert displayed: {str(e)}"
            }


_browser_session = BrowserSession()


class BrowserNavigateTool(BaseTool):
    name = "browser_navigate"
    description = "Navigate browser to a URL (e.g. 'http://internal.centra/portal/invoices') and inspect forms and elements."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL or internal portal destination"
            }
        },
        "required": ["url"]
    }

    def run(self, url: str) -> Dict[str, Any]:
        return _browser_session.navigate(url)


class BrowserFillFormTool(BaseTool):
    name = "browser_fill_form"
    description = "Fill out and submit an HTML form on the current web page."
    parameters_schema = {
        "type": "object",
        "properties": {
            "form_id": {
                "type": "string",
                "description": "ID of the form element, e.g. 'invoice-form'"
            },
            "form_data": {
                "type": "object",
                "description": "Key-value dictionary matching form input fields (e.g. vendor_name, invoice_number, amount, due_date, po_number)"
            }
        },
        "required": ["form_id", "form_data"]
    }

    def run(self, form_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        return _browser_session.fill_and_submit_form(form_id, form_data)
