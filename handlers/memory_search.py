"""
Claude-Mem Handler
==================

Memory search via Claude-mem HTTP API integration.

Maps unified-mcp tools to Claude-mem's API endpoints:
- mem_search → /api/search (search observations)
- mem_get_observation → /api/observation/:id (get by ID)
- mem_recent_context → /api/recent (recent sessions)
- mem_timeline → /api/timeline (timeline view)
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from core.capability_loader import CapabilityHandler


class ClaudeMemHandler(CapabilityHandler):
    """Handler for Claude-mem memory search tools."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.api_url = config.get("api_url", "http://localhost:37777")
        self.http_client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize Claude-mem - verify API is accessible."""
        self.http_client = httpx.AsyncClient(timeout=30.0)

        try:
            # Test connection to Claude-mem API
            response = await self.http_client.get(f"{self.api_url}/health")
            if response.status_code == 200:
                self.logger.info(f"Claude-mem API accessible at {self.api_url}")
            else:
                self.logger.warning(
                    f"Claude-mem API returned status {response.status_code}. "
                    "Memory search may not work correctly."
                )
        except Exception as e:
            self.logger.warning(
                f"Could not connect to Claude-mem API at {self.api_url}: {e}. "
                "Ensure Claude-mem is running with: npm start (in claude-mem directory)"
            )

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "mem_search": {
                "name": "mem_search",
                "description": (
                    "Search memory observations using semantic search. "
                    "Returns relevant observations from past sessions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (natural language)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            "mem_get_observation": {
                "name": "mem_get_observation",
                "description": "Get a specific observation by ID",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Observation ID",
                        }
                    },
                    "required": ["id"],
                },
            },
            "mem_recent_context": {
                "name": "mem_recent_context",
                "description": (
                    "Get recent context from past sessions. "
                    "Returns the most recent observations and insights."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of observations (default: 20)",
                            "default": 20,
                        }
                    },
                },
            },
            "mem_timeline": {
                "name": "mem_timeline",
                "description": (
                    "Get timeline view of observations. "
                    "Returns chronological view of past sessions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of timeline entries (default: 50)",
                            "default": 50,
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for timeline (ISO format)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for timeline (ISO format)",
                        },
                    },
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a Claude-mem tool."""
        if tool_name == "mem_search":
            return await self._search(arguments)
        elif tool_name == "mem_get_observation":
            return await self._get_observation(arguments)
        elif tool_name == "mem_recent_context":
            return await self._recent_context(arguments)
        elif tool_name == "mem_timeline":
            return await self._timeline(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _search(self, args: dict) -> dict:
        """
        Search memory observations.

        Calls Claude-mem API: POST /api/search
        """
        query = args["query"]
        limit = args.get("limit", 10)

        try:
            response = await self.http_client.post(
                f"{self.api_url}/api/search",
                json={"query": query, "limit": limit}
            )
            response.raise_for_status()
            result = response.json()

            return {
                "status": "success",
                "tool": "mem_search",
                "query": query,
                "results": result,
            }

        except httpx.HTTPError as e:
            self.logger.error(f"Claude-mem API error: {e}")
            raise RuntimeError(f"Claude-mem API error: {e}")

    async def _get_observation(self, args: dict) -> dict:
        """
        Get observation by ID.

        Calls Claude-mem API: GET /api/observation/:id
        """
        obs_id = args["id"]

        try:
            response = await self.http_client.get(
                f"{self.api_url}/api/observation/{obs_id}"
            )
            response.raise_for_status()
            result = response.json()

            return {
                "status": "success",
                "tool": "mem_get_observation",
                "id": obs_id,
                "observation": result,
            }

        except httpx.HTTPError as e:
            self.logger.error(f"Claude-mem API error: {e}")
            raise RuntimeError(f"Claude-mem API error: {e}")

    async def _recent_context(self, args: dict) -> dict:
        """
        Get recent context.

        Calls Claude-mem API: GET /api/recent
        """
        limit = args.get("limit", 20)

        try:
            response = await self.http_client.get(
                f"{self.api_url}/api/recent",
                params={"limit": limit}
            )
            response.raise_for_status()
            result = response.json()

            return {
                "status": "success",
                "tool": "mem_recent_context",
                "limit": limit,
                "observations": result,
            }

        except httpx.HTTPError as e:
            self.logger.error(f"Claude-mem API error: {e}")
            raise RuntimeError(f"Claude-mem API error: {e}")

    async def _timeline(self, args: dict) -> dict:
        """
        Get timeline view.

        Calls Claude-mem API: GET /api/timeline
        """
        limit = args.get("limit", 50)
        start_date = args.get("start_date")
        end_date = args.get("end_date")

        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            response = await self.http_client.get(
                f"{self.api_url}/api/timeline",
                params=params
            )
            response.raise_for_status()
            result = response.json()

            return {
                "status": "success",
                "tool": "mem_timeline",
                "timeline": result,
            }

        except httpx.HTTPError as e:
            self.logger.error(f"Claude-mem API error: {e}")
            raise RuntimeError(f"Claude-mem API error: {e}")

    async def cleanup(self) -> None:
        """Cleanup HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
