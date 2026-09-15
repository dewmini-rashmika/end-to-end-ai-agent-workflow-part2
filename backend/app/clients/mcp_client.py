"""
MCP Client — wraps httpx calls to local MCP server SSE endpoints.
Agents import tool functions from here rather than calling HTTP directly.
"""
from typing import Any
import httpx

from app.config.settings import settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Generic MCP client that calls a FastMCP server's tool via HTTP POST.
    FastMCP exposes: POST /tools/call  { "name": "<tool>", "arguments": {...} }
    """

    def __init__(self, base_url: str, server_name: str):
        self.base_url = base_url.rstrip("/")
        self.server_name = server_name

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Invoke a tool on the MCP server."""
        url = f"{self.base_url}/tools/call"
        payload = {"name": tool_name, "arguments": arguments}
        logger.info("mcp_tool_call", server=self.server_name, tool=tool_name)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # FastMCP wraps results in content array
                content = data.get("content", [{}])
                if content and isinstance(content, list):
                    text = content[0].get("text", "{}")
                    import json as _json
                    try:
                        return _json.loads(text)
                    except Exception:
                        return {"status": "success", "raw": text}
                return data
            except httpx.HTTPError as e:
                logger.error(
                    "mcp_call_failed",
                    server=self.server_name,
                    tool=tool_name,
                    error=str(e),
                )
                return {"status": "error", "message": str(e)}


# ── Pre-configured clients ────────────────────────────────────────────────────

flight_mcp = MCPClient(
    base_url=f"http://localhost:{settings.MCP_FLIGHT_PORT}",
    server_name="flight_mcp",
)

hotel_mcp = MCPClient(
    base_url=f"http://localhost:{settings.MCP_HOTEL_PORT}",
    server_name="hotel_mcp",
)

weather_mcp = MCPClient(
    base_url=f"http://localhost:{settings.MCP_WEATHER_PORT}",
    server_name="weather_mcp",
)

budget_mcp = MCPClient(
    base_url=f"http://localhost:{settings.MCP_BUDGET_PORT}",
    server_name="budget_mcp",
)
