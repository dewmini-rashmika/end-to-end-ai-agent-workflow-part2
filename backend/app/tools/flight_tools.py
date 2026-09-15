"""
Flight tools — thin wrappers around the Flight MCP client.
These are the functions passed to the Flight LLM agent as tools.
"""
from typing import Any, Optional
from app.clients.mcp_client import flight_mcp


async def search_flights(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
    cabin_class: str = "economy",
) -> dict[str, Any]:
    """Search for available flights via AviationStack MCP."""
    return await flight_mcp.call_tool(
        "search_flights",
        {
            "origin_iata": origin_iata,
            "destination_iata": destination_iata,
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": passengers,
            "cabin_class": cabin_class,
        },
    )


async def get_flight_status(flight_iata: str, flight_date: str) -> dict[str, Any]:
    """Get real-time flight status."""
    return await flight_mcp.call_tool(
        "get_flight_status",
        {"flight_iata": flight_iata, "flight_date": flight_date},
    )


async def get_airports(search_term: str) -> dict[str, Any]:
    """Search airports by city or name."""
    return await flight_mcp.call_tool("get_airports", {"search_term": search_term})


# LiteLLM tool schema definitions (OpenAI function-calling format)
FLIGHT_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for available flights between two airports on a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin_iata": {"type": "string", "description": "Departure IATA code, e.g. LHR"},
                    "destination_iata": {"type": "string", "description": "Arrival IATA code, e.g. DXB"},
                    "departure_date": {"type": "string", "description": "Date YYYY-MM-DD"},
                    "return_date": {"type": "string", "description": "Return date YYYY-MM-DD (optional)"},
                    "passengers": {"type": "integer", "default": 1},
                    "cabin_class": {"type": "string", "enum": ["economy", "business", "first"]},
                },
                "required": ["origin_iata", "destination_iata", "departure_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_airports",
            "description": "Find airport IATA codes by city or airport name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "City or airport name"}
                },
                "required": ["search_term"],
            },
        },
    },
]

FLIGHT_TOOL_MAP = {
    "search_flights": search_flights,
    "get_airports": get_airports,
    "get_flight_status": get_flight_status,
}
