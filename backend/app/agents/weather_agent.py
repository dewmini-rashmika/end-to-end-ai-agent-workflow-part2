"""
Weather Agent — retrieves forecasts from the Custom Weather MCP server.
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.state import TravelState
from app.clients.llm_client import weather_llm
from app.config.system_prompts import WEATHER_AGENT_SYSTEM_PROMPT
from app.tools.weather_tools import WEATHER_TOOL_SCHEMAS, WEATHER_TOOL_MAP


class WeatherAgent(BaseAgent):
    agent_name = "weather_agent"
    system_prompt = WEATHER_AGENT_SYSTEM_PROMPT
    tool_schemas = WEATHER_TOOL_SCHEMAS
    tool_map = WEATHER_TOOL_MAP

    def __init__(self):
        super().__init__(llm_client=weather_llm)

    def _build_user_message(self, state: TravelState) -> str:
        tc = state.trip_constraints
        return (
            f"Get the weather forecast for this trip:\n"
            f"- Destination: {tc.destination or 'unknown'}\n"
            f"- Travel dates: {tc.departure_date or 'unknown'} to {tc.return_date or 'unknown'}\n"
            f"- Traveller interests: {', '.join(tc.interests) if tc.interests else 'general sightseeing'}\n\n"
            "Use get_weather_forecast to retrieve the forecast. "
            "Also call get_weather_alerts if there are any concerns. "
            "Provide packing suggestions and highlight any days that might affect outdoor plans."
        )

    def _parse_output(self, content: str, state: TravelState) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {"weather_results": data}
        except json.JSONDecodeError:
            return {"raw_content": content}

    def _apply_output_to_state(self, output: dict, state: TravelState) -> None:
        state.weather_results = output
