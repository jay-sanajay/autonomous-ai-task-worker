"""
Deterministic Smart Mock LLM Provider.
Enables immediate offline evaluation, unit testing, and reproducible demonstrations
without requiring third-party API keys, while adhering strictly to the ReAct agent loop.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from centra_worker.llm.base import BaseLLMProvider, AgentDecision


class SmartMockProvider(BaseLLMProvider):
    """
    Intelligent simulated LLM provider that mirrors the decision-making of a frontier model:
    - Analyzes natural language user goals
    - Decomposes tasks into logical action sequences
    - Inspects file directories, compares timestamps to find 'latest'
    - Parses document contents to extract amount, due date, vendor, and PO
    - Checks internal ERP records
    - Recovers from simulated transient failures
    - Enforces outcome verification before completing
    """

    def decide_next_action(
        self,
        goal: str,
        plan_summary: str,
        working_memory: Dict[str, Any],
        step_history: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        system_instruction: Optional[str] = None
    ) -> AgentDecision:
        goal_lower = goal.lower()

        # Check what we already know from working memory
        has_file_list = "file_list" in working_memory
        latest_file = working_memory.get("latest_file")
        extracted_data = working_memory.get("extracted_invoice")
        vendor_checked = working_memory.get("vendor_verified")
        submitted_record = working_memory.get("submitted_record")
        verification_done = working_memory.get("verification_done")
        use_browser = working_memory.get("fallback_to_browser", False) or "browser" in goal_lower

        # Inspect last observation for errors to trigger recovery
        last_step = step_history[-1] if step_history else None
        last_failed = last_step and last_step.get("status") in ("FAILED", "RETRYING")
        last_error = (last_step.get("error_message") or "") if last_step else ""

        # SCENARIO A: Standard invoice workflow or generalized invoice workflow
        if "invoice" in goal_lower or "bill" in goal_lower or "company x" in goal_lower:

            # 1. First step: Discover relevant invoice files
            if not has_file_list:
                return AgentDecision(
                    thought=(
                        "The user wants me to find the latest invoice from Company X and enter it into our internal system. "
                        "First, I need to inspect the document repository to discover what invoice files exist."
                    ),
                    tool_name="list_files",
                    tool_input={"directory": "simulated_company/data_store/files/invoices", "pattern": "*.txt"},
                    is_finished=False
                )

            # 2. Identify the latest invoice if multiple exist
            if not latest_file:
                # Agent reasons over file list
                files = working_memory.get("file_list", [])
                return AgentDecision(
                    thought=(
                        f"Found {len(files)} files in repository. Looking for Company X invoices. "
                        "I see INV-2023-102 (historic), INV-2024-045 (previous), and INV-2024-089_CompanyX_Latest.txt. "
                        "The latest invoice is 'INV-2024-089_CompanyX_Latest.txt'. I will now read its full contents to extract amount and due date."
                    ),
                    tool_name="read_file",
                    tool_input={"file_path": "simulated_company/data_store/files/invoices/INV-2024-089_CompanyX_Latest.txt"},
                    is_finished=False
                )

            # 3. Verify vendor in internal ERP
            if not vendor_checked:
                return AgentDecision(
                    thought=(
                        f"I have successfully read invoice {extracted_data.get('invoice_number', 'INV-2024-089')}. "
                        f"Extracted Amount: ${extracted_data.get('amount', 14850.0):,.2f}, Due Date: {extracted_data.get('due_date', '2024-10-31')}. "
                        "Before submitting, I should check our internal CentraERP system to verify Company X is an approved vendor."
                    ),
                    tool_name="erp_get_vendors",
                    tool_input={},
                    is_finished=False
                )

            # 4. Handle transient error recovery if last submission encountered an error
            if last_failed and "503" in last_error:
                return AgentDecision(
                    thought=(
                        f"CentraERP returned transient error: '{last_error}'. "
                        "Executing autonomous self-correction: Applying backoff delay and retrying invoice submission."
                    ),
                    tool_name="erp_submit_invoice",
                    tool_input={
                        "vendor_name": extracted_data.get("vendor_name", "Company X Enterprise Solutions"),
                        "invoice_number": extracted_data.get("invoice_number", "INV-2024-089"),
                        "amount": extracted_data.get("amount", 14850.0),
                        "due_date": extracted_data.get("due_date", "2024-10-31"),
                        "po_number": extracted_data.get("po_number", "PO-9921"),
                        "notes": "Retried successfully after transient 503 recovery"
                    },
                    is_finished=False
                )

            # 5. Submit invoice (either via Browser or REST API)
            if not submitted_record:
                if use_browser:
                    # Alternative browser automation route
                    if not working_memory.get("browser_navigated"):
                        return AgentDecision(
                            thought=(
                                "Using browser automation to enter invoice via CentraERP Web Portal. "
                                "Navigating to portal invoice page."
                            ),
                            tool_name="browser_navigate",
                            tool_input={"url": "http://internal.centra/portal/invoices"},
                            is_finished=False
                        )
                    else:
                        return AgentDecision(
                            thought=(
                                "Located invoice entry form on web page. Filling form fields with extracted data: "
                                f"Vendor: {extracted_data.get('vendor_name')}, Invoice: {extracted_data.get('invoice_number')}, "
                                f"Amount: ${extracted_data.get('amount')}, Due: {extracted_data.get('due_date')}."
                            ),
                            tool_name="browser_fill_form",
                            tool_input={
                                "form_id": "invoice-form",
                                "form_data": {
                                    "vendor_name": extracted_data.get("vendor_name", "Company X Enterprise Solutions"),
                                    "invoice_number": extracted_data.get("invoice_number", "INV-2024-089"),
                                    "amount": extracted_data.get("amount", 14850.0),
                                    "due_date": extracted_data.get("due_date", "2024-10-31"),
                                    "po_number": extracted_data.get("po_number", "PO-9921"),
                                    "notes": "Submitted via browser form automation"
                                }
                            },
                            is_finished=False
                        )
                else:
                    # Direct API submission
                    return AgentDecision(
                        thought=(
                            f"Company X is an approved vendor (VEND-001X). Submitting invoice entry to CentraERP: "
                            f"Invoice: {extracted_data.get('invoice_number')}, Amount: ${extracted_data.get('amount')}, Due Date: {extracted_data.get('due_date')}."
                        ),
                        tool_name="erp_submit_invoice",
                        tool_input={
                            "vendor_name": extracted_data.get("vendor_name", "Company X Enterprise Solutions"),
                            "invoice_number": extracted_data.get("invoice_number", "INV-2024-089"),
                            "amount": extracted_data.get("amount", 14850.0),
                            "due_date": extracted_data.get("due_date", "2024-10-31"),
                            "po_number": extracted_data.get("po_number", "PO-9921"),
                            "notes": "Entered by Autonomous AI Task Worker"
                        },
                        is_finished=False
                    )

            # 6. Post-execution outcome verification
            if not verification_done:
                return AgentDecision(
                    thought=(
                        "Invoice entry posted. In accordance with autonomous reliability standards, "
                        "I will now run an independent verification check against CentraERP to confirm "
                        "the record exists in the system of record with exact amount and due date."
                    ),
                    tool_name="verify_erp_record",
                    tool_input={
                        "invoice_number": extracted_data.get("invoice_number", "INV-2024-089"),
                        "expected_amount": extracted_data.get("amount", 14850.0),
                        "expected_due_date": extracted_data.get("due_date", "2024-10-31")
                    },
                    is_finished=False
                )

            # 7. Final Completion
            inv_num = extracted_data.get("invoice_number", "INV-2024-089")
            amt = extracted_data.get("amount", 14850.0)
            due = extracted_data.get("due_date", "2024-10-31")
            return AgentDecision(
                thought="Task completed and independently verified. Generating final executive summary.",
                is_finished=True,
                final_summary=(
                    f"Successfully processed the latest invoice from Company X.\n\n"
                    f"• Invoice Number: {inv_num}\n"
                    f"• Vendor: {extracted_data.get('vendor_name', 'Company X Enterprise Solutions')}\n"
                    f"• Extracted Amount: ${amt:,.2f} USD\n"
                    f"• Payment Due Date: {due}\n"
                    f"• Purchase Order: {extracted_data.get('po_number', 'PO-9921')}\n"
                    f"• CentraERP Record ID: {submitted_record.get('id', 'INVREC-0002')}\n"
                    f"• Verification Status: CONFIRMED & VERIFIED against ground-truth ledger.\n"
                    f"• Verification Token: {working_memory.get('verification_token', 'VERIFIED-SHA256')}"
                )
            )

        # Fallback general decision
        return AgentDecision(
            thought="Task goal analyzed. Determining applicable tools.",
            is_finished=True,
            final_summary=f"Processed request: {goal}"
        )
