"""
Base MCP server helper — creates a FastAPI app with a /tools/call endpoint.
All MCP servers inherit from this pattern instead of using fastmcp.
"""
from __future__ import annotations

import json
import traceback
from typing import Any, Callable, Awaitable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import uvicorn

from app.config.logging_config import get_logger

logger = get_logger(__name__)


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


class MCPServer:
    """
    Lightweight FastAPI-based MCP server.
    Exposes tools as POST /tools/call and GET /tools/list endpoints.
    """

    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self._tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._tool_schemas: dict[str, dict] = {}

        self.app = FastAPI(title=name, version="1.0.0")
        self._register_routes()

    def tool(self, schema: dict | None = None):
        """Decorator to register a function as an MCP tool."""
        def decorator(fn: Callable):
            self._tools[fn.__name__] = fn
            if schema:
                self._tool_schemas[fn.__name__] = schema
            else:
                self._tool_schemas[fn.__name__] = {
                    "name": fn.__name__,
                    "description": fn.__doc__ or "",
                }
            return fn
        return decorator

    def _register_routes(self):
        @self.app.get("/health")
        async def health():
            return {"status": "ok", "server": self.name}

        @self.app.get("/tools/list")
        async def list_tools():
            return {"tools": list(self._tool_schemas.values())}

        @self.app.post("/tools/call")
        async def call_tool(req: ToolCallRequest):
            tool_fn = self._tools.get(req.name)
            if not tool_fn:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"Tool '{req.name}' not found", "available": list(self._tools.keys())},
                )
            try:
                result = await tool_fn(**req.arguments)
                # Wrap in MCP-style content format
                return {
                    "content": [
                        {"type": "text", "text": json.dumps(result)}
                    ]
                }
            except Exception as e:
                logger.error("tool_call_error", server=self.name, tool=req.name, error=str(e))
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e), "traceback": traceback.format_exc()},
                )

    def run(self):
        logger.info("mcp_server_starting", name=self.name, port=self.port)
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")
