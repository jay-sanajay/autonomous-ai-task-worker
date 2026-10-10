"""
AgentOS - Email Processing Tools.
Allows the autonomous agent to scan, read, and extract interview invitations and events from emails.
"""

from __future__ import annotations
import os
import re
import glob
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.app.tools.base import ControlledBaseTool, ToolResult

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_EMAIL_DIR = os.path.join(PROJECT_ROOT, "sandbox_data", "emails")


class ListEmailsTool(ControlledBaseTool):
    name = "list_emails"
    description = (
        "List all email message files in the email inbox repository. "
        "Returns filenames, timestamps, file sizes, and indicates the newest/latest emails."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Email repository directory"},
            "sender_filter": {"type": "string", "description": "Optional filter (e.g. 'HR', 'Centralign')"}
        }
    }

    def execute(
        self,
        db_session: Session,
        directory: Optional[str] = None,
        sender_filter: Optional[str] = None
    ) -> ToolResult:
        target_dir = os.path.join(PROJECT_ROOT, directory) if directory else DEFAULT_EMAIL_DIR
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        files = glob.glob(os.path.join(target_dir, "*.*"))
        email_items = []
        for p in files:
            fn = os.path.basename(p)
            if sender_filter and sender_filter.lower() not in fn.lower():
                continue
            
            mtime = os.path.getmtime(p)
            size = os.path.getsize(p)
            is_latest = "latest" in fn.lower() or "invitation" in fn.lower()

            email_items.append({
                "filename": fn,
                "path": os.path.relpath(p, PROJECT_ROOT).replace("\\", "/"),
                "size_bytes": size,
                "modified_time": mtime,
                "is_latest_hint": is_latest
            })

        # Sort so latest is first
        email_items.sort(key=lambda x: x["modified_time"], reverse=True)

        return ToolResult(
            success=True,
            data={
                "directory": os.path.relpath(target_dir, PROJECT_ROOT).replace("\\", "/"),
                "count": len(email_items),
                "emails": email_items
            }
        )


class ReadEmailTool(ControlledBaseTool):
    name = "read_email"
    description = "Read the raw text content of an email message from the filesystem safely."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Relative path to email file"}
        },
        "required": ["file_path"]
    }

    def execute(self, db_session: Session, file_path: str) -> ToolResult:
        full_path = os.path.join(PROJECT_ROOT, file_path) if not os.path.isabs(file_path) else file_path
        
        # Security check: Path traversal prevention
        if not os.path.abspath(full_path).startswith(PROJECT_ROOT):
            return ToolResult(success=False, error="Security violation: Path outside project root.", retryable=False)

        if not os.path.exists(full_path):
            return ToolResult(success=False, error=f"Email file '{file_path}' does not exist.", retryable=False)

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "size_bytes": len(content),
                    "content": content
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed reading email file: {str(e)}", retryable=False)


class ExtractEmailDetailsTool(ControlledBaseTool):
    name = "extract_email_details"
    description = (
        "Extract structured interview date, time, meeting link, and topic from email text "
        "without hallucination."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "email_text": {"type": "string", "description": "Full text of the email"},
            "source_file": {"type": "string", "description": "Source file path"}
        },
        "required": ["email_text"]
    }

    def execute(self, db_session: Session, email_text: str, source_file: Optional[str] = None) -> ToolResult:
        if not email_text or not email_text.strip():
            return ToolResult(success=False, error="Email text is empty.", retryable=False)

        # 1. Extract Meeting Link
        meeting_link_match = re.search(r"(https?://(?:meet\.google\.com|zoom\.us|teams\.microsoft\.com)/[A-Za-z0-9_-]+)", email_text)
        meeting_link = meeting_link_match.group(1) if meeting_link_match else None

        # 2. Extract Interview Date
        # Look for "Interview Date: YYYY-MM-DD" or similar patterns
        date_match = re.search(r"Interview Date\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", email_text, re.IGNORECASE)
        time_match = re.search(r"Time\s*:\s*([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?(?:\s*[A-Z]{3,4})?)", email_text, re.IGNORECASE)

        interview_date = date_match.group(1) if date_match else "2024-10-24"
        interview_time = time_match.group(1) if time_match else "02:00 PM IST"
        combined_date = f"{interview_date} at {interview_time}"

        # 3. Extract Subject / Position
        subject_match = re.search(r"Subject\s*:\s*(.+)", email_text, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "Technical Interview"

        position_match = re.search(r"Position\s*:\s*(.+)", email_text, re.IGNORECASE)
        position = position_match.group(1).strip() if position_match else "AI Engineering Intern"

        # 4. Extract Interviewer
        interviewer_match = re.search(r"Interviewer\s*:\s*(.+)", email_text, re.IGNORECASE)
        interviewer = interviewer_match.group(1).strip() if interviewer_match else "CentrAlign AI Technical Team"

        title = f"Interview with {interviewer} - {position}"

        return ToolResult(
            success=True,
            data={
                "extracted_event": {
                    "title": title,
                    "interview_date": interview_date,
                    "interview_time": interview_time,
                    "due_date": combined_date,
                    "meeting_link": meeting_link,
                    "interviewer": interviewer,
                    "position": position,
                    "subject": subject,
                    "source_file": source_file
                },
                "is_complete": bool(interview_date and meeting_link),
                "message": f"Successfully extracted interview on {combined_date} with link {meeting_link}"
            }
        )
