"""
Hotel Agent — searches for accommodation via the Tavily MCP server.
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.state import TravelState
from app.clients.llm_client import hotel_llm
from app.config.system_prompts import HOTEL_AGENT_SYSTEM_PROMPT
from app.tools.hotel_tools import HOTEL_TOOL_SCHEMAS, HOTEL_TOOL_MAP


class HotelAgent(BaseAgent):
    agent_name = "hotel_agent"
    system_prompt = HOTEL_AGENT_SYSTEM_PROMPT
    tool_schemas = HOTEL_TOOL_SCHEMAS
    tool_map = HOTEL_TOOL_MAP

    def __init__(self):
        super().__init__(llm_client=hotel_llm)

    def _build_user_message(self, state: TravelState) -> str:
        tc = state.trip_constraints
        budget_per_night = (
            round(tc.budget_usd * 0.30 / max(tc.duration_days or 5, 1), 2)
            if tc.budget_usd
            else None
        )
        return (
            f"Find accommodation for this trip:\n"
            f"- Destination: {tc.destination or 'unknown'}\n"
            f"- Check-in: {tc.departure_date or 'unknown'}\n"
            f"- Check-out: {tc.return_date or 'unknown'}\n"
            f"- Guests: {tc.travelers}\n"
            f"- Accommodation type: {tc.accommodation_type}\n"
            f"- Budget per night: {f'${budget_per_night}' if budget_per_night else 'flexible'}\n"
            f"- Interests/preferences: {', '.join(tc.interests) if tc.interests else 'none specified'}\n"
            f"- Budget level: {tc.budget_level}\n\n"
            f"Original request: {state.user_input}\n\n"
            "Use search_hotels to find the best options. Prioritise free cancellation and good reviews."
        )

    def _parse_output(self, content: str, state: TravelState) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {"hotel_results": data}
        except json.JSONDecodeError:
            return {"raw_content": content, "hotel_results": []}

    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        state.hotel_results = output
