"""
AgentOS - Customer Support Management Tools.
Allows the agent to retrieve unresolved support tickets, prioritize them, and update statuses.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult
from backend.app.database.models import SupportTicket


class ListSupportTicketsTool(ControlledBaseTool):
    name = "list_support_tickets"
    description = (
        "Retrieve customer support tickets from the database. "
        "Allows filtering by status ('OPEN', 'IN_PROGRESS', 'RESOLVED') or priority ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "status_filter": {"type": "string", "enum": ["ALL", "OPEN", "IN_PROGRESS", "RESOLVED"], "default": "OPEN"},
            "priority_filter": {"type": "string", "enum": ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"], "default": "ALL"}
        }
    }

    def execute(
        self,
        db_session: Session,
        status_filter: str = "OPEN",
        priority_filter: str = "ALL"
    ) -> ToolResult:
        query = db_session.query(SupportTicket)
        if status_filter != "ALL":
            query = query.filter(SupportTicket.status == status_filter.upper())
        if priority_filter != "ALL":
            query = query.filter(SupportTicket.priority == priority_filter.upper())

        tickets = query.order_by(SupportTicket.id.asc()).all()

        return ToolResult(
            success=True,
            data={
                "count": len(tickets),
                "tickets": [
                    {
                        "id": t.id,
                        "ticket_code": t.ticket_code,
                        "customer_name": t.customer_name,
                        "subject": t.subject,
                        "description": t.description,
                        "priority": t.priority,
                        "status": t.status,
                        "created_at": t.created_at.isoformat()
                    }
                    for t in tickets
                ]
            }
        )


class UpdateSupportTicketTool(ControlledBaseTool):
    name = "update_support_ticket"
    description = "Update a customer support ticket status or priority after resolving an inquiry."
    parameters_schema = {
        "type": "object",
        "properties": {
            "ticket_code": {"type": "string", "description": "Unique ticket code (e.g. TICK-101)"},
            "new_status": {"type": "string", "enum": ["OPEN", "IN_PROGRESS", "RESOLVED"], "description": "New status"},
            "new_priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"], "description": "Updated priority"}
        },
        "required": ["ticket_code"]
    }

    def execute(
        self,
        db_session: Session,
        ticket_code: str,
        new_status: Optional[str] = None,
        new_priority: Optional[str] = None
    ) -> ToolResult:
        ticket = db_session.query(SupportTicket).filter(SupportTicket.ticket_code == ticket_code.strip()).first()
        if not ticket:
            return ToolResult(success=False, error=f"Ticket '{ticket_code}' not found.", retryable=False)

        if new_status:
            ticket.status = new_status.upper()
            if new_status.upper() == "RESOLVED":
                ticket.resolved_at = datetime.now(timezone.utc)
        if new_priority:
            ticket.priority = new_priority.upper()

        db_session.commit()

        return ToolResult(
            success=True,
            data={
                "ticket_code": ticket.ticket_code,
                "customer_name": ticket.customer_name,
                "status": ticket.status,
                "priority": ticket.priority,
                "message": f"Successfully updated ticket {ticket.ticket_code} to status {ticket.status}."
            }
        )
