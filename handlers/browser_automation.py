"""
Playwright Handler
==================

Browser automation via Playwright MCP server integration.

Maps unified-mcp tools to Playwright's MCP tools:
- playwright_navigate → browser_navigate
- playwright_click → browser_click
- playwright_screenshot → browser_take_screenshot
- playwright_fill → browser_type
- playwright_evaluate → browser_evaluate
"""

import asyncio
import json
import shutil
from typing import Any, Optional

from core.capability_loader import CapabilityHandler


class PlaywrightHandler(CapabilityHandler):
    """Handler for Playwright browser automation tools."""

    def __init__(self, config: dict):
        """Initialize handler with config."""
        super().__init__(config)
        self.npx_path: Optional[str] = None
        self.playwright_package = "@playwright/mcp@latest"
        self.mcp_process: Optional[asyncio.subprocess.Process] = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize Playwright - verify Node.js and npx installation."""
        # Check if npx is installed
        self.npx_path = shutil.which("npx")
        if not self.npx_path:
            raise RuntimeError(
                "npx not found. Install Node.js 18+ from https://nodejs.org/"
            )

        self.logger.info(f"npx found at: {self.npx_path}")
        self.logger.info("Playwright MCP will be installed on first use via npx")
        self.initialized = True

    async def get_tool_schema(self, tool_name: str) -> dict:
        """Get JSON schema for a tool."""
        schemas = {
            "playwright_navigate": {
                "name": "playwright_navigate",
                "description": "Navigate to a URL in the browser",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to",
                        }
                    },
                    "required": ["url"],
                },
            },
            "playwright_click": {
                "name": "playwright_click",
                "description": "Click an element on the web page",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "string",
                            "description": "Human-readable element description",
                        },
                        "ref": {
                            "type": "string",
                            "description": "Exact target element reference from page snapshot",
                        },
                        "doubleClick": {
                            "type": "boolean",
                            "description": "Whether to perform a double click",
                        },
                    },
                    "required": ["element", "ref"],
                },
            },
            "playwright_screenshot": {
                "name": "playwright_screenshot",
                "description": "Take a screenshot of the current page or element",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": (
                                "File name to save screenshot "
                                "(defaults to page-{timestamp}.png)"
                            ),
                        },
                        "type": {
                            "type": "string",
                            "description": "Image format: png or jpeg (default: png)",
                            "enum": ["png", "jpeg"],
                        },
                        "fullPage": {
                            "type": "boolean",
                            "description": "Take screenshot of full scrollable page",
                        },
                    },
                },
            },
            "playwright_fill": {
                "name": "playwright_fill",
                "description": "Fill text into an input field",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "string",
                            "description": "Human-readable element description",
                        },
                        "ref": {
                            "type": "string",
                            "description": "Exact target element reference from page snapshot",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type into the element",
                        },
                        "submit": {
                            "type": "boolean",
                            "description": "Whether to press Enter after typing",
                        },
                    },
                    "required": ["element", "ref", "text"],
                },
            },
            "playwright_evaluate": {
                "name": "playwright_evaluate",
                "description": "Evaluate JavaScript expression on page or element",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "function": {
                            "type": "string",
                            "description": "JavaScript function to execute: () => { /* code */ }",
                        },
                        "element": {
                            "type": "string",
                            "description": "Optional human-readable element description",
                        },
                        "ref": {
                            "type": "string",
                            "description": "Optional exact element reference",
                        },
                    },
                    "required": ["function"],
                },
            },
        }

        if tool_name not in schemas:
            raise ValueError(f"Unknown tool: {tool_name}")

        return schemas[tool_name]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a Playwright tool."""
        if tool_name == "playwright_navigate":
            return await self._navigate(arguments)
        elif tool_name == "playwright_click":
            return await self._click(arguments)
        elif tool_name == "playwright_screenshot":
            return await self._screenshot(arguments)
        elif tool_name == "playwright_fill":
            return await self._fill(arguments)
        elif tool_name == "playwright_evaluate":
            return await self._evaluate(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _navigate(self, args: dict) -> dict:
        """Navigate to URL using browser_navigate."""
        url = args["url"]
        result = await self._call_playwright_mcp("browser_navigate", {"url": url})

        return {
            "status": "success",
            "tool": "playwright_navigate",
            "url": url,
            "result": result,
        }

    async def _click(self, args: dict) -> dict:
        """Click element using browser_click."""
        result = await self._call_playwright_mcp("browser_click", args)

        return {
            "status": "success",
            "tool": "playwright_click",
            "element": args["element"],
            "result": result,
        }

    async def _screenshot(self, args: dict) -> dict:
        """Take screenshot using browser_take_screenshot."""
        result = await self._call_playwright_mcp("browser_take_screenshot", args)

        return {
            "status": "success",
            "tool": "playwright_screenshot",
            "filename": args.get("filename", "page-{timestamp}.png"),
            "result": result,
        }

    async def _fill(self, args: dict) -> dict:
        """Fill input field using browser_type."""
        result = await self._call_playwright_mcp("browser_type", args)

        return {
            "status": "success",
            "tool": "playwright_fill",
            "element": args["element"],
            "text": args["text"],
            "result": result,
        }

    async def _evaluate(self, args: dict) -> dict:
        """Evaluate JavaScript using browser_evaluate."""
        result = await self._call_playwright_mcp("browser_evaluate", args)

        return {
            "status": "success",
            "tool": "playwright_evaluate",
            "result": result,
        }

    async def _call_playwright_mcp(self, tool_name: str, params: dict) -> Any:
        """
        Call Playwright MCP server tool via npx.

        Args:
            tool_name: MCP tool name
            params: Tool parameters

        Returns:
            Tool result from Playwright MCP server

        Raises:
            RuntimeError: If Playwright MCP call fails
        """
        try:
            self.logger.debug(f"Calling Playwright MCP: {tool_name} with {params}")

            # Start Playwright MCP server process
            process = await asyncio.create_subprocess_exec(
                self.npx_path,
                "-y",
                self.playwright_package,
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
                    f"Playwright MCP initialization error: {init_response['error']}"
                )

            self.logger.debug("Playwright MCP initialized successfully")

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
                    f"No response from Playwright MCP for tool '{tool_name}'. "
                    f"Stderr: {stderr_output if stderr_output else 'none'}"
                )

            tool_response = json.loads(tool_response_line.decode().strip())

            # Close the process
            process.stdin.close()
            await process.wait()

            # Parse response
            if "error" in tool_response:
                raise RuntimeError(f"Playwright MCP error: {tool_response['error']}")

            return tool_response.get("result", {})

        except FileNotFoundError:
            raise RuntimeError(
                f"npx executable not found at {self.npx_path}. "
                "Install Node.js 18+ from https://nodejs.org/"
            )
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON from Playwright MCP")
            raise RuntimeError(f"Invalid JSON from Playwright MCP: {e}")
        except Exception as e:
            self.logger.error(f"Error calling Playwright MCP: {e}")
            # Clean up process if it's still running
            if process and process.returncode is None:
                process.kill()
                await process.wait()
            raise

    async def cleanup(self) -> None:
        """Cleanup Playwright MCP process if running."""
        if self.mcp_process and self.mcp_process.returncode is None:
            self.logger.info("Terminating Playwright MCP process")
            self.mcp_process.terminate()
            try:
                await asyncio.wait_for(self.mcp_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Playwright MCP process did not terminate, killing")
                self.mcp_process.kill()
