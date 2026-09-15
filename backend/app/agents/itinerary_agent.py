"""
Itinerary Agent — synthesises all specialist outputs into a day-by-day plan.
Uses LLM (Llama 3 via MCP or GPT-4o) with optional RAG context injection.
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.state import TravelState
from app.clients.llm_client import itinerary_llm
from app.config.system_prompts import ITINERARY_AGENT_SYSTEM_PROMPT


class ItineraryAgent(BaseAgent):
    agent_name = "itinerary_agent"
    system_prompt = ITINERARY_AGENT_SYSTEM_PROMPT
    tool_schemas = []   # No external tools — synthesis only
    tool_map = {}

    def __init__(self):
        super().__init__(llm_client=itinerary_llm)

    def _build_user_message(self, state: TravelState) -> str:
        tc = state.trip_constraints

        sections = [
            f"## User Request\n{state.user_input}",
            f"## Trip Parameters\n{tc.model_dump_json(indent=2)}",
        ]

        if state.flight_results:
            sections.append(
                f"## Flight Options\n```json\n{json.dumps(state.flight_results, indent=2)}\n```"
            )

        if state.hotel_results:
            sections.append(
                f"## Hotel Options\n```json\n{json.dumps(state.hotel_results, indent=2)}\n```"
            )

        if state.weather_results:
            sections.append(
                f"## Weather Forecast\n```json\n{json.dumps(state.weather_results, indent=2)}\n```"
            )

        if state.budget_analysis:
            sections.append(
                f"## Budget Analysis\n```json\n{json.dumps(state.budget_analysis, indent=2)}\n```"
            )

        if state.rag_context:
            sections.append(
                f"## Destination Knowledge (from knowledge base)\n{state.rag_context}"
            )

        if state.hitl_feedback and state.hitl_status == "changes_requested":
            sections.append(
                f"## HITL Change Request\nThe user has reviewed a previous plan and "
                f"requests the following changes:\n{state.hitl_feedback}\n"
                "Please incorporate these changes into the revised itinerary."
            )

        sections.append(
            "\nUsing ALL the above information, create a detailed, personalised "
            "day-by-day itinerary. Return ONLY valid JSON matching the itinerary_plan schema."
        )

        return "\n\n".join(sections)

    def _parse_output(self, content: str, state: TravelState) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {"itinerary_plan": data}
        except json.JSONDecodeError:
            # Try extracting JSON block from markdown
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return {"raw_content": content}

    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        state.itinerary_plan = output
