from __future__ import annotations
import os
import json
from typing import Dict, Any, List, Optional
from centra_worker.llm.base import BaseLLMProvider, AgentDecision

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        if not genai:
            raise ImportError("google.generativeai is not installed.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def decide_next_action(
        self,
        goal: str,
        plan_summary: str,
        working_memory: Dict[str, Any],
        step_history: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        system_instruction: Optional[str] = None
    ) -> AgentDecision:
        tool_names = [t["function"]["name"] for t in tools_schema]
        prompt = (
            f"You are an autonomous AI Task Worker.\n"
            f"GOAL: {goal}\n"
            f"PLAN: {plan_summary}\n"
            f"MEMORY: {json.dumps(working_memory)}\n"
            f"RECENT STEPS: {json.dumps(step_history[-4:])}\n"
            f"AVAILABLE TOOLS: {json.dumps(tool_names)}\n\n"
            f"Respond in valid JSON format with keys:\n"
            f"- 'thought': your reasoning about current state and next step\n"
            f"- 'tool_name': name of tool to call, or null if goal completed\n"
            f"- 'tool_input': parameters dictionary for tool, or null\n"
            f"- 'is_finished': true if goal completely achieved and verified, else false\n"
            f"- 'final_summary': summary of completion if is_finished is true\n"
        )

        resp = self.model.generate_content(prompt)
        text = resp.text.strip()
        # Clean json backticks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        return AgentDecision(
            thought=data.get("thought", "Proceeding with next autonomous action."),
            tool_name=data.get("tool_name"),
            tool_input=data.get("tool_input"),
            is_finished=data.get("is_finished", False),
            final_summary=data.get("final_summary")
        )
