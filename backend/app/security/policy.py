"""
AgentOS - Human Approval & Permission Policy Engine.
Enforces server-side authorization immediately before tool execution,
binds approvals to exact cryptographic argument hashes (SHA256),
and invalidates approvals if target arguments change.
"""

from __future__ import annotations
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.database.models import ApprovalRequest, AgentTask
from backend.app.agent.dag_planner import RiskClassification

# Tool Risk Matrix
TOOL_RISK_MAP: Dict[str, RiskClassification] = {
    # Read-Only Tools (Permitted automatically)
    "list_invoice_files": RiskClassification.READ_ONLY,
    "read_invoice": RiskClassification.READ_ONLY,
    "extract_invoice_fields": RiskClassification.READ_ONLY,
    "search_vendor": RiskClassification.READ_ONLY,
    "search_existing_invoice": RiskClassification.READ_ONLY,
    "get_payable": RiskClassification.READ_ONLY,
    "verify_payable": RiskClassification.READ_ONLY,
    "list_emails": RiskClassification.READ_ONLY,
    "read_email": RiskClassification.READ_ONLY,
    "extract_email_details": RiskClassification.READ_ONLY,
    "list_task_items": RiskClassification.READ_ONLY,
    "verify_task_item": RiskClassification.READ_ONLY,
    "list_csv_files": RiskClassification.READ_ONLY,
    "inspect_csv": RiskClassification.READ_ONLY,
    "analyze_csv": RiskClassification.READ_ONLY,
    "list_support_tickets": RiskClassification.READ_ONLY,
    "list_inventory": RiskClassification.READ_ONLY,
    "inspect_document": RiskClassification.READ_ONLY,
    "list_contract_files": RiskClassification.READ_ONLY,
    "verify_contract": RiskClassification.READ_ONLY,
    "browser_open_url": RiskClassification.READ_ONLY,
    "browser_inspect_page": RiskClassification.READ_ONLY,
    "browser_verify_page_state": RiskClassification.READ_ONLY,
    "browser_take_screenshot": RiskClassification.READ_ONLY,
    "report_task_result": RiskClassification.READ_ONLY,

    # Low-Risk Reversible Writes
    "extract_contract_details": RiskClassification.LOW_RISK_REVERSIBLE,
    "create_task_item": RiskClassification.LOW_RISK_REVERSIBLE,
    "generate_report": RiskClassification.LOW_RISK_REVERSIBLE,
    "update_support_ticket": RiskClassification.LOW_RISK_REVERSIBLE,
    "browser_fill_field": RiskClassification.LOW_RISK_REVERSIBLE,

    # Consequential Operations (Requires Gating or Verification)
    "create_purchase_request": RiskClassification.CONSEQUENTIAL,
    "browser_click": RiskClassification.CONSEQUENTIAL,
    "create_payable": RiskClassification.CONSEQUENTIAL,  # Triggers HITL approval if amount > policy threshold
}

POLICY_FINANCIAL_THRESHOLD = 10000.00  # Amounts > $10,000 USD require human approval


def compute_argument_hash(arguments: Dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash of tool argument payload."""
    serialized = json.dumps(arguments, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class PolicyEngine:
    """Enforces execution boundaries, risk gates, and cryptographic approval validation."""

    @staticmethod
    def get_tool_risk(tool_name: str, arguments: Dict[str, Any]) -> RiskClassification:
        base_risk = TOOL_RISK_MAP.get(tool_name, RiskClassification.CONSEQUENTIAL)

        # Dynamic financial escalation: create_payable with amount > $10,000 becomes CRITICAL
        if tool_name == "create_payable":
            amt = float(arguments.get("amount", 0.0))
            if amt > POLICY_FINANCIAL_THRESHOLD:
                return RiskClassification.CRITICAL

        return base_risk

    @staticmethod
    def requires_human_approval(
        tool_name: str,
        arguments: Dict[str, Any],
        auto_approve_high_risk: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate if tool execution requires explicit human authorization.
        Returns (requires_approval: bool, reason: str).
        """
        risk = PolicyEngine.get_tool_risk(tool_name, arguments)

        if risk in (RiskClassification.READ_ONLY, RiskClassification.LOW_RISK_REVERSIBLE):
            return False, None

        if risk == RiskClassification.CRITICAL:
            if auto_approve_high_risk:
                return False, None
            amt = float(arguments.get("amount", 0.0))
            return True, f"Financial disbursement of ${amt:,.2f} exceeds autonomous limit of ${POLICY_FINANCIAL_THRESHOLD:,.2f} USD."

        return False, None

    @staticmethod
    def create_approval_request(
        db: Session,
        task_id: str,
        tool_name: str,
        action_description: str,
        arguments: Dict[str, Any],
        risk_reason: str
    ) -> ApprovalRequest:
        """Create a cryptographically bound approval request in SQLite."""
        arg_hash = compute_argument_hash(arguments)
        app_id = f"APP-{hashlib.sha256(f'{task_id}-{time.time()}'.encode()).hexdigest()[:8].upper()}"

        req = ApprovalRequest(
            id=app_id,
            task_id=task_id,
            tool_name=tool_name,
            action_description=action_description,
            risk_level="CRITICAL",
            risk_reason=risk_reason,
            pending_payload=json.dumps(arguments),
            argument_hash=arg_hash,
            status="PENDING",
            created_at=datetime.now(timezone.utc)
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def validate_and_consume_approval(
        db: Session,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that an approved authorization matches the exact tool arguments.
        If the target arguments have changed, invalidates the approval!
        """
        current_hash = compute_argument_hash(arguments)

        app_req = db.query(ApprovalRequest).filter(
            ApprovalRequest.task_id == task_id,
            ApprovalRequest.tool_name == tool_name,
            ApprovalRequest.status == "APPROVED"
        ).order_by(ApprovalRequest.resolved_at.desc()).first()

        if not app_req:
            return False, "No approved authorization found for this operation."

        # Check cryptographic argument match
        if app_req.argument_hash and app_req.argument_hash != current_hash:
            app_req.status = "REJECTED"
            app_req.feedback = "Security Invalidation: Action arguments altered after approval was granted."
            db.commit()
            return False, "Security Invalidation: Action arguments changed after approval was granted. Authorization revoked."

        return True, None
