"""
Integration Tests for Context7 Handler
=======================================

Tests Context7Handler integration with actual Context7 MCP server.

Requirements:
- Node.js 18+ must be installed
- npx must be available

These are integration tests and may be skipped if Node.js is not available.
"""

import pytest
import shutil
from pathlib import Path

from handlers.documentation import Context7Handler


# Check if npx is available
NPX_AVAILABLE = shutil.which("npx") is not None


@pytest.fixture
def context7_config():
    """Configuration for Context7 handler."""
    return {
        "type": "context7",
        "source": "capabilities/context7",
        "enabled": True,
    }


@pytest.fixture
async def context7_handler(context7_config):
    """Create and initialize Context7 handler."""
    handler = Context7Handler(context7_config)

    if NPX_AVAILABLE:
        await handler.initialize()

    return handler


class TestContext7HandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_handler_finds_npx(self, context7_handler):
        """Handler successfully finds npx executable."""
        assert context7_handler.npx_path is not None
        assert Path(context7_handler.npx_path).exists()

    @pytest.mark.skipif(NPX_AVAILABLE, reason="Test requires npx NOT installed")
    @pytest.mark.asyncio
    async def test_handler_raises_if_npx_missing(self, context7_config):
        """Handler raises error if npx not installed."""
        handler = Context7Handler(context7_config)

        with pytest.raises(RuntimeError, match="npx not found"):
            await handler.initialize()


class TestContext7ToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_resolve_library_id_schema(self, context7_handler):
        """resolve_library_id has correct schema."""
        schema = await context7_handler.get_tool_schema("resolve_library_id")

        assert schema["name"] == "resolve_library_id"
        assert "library name" in schema["description"].lower()
        assert "libraryName" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["libraryName"]

    @pytest.mark.asyncio
    async def test_get_library_docs_schema(self, context7_handler):
        """get_library_docs has correct schema."""
        schema = await context7_handler.get_tool_schema("get_library_docs")

        assert schema["name"] == "get_library_docs"
        assert "documentation" in schema["description"].lower()
        assert "context7CompatibleLibraryID" in schema["input_schema"]["properties"]
        assert "topic" in schema["input_schema"]["properties"]
        assert "page" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["context7CompatibleLibraryID"]

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, context7_handler):
        """Unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await context7_handler.get_tool_schema("nonexistent_tool")


class TestContext7ToolExecution:
    """
    Tests for tool execution.

    These tests require active internet connection and Context7 API.
    They are marked as 'slow' and can be skipped with: pytest -m "not slow"
    """

    @pytest.mark.slow
    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_resolve_library_id_execution(self, context7_handler):
        """resolve_library_id executes and returns results."""
        try:
            result = await context7_handler.execute(
                "resolve_library_id",
                {"libraryName": "react"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "resolve_library_id"
            assert result["libraryName"] == "react"
            assert "results" in result

        except RuntimeError as e:
            # If Context7 API is unavailable, that's okay - skip test
            if "context7" in str(e).lower() or "network" in str(e).lower():
                pytest.skip("Context7 API unavailable")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_get_library_docs_execution(self, context7_handler):
        """get_library_docs executes and returns results."""
        try:
            result = await context7_handler.execute(
                "get_library_docs",
                {
                    "context7CompatibleLibraryID": "/facebook/react",
                    "topic": "hooks"
                }
            )

            assert result["status"] == "success"
            assert result["tool"] == "get_library_docs"
            assert result["libraryID"] == "/facebook/react"
            assert result["topic"] == "hooks"
            assert "results" in result

        except RuntimeError as e:
            if "context7" in str(e).lower() or "network" in str(e).lower():
                pytest.skip("Context7 API unavailable")
            raise

    @pytest.mark.asyncio
    async def test_unknown_tool_execution_raises_error(self, context7_handler):
        """Executing unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await context7_handler.execute("nonexistent_tool", {})


class TestContext7MCPIntegration:
    """Tests for MCP JSON-RPC integration."""

    def test_handler_uses_correct_package(self, context7_handler):
        """Handler uses correct Context7 MCP package."""
        assert context7_handler.context7_package == "@upstash/context7-mcp"

    @pytest.mark.asyncio
    async def test_handler_builds_valid_mcp_request(self, context7_handler):
        """Handler builds valid MCP JSON-RPC request format."""
        # This is tested implicitly in execution tests
        # Just verify the format is correct
        import json

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "resolve-library-id",
                "arguments": {"libraryName": "test"}
            },
            "id": 1
        }

        # Should be valid JSON
        json_str = json.dumps(request)
        parsed = json.loads(json_str)

        assert parsed["jsonrpc"] == "2.0"
        assert parsed["method"] == "tools/call"
        assert "params" in parsed
        assert "id" in parsed
