from __future__ import annotations
import uuid
from typing import Dict, Any, Optional, Tuple
from centra_worker.models.approval import ApprovalRequest, RiskLevel
from centra_worker.tools.base import BaseTool


class ApprovalGuard:
    def __init__(self, auto_approve_high_risk: bool = False):
        self.auto_approve_high_risk = auto_approve_high_risk
        self.pending_approvals: Dict[str, ApprovalRequest] = {}

    def check_tool_call(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any]
    ) -> Tuple[bool, Optional[ApprovalRequest]]:
        """
        Evaluate if tool call requires human-in-the-loop sign-off.
        Returns: (requires_approval: bool, ApprovalRequest)
        """
        if self.auto_approve_high_risk:
            return False, None

        risk_level, risk_reason = tool.assess_risk(arguments)

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            req_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
            request = ApprovalRequest(
                approval_id=req_id,
                tool_name=tool.name,
                action_description=f"Execute {tool.name} with sensitive parameters",
                risk_level=risk_level,
                risk_reason=risk_reason or "High-risk operation triggered.",
                pending_payload=arguments,
                status="PENDING"
            )
            self.pending_approvals[req_id] = request
            return True, request

        return False, None

    def approve(self, approval_id: str, approver: str = "Admin_User", feedback: Optional[str] = None) -> Optional[ApprovalRequest]:
        req = self.pending_approvals.get(approval_id)
        if req:
            req.status = "APPROVED"
            req.resolved_by = approver
            req.user_feedback = feedback
            return req
        return None

    def reject(self, approval_id: str, approver: str = "Admin_User", feedback: Optional[str] = None) -> Optional[ApprovalRequest]:
        req = self.pending_approvals.get(approval_id)
        if req:
            req.status = "REJECTED"
            req.resolved_by = approver
            req.user_feedback = feedback
            return req
        return None
