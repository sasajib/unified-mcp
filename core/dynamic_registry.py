"""
Dynamic Tool Registry
=====================

Core registry for managing MCP tool capabilities with lazy loading.

Based on Docker MCP Gateway pattern with dynamic tool discovery.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ToolCapability:
    """
    Represents a loadable tool capability module.

    A capability is a collection of related tools provided by an external
    service or library (e.g., Codanna for code understanding).

    Attributes:
        name: Capability identifier (e.g., "code_understanding")
        enabled: Whether this capability is active
        type: Capability type (e.g., "codanna", "context7")
        source: Path to capability source (git submodule or module)
        tools: List of tool names provided by this capability
        lazy_load: Whether to delay loading until first use
        description: Human-readable capability description
        api_url: Optional API URL for HTTP-based capabilities
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.enabled = config.get("enabled", False)
        self.type = config["type"]
        self.source = Path(config["source"])
        self.tools = config.get("tools", [])
        self.lazy_load = config.get("lazy_load", True)
        self.description = config.get("description", "")
        self.api_url = config.get("api_url")

        # Internal state
        self._loaded = False
        self._handler: Optional[Any] = None

    async def load(self) -> Any:
        """
        Lazy load the capability handler.

        Returns:
            The loaded capability handler instance.

        Raises:
            ImportError: If handler module cannot be imported.
            RuntimeError: If handler initialization fails.
        """
        if self._loaded and self._handler:
            return self._handler

        logger.info(f"Loading capability: {self.name} (type: {self.type})")

        try:
            # Build config dict for handler
            config = {
                "name": self.name,
                "type": self.type,
                "source": str(self.source),
                "enabled": self.enabled,
                "tools": self.tools,
                "description": self.description,
            }

            # Add api_url if present
            if self.api_url:
                config["api_url"] = self.api_url

            # Import handler based on type
            if self.type == "codanna":
                from handlers.code_understanding import CodannaHandler

                self._handler = CodannaHandler(config)
            elif self.type == "context7":
                from handlers.documentation import Context7Handler

                self._handler = Context7Handler(config)
            elif self.type == "playwright":
                from handlers.browser_automation import PlaywrightHandler

                self._handler = PlaywrightHandler(config)
            elif self.type == "claude-mem":
                from handlers.memory_search import ClaudeMemHandler

                self._handler = ClaudeMemHandler(config)
            elif self.type == "graphiti_ladybug":
                from handlers.knowledge_graph import GraphitiHandler

                self._handler = GraphitiHandler(config)
            else:
                raise ValueError(f"Unknown capability type: {self.type}")

            # Initialize handler
            await self._handler.initialize()
            self._loaded = True

            logger.info(f"Capability loaded successfully: {self.name}")
            return self._handler

        except ImportError as e:
            logger.error(f"Failed to import handler for {self.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            raise RuntimeError(f"Handler initialization failed: {e}") from e

    def unload(self) -> None:
        """
        Unload capability to free resources.

        Useful for disabling capabilities at runtime or cleaning up.
        """
        logger.info(f"Unloading capability: {self.name}")
        self._loaded = False
        self._handler = None

    def is_loaded(self) -> bool:
        """Check if capability is currently loaded."""
        return self._loaded

    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "unloaded"
        return f"<ToolCapability {self.name} ({status})>"


class DynamicToolRegistry:
    """
    Dynamic tool registry with progressive discovery.

    Manages all MCP tool capabilities and provides the 3-step progressive
    discovery interface:
    1. search_tools() - Minimal preview (50 tokens)
    2. describe_tools() - Full schemas (200 tokens per tool)
    3. execute_tool() - Run the tool

    This architecture achieves 96-160x token reduction compared to static
    tool loading by only exposing tools when needed.
    """

    def __init__(self, catalog_path: Path):
        """
        Initialize registry from catalog configuration.

        Args:
            catalog_path: Path to catalog.yaml file

        Raises:
            FileNotFoundError: If catalog file doesn't exist
            yaml.YAMLError: If catalog file is invalid
        """
        self.catalog_path = catalog_path
        self.capabilities: Dict[str, ToolCapability] = {}
        self.config: Dict[str, Any] = {}

        self._load_catalog()
        logger.info(f"Registry initialized with {len(self.capabilities)} capabilities")

    def _load_catalog(self) -> None:
        """Load capability catalog from YAML file."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")

        with open(self.catalog_path) as f:
            self.config = yaml.safe_load(f)

        # Create ToolCapability instances
        for name, cfg in self.config.get("capabilities", {}).items():
            self.capabilities[name] = ToolCapability(name, cfg)

        logger.debug(f"Loaded {len(self.capabilities)} capabilities from catalog")

    async def search_tools(self, query: str, max_results: int = 10) -> List[dict]:
        """
        Step 1: Progressive Discovery - Search for relevant tools.

        Returns minimal preview (name + 1-line description) matching the query.

        Args:
            query: Natural language search query
            max_results: Maximum number of results to return

        Returns:
            List of tool previews with estimated token costs

        Example:
            >>> results = await registry.search_tools("code search")
            >>> results[0]
            {
                'name': 'search_code',
                'capability': 'code_understanding',
                'description': 'Search codebase semantically',
                'tokens_estimate': 200
            }
        """
        logger.debug(f"Searching tools with query: '{query}'")
        matching_tools = []

        # Search across all enabled capabilities
        for cap_name, capability in self.capabilities.items():
            if not capability.enabled:
                continue

            # Simple keyword matching (can be enhanced with semantic search)
            query_lower = query.lower()

            for tool_name in capability.tools:
                # Match tool name or capability description
                if (
                    query_lower in tool_name.lower()
                    or query_lower in capability.description.lower()
                ):
                    matching_tools.append(
                        {
                            "name": tool_name,
                            "capability": cap_name,
                            "description": self._get_short_description(tool_name),
                            "tokens_estimate": 200,  # Estimated cost for full schema
                        }
                    )

        # Limit results
        results = matching_tools[:max_results]
        logger.info(f"Found {len(results)} matching tools")
        return results

    async def describe_tools(self, tool_names: List[str]) -> List[dict]:
        """
        Step 2: Progressive Discovery - Get full schemas for specific tools.

        Lazy loads capabilities as needed and returns complete tool definitions.

        Args:
            tool_names: List of tool names to describe

        Returns:
            List of complete tool schemas with input/output definitions

        Example:
            >>> schemas = await registry.describe_tools(["search_code"])
            >>> schemas[0]["input_schema"]["properties"]
            {'query': {'type': 'string', 'description': 'Search query'}, ...}
        """
        logger.debug(f"Describing tools: {tool_names}")
        descriptions = []

        for tool_name in tool_names:
            capability = self._find_capability_for_tool(tool_name)
            if not capability:
                logger.warning(f"Tool '{tool_name}' not found in any capability")
                continue

            # Lazy load capability if needed
            try:
                handler = await capability.load()
                schema = await handler.get_tool_schema(tool_name)
                descriptions.append(schema)
            except Exception as e:
                logger.error(f"Failed to get schema for {tool_name}: {e}")
                descriptions.append(
                    {
                        "name": tool_name,
                        "error": str(e),
                    }
                )

        logger.info(f"Described {len(descriptions)} tools")
        return descriptions

    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Step 3: Progressive Discovery - Execute a tool.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails

        Example:
            >>> result = await registry.execute_tool(
            ...     "search_code",
            ...     {"query": "authentication"}
            ... )
        """
        logger.info(f"Executing tool: {tool_name}")

        capability = self._find_capability_for_tool(tool_name)
        if not capability:
            raise ValueError(f"Tool '{tool_name}' not found in any capability")

        # Lazy load capability
        handler = await capability.load()

        # Execute tool
        try:
            result = await handler.execute(tool_name, arguments)
            logger.debug(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            raise

    def _find_capability_for_tool(self, tool_name: str) -> Optional[ToolCapability]:
        """Find which capability provides a given tool."""
        for capability in self.capabilities.values():
            if tool_name in capability.tools:
                return capability
        return None

    def _get_short_description(self, tool_name: str) -> str:
        """
        Get 1-line description for tool (for search results).

        This is used in progressive discovery Step 1 to provide minimal
        context about each tool without loading the full schema.
        """
        descriptions = {
            # Code understanding (Codanna)
            "search_code": "Search codebase semantically",
            "get_call_graph": "Get function call relationships",
            "find_symbol": "Find symbol definition (sub-10ms)",
            "find_implementations": "Find implementations of interface/class",
            # Documentation (Context7)
            "resolve_library_id": "Resolve library name to Context7 ID",
            "get_library_docs": "Fetch up-to-date library documentation",
            # Browser automation (Playwright)
            "playwright_navigate": "Navigate browser to URL",
            "playwright_screenshot": "Take screenshot of page",
            "playwright_click": "Click element on page",
            "playwright_fill": "Fill input field",
            "playwright_select": "Select dropdown option",
            "playwright_evaluate": "Execute JavaScript in browser",
            "playwright_get_text": "Get text content of element",
            "playwright_hover": "Hover over element",
            # Memory search (Claude-mem)
            "mem_search": "Search past session observations",
            "mem_get_observation": "Get specific observation by ID",
            "mem_recent_context": "Get recent session context",
            "mem_timeline": "Get timeline around observation",
            # Knowledge graph (Graphiti)
            "store_insight": "Store cross-session knowledge",
            "search_insights": "Search past insights & decisions",
            "query_graph": "Query knowledge graph with Cypher",
            "add_episode": "Add episode to knowledge graph",
        }
        return descriptions.get(tool_name, "No description available")

    async def enable_capability(self, name: str) -> dict:
        """
        Dynamically enable a capability at runtime.

        Args:
            name: Capability name

        Returns:
            Status message

        Example:
            >>> await registry.enable_capability("browser_automation")
        """
        if name not in self.capabilities:
            return {"error": f"Capability '{name}' not found"}

        self.capabilities[name].enabled = True
        logger.info(f"Enabled capability: {name}")
        return {"status": f"Capability '{name}' enabled"}

    async def disable_capability(self, name: str) -> dict:
        """
        Dynamically disable a capability at runtime.

        Unloads the capability to free resources.

        Args:
            name: Capability name

        Returns:
            Status message
        """
        if name not in self.capabilities:
            return {"error": f"Capability '{name}' not found"}

        self.capabilities[name].enabled = False
        self.capabilities[name].unload()
        logger.info(f"Disabled capability: {name}")
        return {"status": f"Capability '{name}' disabled"}

    async def get_enabled_capabilities(self) -> List[str]:
        """Get list of currently enabled capabilities."""
        return [name for name, cap in self.capabilities.items() if cap.enabled]

    async def get_all_capabilities(self) -> List[dict]:
        """
        Get information about all capabilities.

        Returns:
            List of capability info dicts with name, status, tools, etc.
        """
        return [
            {
                "name": cap.name,
                "enabled": cap.enabled,
                "type": cap.type,
                "tools": cap.tools,
                "description": cap.description,
                "loaded": cap.is_loaded(),
            }
            for cap in self.capabilities.values()
        ]

    def get_discovery_config(self) -> dict:
        """Get progressive discovery configuration from catalog."""
        return self.config.get("discovery", {})

    def reload_catalog(self) -> None:
        """Reload catalog from file (useful for config changes)."""
        logger.info("Reloading catalog...")
        self._load_catalog()
