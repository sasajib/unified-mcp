"""
Integration Tests for Graphiti Handler
=======================================

Tests GraphitiHandler integration with Graphiti + LadybugDB.

Requirements:
- Python 3.12+ (for Graphiti)
- real_ladybug package installed
- graphiti_core package installed
- OpenAI API key (for embeddings/LLM)

These are integration tests and may be skipped if dependencies are not available.
"""

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from handlers.knowledge_graph import GraphitiHandler

# Check if required packages are available
try:
    import graphiti_core
    import real_ladybug as lb

    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False

# Check if OpenAI API key is set
OPENAI_API_KEY_SET = os.getenv("OPENAI_API_KEY") is not None


@pytest.fixture
def graphiti_config():
    """Configuration for Graphiti handler with temporary database."""
    with TemporaryDirectory() as tmpdir:
        yield {
            "type": "graphiti_ladybug",
            "source": tmpdir,
            "enabled": True,
        }


@pytest.fixture
async def graphiti_handler(graphiti_config):
    """Create and initialize Graphiti handler."""
    handler = GraphitiHandler(graphiti_config)

    if GRAPHITI_AVAILABLE and OPENAI_API_KEY_SET:
        await handler.initialize()

    yield handler

    # Cleanup
    if handler.graphiti:
        await handler.cleanup()


class TestGraphitiHandlerInitialization:
    """Tests for handler initialization."""

    @pytest.mark.skipif(
        not GRAPHITI_AVAILABLE, reason="Graphiti/LadybugDB not installed"
    )
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_handler_initializes_successfully(self, graphiti_handler):
        """Handler successfully initializes with LadybugDB."""
        assert graphiti_handler.graphiti is not None
        assert graphiti_handler.db_path is not None
        assert Path(graphiti_handler.db_path).parent.exists()

    @pytest.mark.skipif(
        GRAPHITI_AVAILABLE, reason="Test requires Graphiti NOT installed"
    )
    @pytest.mark.asyncio
    async def test_handler_raises_if_graphiti_missing(self, graphiti_config):
        """Handler raises error if Graphiti not installed."""
        with pytest.raises(ImportError, match="real_ladybug is required"):
            handler = GraphitiHandler(graphiti_config)
            await handler.initialize()


class TestGraphitiToolSchemas:
    """Tests for tool schema definitions."""

    @pytest.mark.asyncio
    async def test_store_insight_schema(self, graphiti_handler):
        """store_insight has correct schema."""
        schema = await graphiti_handler.get_tool_schema("store_insight")

        assert schema["name"] == "store_insight"
        assert "insight" in schema["description"].lower()
        assert "content" in schema["input_schema"]["properties"]
        assert "source" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["content"]

    @pytest.mark.asyncio
    async def test_search_insights_schema(self, graphiti_handler):
        """search_insights has correct schema."""
        schema = await graphiti_handler.get_tool_schema("search_insights")

        assert schema["name"] == "search_insights"
        assert "search" in schema["description"].lower()
        assert "query" in schema["input_schema"]["properties"]
        assert "limit" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_query_graph_schema(self, graphiti_handler):
        """query_graph has correct schema."""
        schema = await graphiti_handler.get_tool_schema("query_graph")

        assert schema["name"] == "query_graph"
        assert "cypher" in schema["description"].lower()
        assert "cypher_query" in schema["input_schema"]["properties"]
        assert "params" in schema["input_schema"]["properties"]
        assert schema["input_schema"]["required"] == ["cypher_query"]

    @pytest.mark.asyncio
    async def test_add_episode_schema(self, graphiti_handler):
        """add_episode has correct schema."""
        schema = await graphiti_handler.get_tool_schema("add_episode")

        assert schema["name"] == "add_episode"
        assert "episode" in schema["description"].lower()
        assert "name" in schema["input_schema"]["properties"]
        assert "content" in schema["input_schema"]["properties"]
        assert "source_description" in schema["input_schema"]["properties"]
        assert set(schema["input_schema"]["required"]) == {"name", "content"}

    @pytest.mark.asyncio
    async def test_unknown_tool_raises_error(self, graphiti_handler):
        """Unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await graphiti_handler.get_tool_schema("nonexistent_tool")


class TestGraphitiToolExecution:
    """
    Tests for tool execution.

    These tests require Graphiti, LadybugDB, and OpenAI API key.
    They are marked as 'slow' and can be skipped with: pytest -m "not slow"
    """

    @pytest.mark.slow
    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_store_insight_execution(self, graphiti_handler):
        """store_insight executes and stores knowledge."""
        try:
            result = await graphiti_handler.execute(
                "store_insight",
                {
                    "content": "The unified-mcp project uses progressive discovery to reduce token usage.",
                    "source": "test case",
                },
            )

            assert result["status"] == "success"
            assert result["tool"] == "store_insight"
            assert "message" in result
            assert (
                result["content"]
                == "The unified-mcp project uses progressive discovery to reduce token usage."
            )

        except Exception as e:
            # If Graphiti/OpenAI fails, skip test
            if "openai" in str(e).lower() or "api" in str(e).lower():
                pytest.skip("OpenAI API unavailable or error")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_add_episode_execution(self, graphiti_handler):
        """add_episode executes and stores episode."""
        try:
            result = await graphiti_handler.execute(
                "add_episode",
                {
                    "name": "Test Episode",
                    "content": "This is a test conversation about implementing MCP servers.",
                    "source_description": "test conversation",
                },
            )

            assert result["status"] == "success"
            assert result["tool"] == "add_episode"
            assert "episode_uuid" in result
            assert result["name"] == "Test Episode"

        except Exception as e:
            if "openai" in str(e).lower() or "api" in str(e).lower():
                pytest.skip("OpenAI API unavailable or error")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_search_insights_execution(self, graphiti_handler):
        """search_insights executes and returns results."""
        try:
            # First add some data
            await graphiti_handler.execute(
                "store_insight", {"content": "Python is a programming language"}
            )

            # Then search
            result = await graphiti_handler.execute(
                "search_insights", {"query": "programming language", "limit": 5}
            )

            assert result["status"] == "success"
            assert result["tool"] == "search_insights"
            assert result["query"] == "programming language"
            assert "results" in result
            assert "count" in result
            assert isinstance(result["results"], dict)

        except Exception as e:
            if "openai" in str(e).lower() or "api" in str(e).lower():
                pytest.skip("OpenAI API unavailable or error")
            raise

    @pytest.mark.slow
    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_query_graph_execution(self, graphiti_handler):
        """query_graph executes Cypher query."""
        try:
            # Simple query to list all nodes
            result = await graphiti_handler.execute(
                "query_graph", {"cypher_query": "MATCH (n) RETURN n LIMIT 10"}
            )

            assert result["status"] == "success"
            assert result["tool"] == "query_graph"
            assert "results" in result
            assert "count" in result
            assert isinstance(result["results"], list)

        except Exception as e:
            if "openai" in str(e).lower() or "api" in str(e).lower():
                pytest.skip("OpenAI API unavailable or error")
            raise

    @pytest.mark.asyncio
    async def test_unknown_tool_execution_raises_error(self, graphiti_handler):
        """Executing unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await graphiti_handler.execute("nonexistent_tool", {})


class TestGraphitiLadybugDBIntegration:
    """Tests for Graphiti + LadybugDB integration."""

    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    def test_handler_uses_ladybugdb(self, graphiti_handler):
        """Handler uses LadybugDB as graph backend."""
        # The handler should create a database path
        assert hasattr(graphiti_handler, "db_path")

    @pytest.mark.asyncio
    async def test_cleanup_method_exists(self, graphiti_handler):
        """Handler has cleanup method for resource management."""
        assert hasattr(graphiti_handler, "cleanup")
        assert callable(graphiti_handler.cleanup)

    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    @pytest.mark.skipif(not OPENAI_API_KEY_SET, reason="OpenAI API key not set")
    @pytest.mark.asyncio
    async def test_database_file_created(self, graphiti_handler):
        """Database file is created on initialization."""
        # Check if database directory exists
        assert graphiti_handler.db_path is not None
        db_dir = Path(graphiti_handler.db_path).parent
        assert db_dir.exists()


class TestLadybugDriver:
    """Tests for custom LadybugDriver implementation."""

    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    def test_driver_imports_successfully(self):
        """LadybugDriver can be imported."""
        from handlers.knowledge_graph import LadybugDriver

        assert LadybugDriver is not None

    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    def test_driver_session_imports_successfully(self):
        """LadybugDriverSession can be imported."""
        from handlers.knowledge_graph import LadybugDriverSession

        assert LadybugDriverSession is not None

    @pytest.mark.skipif(not GRAPHITI_AVAILABLE, reason="Graphiti not installed")
    def test_driver_has_required_methods(self):
        """LadybugDriver implements required GraphDriver methods."""
        from handlers.knowledge_graph import LadybugDriver

        required_methods = [
            "execute_query",
            "session",
            "close",
            "delete_all_indexes",
            "build_indices_and_constraints",
        ]

        for method in required_methods:
            assert hasattr(LadybugDriver, method)
