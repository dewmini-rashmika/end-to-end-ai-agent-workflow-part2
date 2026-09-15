"""
Budget Agent — analyses trip costs using the Budget MCP server.
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.state import TravelState
from app.clients.llm_client import budget_llm
from app.config.system_prompts import BUDGET_AGENT_SYSTEM_PROMPT
from app.tools.budget_tools import BUDGET_TOOL_SCHEMAS, BUDGET_TOOL_MAP


class BudgetAgent(BaseAgent):
    agent_name = "budget_agent"
    system_prompt = BUDGET_AGENT_SYSTEM_PROMPT
    tool_schemas = BUDGET_TOOL_SCHEMAS
    tool_map = BUDGET_TOOL_MAP

    def __init__(self):
        super().__init__(llm_client=budget_llm)

    def _build_user_message(self, state: TravelState) -> str:
        tc = state.trip_constraints

        # Extract known costs from already-run agents
        flight_cost = None
        if state.flight_results:
            flights = state.flight_results.get("flights", [])
            if flights:
                flight_cost = flights[0].get("total_price_usd")

        hotel_cost = None
        if state.hotel_results:
            hotels = state.hotel_results.get("hotels", [])
            if hotels:
                hotel_cost = hotels[0].get("total_price_usd")

        return (
            f"Analyse the budget for this trip:\n"
            f"- Destination: {tc.destination or 'unknown'}\n"
            f"- Duration: {tc.duration_days or 'unknown'} days\n"
            f"- Travelers: {tc.travelers}\n"
            f"- Budget level: {tc.budget_level}\n"
            f"- User stated budget: {f'${tc.budget_usd} USD' if tc.budget_usd else 'not specified'}\n"
            f"- Known flight cost: {f'${flight_cost}' if flight_cost else 'unknown'}\n"
            f"- Known accommodation cost: {f'${hotel_cost}' if hotel_cost else 'unknown'}\n\n"
            "Call estimate_trip_cost for a full breakdown. "
            "Also call get_exchange_rates to provide costs in the local currency. "
            "Provide practical savings tips for this destination."
        )

    def _parse_output(self, content: str, state: TravelState) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {"budget_analysis": data}
        except json.JSONDecodeError:
            return {"raw_content": content}

    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        state.budget_analysis = output
