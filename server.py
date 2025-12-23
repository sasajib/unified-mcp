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
import os
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from core import DynamicToolRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Log environment variables for Graphiti
logger.info("=== Environment Variables ===")
logger.info(f"GRAPHITI_ENABLED: {os.getenv('GRAPHITI_ENABLED', 'not set')}")
logger.info(f"GRAPHITI_LLM_PROVIDER: {os.getenv('GRAPHITI_LLM_PROVIDER', 'not set')}")
logger.info(f"GRAPHITI_EMBEDDER_PROVIDER: {os.getenv('GRAPHITI_EMBEDDER_PROVIDER', 'not set')}")
logger.info(f"GRAPHITI_LLM_MODEL: {os.getenv('GRAPHITI_LLM_MODEL', 'not set')}")
logger.info(f"GRAPHITI_EMBEDDER_MODEL: {os.getenv('GRAPHITI_EMBEDDER_MODEL', 'not set')}")
logger.info(f"GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
logger.info(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
logger.info("============================")

# Create MCP server
app = Server("unified-dynamic-mcp")

# Initialize registry
CATALOG_PATH = Path(__file__).parent / "config" / "catalog.yaml"
registry = DynamicToolRegistry(CATALOG_PATH)

logger.info(f"Unified MCP Server initialized with {len(registry.capabilities)} capabilities")


# ============================================================================
# MCP PROTOCOL HANDLERS
# ============================================================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools for MCP protocol."""
    logger.info("list_tools (MCP protocol) called")

    return [
        Tool(
            name="search_tools",
            description="Search for relevant tools using natural language query. Returns lightweight previews (~50 tokens for 10 tools).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'code search', 'authentication')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="describe_tools",
            description="Get full schemas for specific tools. Returns detailed schemas (~200 tokens per tool).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tool names to describe"
                    }
                },
                "required": ["tool_names"]
            }
        ),
        Tool(
            name="execute_tool",
            description="Execute a specific tool with given arguments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to execute"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool arguments as key-value pairs"
                    }
                },
                "required": ["tool_name", "arguments"]
            }
        ),
        Tool(
            name="list_capabilities",
            description="List all available capabilities and their status.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="enable_capability",
            description="Dynamically enable a capability at runtime.",
            inputSchema={
                "type": "object",
                "properties": {
                    "capability_name": {
                        "type": "string",
                        "description": "Name of capability to enable"
                    }
                },
                "required": ["capability_name"]
            }
        ),
        Tool(
            name="disable_capability",
            description="Dynamically disable a capability at runtime.",
            inputSchema={
                "type": "object",
                "properties": {
                    "capability_name": {
                        "type": "string",
                        "description": "Name of capability to disable"
                    }
                },
                "required": ["capability_name"]
            }
        ),
        Tool(
            name="get_server_info",
            description="Get information about the unified MCP server.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


# ============================================================================
# ============================================================================
# MCP TOOL CALL HANDLER (Routes to specific implementations)
# ============================================================================


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """Unified tool call handler - routes to specific implementations."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        # Route to the appropriate tool implementation
        if name == "search_tools":
            return await handle_search_tools(arguments)
        elif name == "describe_tools":
            return await handle_describe_tools(arguments)
        elif name == "execute_tool":
            return await handle_execute_tool(arguments)
        elif name == "list_capabilities":
            return await handle_list_capabilities(arguments)
        elif name == "enable_capability":
            return await handle_enable_capability(arguments)
        elif name == "disable_capability":
            return await handle_disable_capability(arguments)
        elif name == "get_server_info":
            return await handle_get_server_info(arguments)
        else:
            return [{"type": "text", "text": f"Error: Unknown tool '{name}'"}]
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return [{"type": "text", "text": f"Error: {str(e)}"}]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================


async def handle_search_tools(arguments: dict) -> list:
    """Search for relevant tools."""
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)
    
    logger.info(f"search_tools: query='{query}', max_results={max_results}")
    
    try:
        results = await registry.search_tools(query, max_results)
        
        if not results:
            return [{"type": "text", "text": f"No tools found matching '{query}'"}]
        
        text = f"Found {len(results)} matching tools:\n\n"
        for r in results:
            text += f"• **{r['name']}** ({r['capability']})\n"
            text += f"  {r['description']}\n"
            text += f"  Est. tokens: {r.get('tokens_estimate', 'N/A')}\n\n"
        
        text += "\nNext step: Use describe_tools([names]) to get full schemas"
        
        return [{"type": "text", "text": text}]
    except Exception as e:
        logger.error(f"search_tools failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_describe_tools(arguments: dict) -> list:
    """Get full schemas for specific tools."""
    tool_names = arguments.get("tool_names", [])
    
    logger.info(f"describe_tools: {tool_names}")
    
    try:
        schemas = await registry.describe_tools(tool_names)
        
        if not schemas:
            return [{"type": "text", "text": "No schemas found"}]
        
        text = f"Tool schemas ({len(schemas)} tools):\n\n"
        for schema in schemas:
            text += f"### {schema['name']}\n"
            text += f"{schema.get('description', 'No description')}\n\n"
            text += "**Input Schema:**\n```json\n"
            import json
            text += json.dumps(schema.get('input_schema', {}), indent=2)
            text += "\n```\n\n"
        
        text += "\nNext step: Use execute_tool(name, args) to run a tool"
        
        return [{"type": "text", "text": text}]
    except Exception as e:
        logger.error(f"describe_tools failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_execute_tool(arguments: dict) -> list:
    """Execute a specific tool."""
    tool_name = arguments.get("tool_name", "")
    tool_arguments = arguments.get("arguments", {})
    
    logger.info(f"execute_tool: {tool_name} with args {tool_arguments}")
    
    try:
        result = await registry.execute_tool(tool_name, tool_arguments)
        
        import json
        result_text = json.dumps(result, indent=2)
        
        return [{"type": "text", "text": f"Tool '{tool_name}' result:\n```json\n{result_text}\n```"}]
    except Exception as e:
        logger.error(f"execute_tool failed: {e}")
        return [{"type": "text", "text": f"Error executing '{tool_name}': {str(e)}"}]


async def handle_list_capabilities(arguments: dict) -> list:
    """List all available capabilities."""
    logger.info("list_capabilities called")
    
    try:
        capabilities = await registry.get_all_capabilities()
        
        text = f"Available capabilities ({len(capabilities)}):\n\n"
        for cap in capabilities:
            status = "✓ Enabled" if cap.get('enabled') else "✗ Disabled"
            text += f"• **{cap['name']}** [{status}]\n"
            text += f"  Type: {cap.get('type', 'unknown')}\n"
            text += f"  Tools: {', '.join(cap.get('tools', []))}\n"
            text += f"  {cap.get('description', '')}\n\n"
        
        return [{"type": "text", "text": text}]
    except Exception as e:
        logger.error(f"list_capabilities failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_enable_capability(arguments: dict) -> list:
    """Enable a capability."""
    capability_name = arguments.get("capability_name", "")
    
    logger.info(f"enable_capability: {capability_name}")
    
    try:
        result = await registry.enable_capability(capability_name)
        return [{"type": "text", "text": f"✓ Enabled capability '{capability_name}'"}]
    except Exception as e:
        logger.error(f"enable_capability failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_disable_capability(arguments: dict) -> list:
    """Disable a capability."""
    capability_name = arguments.get("capability_name", "")
    
    logger.info(f"disable_capability: {capability_name}")
    
    try:
        result = await registry.disable_capability(capability_name)
        return [{"type": "text", "text": f"✓ Disabled capability '{capability_name}'"}]
    except Exception as e:
        logger.error(f"disable_capability failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_get_server_info(arguments: dict) -> list:
    """Get server information."""
    logger.info("get_server_info called")
    
    try:
        enabled = await registry.get_enabled_capabilities()
        discovery_config = registry.get_discovery_config()
        
        info = {
            "name": "unified-dynamic-mcp",
            "version": "1.0.0",
            "capabilities_count": len(registry.capabilities),
            "enabled_capabilities": enabled,
            "discovery_mode": discovery_config.get("mode", "progressive"),
            "max_tools_in_context": discovery_config.get("max_tools_in_context", 10),
        }
        
        import json
        text = "Unified MCP Server Info:\n```json\n"
        text += json.dumps(info, indent=2)
        text += "\n```"
        
        return [{"type": "text", "text": text}]
    except Exception as e:
        logger.error(f"get_server_info failed: {e}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]



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
