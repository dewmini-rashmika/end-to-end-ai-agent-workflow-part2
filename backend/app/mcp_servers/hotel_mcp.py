"""
Hotel MCP Server — Tavily Search API wrapper.
Runs on port 8002. Exposes: search_hotels, get_hotel_details.
"""
import re
from typing import Optional

import httpx

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.mcp_servers.base_mcp import MCPServer

logger = get_logger(__name__)

server = MCPServer(name="Tavily Hotel MCP - TripMate", port=settings.MCP_HOTEL_PORT)

TAVILY_BASE = "https://api.tavily.com"


async def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return _mock_hotel_results(query)
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(
                f"{TAVILY_BASE}/search",
                json={"api_key": api_key, "query": query, "search_depth": "advanced", "max_results": max_results, "include_answer": True},
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as e:
            logger.error("tavily_http_error", error=str(e))
            return _mock_hotel_results(query)


def _mock_hotel_results(query: str) -> list[dict]:
    return [
        {"title": "JW Marriott Hotel Dubai", "url": "https://www.marriott.com", "content": "5-star hotel in Downtown Dubai. Price: $220/night. Free cancellation. Pool, Gym, Multiple restaurants, Business centre.", "score": 0.92},
        {"title": "Atlantis The Palm", "url": "https://www.atlantis.com/dubai", "content": "5-star resort on Palm Jumeirah. Price: $380/night. Water park, beach access, multiple pools. Free cancellation available.", "score": 0.90},
        {"title": "Premier Inn Dubai", "url": "https://www.premierinn.com", "content": "Budget-friendly 3-star hotel. Price: $85/night. Free cancellation. City centre location, breakfast included.", "score": 0.82},
        {"title": "Rove Downtown", "url": "https://www.rovehotels.com", "content": "Modern 3-star hotel in Downtown Dubai. Price: $110/night. Free cancellation. Near Dubai Mall and Burj Khalifa.", "score": 0.80},
    ]


def _parse_hotel(result: dict, check_in: str, check_out: str, nights: int) -> dict:
    content = result.get("content", "")
    price_per_night = 150
    price_match = re.search(r"\$(\d+(?:,\d+)?)/night", content)
    if price_match:
        price_per_night = int(price_match.group(1).replace(",", ""))
    free_cancellation = "free cancellation" in content.lower()
    rating = 5 if "5-star" in content.lower() else (4 if "4-star" in content.lower() else 3)
    return {
        "name": result.get("title", "Unknown Hotel"),
        "url": result.get("url"),
        "star_rating": rating,
        "price_per_night_usd": price_per_night,
        "total_price_usd": price_per_night * nights,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "free_cancellation": free_cancellation,
        "description": content[:300],
        "relevance_score": result.get("score", 0),
    }


@server.tool()
async def search_hotels(
    destination: str,
    check_in_date: str,
    check_out_date: str,
    guests: int = 2,
    budget_per_night_usd: Optional[float] = None,
    accommodation_type: str = "hotel",
    star_rating_min: int = 3,
) -> dict:
    """Search for hotels and accommodation at a destination."""
    from datetime import date
    logger.info("search_hotels", destination=destination, check_in=check_in_date)
    try:
        nights = max((date.fromisoformat(check_out_date) - date.fromisoformat(check_in_date)).days, 1)
    except ValueError:
        nights = 1
    budget_clause = f"under ${budget_per_night_usd}/night" if budget_per_night_usd else ""
    query = f"best {star_rating_min}+ star {accommodation_type}s in {destination} {budget_clause} price amenities reviews"
    results = await _tavily_search(query, max_results=6)
    hotels = [_parse_hotel(r, check_in_date, check_out_date, nights) for r in results]
    if budget_per_night_usd:
        hotels = [h for h in hotels if h["price_per_night_usd"] <= budget_per_night_usd]
    hotels.sort(key=lambda h: h["relevance_score"], reverse=True)
    return {
        "status": "success",
        "destination": destination,
        "check_in": check_in_date,
        "check_out": check_out_date,
        "nights": nights,
        "guests": guests,
        "hotels": hotels[:5],
        "total_found": len(hotels),
    }


@server.tool()
async def get_hotel_details(hotel_name: str, destination: str) -> dict:
    """Get detailed information about a specific hotel."""
    results = await _tavily_search(f"{hotel_name} {destination} amenities reviews", max_results=2)
    if not results:
        return {"status": "not_found", "hotel": hotel_name}
    return {"status": "success", "hotel": {"name": hotel_name, "destination": destination, "details": results[0].get("content", ""), "source_url": results[0].get("url")}}


if __name__ == "__main__":
    server.run()
