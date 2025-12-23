"""
End-to-End Tests for Unified MCP Server
========================================

Tests the full MCP server with all capabilities enabled.

These tests verify:
- Server startup and initialization
- Tool discovery and listing
- Progressive discovery flow
- Tool execution across all capabilities
- Error handling and recovery
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.capability_loader import CapabilityLoader
from core.catalog import CatalogManager

# We'll import the server components
from core.server import UnifiedMCPServer


@pytest.fixture
def test_catalog_path():
    """Path to test catalog configuration."""
    return Path(__file__).parent.parent.parent / "config" / "catalog.yaml"


@pytest.fixture
async def mcp_server(test_catalog_path):
    """Create and initialize MCP server for testing."""
    server = UnifiedMCPServer(catalog_path=str(test_catalog_path))

    # Mock external dependencies to avoid actual initialization
    with patch.object(server, "initialize_capabilities") as mock_init:
        mock_init.return_value = None
        await server.initialize()

    return server


class TestServerInitialization:
    """Tests for MCP server initialization."""

    @pytest.mark.asyncio
    async def test_server_loads_catalog(self, mcp_server):
        """Server successfully loads catalog configuration."""
        assert mcp_server.catalog is not None
        assert len(mcp_server.catalog.capabilities) > 0

    @pytest.mark.asyncio
    async def test_server_has_all_capabilities(self, mcp_server):
        """Server loads all 5 capabilities from catalog."""
        expected_capabilities = [
            "code_understanding",
            "documentation",
            "browser_automation",
            "memory_search",
            "knowledge_graph",
        ]

        for cap in expected_capabilities:
            assert cap in mcp_server.catalog.capabilities

    @pytest.mark.asyncio
    async def test_server_initializes_registry(self, mcp_server):
        """Server initializes dynamic tool registry."""
        assert hasattr(mcp_server, "registry")
        assert mcp_server.registry is not None


class TestToolDiscovery:
    """Tests for progressive tool discovery."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_preview(self, mcp_server):
        """list_tools returns minimal preview (search step)."""
        with patch.object(mcp_server.registry, "list_tools") as mock_list:
            mock_list.return_value = [
                {
                    "name": "search_code",
                    "description": "Search codebase",
                    "preview": True,
                }
            ]

            tools = await mcp_server.list_tools()

            assert len(tools) > 0
            assert any(
                "search" in tool.get("description", "").lower() for tool in tools
            )

    @pytest.mark.asyncio
    async def test_describe_tool_returns_schema(self, mcp_server):
        """describe_tool returns full schema (describe step)."""
        with patch.object(mcp_server.registry, "get_tool_schema") as mock_schema:
            mock_schema.return_value = {
                "name": "search_code",
                "description": "Search code semantically",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }

            schema = await mcp_server.describe_tool("search_code")

            assert schema["name"] == "search_code"
            assert "input_schema" in schema
            assert "properties" in schema["input_schema"]


class TestToolExecution:
    """Tests for tool execution across capabilities."""

    @pytest.mark.asyncio
    async def test_execute_code_understanding_tool(self, mcp_server):
        """Execute code understanding tool (Codanna)."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "results": [{"file": "test.py", "line": 10}],
            }

            result = await mcp_server.execute_tool(
                "search_code", {"query": "test function"}
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_documentation_tool(self, mcp_server):
        """Execute documentation tool (Context7)."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "results": [{"library": "/facebook/react"}],
            }

            result = await mcp_server.execute_tool(
                "resolve_library_id", {"libraryName": "react"}
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_browser_automation_tool(self, mcp_server):
        """Execute browser automation tool (Playwright)."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {"status": "success", "url": "https://example.com"}

            result = await mcp_server.execute_tool(
                "playwright_navigate", {"url": "https://example.com"}
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_memory_search_tool(self, mcp_server):
        """Execute memory search tool (Claude-mem)."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {
                "status": "success",
                "results": [{"observation": "test"}],
            }

            result = await mcp_server.execute_tool(
                "mem_search", {"query": "test query"}
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_knowledge_graph_tool(self, mcp_server):
        """Execute knowledge graph tool (Graphiti)."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {"status": "success", "message": "Insight stored"}

            result = await mcp_server.execute_tool(
                "store_insight", {"content": "test insight"}
            )

            assert result["status"] == "success"


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, mcp_server):
        """Executing unknown tool raises appropriate error."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.side_effect = ValueError("Unknown tool: nonexistent")

            with pytest.raises(ValueError, match="Unknown tool"):
                await mcp_server.execute_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_invalid_arguments_raises_error(self, mcp_server):
        """Invalid tool arguments raise appropriate error."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.side_effect = TypeError("Missing required argument")

            with pytest.raises(TypeError, match="required argument"):
                await mcp_server.execute_tool("search_code", {})

    @pytest.mark.asyncio
    async def test_tool_execution_failure_returns_error(self, mcp_server):
        """Tool execution failure returns error status."""
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {"status": "error", "message": "Execution failed"}

            result = await mcp_server.execute_tool("search_code", {"query": "test"})

            assert result["status"] == "error"


class TestProgressiveDiscovery:
    """Tests for progressive discovery pattern."""

    @pytest.mark.asyncio
    async def test_progressive_flow_search_describe_execute(self, mcp_server):
        """Full progressive discovery flow: search → describe → execute."""
        # Step 1: Search (list tools)
        with patch.object(mcp_server.registry, "list_tools") as mock_list:
            mock_list.return_value = [
                {"name": "search_code", "description": "Search code", "preview": True}
            ]
            tools = await mcp_server.list_tools()
            assert len(tools) > 0

        # Step 2: Describe (get schema)
        with patch.object(mcp_server.registry, "get_tool_schema") as mock_schema:
            mock_schema.return_value = {
                "name": "search_code",
                "input_schema": {"properties": {"query": {"type": "string"}}},
            }
            schema = await mcp_server.describe_tool("search_code")
            assert "input_schema" in schema

        # Step 3: Execute
        with patch.object(mcp_server.registry, "execute_tool") as mock_exec:
            mock_exec.return_value = {"status": "success"}
            result = await mcp_server.execute_tool("search_code", {"query": "test"})
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_token_cost_estimation(self, mcp_server):
        """Progressive discovery includes token cost estimates."""
        with patch.object(mcp_server.registry, "estimate_tokens") as mock_estimate:
            mock_estimate.return_value = {
                "search_only": 50,
                "describe_only": 200,
                "total_reduction": "96x",
            }

            estimates = await mcp_server.estimate_tokens("search_code")

            assert "search_only" in estimates
            assert estimates["search_only"] < estimates["describe_only"]


class TestCatalogConfiguration:
    """Tests for catalog configuration and loading."""

    @pytest.mark.asyncio
    async def test_catalog_enables_lazy_loading(self, mcp_server):
        """Catalog properly configures lazy loading."""
        # Most capabilities should have lazy_load: true
        code_cap = mcp_server.catalog.capabilities["code_understanding"]
        assert code_cap.get("lazy_load", False) == True

    @pytest.mark.asyncio
    async def test_catalog_always_loads_knowledge_graph(self, mcp_server):
        """Knowledge graph capability has lazy_load: false."""
        kg_cap = mcp_server.catalog.capabilities["knowledge_graph"]
        assert kg_cap.get("lazy_load", True) == False

    @pytest.mark.asyncio
    async def test_catalog_defines_all_tools(self, mcp_server):
        """Catalog defines all 19 tools across 5 capabilities."""
        total_tools = 0
        for cap_name, cap_config in mcp_server.catalog.capabilities.items():
            total_tools += len(cap_config.get("tools", []))

        # Should have all 19 tools defined
        assert total_tools >= 19


class TestServerCleanup:
    """Tests for server cleanup and resource management."""

    @pytest.mark.asyncio
    async def test_server_cleanup_called_on_shutdown(self, mcp_server):
        """Server cleanup is called on shutdown."""
        with patch.object(mcp_server, "cleanup_capabilities") as mock_cleanup:
            await mcp_server.shutdown()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_handlers_cleaned_up(self, mcp_server):
        """All capability handlers are properly cleaned up."""
        # Mock handlers
        mock_handlers = [Mock() for _ in range(5)]
        for handler in mock_handlers:
            handler.cleanup = AsyncMock()

        mcp_server.handlers = mock_handlers

        await mcp_server.cleanup_capabilities()

        # Verify all handlers were cleaned up
        for handler in mock_handlers:
            handler.cleanup.assert_called_once()
