from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DiscoveredEntity(BaseModel):
    key: str
    value: Any
    source: str
    confidence: float = 1.0
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkingMemory(BaseModel):
    """
    Stateful scratchpad and entity store maintained across the agent's execution loop.
    Allows the agent to remember discovered invoice numbers, amounts, dates, and API responses.
    """
    entities: Dict[str, Any] = Field(default_factory=dict)
    scratchpad: List[str] = Field(default_factory=list)
    action_log: List[Dict[str, Any]] = Field(default_factory=list)

    def set(self, key: str, value: Any, source: str = "execution"):
        self.entities[key] = value
        self.scratchpad.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Learned '{key}' = {value} (from {source})")

    def get(self, key: str, default: Any = None) -> Any:
        return self.entities.get(key, default)

    def append_note(self, note: str):
        self.scratchpad.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {note}")

    def log_action(self, action_name: str, payload: Any, result: Any):
        self.action_log.append({
            "action": action_name,
            "payload": payload,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def summary(self) -> Dict[str, Any]:
        return {
            "entities": self.entities,
            "recent_notes": self.scratchpad[-5:] if self.scratchpad else []
        }
