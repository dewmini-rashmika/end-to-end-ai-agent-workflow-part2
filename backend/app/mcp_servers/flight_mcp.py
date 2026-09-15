"""
Flight MCP Server — AviationStack API wrapper.
Runs on port 8001. Exposes: search_flights, get_flight_status, get_airports.
"""
from typing import Optional

import httpx

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.mcp_servers.base_mcp import MCPServer

logger = get_logger(__name__)

server = MCPServer(name="AviationStack MCP - TripMate", port=settings.MCP_FLIGHT_PORT)

AVIATIONSTACK_BASE = "http://api.aviationstack.com/v1"


async def _call_aviationstack(endpoint: str, params: dict) -> dict:
    api_key = settings.AVIATIONSTACK_API_KEY
    if not api_key:
        return _mock_flight_data(endpoint, params)
    params["access_key"] = api_key
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.get(f"{AVIATIONSTACK_BASE}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("aviationstack_http_error", error=str(e))
            return _mock_flight_data(endpoint, params)


def _mock_flight_data(endpoint: str, params: dict) -> dict:
    origin = params.get("dep_iata", "LHR")
    dest = params.get("arr_iata", "DXB")
    return {
        "data": [
            {
                "flight": {"iata": "EK001"},
                "airline": {"name": "Emirates"},
                "departure": {"iata": origin, "scheduled": "2026-10-15T08:00:00+00:00", "terminal": "3"},
                "arrival": {"iata": dest, "scheduled": "2026-10-15T18:30:00+00:00", "terminal": "3"},
                "flight_status": "scheduled",
                "price_usd": 420.0, "stops": 0, "duration_minutes": 390, "cabin_class": "economy",
            },
            {
                "flight": {"iata": "FZ202"},
                "airline": {"name": "FlyDubai"},
                "departure": {"iata": origin, "scheduled": "2026-10-15T14:00:00+00:00", "terminal": "2"},
                "arrival": {"iata": dest, "scheduled": "2026-10-16T00:30:00+00:00", "terminal": "2"},
                "flight_status": "scheduled",
                "price_usd": 310.0, "stops": 1, "duration_minutes": 510, "cabin_class": "economy",
            },
            {
                "flight": {"iata": "BA007"},
                "airline": {"name": "British Airways"},
                "departure": {"iata": origin, "scheduled": "2026-10-15T10:30:00+00:00", "terminal": "5"},
                "arrival": {"iata": dest, "scheduled": "2026-10-15T21:45:00+00:00", "terminal": "1"},
                "flight_status": "scheduled",
                "price_usd": 380.0, "stops": 0, "duration_minutes": 435, "cabin_class": "economy",
            },
        ],
        "pagination": {"total": 3},
    }


@server.tool()
async def search_flights(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
    cabin_class: str = "economy",
) -> dict:
    """Search for available flights between two airports."""
    logger.info("search_flights", origin=origin_iata, destination=destination_iata, date=departure_date)
    params = {
        "dep_iata": origin_iata.upper(),
        "arr_iata": destination_iata.upper(),
        "flight_date": departure_date,
        "limit": 10,
    }
    raw = await _call_aviationstack("flights", params)
    flights = []
    for item in raw.get("data", []):
        dep = item.get("departure", {})
        arr = item.get("arrival", {})
        price = item.get("price_usd", 0)
        stops = item.get("stops", 0)
        duration = item.get("duration_minutes", 0)
        value_score = (price / 100) + (duration / 60) + (stops * 2)
        flights.append({
            "flight_number": item.get("flight", {}).get("iata", "N/A"),
            "airline": item.get("airline", {}).get("name", "Unknown"),
            "origin": dep.get("iata"),
            "destination": arr.get("iata"),
            "departure_time": dep.get("scheduled"),
            "arrival_time": arr.get("scheduled"),
            "duration_minutes": duration,
            "stops": stops,
            "price_per_person_usd": price,
            "total_price_usd": price * passengers,
            "cabin_class": item.get("cabin_class", cabin_class),
            "value_score": round(value_score, 2),
            "status": item.get("flight_status"),
        })
    flights.sort(key=lambda x: x["value_score"])
    return {
        "status": "success",
        "origin": origin_iata.upper(),
        "destination": destination_iata.upper(),
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers,
        "flights": flights[:5],
        "total_found": len(flights),
    }


@server.tool()
async def get_flight_status(flight_iata: str, flight_date: str) -> dict:
    """Get the current status of a specific flight."""
    params = {"flight_iata": flight_iata, "flight_date": flight_date}
    raw = await _call_aviationstack("flights", params)
    if not raw.get("data"):
        return {"status": "not_found", "flight": flight_iata}
    item = raw["data"][0]
    return {
        "status": "success",
        "flight": {
            "flight_number": flight_iata,
            "airline": item.get("airline", {}).get("name"),
            "status": item.get("flight_status"),
            "departure": item.get("departure", {}),
            "arrival": item.get("arrival", {}),
        },
    }


@server.tool()
async def get_airports(search_term: str) -> dict:
    """Search for airports by city or name."""
    params = {"search": search_term, "limit": 5}
    raw = await _call_aviationstack("airports", params)
    airports = [
        {"name": a.get("airport_name"), "iata": a.get("iata_code"), "city": a.get("city_iata_code"), "country": a.get("country_name")}
        for a in raw.get("data", [])
    ] or [
        {"name": f"{search_term} International Airport", "iata": search_term[:3].upper(), "city": search_term, "country": "Unknown"}
    ]
    return {"status": "success", "airports": airports}


if __name__ == "__main__":
    server.run()
