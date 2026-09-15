"""
Budget tools — wrappers around the Budget MCP client.
"""
from typing import Any, Optional
from app.clients.mcp_client import budget_mcp


async def get_exchange_rates(
    base_currency: str = "USD",
    target_currencies: Optional[list[str]] = None,
) -> dict[str, Any]:
    return await budget_mcp.call_tool(
        "get_exchange_rates",
        {"base_currency": base_currency, "target_currencies": target_currencies},
    )


async def estimate_trip_cost(
    destination: str,
    duration_days: int,
    travelers: int = 1,
    budget_level: str = "mid",
    flight_cost_usd: Optional[float] = None,
    accommodation_cost_usd: Optional[float] = None,
    user_budget_usd: Optional[float] = None,
) -> dict[str, Any]:
    return await budget_mcp.call_tool(
        "estimate_trip_cost",
        {
            "destination": destination,
            "duration_days": duration_days,
            "travelers": travelers,
            "budget_level": budget_level,
            "flight_cost_usd": flight_cost_usd,
            "accommodation_cost_usd": accommodation_cost_usd,
            "user_budget_usd": user_budget_usd,
        },
    )


async def get_cost_of_living(destination: str) -> dict[str, Any]:
    return await budget_mcp.call_tool(
        "get_cost_of_living", {"destination": destination}
    )


BUDGET_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rates",
            "description": "Get current currency exchange rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {"type": "string", "default": "USD"},
                    "target_currencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target currency codes",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_trip_cost",
            "description": "Estimate the full cost of a trip including flights, accommodation, food, activities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "duration_days": {"type": "integer"},
                    "travelers": {"type": "integer", "default": 1},
                    "budget_level": {
                        "type": "string",
                        "enum": ["budget", "mid", "luxury"],
                        "default": "mid",
                    },
                    "flight_cost_usd": {"type": "number"},
                    "accommodation_cost_usd": {"type": "number"},
                    "user_budget_usd": {"type": "number"},
                },
                "required": ["destination", "duration_days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cost_of_living",
            "description": "Get cost-of-living estimates for a destination city.",
            "parameters": {
                "type": "object",
                "properties": {"destination": {"type": "string"}},
                "required": ["destination"],
            },
        },
    },
]

BUDGET_TOOL_MAP = {
    "get_exchange_rates": get_exchange_rates,
    "estimate_trip_cost": estimate_trip_cost,
    "get_cost_of_living": get_cost_of_living,
}
