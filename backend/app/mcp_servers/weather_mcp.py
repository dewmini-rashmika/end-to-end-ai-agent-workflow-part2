"""
Weather MCP Server — OpenWeatherMap API wrapper.
Runs on port 8003. Exposes: get_weather_forecast, get_current_weather, get_weather_alerts.
"""
import httpx

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.mcp_servers.base_mcp import MCPServer

logger = get_logger(__name__)

server = MCPServer(name="Custom Weather MCP - TripMate", port=settings.MCP_WEATHER_PORT)

OWM_BASE = "https://api.openweathermap.org/data/3.0"
OWM_GEO_BASE = "http://api.openweathermap.org/geo/1.0"

MOCK_COORDS = {
    "dubai": (25.2048, 55.2708), "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503), "new york": (40.7128, -74.0060),
    "paris": (48.8566, 2.3522), "bangkok": (13.7563, 100.5018),
    "bali": (-8.3405, 115.0919), "singapore": (1.3521, 103.8198),
    "colombo": (6.9271, 79.8612),
}


async def _get_coordinates(city: str):
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return MOCK_COORDS.get(city.lower(), (25.2048, 55.2708))
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{OWM_GEO_BASE}/direct", params={"q": city, "limit": 1, "appid": api_key})
            resp.raise_for_status()
            data = resp.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
        except httpx.HTTPError:
            pass
    return MOCK_COORDS.get(city.lower(), (25.2048, 55.2708))


async def _fetch_one_call(lat: float, lon: float) -> dict:
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return _mock_weather()
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(f"{OWM_BASE}/onecall", params={"lat": lat, "lon": lon, "exclude": "minutely", "units": "metric", "appid": api_key})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            return _mock_weather()


def _mock_weather() -> dict:
    return {
        "current": {"temp": 32.5, "feels_like": 35.0, "humidity": 60, "wind_speed": 4.2, "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}], "uvi": 8.5},
        "daily": [{"dt": 1728000000 + i * 86400, "summary": "Hot and sunny" if i % 3 != 1 else "Partly cloudy", "temp": {"min": 28 + i, "max": 36 + i, "day": 33 + i}, "feels_like": {"day": 36 + i}, "humidity": 55 + i * 2, "wind_speed": 3.5, "pop": 0.1 if i % 3 != 1 else 0.6, "weather": [{"main": "Clear" if i % 3 != 1 else "Rain", "description": "clear sky" if i % 3 != 1 else "light rain", "icon": "01d" if i % 3 != 1 else "10d"}], "uvi": 9.0} for i in range(7)],
        "alerts": [], "timezone": "Asia/Dubai",
    }


def _day_summary(day: dict, date_str: str) -> dict:
    weather = day.get("weather", [{}])[0]
    return {
        "date": date_str, "condition": weather.get("main", "Unknown"),
        "description": weather.get("description", "").capitalize(),
        "temp_min_c": round(day.get("temp", {}).get("min", 0), 1),
        "temp_max_c": round(day.get("temp", {}).get("max", 0), 1),
        "feels_like_c": round(day.get("feels_like", {}).get("day", 0), 1),
        "humidity_pct": day.get("humidity", 0),
        "wind_speed_ms": round(day.get("wind_speed", 0), 1),
        "precipitation_chance_pct": round(day.get("pop", 0) * 100),
        "uv_index": round(day.get("uvi", 0), 1),
    }


def _packing_list(summaries: list) -> list:
    items = {"Passport & documents", "Travel adapter", "Phone charger"}
    avg_temp = sum(d["temp_max_c"] for d in summaries) / max(len(summaries), 1)
    has_rain = any(d["precipitation_chance_pct"] > 40 for d in summaries)
    high_uv = any(d["uv_index"] > 6 for d in summaries)
    if avg_temp > 28:
        items.update(["Lightweight clothing", "Shorts", "Sandals", "Hat", "Sunglasses"])
    elif avg_temp > 15:
        items.update(["Light jacket", "T-shirts", "Comfortable shoes"])
    else:
        items.update(["Warm coat", "Layers", "Waterproof boots"])
    if has_rain:
        items.update(["Compact umbrella", "Waterproof jacket"])
    if high_uv:
        items.update(["SPF 50+ sunscreen", "After-sun lotion"])
    return sorted(items)


@server.tool()
async def get_weather_forecast(destination: str, start_date: str, end_date: str) -> dict:
    """Get a daily weather forecast for a destination over a date range."""
    from datetime import date, timedelta
    coords = await _get_coordinates(destination)
    data = await _fetch_one_call(*coords)
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        start = date.today()
        end = start + timedelta(days=5)
    trip_days = (end - start).days + 1
    daily_data = data.get("daily", [])[:min(trip_days, 7)]
    summaries = [_day_summary(day, (start + timedelta(days=i)).isoformat()) for i, day in enumerate(daily_data)]
    warnings = []
    for day in summaries:
        if day["precipitation_chance_pct"] > 60:
            warnings.append(f"{day['date']}: High rain ({day['precipitation_chance_pct']}%) — consider indoor activities")
        if day["uv_index"] > 8:
            warnings.append(f"{day['date']}: Very high UV ({day['uv_index']}) — use sunscreen")
    return {"status": "success", "destination": destination, "daily_forecast": summaries, "packing_suggestions": _packing_list(summaries), "activity_warnings": warnings, "weather_alerts": []}


@server.tool()
async def get_current_weather(destination: str) -> dict:
    """Get current weather conditions for a destination."""
    coords = await _get_coordinates(destination)
    data = await _fetch_one_call(*coords)
    current = data.get("current", {})
    weather = current.get("weather", [{}])[0]
    return {"status": "success", "destination": destination, "temperature_c": current.get("temp"), "feels_like_c": current.get("feels_like"), "humidity_pct": current.get("humidity"), "wind_speed_ms": current.get("wind_speed"), "condition": weather.get("main"), "description": weather.get("description", "").capitalize(), "uv_index": current.get("uvi")}


@server.tool()
async def get_weather_alerts(destination: str) -> dict:
    """Get active weather alerts for a destination."""
    coords = await _get_coordinates(destination)
    data = await _fetch_one_call(*coords)
    return {"status": "success", "destination": destination, "alerts": data.get("alerts", []), "alert_count": len(data.get("alerts", []))}


if __name__ == "__main__":
    server.run()
