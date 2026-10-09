"""
Failure Detection and Self-Correction Engine for CentraWorker.
Detects tool execution failures, categorizes error types, and determines recovery policies:
exponential backoff, alternative tool fallback, or human escalation.
"""

from __future__ import annotations
import time
from enum import Enum
from typing import Dict, Any, Optional, Tuple


class ErrorCategory(str, Enum):
    TRANSIENT_503_OR_NETWORK = "TRANSIENT_503_OR_NETWORK"
    SCHEMA_VALIDATION = "SCHEMA_VALIDATION"
    ALTERNATIVE_REQUIRED = "ALTERNATIVE_REQUIRED"
    PERMISSION_OR_RISK = "PERMISSION_OR_RISK"
    FATAL = "FATAL"


class RecoveryAction(BaseModel if False else object):
    pass


class FailureHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}

    def is_failure(self, tool_output: Any) -> bool:
        if isinstance(tool_output, dict):
            status = tool_output.get("status", "").lower()
            if status in ("error", "transient_error", "validation_error"):
                return True
            if tool_output.get("verified") is False:
                return True
        return False

    def categorize_error(self, tool_name: str, tool_output: Dict[str, Any]) -> Tuple[ErrorCategory, str]:
        err_msg = str(tool_output.get("error") or tool_output.get("reason") or "Unknown error")
        err_lower = err_msg.lower()

        # Transient 503 / Network
        if "503" in err_lower or "overloaded" in err_lower or "connection" in err_lower or "timeout" in err_lower:
            return ErrorCategory.TRANSIENT_503_OR_NETWORK, err_msg

        # Schema / Missing field
        if "missing" in err_lower or "validation" in err_lower or "invalid format" in err_lower:
            return ErrorCategory.SCHEMA_VALIDATION, err_msg

        # Fallback to browser if REST API has persistent failure
        if tool_name == "erp_submit_invoice" and self.retry_counts.get(tool_name, 0) >= 2:
            return ErrorCategory.ALTERNATIVE_REQUIRED, "REST API repeatedly failing. Switching to Browser Web Portal fallback."

        return ErrorCategory.FATAL, err_msg

    def decide_recovery(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Formulate autonomous recovery plan.
        """
        category, err_msg = self.categorize_error(tool_name, tool_output)
        current_retries = self.retry_counts.get(tool_name, 0)

        if category == ErrorCategory.TRANSIENT_503_OR_NETWORK:
            if current_retries < self.max_retries:
                self.retry_counts[tool_name] = current_retries + 1
                backoff_sec = 0.5 * (2 ** current_retries)
                return {
                    "action": "RETRY_WITH_BACKOFF",
                    "delay_seconds": backoff_sec,
                    "retry_count": current_retries + 1,
                    "message": f"Detected transient service error ({err_msg}). Applying {backoff_sec}s exponential backoff before retry.",
                    "tool_name": tool_name,
                    "tool_input": tool_input
                }
            else:
                # Fall back to alternative tool
                return {
                    "action": "SWITCH_TO_ALTERNATIVE_TOOL",
                    "alternative_tool": "browser_fill_form",
                    "message": "Max retries reached on REST API. Switching to Browser Web Portal form entry.",
                    "tool_name": "browser_navigate",
                    "tool_input": {"url": "http://internal.centra/portal/invoices"}
                }

        elif category == ErrorCategory.ALTERNATIVE_REQUIRED:
            return {
                "action": "SWITCH_TO_ALTERNATIVE_TOOL",
                "alternative_tool": "browser_fill_form",
                "message": "Switching to Web Portal browser entry as alternative path.",
                "tool_name": "browser_navigate",
                "tool_input": {"url": "http://internal.centra/portal/invoices"}
            }

        elif category == ErrorCategory.SCHEMA_VALIDATION:
            # Self-correction: attempt to heal payload or report
            return {
                "action": "SCHEMA_HEALING",
                "message": f"Encountered validation error ({err_msg}). Checking documents for missing attributes.",
                "tool_name": "read_file",
                "tool_input": tool_input
            }

        return {
            "action": "ESCALATE_OR_HALT",
            "message": f"Non-recoverable failure encountered: {err_msg}",
            "tool_name": None
        }

    def reset(self):
        self.retry_counts.clear()
