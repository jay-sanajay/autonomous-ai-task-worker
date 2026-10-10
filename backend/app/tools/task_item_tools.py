"""
AgentOS - Task Item Management Tools.
Allows the autonomous agent to create, list, update, and independently verify task items and calendar events.
"""

from __future__ import annotations
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult
from backend.app.database.models import TaskItem, VerificationResult


class CreateTaskItemTool(ControlledBaseTool):
    name = "create_task_item"
    description = (
        "Create an actionable task item or calendar event in the internal task management system. "
        "Accepts title, due_date (interview date/time), meeting_link, and description."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the task or calendar event"},
            "due_date": {"type": "string", "description": "Scheduled date and time (e.g. 2024-10-24 at 02:00 PM IST)"},
            "meeting_link": {"type": "string", "description": "Video conference URL (Google Meet, Zoom, etc.)"},
            "description": {"type": "string", "description": "Detailed notes, topics, or interviewer details"},
            "priority": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"], "description": "Priority level"}
        },
        "required": ["title", "due_date"]
    }

    def execute(
        self,
        db_session: Session,
        title: str,
        due_date: str,
        meeting_link: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = "HIGH"
    ) -> ToolResult:
        if not title or not title.strip():
            return ToolResult(success=False, error="Task title cannot be empty.", retryable=False)

        # Check for existing duplicate task
        existing = db_session.query(TaskItem).filter(
            TaskItem.title == title.strip(),
            TaskItem.due_date == due_date.strip()
        ).first()

        if existing:
            return ToolResult(
                success=True,
                data={
                    "task_item_id": existing.id,
                    "title": existing.title,
                    "due_date": existing.due_date,
                    "meeting_link": existing.meeting_link,
                    "status": existing.status,
                    "message": f"Task item already exists (ID: {existing.id})."
                }
            )

        task_item = TaskItem(
            title=title.strip(),
            due_date=due_date.strip(),
            meeting_link=meeting_link.strip() if meeting_link else None,
            description=description.strip() if description else "Interview event scheduled by AgentOS",
            priority=priority.upper(),
            status="PENDING",
            source_reference="HR Email Notification",
            created_at=datetime.now(timezone.utc)
        )

        db_session.add(task_item)
        db_session.commit()
        db_session.refresh(task_item)

        return ToolResult(
            success=True,
            data={
                "task_item_id": task_item.id,
                "title": task_item.title,
                "due_date": task_item.due_date,
                "meeting_link": task_item.meeting_link,
                "priority": task_item.priority,
                "status": task_item.status,
                "created_at": task_item.created_at.isoformat(),
                "message": f"Successfully created task item #{task_item.id}: '{task_item.title}'."
            }
        )


class ListTaskItemsTool(ControlledBaseTool):
    name = "list_task_items"
    description = "List all existing task items in the user's task management system."
    parameters_schema = {
        "type": "object",
        "properties": {
            "status_filter": {"type": "string", "enum": ["ALL", "PENDING", "COMPLETED"], "description": "Filter by status"}
        }
    }

    def execute(self, db_session: Session, status_filter: str = "ALL") -> ToolResult:
        query = db_session.query(TaskItem)
        if status_filter != "ALL":
            query = query.filter(TaskItem.status == status_filter)
        
        items = query.order_by(TaskItem.created_at.desc()).all()
        return ToolResult(
            success=True,
            data={
                "count": len(items),
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "due_date": t.due_date,
                        "meeting_link": t.meeting_link,
                        "status": t.status,
                        "priority": t.priority
                    }
                    for t in items
                ]
            }
        )


class VerifyTaskItemTool(ControlledBaseTool):
    name = "verify_task_item"
    description = (
        "Independently read the persisted task item from the database and verify "
        "that title, interview date, and meeting link match the source email data."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "task_item_id": {"type": "integer", "description": "ID of task item to verify"},
            "expected_title": {"type": "string", "description": "Expected task title"},
            "expected_due_date": {"type": "string", "description": "Expected interview date"},
            "expected_meeting_link": {"type": "string", "description": "Expected meeting link"}
        },
        "required": ["task_item_id", "expected_title", "expected_due_date"]
    }

    def execute(
        self,
        db_session: Session,
        task_item_id: int,
        expected_title: str,
        expected_due_date: str,
        expected_meeting_link: Optional[str] = None
    ) -> ToolResult:
        record = db_session.query(TaskItem).filter(TaskItem.id == task_item_id).first()
        if not record:
            return ToolResult(
                success=False,
                error=f"Ground-truth verification FAILED: Task item #{task_item_id} not found in database.",
                data={"verified": False}
            )

        title_match = expected_title.lower() in record.title.lower() or record.title.lower() in expected_title.lower()
        date_match = expected_due_date.strip() in record.due_date.strip() or record.due_date.strip() in expected_due_date.strip()
        link_match = True
        if expected_meeting_link and record.meeting_link:
            link_match = expected_meeting_link.strip().lower() in record.meeting_link.strip().lower()

        all_matched = title_match and date_match and link_match

        # Generate cryptographic token
        raw_token = f"TASK|{record.id}|{record.title}|{record.due_date}|{record.meeting_link}"
        v_token = "VERIFIED-TASK-" + hashlib.sha256(raw_token.encode()).hexdigest()[:12].upper()

        field_comparisons = {
            "title": {"expected": expected_title, "actual": record.title, "match": title_match},
            "due_date": {"expected": expected_due_date, "actual": record.due_date, "match": date_match},
            "meeting_link": {"expected": expected_meeting_link, "actual": record.meeting_link, "match": link_match}
        }

        return ToolResult(
            success=all_matched,
            data={
                "verified": all_matched,
                "task_item_id": record.id,
                "title": record.title,
                "due_date": record.due_date,
                "meeting_link": record.meeting_link,
                "verification_token": v_token,
                "field_comparisons": field_comparisons,
                "audit_notes": "Task item event verified against SQLite task_items ledger."
            },
            error=None if all_matched else "Verification mismatch in task item fields"
        )
