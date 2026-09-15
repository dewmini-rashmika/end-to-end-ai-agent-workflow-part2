"""
Flight Agent — searches for flights using the AviationStack MCP server.
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.state import TravelState
from app.clients.llm_client import flight_llm
from app.config.system_prompts import FLIGHT_AGENT_SYSTEM_PROMPT
from app.tools.flight_tools import FLIGHT_TOOL_SCHEMAS, FLIGHT_TOOL_MAP


class FlightAgent(BaseAgent):
    agent_name = "flight_agent"
    system_prompt = FLIGHT_AGENT_SYSTEM_PROMPT
    tool_schemas = FLIGHT_TOOL_SCHEMAS
    tool_map = FLIGHT_TOOL_MAP

    def __init__(self):
        super().__init__(llm_client=flight_llm)

    def _build_user_message(self, state: TravelState) -> str:
        tc = state.trip_constraints
        return (
            f"Search for flights for the following trip:\n"
            f"- Origin: {tc.origin or 'unknown'} (IATA: {tc.origin_iata or 'unknown'})\n"
            f"- Destination: {tc.destination or 'unknown'} (IATA: {tc.destination_iata or 'unknown'})\n"
            f"- Departure date: {tc.departure_date or 'unknown'}\n"
            f"- Return date: {tc.return_date or 'one-way'}\n"
            f"- Passengers: {tc.travelers}\n"
            f"- Cabin class: {tc.cabin_class}\n"
            f"- Budget (total): {f'${tc.budget_usd}' if tc.budget_usd else 'flexible'}\n\n"
            f"Original user request: {state.user_input}\n\n"
            "Use the search_flights tool to find options. If IATA codes are unknown, "
            "use get_airports first. Return top 3-5 options ranked by value."
        )

    def _parse_output(self, content: str, state: TravelState) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {"flight_results": data}
        except json.JSONDecodeError:
            return {"raw_content": content, "flight_results": []}

    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        state.flight_results = output
