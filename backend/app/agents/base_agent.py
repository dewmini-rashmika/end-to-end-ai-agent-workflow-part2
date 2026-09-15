"""
BaseAgent — abstract class all specialist agents inherit from.
Handles the common run loop: build messages → call LLM with tools →
store checkpoint → update TravelState.
"""
from __future__ import annotations

import abc
from datetime import datetime
from typing import Any, Optional

from app.agents.state import TravelState
from app.clients.llm_client import LLMClient
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class BaseAgent(abc.ABC):
    """
    Abstract specialist agent.

    Subclasses must implement:
      - agent_name: str
      - system_prompt: str
      - tool_schemas: list[dict]
      - tool_map: dict[str, callable]
      - _build_user_message(state) -> str
      - _parse_output(content, state) -> dict
    """

    agent_name: str = "base_agent"
    system_prompt: str = ""
    tool_schemas: list[dict] = []
    tool_map: dict[str, Any] = {}

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    # ── Public interface ──────────────────────────────────────────────────────

    async def run(self, state: TravelState) -> TravelState:
        """
        Execute the agent: call the LLM with tools, parse output, update state.
        Returns the mutated TravelState.
        """
        logger.info("agent_run_start", agent=self.agent_name, thread=state.thread_id)
        state.update_agent_result(self.agent_name, status="running")

        try:
            messages = self._build_messages(state)

            if self.tool_schemas:
                llm_response = await self.llm.complete_with_tools(
                    messages=messages,
                    tools=self.tool_schemas,
                    tool_map=self.tool_map,
                )
            else:
                llm_response = await self.llm.complete(messages=messages)

            parsed = self._parse_output(llm_response.content, state)
            self._apply_output_to_state(parsed, state)

            state.update_agent_result(
                self.agent_name,
                status="completed",
                output=parsed,
                model_used=llm_response.model,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens,
            )
            state.current_step += 1
            logger.info(
                "agent_run_complete",
                agent=self.agent_name,
                tokens=llm_response.total_tokens,
            )

        except Exception as e:
            logger.error("agent_run_failed", agent=self.agent_name, error=str(e))
            state.update_agent_result(
                self.agent_name, status="failed", error=str(e)
            )

        return state

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_messages(self, state: TravelState) -> list[dict]:
        """Construct the messages list for the LLM call."""
        user_msg = self._build_user_message(state)
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_msg},
        ]

    # ── Abstract methods ──────────────────────────────────────────────────────

    @abc.abstractmethod
    def _build_user_message(self, state: TravelState) -> str:
        """Return the user-facing prompt for this agent."""
        ...

    @abc.abstractmethod
    def _parse_output(self, content: str, state: TravelState) -> dict:
        """Parse LLM output text into a structured dict."""
        ...

    @abc.abstractmethod
    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        """Write parsed output into the appropriate state field."""
        ...
