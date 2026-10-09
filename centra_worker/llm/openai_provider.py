from __future__ import annotations
import os
import json
from typing import Dict, Any, List, Optional
from centra_worker.llm.base import BaseLLMProvider, AgentDecision

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        if not OpenAI:
            raise ImportError("openai package is not installed.")
        self.client = OpenAI(api_key=self.api_key)

    def decide_next_action(
        self,
        goal: str,
        plan_summary: str,
        working_memory: Dict[str, Any],
        step_history: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        system_instruction: Optional[str] = None
    ) -> AgentDecision:
        system_msg = (
            system_instruction
            or "You are an autonomous AI Task Worker for an enterprise. "
            "You are given an end goal and a set of tools. You reason step-by-step, "
            "use tools to inspect files and systems, detect failures, retry or use alternatives, "
            "and independently verify that your target outcome is achieved before finishing."
        )

        prompt_messages = [
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": (
                    f"USER GOAL:\n{goal}\n\n"
                    f"CURRENT PLAN STATUS:\n{plan_summary}\n\n"
                    f"WORKING MEMORY (Discovered Entities):\n{json.dumps(working_memory, indent=2)}\n\n"
                    f"STEP HISTORY:\n{json.dumps(step_history[-6:], indent=2)}\n\n"
                    "Think carefully about what has been done, what is missing, and what action to take next."
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=prompt_messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None,
            temperature=0.1
        )

        choice = response.choices[0].message
        thought = choice.content or "Determined next action based on system state."

        if choice.tool_calls:
            tc = choice.tool_calls[0]
            tool_name = tc.function.name
            try:
                tool_input = json.loads(tc.function.arguments)
            except Exception:
                tool_input = {}
            return AgentDecision(
                thought=thought,
                tool_name=tool_name,
                tool_input=tool_input,
                is_finished=False
            )
        else:
            return AgentDecision(
                thought=thought,
                is_finished=True,
                final_summary=choice.content
            )
