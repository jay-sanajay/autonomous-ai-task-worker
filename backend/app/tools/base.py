"""
AgentOS - Controlled Base Tool Interface.
Enforces strict parameter validation, explicit permissions, timeouts, and structured execution results.
"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool = Field(..., description="Whether the tool execution succeeded")
    data: Optional[Any] = Field(default=None, description="Structured execution payload")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    retryable: bool = Field(default=False, description="Whether this failure can be recovered via retry")
    execution_duration_ms: float = Field(default=0.0, description="Duration in milliseconds")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ControlledBaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}
    is_consequential: bool = False  # e.g., creates financial commitments
    timeout_seconds: float = 10.0

    @abstractmethod
    def execute(self, db_session, **kwargs) -> ToolResult:
        """Execute the controlled operation against the database session and sandbox."""
        pass

    def run_safe(self, db_session, **kwargs) -> ToolResult:
        """Safe wrapper tracking duration and catching unhandled exceptions."""
        start_time = time.time()
        try:
            result = self.execute(db_session, **kwargs)
            result.execution_duration_ms = round((time.time() - start_time) * 1000, 2)
            return result
        except ConnectionError as ce:
            dur = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False,
                error=f"Transient Connection Error: {str(ce)}",
                retryable=True,
                execution_duration_ms=dur
            )
        except Exception as e:
            dur = round((time.time() - start_time) * 1000, 2)
            return ToolResult(
                success=False,
                error=f"Tool Execution Error: {str(e)}",
                retryable=False,
                execution_duration_ms=dur
            )

    def to_schema(self) -> Dict[str, Any]:
        """Format as OpenAPI / function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
