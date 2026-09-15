"""
LiteLLM client — unified interface for all LLM calls across agents.
Handles tool-call loops, token tracking, retries, and model routing.
"""
import json
from typing import Any, Optional

import litellm
from litellm import acompletion

from app.config.settings import settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)

# Configure LiteLLM globally
litellm.set_verbose = settings.DEBUG
if settings.OPENAI_API_KEY:
    litellm.openai_key = settings.OPENAI_API_KEY
if settings.ANTHROPIC_API_KEY:
    litellm.anthropic_key = settings.ANTHROPIC_API_KEY
if settings.GROQ_API_KEY:
    litellm.groq_key = settings.GROQ_API_KEY


class LLMResponse:
    """Normalised LLM response container."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        tool_calls: list[dict] | None = None,
        finish_reason: str = "stop",
    ):
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tool_calls": self.tool_calls,
            "finish_reason": self.finish_reason,
        }


class LLMClient:
    """
    Wrapper around LiteLLM acompletion.
    Supports agentic tool-call loops with automatic tool execution.
    """

    def __init__(self, model: str, max_tool_iterations: int = 5):
        self.model = model
        self.max_tool_iterations = max_tool_iterations

    async def complete(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_map: Optional[dict[str, Any]] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """
        Single completion call — does NOT execute tool calls.
        Use complete_with_tools for agentic loops.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = await acompletion(**kwargs)
            choice = response.choices[0]
            message = choice.message

            tool_calls = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": json.loads(tc.function.arguments),
                        }
                    )

            usage = response.usage or {}
            return LLMResponse(
                content=message.content or "",
                model=response.model or self.model,
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
            )
        except Exception as e:
            logger.error("llm_completion_error", model=self.model, error=str(e))
            raise

    async def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_map: dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Agentic loop: calls LLM, executes tool calls, feeds results back,
        repeats until finish_reason == 'stop' or max iterations reached.
        Returns the final LLMResponse with the accumulated content.
        """
        current_messages = list(messages)
        total_prompt_tokens = 0
        total_completion_tokens = 0
        final_response = None

        for iteration in range(self.max_tool_iterations):
            logger.info(
                "llm_tool_loop",
                model=self.model,
                iteration=iteration,
                messages_count=len(current_messages),
            )

            resp = await self.complete(
                messages=current_messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            total_prompt_tokens += resp.prompt_tokens
            total_completion_tokens += resp.completion_tokens
            final_response = resp

            if not resp.has_tool_calls:
                break

            # Append assistant message with tool_calls
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": resp.content}
            # Reconstruct tool_calls in OpenAI format for the next turn
            raw_tool_calls = []
            for tc in resp.tool_calls:
                raw_tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                )
            assistant_msg["tool_calls"] = raw_tool_calls
            current_messages.append(assistant_msg)

            # Execute each tool call
            for tc in resp.tool_calls:
                tool_fn = tool_map.get(tc["name"])
                if not tool_fn:
                    tool_result = {"error": f"Unknown tool: {tc['name']}"}
                else:
                    try:
                        tool_result = await tool_fn(**tc["arguments"])
                    except Exception as e:
                        logger.error(
                            "tool_execution_error",
                            tool=tc["name"],
                            error=str(e),
                        )
                        tool_result = {"error": str(e)}

                current_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["name"],
                        "content": json.dumps(tool_result),
                    }
                )

        if final_response is None:
            raise RuntimeError("LLM tool loop produced no response")

        final_response.prompt_tokens = total_prompt_tokens
        final_response.completion_tokens = total_completion_tokens
        return final_response

    async def complete_json(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Convenience: complete with JSON response format and parse the result.
        """
        resp = await self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", resp.content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            logger.error("json_parse_failed", content=resp.content[:200])
            return {"raw_content": resp.content}


# ── Pre-configured clients for each agent ────────────────────────────────────

def get_llm_client(model: str) -> LLMClient:
    """Factory — returns an LLMClient for the given model."""
    return LLMClient(model=model)


supervisor_llm = LLMClient(model=settings.SUPERVISOR_MODEL)
flight_llm = LLMClient(model=settings.FLIGHT_AGENT_MODEL)
hotel_llm = LLMClient(model=settings.HOTEL_AGENT_MODEL)
weather_llm = LLMClient(model=settings.WEATHER_AGENT_MODEL)
budget_llm = LLMClient(model=settings.BUDGET_AGENT_MODEL)
itinerary_llm = LLMClient(model=settings.ITINERARY_AGENT_MODEL)
final_llm = LLMClient(model=settings.FINAL_AGENT_MODEL)
guardrail_llm = LLMClient(model=settings.GUARDRAIL_MODEL)
