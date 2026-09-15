"""
Weather tools — wrappers around the Custom Weather MCP client.
"""
from typing import Any
from app.clients.mcp_client import weather_mcp


async def get_weather_forecast(
    destination: str, start_date: str, end_date: str
) -> dict[str, Any]:
    return await weather_mcp.call_tool(
        "get_weather_forecast",
        {"destination": destination, "start_date": start_date, "end_date": end_date},
    )


async def get_current_weather(destination: str) -> dict[str, Any]:
    return await weather_mcp.call_tool(
        "get_current_weather", {"destination": destination}
    )


async def get_weather_alerts(destination: str) -> dict[str, Any]:
    return await weather_mcp.call_tool(
        "get_weather_alerts", {"destination": destination}
    )


WEATHER_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get a daily weather forecast for a destination over a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["destination", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_alerts",
            "description": "Get active severe weather alerts for a destination.",
            "parameters": {
                "type": "object",
                "properties": {"destination": {"type": "string"}},
                "required": ["destination"],
            },
        },
    },
]

WEATHER_TOOL_MAP = {
    "get_weather_forecast": get_weather_forecast,
    "get_current_weather": get_current_weather,
    "get_weather_alerts": get_weather_alerts,
}
