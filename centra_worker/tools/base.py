from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from centra_worker.models.approval import RiskLevel


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}
    default_risk: RiskLevel = RiskLevel.LOW

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """Execute the tool synchronously or asynchronously."""
        pass

    def assess_risk(self, kwargs: Dict[str, Any]) -> tuple[RiskLevel, Optional[str]]:
        """
        Assess risk for safety/gating.
        Returns (RiskLevel, explanation).
        Override in sensitive tools (e.g. high financial amounts).
        """
        return self.default_risk, None

    def to_schema(self) -> Dict[str, Any]:
        """Return standardized OpenAI/ReAct compatible tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
