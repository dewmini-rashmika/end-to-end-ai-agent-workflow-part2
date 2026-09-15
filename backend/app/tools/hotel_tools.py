"""
Hotel tools — wrappers around the Hotel (Tavily) MCP client.
"""
from typing import Any, Optional
from app.clients.mcp_client import hotel_mcp


async def search_hotels(
    destination: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 2,
    budget_per_night_usd: Optional[float] = None,
    accommodation_type: str = "hotel",
    star_rating_min: int = 3,
) -> dict[str, Any]:
    """Search hotels via Tavily MCP."""
    return await hotel_mcp.call_tool(
        "search_hotels",
        {
            "destination": destination,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "guests": guests,
            "budget_per_night_usd": budget_per_night_usd,
            "accommodation_type": accommodation_type,
            "star_rating_min": star_rating_min,
        },
    )


async def get_hotel_details(hotel_name: str, destination: str) -> dict[str, Any]:
    """Get details for a specific hotel."""
    return await hotel_mcp.call_tool(
        "get_hotel_details",
        {"hotel_name": hotel_name, "destination": destination},
    )


HOTEL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search for hotels and accommodation at a travel destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "check_in_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "check_out_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "guests": {"type": "integer", "default": 2},
                    "budget_per_night_usd": {"type": "number", "description": "Max price per night"},
                    "accommodation_type": {
                        "type": "string",
                        "enum": ["hotel", "hostel", "resort", "apartment"],
                    },
                    "star_rating_min": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["destination", "check_in_date", "check_out_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hotel_details",
            "description": "Get detailed information about a specific hotel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hotel_name": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["hotel_name", "destination"],
            },
        },
    },
]

HOTEL_TOOL_MAP = {
    "search_hotels": search_hotels,
    "get_hotel_details": get_hotel_details,
}
