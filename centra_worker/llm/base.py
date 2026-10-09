from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class AgentDecision(BaseModel):
    thought: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    is_finished: bool = False
    final_summary: Optional[str] = None
    needs_approval: bool = False
    approval_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    @abstractmethod
    def decide_next_action(
        self,
        goal: str,
        plan_summary: str,
        working_memory: Dict[str, Any],
        step_history: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        system_instruction: Optional[str] = None
    ) -> AgentDecision:
        """
        Evaluate current state and return agent reasoning and next action.
        """
        pass
