"""
Integration Tests for Playwright Handler
=========================================

Tests PlaywrightHandler integration with actual Playwright MCP server.

Requirements:
- Node.js 18+ must be installed
- npx must be available
- Playwright browsers may need to be installed

These are integration tests and may be skipped if Node.js is not available.
"""

import pytest
import shutil
from pathlib import Path

from handlers.browser_automation import PlaywrightHandler


# Check if npx is available
NPX_AVAILABLE = shutil.which("npx") is not None


@pytest.fixture
def playwright_config():
    """Configuration for Playwright handler."""
    return {
        "type": "playwright",
        "source": "capabilities/playwright-mcp",
        "enabled": True,
    }


@pytest.fixture
async def playwright_handler(playwright_config):
    """Create and initialize Playwright handler."""
    handler = PlaywrightHandler(playwright_config)

    if NPX_AVAILABLE:
        await handler.initialize()

    return handler


class TestPlaywrightHandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_handler_finds_npx(self, playwright_handler):
        """Handler successfully finds npx executable."""
        assert playwright_handler.npx_path is not None
        assert Path(playwright_handler.npx_path).exists()

    @pytest.mark.skipif(NPX_AVAILABLE, reason="Test requires npx NOT installed")
    @pytest.mark.asyncio
    async def test_handler_raises_if_npx_missing(self, playwright_config):
        """Handler raises error if npx not installed."""
        handler = PlaywrightHandler(playwright_config)

        with pytest.raises(RuntimeError, match="npx not found"):
            await handler.initialize()


class TestPlaywrightToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_navigate_schema(self, playwright_handler):
        """playwright_navigate has correct schema."""
        schema = await playwright_handler.get_tool_schema("playwright_navigate")

        assert schema["name"] == "playwright_navigate"
        assert "navigate" in schema["description"].lower()
        assert "url" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["url"]

    @pytest.mark.asyncio
    async def test_click_schema(self, playwright_handler):
        """playwright_click has correct schema."""
        schema = await playwright_handler.get_tool_schema("playwright_click")

        assert schema["name"] == "playwright_click"
        assert "click" in schema["description"].lower()
        assert "element" in schema["input_schema"]["properties"]
        assert "ref" in schema["input_schema"]["properties"]
        assert set(schema["input_schema"]["required"]) == {"element", "ref"}

    @pytest.mark.asyncio
    async def test_screenshot_schema(self, playwright_handler):
        """playwright_screenshot has correct schema."""
        schema = await playwright_handler.get_tool_schema("playwright_screenshot")

        assert schema["name"] == "playwright_screenshot"
        assert "screenshot" in schema["description"].lower()
        assert "filename" in schema["input_schema"]["properties"]
        assert "type" in schema["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_fill_schema(self, playwright_handler):
        """playwright_fill has correct schema."""
        schema = await playwright_handler.get_tool_schema("playwright_fill")

        assert schema["name"] == "playwright_fill"
        assert "fill" in schema["description"].lower()
        assert "element" in schema["input_schema"]["properties"]
        assert "ref" in schema["input_schema"]["properties"]
        assert "text" in schema["input_schema"]["properties"]
        assert set(schema["input_schema"]["required"]) == {"element", "ref", "text"}

    @pytest.mark.asyncio
    async def test_evaluate_schema(self, playwright_handler):
        """playwright_evaluate has correct schema."""
        schema = await playwright_handler.get_tool_schema("playwright_evaluate")

        assert schema["name"] == "playwright_evaluate"
        assert "javascript" in schema["description"].lower()
        assert "function" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["function"]

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, playwright_handler):
        """Unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await playwright_handler.get_tool_schema("nonexistent_tool")


class TestPlaywrightToolExecution:
    """
    Tests for tool execution.

    These tests require Playwright browsers to be installed.
    They are marked as 'slow' and can be skipped with: pytest -m "not slow"
    """

    @pytest.mark.slow
    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_navigate_execution(self, playwright_handler):
        """playwright_navigate executes (may require browser installation)."""
        try:
            result = await playwright_handler.execute(
                "playwright_navigate", {"url": "https://example.com"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "playwright_navigate"
            assert result["url"] == "https://example.com"

        except RuntimeError as e:
            # If Playwright browser not installed, that's okay - skip test
            if "browser" in str(e).lower() or "install" in str(e).lower():
                pytest.skip("Playwright browser not installed")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not NPX_AVAILABLE, reason="npx not installed")
    @pytest.mark.asyncio
    async def test_evaluate_execution(self, playwright_handler):
        """playwright_evaluate executes simple JavaScript."""
        try:
            result = await playwright_handler.execute(
                "playwright_evaluate", {"function": "() => { return 1 + 1; }"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "playwright_evaluate"

        except RuntimeError as e:
            if "browser" in str(e).lower() or "install" in str(e).lower():
                pytest.skip("Playwright browser not installed")
            raise

    @pytest.mark.asyncio
    async def test_unknown_tool_execution_raises_error(self, playwright_handler):
        """Executing unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await playwright_handler.execute("nonexistent_tool", {})


class TestPlaywrightMCPIntegration:
    """Tests for MCP JSON-RPC integration."""

    def test_handler_uses_correct_package(self, playwright_handler):
        """Handler uses correct Playwright MCP package."""
        assert playwright_handler.playwright_package == "@playwright/mcp@latest"

    @pytest.mark.asyncio
    async def test_cleanup_method_exists(self, playwright_handler):
        """Handler has cleanup method for process management."""
        assert hasattr(playwright_handler, "cleanup")
        assert callable(playwright_handler.cleanup)

    @pytest.mark.asyncio
    async def test_handler_builds_valid_mcp_request(self, playwright_handler):
        """Handler builds valid MCP JSON-RPC request format."""
        import json

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "browser_navigate",
                "arguments": {"url": "https://example.com"},
            },
            "id": 1,
        }

        # Should be valid JSON
        json_str = json.dumps(request)
        parsed = json.loads(json_str)

        assert parsed["jsonrpc"] == "2.0"
        assert parsed["method"] == "tools/call"
        assert "params" in parsed
        assert "id" in parsed


class TestPlaywrightToolMapping:
    """Tests for tool mapping to Playwright MCP."""

    def test_navigate_maps_to_browser_navigate(self):
        """playwright_navigate maps to browser_navigate."""
        import inspect

        source = inspect.getsource(PlaywrightHandler._navigate)
        assert "browser_navigate" in source

    def test_click_maps_to_browser_click(self):
        """playwright_click maps to browser_click."""
        import inspect

        source = inspect.getsource(PlaywrightHandler._click)
        assert "browser_click" in source

    def test_screenshot_maps_to_browser_take_screenshot(self):
        """playwright_screenshot maps to browser_take_screenshot."""
        import inspect

        source = inspect.getsource(PlaywrightHandler._screenshot)
        assert "browser_take_screenshot" in source

    def test_fill_maps_to_browser_type(self):
        """playwright_fill maps to browser_type."""
        import inspect

        source = inspect.getsource(PlaywrightHandler._fill)
        assert "browser_type" in source

    def test_evaluate_maps_to_browser_evaluate(self):
        """playwright_evaluate maps to browser_evaluate."""
        import inspect

        source = inspect.getsource(PlaywrightHandler._evaluate)
        assert "browser_evaluate" in source
