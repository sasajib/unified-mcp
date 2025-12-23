#!/usr/bin/env python3
"""
Unified Dynamic MCP Server
===========================

Main entry point for the unified MCP server with progressive discovery.

This server consolidates multiple capabilities (code understanding,
documentation, browser automation, memory, knowledge graph) into a
single MCP server with dramatic token reduction through progressive
discovery.

Usage:
    python server.py

Configuration:
    Edit config/catalog.yaml to enable/disable capabilities
"""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server

from core import DynamicToolRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("unified-dynamic-mcp")

# Initialize registry
CATALOG_PATH = Path(__file__).parent / "config" / "catalog.yaml"
registry = DynamicToolRegistry(CATALOG_PATH)

logger.info(f"Unified MCP Server initialized with {len(registry.capabilities)} capabilities")


# ============================================================================
# PROGRESSIVE DISCOVERY TOOLS (Core Interface)
# ============================================================================


@app.call_tool()
async def search_tools(query: str, max_results: int = 10) -> dict:
    """
    Step 1: Search for relevant tools (minimal preview).

    Token cost: ~50 tokens for 10 tools

    Args:
        query: Natural language search query (e.g., "code search")
        max_results: Maximum number of results to return

    Returns:
        {
            'matches': [
                {
                    'name': 'search_code',
                    'capability': 'code_understanding',
                    'description': 'Search codebase semantically',
                    'tokens_estimate': 200
                },
                ...
            ],
            'next_step': 'Call describe_tools([names]) to get full schemas'
        }

    Example:
        search_tools("authentication") → List of auth-related tools
    """
    logger.info(f"search_tools called with query: '{query}'")

    try:
        results = await registry.search_tools(query, max_results)
        return {
            "matches": results,
            "count": len(results),
            "next_step": "Call describe_tools([names]) to get full schemas",
        }
    except Exception as e:
        logger.error(f"search_tools failed: {e}")
        return {"error": str(e), "matches": []}


@app.call_tool()
async def describe_tools(tool_names: list) -> dict:
    """
    Step 2: Get full schemas for specific tools.

    Token cost: ~200 tokens per tool

    Args:
        tool_names: List of tool names to describe

    Returns:
        {
            'tools': [
                {
                    'name': 'search_code',
                    'description': '...',
                    'input_schema': {...},
                    'examples': [...]
                },
                ...
            ],
            'next_step': 'Call execute_tool(name, args) to run'
        }

    Example:
        describe_tools(["search_code", "get_call_graph"])
    """
    logger.info(f"describe_tools called for: {tool_names}")

    try:
        schemas = await registry.describe_tools(tool_names)
        return {
            "tools": schemas,
            "count": len(schemas),
            "next_step": "Call execute_tool(name, args) to run a tool",
        }
    except Exception as e:
        logger.error(f"describe_tools failed: {e}")
        return {"error": str(e), "tools": []}


@app.call_tool()
async def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    Step 3: Execute a tool.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as dict

    Returns:
        Tool execution result

    Example:
        execute_tool("search_code", {"query": "auth", "language": "python"})
    """
    logger.info(f"execute_tool called: {tool_name}")

    try:
        result = await registry.execute_tool(tool_name, arguments)
        return result
    except ValueError as e:
        logger.error(f"Tool not found: {e}")
        return {"error": f"Tool not found: {tool_name}"}
    except Exception as e:
        logger.error(f"execute_tool failed: {e}")
        return {"error": str(e)}


# ============================================================================
# CAPABILITY MANAGEMENT TOOLS (Runtime Control)
# ============================================================================


@app.call_tool()
async def list_capabilities() -> dict:
    """
    List all available capabilities and their status.

    Returns:
        {
            'capabilities': [
                {
                    'name': 'code_understanding',
                    'enabled': True,
                    'type': 'codanna',
                    'tools': ['search_code', 'get_call_graph', ...],
                    'description': '...',
                    'loaded': False
                },
                ...
            ]
        }

    Example:
        list_capabilities() → See all available capabilities
    """
    logger.info("list_capabilities called")

    try:
        capabilities = await registry.get_all_capabilities()
        return {"capabilities": capabilities, "count": len(capabilities)}
    except Exception as e:
        logger.error(f"list_capabilities failed: {e}")
        return {"error": str(e), "capabilities": []}


@app.call_tool()
async def enable_capability(capability_name: str) -> dict:
    """
    Dynamically enable a capability at runtime.

    Args:
        capability_name: Name of capability to enable

    Returns:
        {'status': 'Capability enabled'}

    Example:
        enable_capability("browser_automation")
    """
    logger.info(f"enable_capability called: {capability_name}")

    try:
        result = await registry.enable_capability(capability_name)
        return result
    except Exception as e:
        logger.error(f"enable_capability failed: {e}")
        return {"error": str(e)}


@app.call_tool()
async def disable_capability(capability_name: str) -> dict:
    """
    Dynamically disable a capability at runtime.

    Unloads the capability to free resources.

    Args:
        capability_name: Name of capability to disable

    Returns:
        {'status': 'Capability disabled'}

    Example:
        disable_capability("browser_automation")
    """
    logger.info(f"disable_capability called: {capability_name}")

    try:
        result = await registry.disable_capability(capability_name)
        return result
    except Exception as e:
        logger.error(f"disable_capability failed: {e}")
        return {"error": str(e)}


@app.call_tool()
async def get_server_info() -> dict:
    """
    Get information about the unified MCP server.

    Returns:
        {
            'name': 'unified-dynamic-mcp',
            'version': '1.0.0',
            'capabilities_count': 5,
            'enabled_capabilities': ['code_understanding', ...],
            'discovery_mode': 'progressive',
            'token_estimate': {...}
        }

    Example:
        get_server_info() → Server metadata and stats
    """
    logger.info("get_server_info called")

    try:
        enabled = await registry.get_enabled_capabilities()
        discovery_config = registry.get_discovery_config()

        return {
            "name": "unified-dynamic-mcp",
            "version": "1.0.0",
            "capabilities_count": len(registry.capabilities),
            "enabled_capabilities": enabled,
            "discovery_mode": discovery_config.get("mode", "progressive"),
            "max_tools_in_context": discovery_config.get("max_tools_in_context", 10),
        }
    except Exception as e:
        logger.error(f"get_server_info failed: {e}")
        return {"error": str(e)}


# ============================================================================
# SERVER LIFECYCLE
# ============================================================================


async def main():
    """Main server entry point."""
    logger.info("=" * 60)
    logger.info("Unified Dynamic MCP Server")
    logger.info("=" * 60)
    logger.info(f"Catalog: {CATALOG_PATH}")
    logger.info(f"Capabilities: {len(registry.capabilities)}")
    logger.info("Starting server...")

    try:
        # Run MCP server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server running on stdio")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
