"""
AgentOS - Structured Error Taxonomy & Adaptive Recovery Policy Engine.
Defines formal error classifications, retry limits, and recovery strategies
to prevent retry loops, recursive expansion, and unbounded calls.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    TRANSIENT_NETWORK_ERROR = "TRANSIENT_NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    MISSING_DATA = "MISSING_DATA"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    STALE_BROWSER_STATE = "STALE_BROWSER_STATE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    PERMANENT_TOOL_FAILURE = "PERMANENT_TOOL_FAILURE"


class RecoveryActionType(str, Enum):
    RETRY_BACKOFF = "RETRY_BACKOFF"
    REPLAN_ALTERNATIVE = "REPLAN_ALTERNATIVE"
    CORRECT_ARGUMENTS = "CORRECT_ARGUMENTS"
    REFRESH_BROWSER_STATE = "REFRESH_BROWSER_STATE"
    PAUSE_FOR_APPROVAL = "PAUSE_FOR_APPROVAL"
    ABORT_WITH_REPORT = "ABORT_WITH_REPORT"
    RESOLVE_DUPLICATE = "RESOLVE_DUPLICATE"


class RecoveryPolicy(BaseModel):
    action: RecoveryActionType
    retryable: bool
    backoff_seconds: float = 0.0
    suggested_strategy: str
    replan_required: bool = False
    requires_human: bool = False


def classify_error(
    error_message: Optional[str],
    tool_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> ErrorCategory:
    """Categorize raw execution errors into structured taxonomical classes."""
    if not error_message:
        return ErrorCategory.PERMANENT_TOOL_FAILURE

    err_lower = error_message.lower()

    if any(k in err_lower for k in ["approval required", "high risk", "policy threshold", "paused for sign-off"]):
        return ErrorCategory.APPROVAL_REQUIRED

    if any(k in err_lower for k in ["duplicate", "already exists", "idempotency key"]):
        return ErrorCategory.DUPLICATE_RECORD

    if any(k in err_lower for k in ["503", "502", "504", "transient", "connection reset", "connection refused", "econnreset"]):
        return ErrorCategory.TRANSIENT_NETWORK_ERROR

    if any(k in err_lower for k in ["timeout", "timed out", "navigation timeout", "deadline exceeded"]):
        return ErrorCategory.TIMEOUT

    if any(k in err_lower for k in ["stale element", "detached from document", "element not visible", "target closed"]):
        return ErrorCategory.STALE_BROWSER_STATE

    if any(k in err_lower for k in ["verification failed", "mismatch", "ground-truth verification"]):
        return ErrorCategory.VERIFICATION_FAILURE

    if any(k in err_lower for k in ["disallowed domain", "permission denied", "forbidden", "restricted workspace"]):
        return ErrorCategory.PERMISSION_DENIED

    if any(k in err_lower for k in ["not found", "file not found", "no such file", "does not exist in database"]):
        return ErrorCategory.RESOURCE_NOT_FOUND

    if any(k in err_lower for k in ["missing required", "invalid argument", "validation error", "unrecognized argument"]):
        return ErrorCategory.INVALID_ARGUMENTS

    if any(k in err_lower for k in ["missing data", "empty content", "no rows found"]):
        return ErrorCategory.MISSING_DATA

    return ErrorCategory.PERMANENT_TOOL_FAILURE


def get_recovery_policy(
    category: ErrorCategory,
    retry_count: int = 0,
    max_retries: int = 3,
    error_detail: Optional[str] = None
) -> RecoveryPolicy:
    """Determine autonomous recovery action based on error category and retry budget."""
    if retry_count >= max_retries:
        return RecoveryPolicy(
            action=RecoveryActionType.ABORT_WITH_REPORT,
            retryable=False,
            suggested_strategy=f"Retry budget exhausted ({retry_count}/{max_retries} attempts). Aborting with honest audit trail."
        )

    if category == ErrorCategory.APPROVAL_REQUIRED:
        return RecoveryPolicy(
            action=RecoveryActionType.PAUSE_FOR_APPROVAL,
            retryable=False,
            requires_human=True,
            suggested_strategy="Action exceeds policy threshold. Pausing execution for executive authorization."
        )

    if category == ErrorCategory.DUPLICATE_RECORD:
        return RecoveryPolicy(
            action=RecoveryActionType.RESOLVE_DUPLICATE,
            retryable=False,
            suggested_strategy="Record already exists. Inspect existing ledger entry and prevent duplicate commitment."
        )

    if category == ErrorCategory.TRANSIENT_NETWORK_ERROR:
        backoff = min(0.5 * (2 ** retry_count), 4.0)
        return RecoveryPolicy(
            action=RecoveryActionType.RETRY_BACKOFF,
            retryable=True,
            backoff_seconds=backoff,
            suggested_strategy=f"Transient failure detected. Retrying with exponential backoff ({backoff}s)."
        )

    if category == ErrorCategory.TIMEOUT:
        backoff = min(1.0 * (1.5 ** retry_count), 5.0)
        return RecoveryPolicy(
            action=RecoveryActionType.RETRY_BACKOFF,
            retryable=True,
            backoff_seconds=backoff,
            suggested_strategy="Operation timed out. Retrying with increased latency window."
        )

    if category == ErrorCategory.STALE_BROWSER_STATE:
        return RecoveryPolicy(
            action=RecoveryActionType.REFRESH_BROWSER_STATE,
            retryable=True,
            backoff_seconds=0.5,
            suggested_strategy="Stale DOM element reference. Refreshing page DOM and re-locating element via stable accessibility selector."
        )

    if category == ErrorCategory.RESOURCE_NOT_FOUND:
        return RecoveryPolicy(
            action=RecoveryActionType.REPLAN_ALTERNATIVE,
            retryable=True,
            replan_required=True,
            suggested_strategy="Target resource missing. Replanning using alternative discovery path or directory search."
        )

    if category == ErrorCategory.INVALID_ARGUMENTS:
        return RecoveryPolicy(
            action=RecoveryActionType.CORRECT_ARGUMENTS,
            retryable=True,
            suggested_strategy="Parameter schema mismatch. Validating and correcting arguments against tool OpenAPI definition."
        )

    if category == ErrorCategory.VERIFICATION_FAILURE:
        return RecoveryPolicy(
            action=RecoveryActionType.ABORT_WITH_REPORT,
            retryable=False,
            suggested_strategy="Ground-truth verification critic detected state mismatch. Flagging verification failure."
        )

    return RecoveryPolicy(
        action=RecoveryActionType.ABORT_WITH_REPORT,
        retryable=False,
        suggested_strategy="Permanent or fatal failure encountered. Terminating safely without repeating side effects."
    )
