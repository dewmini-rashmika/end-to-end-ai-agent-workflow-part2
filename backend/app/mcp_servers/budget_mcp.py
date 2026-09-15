"""
Budget MCP Server — ExchangeRate API + cost estimates.
Runs on port 8004. Exposes: get_exchange_rates, estimate_trip_cost, get_cost_of_living.
"""
from typing import Optional

import httpx

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.mcp_servers.base_mcp import MCPServer

logger = get_logger(__name__)

server = MCPServer(name="Budget MCP - TripMate", port=settings.MCP_BUDGET_PORT)

EXCHANGERATE_BASE = "https://v6.exchangerate-api.com/v6"

CITY_COST_INDEX = {
    "dubai": {"budget": 80, "mid": 180, "luxury": 450, "currency": "AED"},
    "london": {"budget": 90, "mid": 200, "luxury": 500, "currency": "GBP"},
    "tokyo": {"budget": 60, "mid": 140, "luxury": 400, "currency": "JPY"},
    "paris": {"budget": 85, "mid": 190, "luxury": 480, "currency": "EUR"},
    "new york": {"budget": 100, "mid": 250, "luxury": 600, "currency": "USD"},
    "bangkok": {"budget": 40, "mid": 90, "luxury": 220, "currency": "THB"},
    "bali": {"budget": 35, "mid": 80, "luxury": 200, "currency": "IDR"},
    "singapore": {"budget": 75, "mid": 160, "luxury": 400, "currency": "SGD"},
    "colombo": {"budget": 30, "mid": 70, "luxury": 180, "currency": "LKR"},
    "default": {"budget": 60, "mid": 150, "luxury": 380, "currency": "USD"},
}

MOCK_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "AED": 3.67,
    "THB": 35.2, "IDR": 15800, "SGD": 1.35, "LKR": 320.0, "CAD": 1.37, "AUD": 1.55, "INR": 83.5,
}


async def _fetch_rates(base: str = "USD") -> dict:
    api_key = settings.EXCHANGERATE_API_KEY
    if not api_key:
        return {"base_code": "USD", "conversion_rates": MOCK_RATES}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{EXCHANGERATE_BASE}/{api_key}/latest/{base}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return {"base_code": "USD", "conversion_rates": MOCK_RATES}


@server.tool()
async def get_exchange_rates(base_currency: str = "USD", target_currencies: Optional[list] = None) -> dict:
    """Get current currency exchange rates."""
    data = await _fetch_rates(base_currency.upper())
    all_rates = data.get("conversion_rates", {})
    rates = {k: all_rates[k] for k in target_currencies if k in all_rates} if target_currencies else all_rates
    return {"status": "success", "base_currency": base_currency.upper(), "rates": rates}


@server.tool()
async def estimate_trip_cost(
    destination: str, duration_days: int, travelers: int = 1,
    budget_level: str = "mid", flight_cost_usd: Optional[float] = None,
    accommodation_cost_usd: Optional[float] = None, user_budget_usd: Optional[float] = None,
) -> dict:
    """Estimate the total cost of a trip including all categories."""
    index = CITY_COST_INDEX.get(destination.lower(), CITY_COST_INDEX["default"])
    daily = index[budget_level]
    breakdown = {
        "meals": round(daily * 0.30 * duration_days * travelers, 2),
        "local_transport": round(daily * 0.15 * duration_days * travelers, 2),
        "activities_attractions": round(daily * 0.25 * duration_days * travelers, 2),
        "shopping_misc": round(daily * 0.20 * duration_days * travelers, 2),
        "tips_fees": round(daily * 0.10 * duration_days * travelers, 2),
    }
    est_flight = {"budget": 350, "mid": 650, "luxury": 1200}[budget_level]
    breakdown["flights"] = round((flight_cost_usd if flight_cost_usd else est_flight * travelers), 2)
    nightly = {"budget": 40, "mid": 120, "luxury": 350}[budget_level]
    breakdown["accommodation"] = round((accommodation_cost_usd if accommodation_cost_usd else nightly * duration_days), 2)
    subtotal = sum(breakdown.values())
    breakdown["contingency_10pct"] = round(subtotal * 0.10, 2)
    total = round(sum(breakdown.values()), 2)
    budget_status = "no_budget_set"
    budget_gap = None
    if user_budget_usd:
        budget_status = "within_budget" if total <= user_budget_usd else "over_budget"
        budget_gap = round(abs(user_budget_usd - total), 2)
    rates_data = await _fetch_rates("USD")
    local_currency = index["currency"]
    local_rate = rates_data.get("conversion_rates", {}).get(local_currency, 1)
    tips = [
        "Book flights 6-8 weeks in advance for best prices",
        "Use public transport instead of taxis where possible",
        "Eat where locals eat — avoid tourist-trap restaurants",
        "Look for free walking tours and museum free days",
        "Buy travel insurance to avoid unexpected costs",
    ]
    return {
        "status": "success", "destination": destination, "duration_days": duration_days,
        "travelers": travelers, "budget_level": budget_level, "total_estimated_usd": total,
        "total_estimated_local": round(total * local_rate, 2), "local_currency": local_currency,
        "breakdown": breakdown, "cost_per_person_usd": round(total / travelers, 2),
        "cost_per_day_usd": round(total / duration_days, 2), "budget_status": budget_status,
        "budget_gap_usd": budget_gap, "savings_tips": tips[:5],
    }


@server.tool()
async def get_cost_of_living(destination: str) -> dict:
    """Get cost-of-living overview for a destination."""
    index = CITY_COST_INDEX.get(destination.lower(), CITY_COST_INDEX["default"])
    return {
        "status": "success", "destination": destination,
        "daily_budget_usd": {"budget_traveller": index["budget"], "mid_range_traveller": index["mid"], "luxury_traveller": index["luxury"]},
        "local_currency": index["currency"],
    }


if __name__ == "__main__":
    server.run()
