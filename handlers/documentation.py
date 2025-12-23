"""
Context7 Handler
================

Documentation retrieval via Context7 MCP server integration.

Maps unified-mcp tools to Context7's MCP tools:
- resolve_library_id → resolve-library-id (find library by name)
- get_library_docs → get-library-docs (fetch documentation)
"""

import asyncio
import json
import shutil
from typing import Any, Optional

from core.capability_loader import CapabilityHandler


class Context7Handler(CapabilityHandler):
    """Handler for Context7 documentation tools."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.npx_path: Optional[str] = None
        self.context7_package = "@upstash/context7-mcp"

    async def initialize(self) -> None:
        """Initialize Context7 - verify Node.js and npx installation."""
        # Check if npx is installed
        self.npx_path = shutil.which("npx")
        if not self.npx_path:
            raise RuntimeError(
                "npx not found. Install Node.js 18+ from https://nodejs.org/"
            )

        self.logger.info(f"npx found at: {self.npx_path}")
        self.logger.info("Context7 will be installed on first use via npx")

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "resolve_library_id": {
                "name": "resolve_library_id",
                "description": (
                    "Resolve a general library name into a Context7-compatible library ID. "
                    "Returns matching libraries with details to help select the right one."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "libraryName": {
                            "type": "string",
                            "description": (
                                "Library name to search for "
                                "(e.g., 'react', 'next.js', 'supabase')"
                            ),
                        }
                    },
                    "required": ["libraryName"],
                },
            },
            "get_library_docs": {
                "name": "get_library_docs",
                "description": (
                    "Fetch up-to-date documentation for a library using "
                    "Context7-compatible library ID. Returns version-specific "
                    "code examples and API documentation."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "context7CompatibleLibraryID": {
                            "type": "string",
                            "description": (
                                "Exact Context7-compatible library ID "
                                "(e.g., '/mongodb/docs', '/vercel/next.js', "
                                "'/supabase/supabase'). Use resolve_library_id "
                                "first to find this ID."
                            ),
                        },
                        "topic": {
                            "type": "string",
                            "description": (
                                "Optional topic to focus docs on "
                                "(e.g., 'routing', 'hooks', 'authentication')"
                            ),
                        },
                        "page": {
                            "type": "integer",
                            "description": (
                                "Page number for pagination (1-10). If context is not sufficient, "
                                "try page=2, page=3, etc. with the same topic. Default: 1"
                            ),
                            "default": 1,
                            "minimum": 1,
                            "maximum": 10,
                        },
                    },
                    "required": ["context7CompatibleLibraryID"],
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a Context7 tool."""
        if tool_name == "resolve_library_id":
            return await self._resolve_library_id(arguments)
        elif tool_name == "get_library_docs":
            return await self._get_library_docs(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _resolve_library_id(self, args: dict) -> dict:
        """
        Resolve library name to Context7 ID.

        Uses Context7 MCP tool: resolve-library-id
        """
        library_name = args["libraryName"]

        # Call Context7 MCP server via npx
        result = await self._call_context7_mcp(
            "resolve-library-id", {"libraryName": library_name}
        )

        return {
            "status": "success",
            "tool": "resolve_library_id",
            "libraryName": library_name,
            "results": result,
        }

    async def _get_library_docs(self, args: dict) -> dict:
        """
        Get library documentation.

        Uses Context7 MCP tool: get-library-docs
        """
        library_id = args["context7CompatibleLibraryID"]
        topic = args.get("topic")
        page = args.get("page", 1)

        # Build parameters for Context7 MCP
        params = {"context7CompatibleLibraryID": library_id}
        if topic:
            params["topic"] = topic
        if page != 1:
            params["page"] = page

        result = await self._call_context7_mcp("get-library-docs", params)

        return {
            "status": "success",
            "tool": "get_library_docs",
            "libraryID": library_id,
            "topic": topic,
            "page": page,
            "results": result,
        }

    async def _call_context7_mcp(self, tool_name: str, params: dict) -> Any:
        """
        Call Context7 MCP server tool via npx.

        Args:
            tool_name: MCP tool name
            params: Tool parameters

        Returns:
            Tool result from Context7 MCP server

        Raises:
            RuntimeError: If Context7 MCP call fails
        """
        try:
            self.logger.debug(f"Calling Context7 MCP: {tool_name} with {params}")

            # Start Context7 MCP server process
            process = await asyncio.create_subprocess_exec(
                self.npx_path,
                "-y",
                self.context7_package,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Step 1: Send MCP initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "unified-mcp", "version": "1.0.0"},
                },
            }

            init_json = json.dumps(initialize_request) + "\n"
            process.stdin.write(init_json.encode())
            await process.stdin.drain()

            # Step 2: Read initialize response
            init_response_line = await process.stdout.readline()
            init_response = json.loads(init_response_line.decode().strip())

            if "error" in init_response:
                raise RuntimeError(
                    f"Context7 MCP initialization error: {init_response['error']}"
                )

            self.logger.debug("Context7 MCP initialized successfully")

            # Step 3: Send tools/call request
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params},
            }

            tool_json = json.dumps(tool_request) + "\n"
            process.stdin.write(tool_json.encode())
            await process.stdin.drain()

            # Step 4: Read tools/call response
            tool_response_line = await process.stdout.readline()

            if not tool_response_line:
                # Try to get any stderr output for debugging
                stderr_output = ""
                try:
                    stderr_data = await asyncio.wait_for(
                        process.stderr.read(), timeout=1.0
                    )
                    stderr_output = stderr_data.decode("utf-8").strip()
                except asyncio.TimeoutError:
                    pass

                raise RuntimeError(
                    f"No response from Context7 MCP for tool '{tool_name}'. "
                    f"Stderr: {stderr_output if stderr_output else 'none'}"
                )

            tool_response = json.loads(tool_response_line.decode().strip())

            # Close the process
            process.stdin.close()
            await process.wait()

            # Parse response
            if "error" in tool_response:
                raise RuntimeError(f"Context7 MCP error: {tool_response['error']}")

            return tool_response.get("result", {})

        except FileNotFoundError:
            raise RuntimeError(
                f"npx executable not found at {self.npx_path}. "
                "Install Node.js 18+ from https://nodejs.org/"
            )
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON from Context7 MCP")
            raise RuntimeError(f"Invalid JSON from Context7 MCP: {e}")
        except Exception as e:
            self.logger.error(f"Error calling Context7 MCP: {e}")
            # Clean up process if it's still running
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            raise
