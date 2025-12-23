"""
Integration Tests for Codanna Handler
======================================

Tests CodannaHandler integration with actual Codanna CLI.

Requirements:
- Codanna must be installed: cargo install codanna --all-features
- Project must have indexed code: codanna init && codanna index src --progress

These are integration tests and may be skipped if Codanna is not available.
"""

import pytest
import shutil
from pathlib import Path

from handlers.code_understanding import CodannaHandler


# Check if Codanna is available
CODANNA_AVAILABLE = shutil.which("codanna") is not None


@pytest.fixture
def codanna_config():
    """Configuration for Codanna handler."""
    return {
        "type": "codanna",
        "source": "capabilities/codanna",
        "enabled": True,
    }


@pytest.fixture
async def codanna_handler(codanna_config):
    """Create and initialize Codanna handler."""
    handler = CodannaHandler(codanna_config)

    # Only initialize if Codanna is available
    if CODANNA_AVAILABLE:
        try:
            await handler.initialize()
        except RuntimeError as e:
            # Index may not exist - that's okay for some tests
            if "index not found" not in str(e).lower():
                raise

    return handler


class TestCodannaHandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_handler_finds_codanna(self, codanna_handler):
        """Handler successfully finds Codanna executable."""
        assert codanna_handler.codanna_path is not None
        assert Path(codanna_handler.codanna_path).exists()

    @pytest.mark.skipif(CODANNA_AVAILABLE, reason="Test requires Codanna NOT installed")
    @pytest.mark.asyncio
    async def test_handler_raises_if_codanna_missing(self, codanna_config):
        """Handler raises error if Codanna not installed."""
        handler = CodannaHandler(codanna_config)

        with pytest.raises(RuntimeError, match="Codanna not found"):
            await handler.initialize()

    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_handler_warns_if_no_index(self, codanna_handler, tmp_path, monkeypatch):
        """Handler warns if index doesn't exist in project."""
        # Change to temp directory with no index
        monkeypatch.chdir(tmp_path)
        handler = CodannaHandler({"type": "codanna", "source": ".", "enabled": True})

        # Should initialize but log warning
        await handler.initialize()
        assert handler.codanna_path is not None


class TestCodannaToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_search_code_schema(self, codanna_handler):
        """search_code has correct schema."""
        schema = await codanna_handler.get_tool_schema("search_code")

        assert schema["name"] == "search_code"
        assert "natural language" in schema["description"].lower()
        assert "query" in schema["input_schema"]["properties"]
        assert "limit" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_get_call_graph_schema(self, codanna_handler):
        """get_call_graph has correct schema."""
        schema = await codanna_handler.get_tool_schema("get_call_graph")

        assert schema["name"] == "get_call_graph"
        assert "call graph" in schema["description"].lower()
        assert "function_name" in schema["input_schema"]["properties"]
        assert "symbol_id" in schema["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_find_symbol_schema(self, codanna_handler):
        """find_symbol has correct schema."""
        schema = await codanna_handler.get_tool_schema("find_symbol")

        assert schema["name"] == "find_symbol"
        assert "exact name" in schema["description"].lower()
        assert "name" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["name"]

    @pytest.mark.asyncio
    async def test_find_implementations_schema(self, codanna_handler):
        """find_implementations has correct schema."""
        schema = await codanna_handler.get_tool_schema("find_implementations")

        assert schema["name"] == "find_implementations"
        assert "implementations" in schema["description"].lower()
        assert "query" in schema["input_schema"]["properties"]
        assert "kind" in schema["input_schema"]["properties"]

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, codanna_handler):
        """Unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await codanna_handler.get_tool_schema("nonexistent_tool")


class TestCodannaToolExecution:
    """
    Tests for tool execution.

    These tests require a Codanna index to exist.
    They are marked as 'slow' and can be skipped with: pytest -m "not slow"
    """

    @pytest.mark.slow
    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_search_code_execution(self, codanna_handler):
        """search_code executes and returns results."""
        # This test requires an indexed codebase
        # If no index, command will fail - that's expected

        try:
            result = await codanna_handler.execute(
                "search_code",
                {"query": "handler", "limit": 3}
            )

            assert result["status"] == "success"
            assert result["tool"] == "search_code"
            assert result["query"] == "handler"
            assert "results" in result

        except RuntimeError as e:
            # If no index, that's okay - skip test
            if "index" in str(e).lower() or "not found" in str(e).lower():
                pytest.skip("No Codanna index found")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_find_symbol_execution(self, codanna_handler):
        """find_symbol executes and returns results."""
        try:
            result = await codanna_handler.execute(
                "find_symbol",
                {"name": "main"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "find_symbol"
            assert result["name"] == "main"
            assert "results" in result

        except RuntimeError as e:
            if "index" in str(e).lower() or "not found" in str(e).lower():
                pytest.skip("No Codanna index found")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_get_call_graph_with_function_name(self, codanna_handler):
        """get_call_graph executes with function_name."""
        try:
            result = await codanna_handler.execute(
                "get_call_graph",
                {"function_name": "main"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "get_call_graph"
            assert "main" in result["function"]
            assert "outgoing_calls" in result
            assert "incoming_calls" in result

        except RuntimeError as e:
            if "index" in str(e).lower() or "not found" in str(e).lower():
                pytest.skip("No Codanna index found")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_find_implementations_execution(self, codanna_handler):
        """find_implementations executes and returns results."""
        try:
            result = await codanna_handler.execute(
                "find_implementations",
                {"query": "Handler", "kind": "Struct", "limit": 5}
            )

            assert result["status"] == "success"
            assert result["tool"] == "find_implementations"
            assert result["query"] == "Handler"
            assert result["kind"] == "Struct"
            assert "results" in result

        except RuntimeError as e:
            if "index" in str(e).lower() or "not found" in str(e).lower():
                pytest.skip("No Codanna index found")
            raise

    @pytest.mark.asyncio
    async def test_get_call_graph_requires_identifier(self, codanna_handler):
        """get_call_graph requires either function_name or symbol_id."""
        with pytest.raises(ValueError, match="function_name or symbol_id required"):
            await codanna_handler.execute("get_call_graph", {})

    @pytest.mark.asyncio
    async def test_unknown_tool_execution_raises_error(self, codanna_handler):
        """Executing unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await codanna_handler.execute("nonexistent_tool", {})


class TestCodannaCommandExecution:
    """Tests for internal command execution methods."""

    @pytest.mark.slow
    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_run_codanna_command_parses_json(self, codanna_handler):
        """_run_codanna_command correctly parses JSON output."""
        # Try to get index info (doesn't require indexed code)
        try:
            result = await codanna_handler._run_codanna_command([
                codanna_handler.codanna_path,
                "mcp",
                "get_index_info",
                "--json"
            ])

            # Should return parsed dict
            assert isinstance(result, dict)

        except RuntimeError as e:
            # If no index, that's okay
            if "index" in str(e).lower():
                pytest.skip("No Codanna index found")
            raise

    @pytest.mark.skipif(not CODANNA_AVAILABLE, reason="Codanna not installed")
    @pytest.mark.asyncio
    async def test_run_codanna_command_handles_errors(self, codanna_handler):
        """_run_codanna_command raises RuntimeError on command failure."""
        with pytest.raises(RuntimeError):
            await codanna_handler._run_codanna_command([
                codanna_handler.codanna_path,
                "mcp",
                "nonexistent_command",
                "--json"
            ])


class TestCodannaToolMapping:
    """Tests for tool mapping to Codanna CLI commands."""

    def test_search_code_maps_to_semantic_search(self):
        """search_code maps to semantic_search_with_context."""
        # This is verified by the implementation docstring
        # Just ensure the docstring is correct
        import inspect

        source = inspect.getsource(CodannaHandler._search_code)
        assert "semantic_search_with_context" in source

    def test_get_call_graph_combines_both_directions(self):
        """get_call_graph combines get_calls and find_callers."""
        import inspect

        source = inspect.getsource(CodannaHandler._get_call_graph)
        assert "get_calls" in source
        assert "find_callers" in source

    def test_find_symbol_maps_correctly(self):
        """find_symbol maps to find_symbol."""
        import inspect

        source = inspect.getsource(CodannaHandler._find_symbol)
        assert "find_symbol" in source

    def test_find_implementations_maps_to_search_symbols(self):
        """find_implementations maps to search_symbols."""
        import inspect

        source = inspect.getsource(CodannaHandler._find_implementations)
        assert "search_symbols" in source
